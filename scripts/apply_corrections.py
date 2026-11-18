"""Apply the documented cell corrections in build_input/corrections.csv.

Every correction states the old value; the script stops if the old value is not what it finds,
so a corrected cell can never be changed twice or silently.
usage: python3 -I scripts/apply_corrections.py <extracted.csv> <corrections.csv> <out.csv>
"""
import csv, sys
src, corr, out = sys.argv[1:4]
rows = list(csv.DictReader(open(src, encoding='utf-8', newline='')))
cols = list(rows[0].keys())
by = {r['set_id']: r for r in rows}
n = 0
for c in csv.DictReader(open(corr, encoding='utf-8', newline='')):
    r = by.get(c['set_id'])
    if r is None: raise SystemExit(f"correction for unknown set {c['set_id']}")
    if r[c['column']] != c['old_value']:
        raise SystemExit(f"{c['set_id']} {c['column']} is {r[c['column']]!r}, expected {c['old_value']!r}")
    r[c['column']] = c['new_value']; n += 1
with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
print(f'{n} corrections applied')
