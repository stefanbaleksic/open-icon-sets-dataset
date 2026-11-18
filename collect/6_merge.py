"""Assemble the collected values into the release column layout (same 124 columns, same order).
Cells that these scripts do not measure stay empty (see COVERAGE.md). Writes work/collected.csv."""
import csv, json, os, collections
from datetime import datetime
from common import WORK, SEED, COLLECTION_DAY, CUTOFF, CUTOFF_ISO
REL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'icon_sets_v3.csv')
header = list(csv.DictReader(open(REL, encoding='utf-8')).fieldnames)
seed = list(csv.DictReader(open(os.path.join(SEED, 'identity_seed.csv'), encoding='utf-8')))
iconify = json.load(open(os.path.join(WORK, 'iconify_sets.json'), encoding='utf-8'))
npm = json.load(open(os.path.join(WORK, 'npm.json'), encoding='utf-8'))
web = json.load(open(os.path.join(WORK, 'web.json'), encoding='utf-8'))
git = json.load(open(os.path.join(WORK, 'git.json'), encoding='utf-8'))
import gzip
_ic_path = os.path.join(WORK, 'icon_content.json')
if os.path.exists(_ic_path):
    icon_content = json.load(open(_ic_path, encoding='utf-8'))   # 3c_icon_content.py
else:
    icon_content = json.load(gzip.open(_ic_path + '.gz', 'rt', encoding='utf-8'))   # saved evidence (compressed)
yn = lambda b: '' if b is None else ('yes' if b else 'no')
num = lambda v: '' if v is None else v

repo_count = collections.Counter(r['repo_url'].lower() for r in seed if r['repo_url'])
rows = []
for i, s in enumerate(seed, 1):
    r = {c: '' for c in header}
    sid = s['set_id']; ic = iconify.get(sid) if s['frame'] == 'iconify' else None
    r.update({'id': str(i), 'set_id': sid, 'checked_on': COLLECTION_DAY.isoformat(), 'frame': s['frame']})
    pk = npm.get(s['iconify_package'] or '', {}) if s['iconify_package'] else {}
    info = pk.get('iconify_info') or {}   # the set as it stood on the cut-off day (see 3_npm.py)
    if ic and ic.get('in_frame'):
        lic = info.get('license') or {}
        r.update({'name': info.get('name') or ic['name'],
                  'author': ((info.get('author') or {}).get('name') or ic['author_name'] or ''),
                  'iconify_category': info.get('category') or ic['category'] or '',
                  'iconify_tags': ';'.join(info.get('tags') or ic['tags']),
                  'grid_px': num(info.get('height') or ic['height']),
                  'palette': ('multicolor' if info.get('palette', ic['palette']) else 'monotone') if info.get('palette', ic['palette']) is not None else '',
                  'icons_total': num(pk.get('iconify_icons_total_pkg', info.get('total', ic['total']))),
                  'icons_total_source': 'Iconify set on the cut-off day (npm package of that date; style variants counted separately)',
                  'iconify_license': lic.get('spdx') or ic['license_spdx'] or '',
                  'iconify_license_url': lic.get('url') or ic['license_url'] or '',
                  'sample_icons': ';'.join((info.get('samples') or ic['samples'])[:3]),  # the release shows the first three samples
                  'icons_aliases_n': num(pk.get('iconify_aliases_n')), 'icons_hidden_n': num(pk.get('iconify_hidden_n')),
                  'iconify_categories_n': num(ic.get('categories_n')),
                  'iconify_set_last_modified': pk.get('iconify_last_modified') or ''})
    else:
        r.update({'name': s['name'], 'author': s['author']})
    r.setdefault('iconify_categories_n', 0)  # 0 for sets outside Iconify (as in the release)
    ic_m = icon_content.get(sid) or {}
    ICON_FIELDS = ['icon_viewbox_px', 'icons_own_size_pct', 'icons_currentcolor_pct', 'icons_hardcoded_color_pct', 'icons_gradient_pct',
                   'icons_stroke_based_pct', 'icons_animated_n', 'stroke_width_mode', 'median_icon_bytes', 'mean_icon_bytes',
                   'measured_palette', 'icon_construction', 'remix_name_overlap_pct', 'icons_fingerprinted_n',
                   'icon_overlap_max_pct', 'icon_overlap_with', 'icon_overlap_basis', 'style_variants', 'style_variants_n',
                   'unique_base_names', 'iconify_version']
    for f in ICON_FIELDS:
        v = ic_m.get(f)
        r[f] = '' if v is None else (yn(v) if isinstance(v, bool) else v)
    r['iconify_package'] = s['iconify_package']
    if s['iconify_package'] and s['iconify_package'] in npm:
        e = npm[s['iconify_package']]
        r.update({'iconify_package_version': e.get('iconify_package_version') or '',
                  'iconify_package_last_publish': e.get('iconify_package_last_publish') or '',
                  'iconify_downloads_30d': num(e.get('iconify_downloads_30d')),
                  'iconify_downloads_365d': num(e.get('iconify_downloads_365d'))})
    # npm
    if s['npm_package'] and s['npm_package'] in npm:
        e = npm[s['npm_package']]
        r.update({'npm_package': s['npm_package'], 'npm_latest_version': e.get('npm_latest_version') or '',
                  'npm_license_declared': e.get('npm_license_declared') or '', 'npm_last_publish': e.get('npm_last_publish') or '',
                  'npm_first_publish': e.get('npm_first_publish') or '', 'npm_versions_total': num(e.get('npm_versions_total')),
                  'npm_maintainers_n': num(e.get('npm_maintainers_n')), 'npm_dependencies_n': num(e.get('npm_dependencies_n')),
                  'npm_peer_dependencies_n': num(e.get('npm_peer_dependencies_n')),
                  'npm_unpacked_size_bytes': num(e.get('npm_unpacked_size_bytes')),
                  'npm_has_types': yn(e.get('npm_has_types')), 'npm_module_type': e.get('npm_module_type') or '',
                  'npm_has_exports_map': yn(e.get('npm_has_exports_map')), 'npm_homepage': e.get('npm_homepage') or '',
                  'npm_downloads_30d': num(e.get('npm_downloads_30d')), 'npm_downloads_365d': num(e.get('npm_downloads_365d')),
                  'npm_downloads_prev30d': num(e.get('npm_downloads_prev30d')),
                  'npm_file_count_registry': num(e.get('npm_file_count_registry')),
                  'npm_deprecated': yn(e.get('npm_deprecated')), 'npm_provenance': yn(e.get('npm_provenance')),
                  'npm_unpacked_size_measured_bytes': num(e.get('npm_unpacked_size_measured_bytes')),
                  'npm_package_files': num(e.get('npm_package_files')), 'npm_package_svg_files': num(e.get('npm_package_svg_files')),
                  'npm_package_font_files': num(e.get('npm_package_font_files')),
                  'npm_downloads_change_pct': (round(100.0 * (e['npm_downloads_30d'] - e['npm_downloads_prev30d']) / e['npm_downloads_prev30d'], 1)
                                               if e.get('npm_downloads_prev30d') else ''),
                  'stable_releases_730d': num(e.get('stable_releases_730d')),
                  'release_gap_median_days': '' if e.get('release_gap_median_days') is None else round(e['release_gap_median_days'], 1)})
        j = web['jsdelivr'].get(s['npm_package'], {})
        r['npm_jsdelivr_hits_30d'] = num(j.get('npm_jsdelivr_hits_30d'))
    # repository
    url = s['repo_url']
    if url:
        r['repo_url'] = url; r['repo_source'] = ''
        r['sets_from_same_repo'] = str(repo_count[url.lower()])
        g = git['repos'].get(url)
        if g:
            r['repo_status'] = g.get('status', '')
            if g.get('status') == 'ok':
                first = datetime.fromisoformat(g['first_date'])
                r.update({'repo_last_commit_date': g['last_date'], 'repo_commit_sha': g['sha'],
                          'repo_first_commit_date': g['first_date'],
                          'repo_age_years': round((CUTOFF.date() - first.date()).days / 365.25, 1),
                          'repo_days_since_last_commit': g['days_since_last'],
                          'repo_activity': ('' if g.get('days_since_last') is None else ('active' if g['days_since_last'] <= 90 else 'recent' if g['days_since_last'] <= 365 else 'dormant')),
                          'repo_commits_total': g['commits_total'], 'repo_commits_365d': g['commits_365d'],
                          'repo_authors_total': g['authors_total'], 'repo_authors_365d': g['authors_365d'],
                          'repo_top_author_share_365d': num(g['top_author_share_365d']),
                          'repo_default_branch': g['default_branch'], 'repo_semver_tags': g['semver_tags'],
                          'repo_latest_semver_tag': g['latest_semver_tag'] or '',
                          'repo_latest_semver_tag_date': g['latest_semver_tag_date'] or '',
                          'repo_files_total': g['files_total'], 'repo_svg_files': g['svg_files'],
                          'repo_has_readme': yn(g['has_readme']), 'repo_has_changelog': yn(g['has_changelog']),
                          'repo_has_contributing': yn(g['has_contributing']), 'repo_has_security_policy': yn(g['has_security_policy']),
                          'repo_has_ci': yn(g['has_ci']), 'repo_has_icon_font': yn(g['has_icon_font']),
                          'repo_has_design_files': yn(g['has_design_files'])})
        w = web['github'].get(url)
        if w:
            r.update({'gh_stars': num(w['gh_stars']), 'gh_forks': num(w['gh_forks']), 'gh_created_date': w['gh_created_date']})
        pkgdir = s['repo_package_dir']
        if pkgdir:
            r['repo_package_dir'] = pkgdir
            p = git['packages'].get(f'{url}#{pkgdir}')
            if p and 'commits_365d' in p:
                r.update({'pkg_commits_total': p['commits_total'], 'pkg_commits_365d': p['commits_365d'],
                          'pkg_authors_365d': p['authors_365d'], 'pkg_last_commit_date': p.get('last_date', '')})
    rows.append(r)

with open(os.path.join(WORK, 'collected.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=header); w.writeheader(); w.writerows(rows)
print(f'collected rows: {len(rows)}')
