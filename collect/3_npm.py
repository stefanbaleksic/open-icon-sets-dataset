"""npm registry (packuments), npm download counts and the Iconify icon packages.
Writes work/npm.json: one entry per package name, with everything measured up to CUTOFF."""
import csv, io, json, os, re, statistics, tarfile, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta
from common import get_json, q, WORK, SEED, CUTOFF, DL30, DL30_PREV, DL365, utc_day, USER_AGENT

MAX_TARBALL = 150 * 1024 * 1024  # larger packages are not opened (recorded as blank)

STABLE = re.compile(r'^\d+\.\d+\.\d+$')
seed = list(csv.DictReader(open(os.path.join(SEED, 'identity_seed.csv'), encoding='utf-8')))
names = set()
for r in seed:
    if r['npm_package']: names.add(r['npm_package'])
    if r['iconify_package']: names.add(r['iconify_package'])

def downloads(pkg, span):
    d = get_json(f'https://api.npmjs.org/downloads/point/{span[0]}:{span[1]}/{pkg}')
    return d.get('downloads') if d else None

def packument(pkg):
    doc = get_json(f'https://registry.npmjs.org/{q(pkg)}')
    if doc is None: return None
    t = doc.get('time', {})
    before = {v: ts for v, ts in t.items() if v not in ('created', 'modified') and datetime.fromisoformat(ts.replace('Z', '+00:00')) <= CUTOFF}
    latest = (doc.get('dist-tags') or {}).get('latest')
    # the tag may have moved after the cut-off: use the tagged version only if it existed on the cut-off day,
    # otherwise the newest stable version published by then (the tag history is not available)
    if latest not in before:
        cand = [(ts, v) for v, ts in before.items() if STABLE.match(v)]
        latest = max(cand)[1] if cand else None
    lv = (doc.get('versions') or {}).get(latest, {}) if latest else {}
    dist = lv.get('dist') or {}
    tf_facts = None
    try:
        tf_facts = tarball_facts(dist.get('tarball'), dist.get('unpackedSize'))
    except Exception as e:
        print('tarball not read:', name, e, flush=True)
    stable = sorted((datetime.fromisoformat(ts.replace('Z', '+00:00')), v) for v, ts in before.items() if STABLE.match(v))
    cutoff730 = CUTOFF - timedelta(days=730)
    recent = [d for d, _ in stable if d >= cutoff730]
    gaps = [(b - a).days for a, b in zip(recent, recent[1:])]
    return {
        'npm_latest_version': latest,
        'npm_last_publish': last_publish(t, latest),
        'npm_first_publish': utc_day(t['created']) if 'created' in t else None,
        'npm_versions_total': len(doc.get('versions') or {}),
        'npm_maintainers_n': len(doc.get('maintainers') or []),
        'npm_license_declared': license_text(doc.get('license')),
        'npm_homepage': doc.get('homepage'),
        'npm_dependencies_n': len(lv.get('dependencies') or {}),
        'npm_peer_dependencies_n': len(lv.get('peerDependencies') or {}),
        'npm_unpacked_size_bytes': (lv.get('dist') or {}).get('unpackedSize'),
        'npm_has_types': bool(lv.get('types') or lv.get('typings') or (tf_facts and tf_facts['npm_dts_files'] > 0)),
        'npm_module_type': lv.get('type'),
        'npm_has_exports_map': 'exports' in lv,
        'npm_file_count_registry': dist.get('fileCount'),
        'npm_deprecated': bool(lv.get('deprecated')),
        'npm_provenance': provenance(name, latest) if latest else None,
        **(tf_facts or {}),
        'stable_releases_730d': len(recent),
        'release_gap_median_days': statistics.median(gaps) if len(recent) >= 10 and gaps else None,
    }

def last_publish(t, latest):
    if latest not in t: return None
    ts = datetime.fromisoformat(t[latest].replace('Z', '+00:00'))
    return utc_day(t[latest]) if ts <= CUTOFF else None

def tarball_facts(url, size):
    """File facts of the published tarball, read in memory (nothing is stored)."""
    if not url or (size or 0) > MAX_TARBALL: return None
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    files = svg = svg_all = font = dts = 0; unpacked = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as tf:
        for m in tf.getmembers():
            if not m.isfile(): continue
            n = m.name.lower(); files += 1; unpacked += m.size
            if n.endswith('.svg'):
                svg_all += 1
                if not os.path.basename(n).startswith('sprite'): svg += 1   # sprite sheets are not icons
            dts += n.endswith('.d.ts')
            font += n.endswith(('.woff', '.woff2', '.ttf', '.otf', '.eot'))
    return {'npm_package_files': files, 'npm_package_svg_files': svg, 'npm_svg_all_n': svg_all, 'npm_package_font_files': font,
            'npm_dts_files': dts, 'npm_unpacked_size_measured_bytes': unpacked}

def provenance(name, version):
    """'yes' when npm publishes a provenance attestation for this version."""
    try:
        return get_json(f'https://registry.npmjs.org/-/npm/v1/attestations/{q(name)}@{version}') is not None
    except urllib.error.HTTPError:
        return False

def license_text(lic):
    if isinstance(lic, str): return lic
    if isinstance(lic, dict): return lic.get('type')
    return None

def tarball_members(url, size, wanted, limit):
    """Read the named members of a published tarball (in memory). Returns {name: bytes}."""
    if not url or (size or 0) > limit: return None
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=300) as r:
        data = r.read()
    got = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as tf:
        for m in tf.getmembers():
            base = m.name.split('/', 1)[-1]
            if m.isfile() and base in wanted:
                got[base] = tf.extractfile(m).read()
    return got

def iconify_pkg(pkg):
    """Iconify set as it stood on the cut-off day: the version published by then, read from its tarball
    (info.json = metadata, icons.json = icons and aliases). The live catalogue has moved on since."""
    doc = get_json(f'https://registry.npmjs.org/{q(pkg)}')
    if doc is None: return None
    t = doc.get('time', {})
    before = {v: ts for v, ts in t.items() if v not in ('created', 'modified') and datetime.fromisoformat(ts.replace('Z', '+00:00')) <= CUTOFF}
    latest = (doc.get('dist-tags') or {}).get('latest')
    if latest not in before:
        cand = [(ts, v) for v, ts in before.items() if STABLE.match(v)]
        latest = max(cand)[1] if cand else None
    if not latest: return None
    dist = (doc.get('versions') or {}).get(latest, {}).get('dist') or {}
    files = tarball_members(dist.get('tarball'), dist.get('unpackedSize'), {'info.json', 'icons.json'}, 400 * 1024 * 1024) or {}
    info = json.loads(files['info.json']) if 'info.json' in files else {}
    icons = json.loads(files['icons.json']) if 'icons.json' in files else {}
    lm = icons.get('lastModified')
    return {'iconify_package_version': latest, 'iconify_package_last_publish': utc_day(t[latest]),
            'iconify_info': info,
            'iconify_icons_total_pkg': info.get('total'),   # the set's total (style variants counted separately)
            'iconify_icons_in_file_n': len(icons.get('icons') or {}),
            'iconify_aliases_n': len(icons.get('aliases') or {}),
            'iconify_hidden_n': sum(1 for v in (icons.get('icons') or {}).values() if v.get('hidden')),
            'iconify_last_modified': datetime.fromtimestamp(lm, timezone.utc).strftime('%Y-%m-%d') if lm else None}

out = {}
for i, name in enumerate(sorted(names), 1):
    entry = {}
    if name.startswith('@iconify-json/'):
        entry.update(iconify_pkg(name) or {})
        entry['iconify_downloads_30d'] = downloads(name, DL30)
        entry['iconify_downloads_365d'] = downloads(name, DL365)
    else:
        p = packument(name)
        if p: entry.update(p)
        entry['npm_downloads_30d'] = downloads(name, DL30)
        entry['npm_downloads_prev30d'] = downloads(name, DL30_PREV)
        entry['npm_downloads_365d'] = downloads(name, DL365)
    out[name] = entry
    if i % 25 == 0: print(f'{i}/{len(names)}', flush=True)
json.dump(out, open(os.path.join(WORK, 'npm.json'), 'w'), indent=1)
print(f'npm: {len(out)} packages collected')
