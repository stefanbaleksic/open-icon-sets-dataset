"""Iconify catalogue: the 233 sets of the frame (not hidden, not Archive / Unmaintained) and their metadata.
Writes work/iconify_sets.json. Hidden or archived sets are recorded with their reason, so the frame can be checked."""
import json, os
from common import get_json, WORK

cols = get_json('https://api.iconify.design/collections')
out = {}
for prefix, c in cols.items():
    if c.get('hidden'):
        out[prefix] = {'in_frame': False, 'reason': 'hidden by Iconify'}
    elif c.get('category') == 'Archive / Unmaintained':
        out[prefix] = {'in_frame': False, 'reason': 'Archive / Unmaintained'}
    else:
        out[prefix] = {
            'in_frame': True, 'name': c.get('name'), 'total': c.get('total'),
            'author_name': (c.get('author') or {}).get('name'), 'author_url': (c.get('author') or {}).get('url'),
            'license_spdx': (c.get('license') or {}).get('spdx'), 'license_title': (c.get('license') or {}).get('title'),
            'license_url': (c.get('license') or {}).get('url'), 'category': c.get('category'),
            'tags': c.get('tags') or [], 'height': c.get('height'), 'palette': c.get('palette'),
            'samples': c.get('samples') or [],
            # live catalogue only: Iconify does not publish the category list in the package
            'categories_n': len((get_json(f'https://api.iconify.design/collection?prefix={prefix}') or {}).get('categories') or {}),
        }
json.dump(out, open(os.path.join(WORK, 'iconify_sets.json'), 'w'), indent=1, ensure_ascii=False)
inframe = [k for k, v in out.items() if v['in_frame']]
print(f'Iconify collections: {len(cols)}; in frame: {len(inframe)}; excluded: {len(cols) - len(inframe)}')
