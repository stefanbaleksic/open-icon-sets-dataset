"""Icon contents of each set, as the package stood on the cut-off day (definitions: data/data_dictionary.csv, collect/RULES.md).
Iconify sets: icons.json of the cut-off version (hidden icons and aliases left out).
Other sets: the .svg files of the cut-off version's tarball (sprite sheets left out).
Writes work/icon_content.json: per set the measures, the names, and one fingerprint per icon with path data.
The measurements are pure functions in icon_measures.py (tested in tests/test_icon_measures.py).
Overlap (icon_overlap_*) is computed here across the sets of the table (see RULES.md)."""
import csv, io, json, os, re, tarfile, urllib.request
from datetime import datetime

from common import get_json, q, WORK, SEED, CUTOFF, USER_AGENT
from icon_measures import (svg_icon, measures, fingerprints, style_variants, base_names, remix_overlap, best_overlap)

STABLE = re.compile(r'^\d+\.\d+\.\d+$')
LIMIT = 400 * 1024 * 1024


def cutoff_version(doc):
    t = doc.get('time', {})
    before = {v: ts for v, ts in t.items() if v not in ('created', 'modified') and datetime.fromisoformat(ts.replace('Z', '+00:00')) <= CUTOFF}
    latest = (doc.get('dist-tags') or {}).get('latest')
    if latest not in before:
        cand = [(ts, v) for v, ts in before.items() if STABLE.match(v)]
        latest = max(cand)[1] if cand else None
    return latest


def read_members(url, size, want):
    """Bytes of the tarball members for which want(name) is true (read in memory)."""
    if not url or (size or 0) > LIMIT:
        return {}
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=300) as r:
        data = r.read()
    out = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as tf:
        for m in tf.getmembers():
            if m.isfile() and want(m.name):
                out[m.name] = tf.extractfile(m).read().decode('utf-8', 'replace')
    return out


def icons_of(is_iconify, doc, latest):
    """Icons of the cut-off version. Returns (icons, Iconify set version or '')."""
    dist = (doc.get('versions') or {}).get(latest, {}).get('dist') or {}
    if is_iconify:
        files = read_members(dist.get('tarball'), dist.get('unpackedSize'),
                             lambda n: n.endswith(('package/icons.json', 'package/info.json')))
        if not files:
            return [], ''
        data = json.loads(next(v for k, v in files.items() if k.endswith('icons.json')))
        version = json.loads(files['package/info.json']).get('version', '') if 'package/info.json' in files else ''
        dh = data.get('height')
        hidden = {n for n, v in data.get('icons', {}).items() if v.get('hidden')}
        out = [{'name': name, 'body': ic.get('body', ''), 'vb_h': ic.get('height', dh), 'own': ('width' in ic or 'height' in ic)}
               for name, ic in data.get('icons', {}).items() if name not in hidden]
        return out, version
    files = read_members(dist.get('tarball'), dist.get('unpackedSize'),
                         lambda n: n.lower().endswith('.svg') and not os.path.basename(n).lower().startswith('sprite'))
    return [i for i in (svg_icon(path, text) for path, text in files.items()) if i], ''


def derive(pkg):
    """Measures of one package (cut-off version). Icon bodies are not kept after this."""
    doc = get_json(f'https://registry.npmjs.org/{q(pkg)}')
    if doc is None:
        return {}
    latest = cutoff_version(doc)
    icons, version = icons_of(pkg.startswith('@iconify-json/'), doc, latest) if latest else ([], '')
    if not icons:
        return {}
    names = [x['name'] for x in icons]
    styles = style_variants(names)
    bases = base_names(names, styles)
    ex, rd = fingerprints(icons)
    m = measures(icons)
    m.update({'style_variants': ';'.join(styles), 'style_variants_n': len(styles), 'unique_base_names': len(bases),
              'icons_fingerprinted_n': len(ex), 'iconify_version': version,
              'base_names': sorted(bases), 'fp_exact': ex, 'fp_rounded': rd})
    return m


if __name__ == '__main__':
    seed = list(csv.DictReader(open(os.path.join(SEED, 'identity_seed.csv'), encoding='utf-8')))
    result = {}
    cache = {}
    for i, s in enumerate(seed, 1):
        sid = s['set_id']
        pkg = s['iconify_package'] if s['frame'] == 'iconify' and s['iconify_package'] else s['npm_package']
        if not pkg:
            result[sid] = {}
            continue
        if pkg not in cache:
            cache[pkg] = derive(pkg)
        result[sid] = dict(cache[pkg])
        if i % 25 == 0:
            print(f'{i}/{len(seed)}', flush=True)

    # Remix Icon base names for the naming overlap
    remix = set(result['ri'].get('base_names', [])) if 'ri' in result else set()
    for sid, m in result.items():
        if m.get('base_names'):
            m['remix_name_overlap_pct'] = remix_overlap(m['base_names'], remix)

    # Overlap of path data between sets of the table (only sets of different packages count)
    pkg_of = {s['set_id']: (s['iconify_package'] if s['frame'] == 'iconify' and s['iconify_package'] else s['npm_package'])
              for s in seed}
    for sid, (pct, other, basis) in best_overlap(result, pkg_of).items():
        m = result[sid]
        if not m:
            continue
        m['icon_overlap_max_pct'] = pct
        m['icon_overlap_with'] = other if pct else ''
        m['icon_overlap_basis'] = basis

    json.dump(result, open(os.path.join(WORK, 'icon_content.json'), 'w'))
    print(f'icon content: {sum(1 for m in result.values() if m)} sets measured')
