"""Writes build_input/corrections.csv from the collected values.

For every cell that the collection scripts measure (the columns compared in tests/collection_compare.md),
where the collected value is not blank and differs from the value in the viewer (before corrections),
one correction row is written: set, column, old value (from the viewer), new value (collected), reason.
Reasons that already exist in corrections.csv are kept. Cells the scripts do not measure are not changed.
Run after collect/run_collect.sh (or run_compare_from_evidence.sh), then scripts/run_all.sh.
usage (repository root): python3 collect/make_corrections.py build/data/icon_sets_extracted.csv evidence/collected.csv
"""
import csv, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
extracted_path, collected_path = sys.argv[1], sys.argv[2]
corr_path = os.path.join(ROOT, 'build_input', 'corrections.csv')

ext = {r['set_id']: r for r in csv.DictReader(open(extracted_path, encoding='utf-8', newline=''))}
col = {r['set_id']: r for r in csv.DictReader(open(collected_path, encoding='utf-8', newline=''))}
header = list(csv.DictReader(open(extracted_path, encoding='utf-8', newline='')).fieldnames)
# Columns that the scripts do not measure stay as they are; identity columns are not corrected.
NOT_CORRECTED = {'id', 'set_id', 'checked_on', 'frame', 'iconify_package', 'original_id'}
measured = [c for c in header if c in next(iter(col.values())) and c not in NOT_CORRECTED]

old_rows = list(csv.DictReader(open(corr_path, encoding='utf-8', newline='')))
old_reason = {(r['set_id'], r['column']): r['reason'] for r in old_rows}
GENERIC = ('Collected from the public sources on 2026-11-18 by collect/ (rule in collect/RULES.md). '
           'The release value was different and is replaced; both are shown in the comparison.')

out = []
for sid in ext:
    if sid not in col: continue
    for c in measured:
        new = col[sid].get(c, '')
        old = ext[sid].get(c, '')
        if new == '' or new == old: continue
        out.append({'set_id': sid, 'column': c, 'old_value': old, 'new_value': new,
                    'reason': old_reason.get((sid, c), GENERIC)})
# Corrections for cells that are not measured are kept as they were.
kept = [r for r in old_rows if r['column'] not in set(measured) or r['set_id'] not in col]
with open(corr_path, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['set_id', 'column', 'old_value', 'new_value', 'reason'])
    w.writeheader()
    for r in kept: w.writerow({k: r[k] for k in w.fieldnames})
    for r in out: w.writerow(r)
print(f'corrections: {len(out)} measured cells, {len(kept)} kept as they were')
