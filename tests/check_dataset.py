import sys
import csv, re, sys, json, collections as C
from datetime import date
path = sys.argv[1]
rows = list(csv.DictReader(open(path, encoding='utf-8', newline='')))
cols = list(rows[0].keys())
fails, warns = [], []
def fail(msg): fails.append(msg)
def warn(msg): warns.append(msg)
CHECKED = date(2026, 11, 16)
NUMERIC = ["id","grid_px","icons_total","sets_from_same_repo","stable_releases_730d","release_gap_median_days","npm_downloads_30d","iconify_downloads_30d","iconify_downloads_365d","icons_hidden_n","icons_aliases_n","iconify_categories_n","style_variants_n","gh_stars","gh_forks","npm_dependents","npm_downloads_prev30d","npm_downloads_365d","repo_commits_total","repo_commits_365d","repo_authors_total","repo_authors_365d","repo_files_total","repo_svg_files","npm_versions_total","npm_unpacked_size_bytes"]
DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
def d(x): return date.fromisoformat(x)
# 1. identifiers
for c in ['id','set_id']:
    cnt = C.Counter(r[c] for r in rows)
    dups = [k for k,v in cnt.items() if v>1]
    if dups: fail(f'duplicate {c}: {dups[:5]}')
if [int(r['id']) for r in rows] != list(range(1, len(rows)+1)): fail('id is not 1..N in order')
# 2. numeric columns parse
for r in rows:
    for c in NUMERIC:
        v = r.get(c, '')
        if v == '': continue
        try: float(v)
        except ValueError: fail(f'row {r["id"]} {c} not numeric: {v!r}')
    for c in ['icons_total','gh_stars','npm_downloads_30d','iconify_downloads_30d']:
        if r.get(c,'') not in ('',) and float(r[c]) < 0: fail(f'row {r["id"]} {c} negative')
    if r['icons_total'] and int(float(r['icons_total'])) == 0: warn(f'row {r["id"]} {r["set_id"]} icons_total = 0')
# 3. dates
for r in rows:
    for c in [k for k in cols if k.endswith('_date') or k in ('checked_on','npm_last_publish','npm_first_publish','gh_created_date')]:
        v = r.get(c,'')
        if v and not DATE.match(v): fail(f'row {r["id"]} {c} bad date {v!r}')
    if r['checked_on'] and r['checked_on'] != CHECKED.isoformat(): warn(f'row {r["id"]} checked_on {r["checked_on"]}')
    lc, fc = r['repo_last_commit_date'], r['repo_first_commit_date']
    if lc and fc and d(fc) > d(lc): fail(f'row {r["id"]} first commit after last commit')
    if lc and d(lc) > CHECKED: fail(f'row {r["id"]} last commit after collection date')
    if r['npm_first_publish'] and r['npm_last_publish'] and d(r['npm_first_publish']) > d(r['npm_last_publish']): fail(f'row {r["id"]} npm first publish after last')
# 4. URLs
for r in rows:
    for c in ['repo_url','npm_homepage','iconify_license_url']:
        v = r.get(c,'')
        if v and not v.startswith(('http://','https://')): fail(f'row {r["id"]} {c} not a URL: {v!r}')
    if r['repo_url'] and r['repo_url'] != r['repo_url'].strip(): fail(f'row {r["id"]} repo_url whitespace')
# 5. licence consistency
LTYPES = {"permissive","public_domain","creative_commons_attribution","cc_share_alike","cc_no_derivatives","cc_non_commercial","copyleft","font_licence","split_or_dual","split_by_asset","custom_restricted","custom_umbrella_permissive","commercial_tiered","see_text","not_classified"}
for r in rows:
    lt = r['license_type']
    if lt and lt not in LTYPES: warn(f'row {r["id"]} license_type not in known list: {lt}')
    if lt == '' : fail(f'row {r["id"]} {r["set_id"]} empty license_type')
    if r['license_check'] == '': fail(f'row {r["id"]} empty license_check')
# 6. same repo => same sets_from_same_repo
by_repo = C.defaultdict(list)
for r in rows:
    if r['repo_url']: by_repo[r['repo_url'].lower()].append(r)
for k, rs in by_repo.items():
    for r in rs:
        if r['sets_from_same_repo'] and int(float(r['sets_from_same_repo'])) != len(rs) and len(rs) > 1:
            warn(f'row {r["id"]} sets_from_same_repo={r["sets_from_same_repo"]} but {len(rs)} rows share repo')
# 7. same npm package => same package-level downloads
by_pkg = C.defaultdict(list)
for r in rows:
    if r['npm_package']: by_pkg[r['npm_package']].append(r)
for k, rs in by_pkg.items():
    vals = {r['npm_downloads_30d'] for r in rs}
    if len(vals) > 1: fail(f'npm package {k}: different downloads across rows {vals}')
# 8. icon overlap in [0,100]
for r in rows:
    v = r['icon_overlap_max_pct']
    if v and not (0 <= float(v) <= 100): fail(f'row {r["id"]} overlap out of range')
# 9. whitespace / encoding artefacts
for r in rows:
    for c,v in r.items():
        if v and v != v.strip(): warn(f'row {r["id"]} {c} has leading/trailing whitespace')
        if v and re.search('Ã|Â|â€', v): fail(f'row {r["id"]} {c} mojibake: {v[:40]!r}')
        if v in ('NaN','nan','None','null','undefined'): fail(f'row {r["id"]} {c} literal {v}')
# 10. no kept row is still a re-packaged copy of an earlier set
by_set = {r['set_id']: r for r in rows}
def _origin(r):
    c=[x for x in (r['repo_first_commit_date'], r['npm_first_publish']) if x]
    return min(c) if c else ''
for r in rows:
    if not r['icon_overlap_max_pct']: continue
    p = by_set.get(r['icon_overlap_with'])
    if p and float(r['icon_overlap_max_pct']) >= 70 and _origin(r) and _origin(p) and _origin(r) > _origin(p):
        fail(f'row {r["id"]} {r["set_id"]} is a re-packaged copy of {p["set_id"]} and should be out of the table')
# 11. dangling overlap references (documented: overlap was computed against all 576 candidates)
for r in rows:
    p = r['icon_overlap_with']
    if p and p not in by_set: warn(f'row {r["id"]} icon_overlap_with refers to removed set {p!r} (overlap computed before removal)')
# 12. data dictionary covers every column
import os
DD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'data_dictionary.csv')
if os.path.exists(DD):
    dd = {r['column'] for r in csv.DictReader(open(DD, encoding='utf-8'))}
    missing = [c for c in cols if c not in dd]
    if missing: fail(f'columns without dictionary entry: {missing}')
print(f'file: {path}  rows={len(rows)} cols={len(cols)}')
print(f'FAIL: {len(fails)}  WARN: {len(warns)}')
for m in fails[:60]: print('  FAIL', m)
for m in warns[:60]: print('  WARN', m)
sys.exit(1 if fails else 0)
