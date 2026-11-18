"""Identity inputs: which npm package and which repository belong to each set, and the candidates that
Iconify does not carry. These are taken from the released table (seed/identity_seed.csv) because the
discovery step (npm search, the v1 candidate list and manual matching) is not part of these scripts.
Measured values are NOT taken from the table; they are collected again by the other scripts."""
import csv, os
from common import SEED
src = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'icon_sets_v3.csv')
rows = list(csv.DictReader(open(src, encoding='utf-8')))
with open(os.path.join(SEED, 'identity_seed.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['set_id', 'name', 'author', 'frame', 'npm_package', 'repo_url', 'repo_package_dir', 'iconify_package'])
    for r in rows:
        w.writerow([r['set_id'], r['name'], r['author'], r['frame'], r['npm_package'], r['repo_url'], r['repo_package_dir'], r['iconify_package']])
print(f'identity seed: {len(rows)} sets')
