"""Duplicate checks for the icon-sets dataset.

usage: python3 -I tests/test_duplicates.py data/icon_sets_v3.csv data/removed_repackaged_copies.csv [build/data/icon_sets_extracted.csv]

FAIL = the table is wrong and must be fixed before release.
INFO = a pattern a person should look at; it is not an error.
Exit status 1 if any FAIL.
"""
import csv, re, sys, collections as C

main_path, removed_path = sys.argv[1], sys.argv[2]
original_path = sys.argv[3] if len(sys.argv) > 3 else None
rows = list(csv.DictReader(open(main_path, encoding='utf-8', newline='')))
removed = list(csv.DictReader(open(removed_path, encoding='utf-8', newline='')))
fails, infos = [], []
def fail(m): fails.append(m)
def info(m): infos.append(m)

def origin(r):
    c = [x for x in (r['repo_first_commit_date'], r['npm_first_publish']) if x]
    return min(c) if c else ''

# T1 identifiers are unique (exact, and case-insensitive for names)
for col in ('id', 'set_id'):
    d = [k for k, v in C.Counter(r[col] for r in rows).items() if v > 1]
    if d: fail(f'T1 duplicate {col}: {d[:5]}')
d = [k for k, v in C.Counter(r['name'].strip().lower() for r in rows).items() if v > 1]
if d: fail(f'T1 duplicate name (case-insensitive): {d[:5]}')

# T2 no two rows with identical content (ignoring id and set_id)
sig = C.Counter(tuple(v for k, v in r.items() if k not in ('id', 'set_id')) for r in rows)
n = sum(v - 1 for v in sig.values() if v > 1)
if n: fail(f'T2 {n} row(s) identical to another row apart from id and set_id')

# T3 no kept row is still a re-packaged copy (>= 70 % of icons in an earlier set in the table)
by = {r['set_id']: r for r in rows}
for r in rows:
    try: ov = float(r['icon_overlap_max_pct'])
    except ValueError: continue
    p = by.get(r['icon_overlap_with'])
    if ov >= 70 and p and origin(r) and origin(p) and origin(r) > origin(p):
        fail(f'T3 {r["set_id"]} ({ov} % in {p["set_id"]}, earlier) is still in the table')

# T4 main table and removed list partition the candidate frame
rem_ids = {r['set_id'] for r in removed}
if set(by) & rem_ids: fail(f'T4 sets both kept and removed: {sorted(set(by) & rem_ids)}')
if len(removed) != len(rem_ids): fail('T4 removed list has duplicate set_id')
if original_path:
    orig = list(csv.DictReader(open(original_path, encoding='utf-8', newline='')))
    orig_ids = {r['set_id'] for r in orig}
    if orig_ids != set(by) | rem_ids:
        fail(f'T4 kept + removed != candidate frame: missing {sorted(orig_ids - set(by) - rem_ids)[:5]}, extra {sorted((set(by) | rem_ids) - orig_ids)[:5]}')
    if len(orig) != len(rows) + len(removed):
        fail(f'T4 counts: {len(orig)} candidates != {len(rows)} kept + {len(removed)} removed')
    orig_by = {r['set_id']: r for r in orig}
    for r in removed:
        if r['original_id'] != orig_by[r['set_id']]['id']:
            fail(f'T4 removed {r["set_id"]} original_id mismatch')
else:
    info('T4 original frame not supplied; partition check skipped')

# T5 sets sharing a repository: sets_from_same_repo equals the number of kept rows sharing it
by_repo = C.defaultdict(list)
for r in rows:
    if r['repo_url']: by_repo[r['repo_url'].lower()].append(r)
for k, rs in by_repo.items():
    for r in rs:
        if r['sets_from_same_repo'] != str(len(rs)):
            fail(f'T5 {r["set_id"]} sets_from_same_repo={r["sets_from_same_repo"]} but {len(rs)} kept rows share the repository')
    if len(rs) > 1:
        info(f'T5 shared repository ({len(rs)} sets, expected for variant sets): {k} -> ' + ', '.join(r['set_id'] for r in rs))

# T6 one npm package: all rows show the same package-level downloads
by_pkg = C.defaultdict(list)
for r in rows:
    if r['npm_package']: by_pkg[r['npm_package']].append(r)
for k, rs in by_pkg.items():
    if len({r['npm_downloads_30d'] for r in rs}) > 1:
        fail(f'T6 npm package {k}: different npm_downloads_30d across rows')
    if len(rs) > 1:
        info(f'T6 one npm package behind {len(rs)} sets (expected for variants): {k}')

# T7 one Iconify package is not listed twice
d = [k for k, v in C.Counter(r['iconify_package'] for r in rows if r['iconify_package']).items() if v > 1]
if d: fail(f'T7 iconify_package listed more than once: {d}')

# T8 remaining overlap pairs at >= 70 % (for review, the rule did not apply)
for r in rows:
    try: ov = float(r['icon_overlap_max_pct'])
    except ValueError: continue
    if ov >= 70:
        info(f'T8 {r["set_id"]} shares {ov} % of icons with {r["icon_overlap_with"]} (later or undated origin, not moved)')

# T9 same display name under different sets: review list (names are not unique by design)
norm = C.defaultdict(list)
for r in rows: norm[re.sub(r'[^a-z0-9]', '', r['name'].lower())].append(r['set_id'])
for k, v in norm.items():
    if len(v) > 1 and k:
        info(f'T9 normalised name "{k}" used by: {", ".join(v)}')

# T10 no kept row refers to a removed set in its overlap fields
for r in rows:
    if r['icon_overlap_with'] and r['icon_overlap_with'] not in by:
        fail(f'T10 {r["set_id"]} icon_overlap_with points at removed set {r["icon_overlap_with"]}')

print(f'duplicate tests: FAIL {len(fails)}, INFO {len(infos)}')
for m in fails: print('  FAIL', m)
for m in infos: print('  INFO', m)
sys.exit(1 if fails else 0)
