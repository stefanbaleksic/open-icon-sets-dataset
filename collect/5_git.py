"""Repository facts from git history (read-only, blobless clones, cut-off CUTOFF).
Commit dates are the committer dates; each commit is assigned to its UTC calendar day.
Writes work/git.json keyed by repo_url and, for package folders, by 'repo_url#package_dir'."""
import csv, json, os, re, subprocess, collections, statistics
from datetime import datetime, timedelta, timezone
from common import WORK, SEED, CUTOFF, CUTOFF_ISO

CLONES = os.path.join(WORK, 'clones'); os.makedirs(CLONES, exist_ok=True)
from common import SEMVER
seed = list(csv.DictReader(open(os.path.join(SEED, 'identity_seed.csv'), encoding='utf-8')))
repos = {}
for r in seed:
    if r['repo_url']:
        repos.setdefault(r['repo_url'], set()).add(r['repo_package_dir'])

def git(path, *args):
    return subprocess.run(['git', '-C', path, *args], capture_output=True, text=True).stdout

def utc(ts):
    return datetime.fromisoformat(ts).astimezone(timezone.utc)

def clone(url):
    slug = re.sub(r'[^A-Za-z0-9_.-]+', '_', url.replace('https://', ''))
    path = os.path.join(CLONES, slug)
    if not os.path.isdir(path):
        r = subprocess.run(['git', 'clone', '-q', '--filter=blob:none', '--no-checkout', url, path], capture_output=True, text=True, timeout=900)
        if r.returncode != 0: return None
    return path

def default_head(path):
    ref = git(path, 'symbolic-ref', '--short', 'refs/remotes/origin/HEAD').strip()
    return ref.replace('origin/', '') if ref else 'main', (ref or 'origin/main')

def facts(path, ref, pkgdir=None):
    args = ['--before', CUTOFF_ISO]
    path_args = ['--', pkgdir] if pkgdir else []
    last = git(path, 'log', ref, *args, '-1', '--format=%H|%cI', *path_args).strip()
    if not last: return {'commits_total': 0}
    sha, cts = last.split('|')
    days = sorted(git(path, 'log', ref, *args, '--format=%cI', *path_args).split())
    first = utc(days[0]).strftime('%Y-%m-%d')
    lastday = utc(cts).strftime('%Y-%m-%d')
    since = (CUTOFF - timedelta(days=365)).strftime('%Y-%m-%dT%H:%M:%SZ')
    # Authors are distinct e-mail addresses; accounts whose name ends in [bot] are not counted.
    y = [l.split('|')[1] for l in git(path, 'log', ref, *args, '--since', since, '--format=%an|%ae', *path_args).splitlines()
         if l.count('|') == 1 and not l.split('|')[0].endswith('[bot]')]
    all_auth = [l.split('|')[1] for l in git(path, 'log', ref, *args, '--format=%an|%ae', *path_args).splitlines()
                if l.count('|') == 1 and not l.split('|')[0].endswith('[bot]')]
    top = collections.Counter(y).most_common(1)
    return {
        'sha': sha, 'last_date': lastday, 'first_date': first,
        'days_since_last': (CUTOFF.date() - utc(cts).date()).days,
        'commits_total': len(days), 'commits_365d': len(git(path, 'log', ref, *args, '--since', since, '--format=%H', *path_args).split()),
        'authors_total': len(set(all_auth)), 'authors_365d': len(set(y)),
        'top_author_share_365d': round(top[0][1] / len(y), 4) if y else None,
    }

def repo_facts(url, pkgdirs):
    path = clone(url)
    if path is None: return {'status': 'not_readable'}, {}
    ref, full = default_head(path)
    if not git(path, 'rev-parse', '--verify', '-q', full).strip():
        return {'status': 'no_head'}, {}
    out = {'status': 'ok', 'default_branch': ref, **facts(path, full)}
    tree = git(path, 'ls-tree', '-r', '--name-only', full).split('\n')
    tree = [t for t in tree if t]
    lower = [t.lower() for t in tree]
    out['files_total'] = len(tree)
    out['svg_files'] = sum(1 for t in lower if t.endswith('.svg'))
    out['has_readme'] = any(re.match(r'^(readme)(\.[a-z]+)?$', os.path.basename(t)) for t in lower)
    # Document rules (see RULES.md): a changelog-type file at the root (CHANGELOG, CHANGES, HISTORY, RELEASES, NEWS); contributing and security policy at the root,
    # in .github/ or in docs/ (GitHub reads these places); CI from the usual CI systems.
    root = lambda pat: any(re.match(pat, t) for t in lower)
    place = lambda name: any(re.match(r'^(|\.github/|docs/)' + name + r'(\.[a-z]+)?$', t) for t in lower)
    out['has_changelog'] = root(r'^(changelog|changes|history|releases|news)([._-][a-z0-9-]+)*(\.[a-z]+)?$')
    out['has_contributing'] = place('contributing')
    out['has_security_policy'] = place('security')
    out['has_ci'] = any(t.startswith('.github/workflows/') or t in ('.travis.yml', '.gitlab-ci.yml', 'azure-pipelines.yml')
                        or t.startswith('.circleci/') for t in lower)
    out['has_icon_font'] = any(t.endswith(('.woff', '.woff2', '.ttf', '.otf', '.eot')) for t in lower)
    # Design files count at the repository root or inside a package folder of this set.
    mains = tuple(d.lower() + '/' for d in pkgdirs if d)
    out['has_design_files'] = any(t.endswith(('.fig', '.sketch', '.afdesign', '.figma', '.xd', '.psd', '.ai')) and ('/' not in t or (mains and t.startswith(mains))) for t in lower)
    tags = git(path, 'for-each-ref', 'refs/tags', '--format=%(refname:short)|%(*committerdate:iso-strict)|%(committerdate:iso-strict)')
    sem = []
    for line in tags.splitlines():
        name, d1, d2 = (line.split('|') + ['', ''])[:3]
        m = SEMVER.match(name)
        ts = d1 or d2
        if m and ts and utc(ts) <= CUTOFF:
            sem.append(((int(m[1]), int(m[2]), int(m[3])), name, utc(ts).strftime('%Y-%m-%d')))
    sem.sort()
    out['semver_tags'] = len(sem)
    out['latest_semver_tag'] = sem[-1][1] if sem else None
    out['latest_semver_tag_date'] = sem[-1][2] if sem else None
    pk = {}
    for d in pkgdirs:
        if d:
            pk[d] = facts(path, full, d)
    return out, pk

out_repos, out_pkgs = {}, {}
for i, (url, dirs) in enumerate(sorted(repos.items()), 1):
    try:
        f, pk = repo_facts(url, dirs)
    except subprocess.TimeoutExpired:
        f, pk = {'status': 'timeout'}, {}
    out_repos[url] = f
    for d, v in pk.items(): out_pkgs[f'{url}#{d}'] = v
    print(f'{i}/{len(repos)} {url} {f.get("status")}', flush=True)
json.dump({'repos': out_repos, 'packages': out_pkgs}, open(os.path.join(WORK, 'git.json'), 'w'), indent=1)
print('git facts written')
