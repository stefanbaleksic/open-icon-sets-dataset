"""Remove re-packaged copies and manual removals; write the main table and the removed list.

Rule (automatic): a set is a re-packaged copy when at least 70 % of its icons appear in another set
(icon_overlap_max_pct / icon_overlap_with) and that other set has an earlier origin date
(earlier of repo first commit and npm first publish).
Manual: sets listed in build_input/manual_removals.csv.
Where the removed set was the partner of an overlap value, the overlap fields of the kept row are blanked:
the new maximum over the kept sets needs the icon data, which is not part of this release.

usage: python3 -I scripts/clean_repackaged_copies.py <extracted.csv> <out_dir>
"""
import csv, sys, os
src, outdir = sys.argv[1], sys.argv[2]
here = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(src, encoding='utf-8', newline='')))
cols = list(rows[0].keys())
by = {r['set_id']: r for r in rows}
HERE = os.path.join(here, '..', 'build_input')

def origin(r):
    c = [x for x in (r['repo_first_commit_date'], r['npm_first_publish']) if x]
    return min(c) if c else ''

REMOVE = {}
for r in rows:
    try: ov = float(r['icon_overlap_max_pct'])
    except ValueError: continue
    if ov < 70: continue
    p = by.get(r['icon_overlap_with'])
    if not p: continue
    o_r, o_p = origin(r), origin(p)
    if o_r and o_p and o_r > o_p:
        REMOVE[r['set_id']] = (f"rule: {ov}% of its icons appear in '{p['set_id']}', "
                               f"which has the earlier origin date ({o_p} vs {o_r})")
for m in csv.DictReader(open(os.path.join(HERE, 'manual_removals.csv'), encoding='utf-8', newline='')):
    if m['set_id'] not in by: raise SystemExit(f"manual removal of unknown set {m['set_id']}")
    REMOVE[m['set_id']] = 'manual: ' + m['reason']

removed = [r for r in rows if r['set_id'] in REMOVE]
kept = [r for r in rows if r['set_id'] not in REMOVE]

# overlap values that pointed at a removed set are no longer valid for the kept table
blanked = []
for r in kept:
    if r['icon_overlap_with'] in REMOVE:
        blanked.append((r['set_id'], r['icon_overlap_with'], r['icon_overlap_max_pct']))
        r['icon_overlap_with'] = ''; r['icon_overlap_max_pct'] = ''; r['icon_overlap_basis'] = ''

for i, r in enumerate(kept, 1): r['id'] = str(i)
cnt = {}
for r in kept:
    if r['repo_url']: cnt[r['repo_url'].lower()] = cnt.get(r['repo_url'].lower(), 0) + 1
for r in kept:
    if r['repo_url']: r['sets_from_same_repo'] = str(cnt[r['repo_url'].lower()])

os.makedirs(os.path.join(outdir, 'data'), exist_ok=True)
with open(f'{outdir}/data/icon_sets_v3.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(kept)
with open(f'{outdir}/data/removed_repackaged_copies.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['original_id', 'set_id', 'name', 'author', 'frame', 'repo_url', 'icons_total', 'reason'])
    for r in removed:
        w.writerow([r['id'], r['set_id'], r['name'], r['author'], r['frame'], r['repo_url'], r['icons_total'], REMOVE[r['set_id']]])
with open(f'{outdir}/data/overlap_blanked.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['set_id', 'former_partner_removed', 'former_icon_overlap_max_pct'])
    w.writerows(blanked)
print(f'kept {len(kept)} removed {len(removed)} overlap values blanked {len(blanked)}')
for r in removed: print(' removed', r['id'], r['set_id'], '-', REMOVE[r['set_id']][:90])
