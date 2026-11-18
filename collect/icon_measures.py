"""Pure measurements of icon contents (standard library only). Definitions: data/data_dictionary.csv and collect/RULES.md.
No network and no file access here, so the functions can be tested with small examples (tests/test_icon_measures.py).
3c_icon_content.py reads the packages and calls these functions."""
import collections, hashlib, os, re, statistics

COLOUR_NAMES = {'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'brown', 'gray', 'grey', 'silver', 'navy',
                'teal', 'maroon', 'olive', 'lime', 'aqua', 'cyan', 'magenta', 'violet', 'gold', 'indigo', 'turquoise',
                'coral', 'salmon', 'tomato', 'crimson', 'orchid', 'khaki', 'beige', 'tan', 'plum', 'lavender', 'ivory'}
SKIP_VALUES = {'none', 'currentcolor', 'inherit', 'freeze', 'transparent'}
BW = {'#000', '#000000', '#fff', '#ffffff', 'black', 'white'}
STYLE_CHECK_MIN_SHARE = 0.2
OVERLAP_MIN_FINGERPRINTS = 20


def num(v):
    """Whole numbers as int, other values rounded to one decimal."""
    if v is None:
        return None
    v = float(v)
    return int(v) if v == int(v) else round(v, 1)


def svg_icon(path, text):
    """One icon from an .svg file: name, body (content between the svg tag and its closing tag, without the tag),
    viewBox height and own-size flag. None if the file has no svg tag.
    Other sets have no set default size, so own is always False (see RULES.md)."""
    m = re.search(r'<svg\b([^>]*)>', text, re.I)
    if not m:
        return None
    attrs = m.group(1)
    vb = re.search(r'viewBox="([^"]+)"', attrs)
    vb_h = float(vb.group(1).split()[-1]) if vb and len(vb.group(1).split()) == 4 else None
    inner = text[m.end():]
    inner = inner[:inner.lower().rfind('</svg>')] if '</svg>' in inner.lower() else inner
    return {'name': os.path.basename(path)[:-4], 'body': inner, 'vb_h': vb_h, 'own': False}


def measures(icons):
    """Share and size measures over one set's icons. Empty dict if there are no icons."""
    n = len(icons)
    if n == 0:
        return {}
    vb = collections.Counter(i['vb_h'] for i in icons if i['vb_h'] is not None)
    cc = sum(1 for i in icons if re.search(r'currentcolor', i['body'], re.I))
    hard = 0; grad = 0; stroke = 0; anim = 0; sw = collections.Counter(); sizes = []
    for i in icons:
        b = i['body']
        sizes.append(len(b.encode('utf-8')))
        if any(v.strip().lower() not in SKIP_VALUES and not v.strip().lower().startswith('url(') and v.strip().lower() not in BW
               and (re.match(r'^#[0-9a-f]{3,8}$', v.strip().lower()) or re.match(r'^(rgb|hsl)a?\(', v.strip().lower())
                    or v.strip().lower() in COLOUR_NAMES)
               for _, v in re.findall(r'\b(fill|stroke|stop-color)="([^"]+)"', b, re.I)):
            hard += 1
        if re.search(r'<(linear|radial)Gradient', b, re.I):
            grad += 1
        if re.search(r'\bstroke="(?!none)[^"]+"', b, re.I) and not re.search(r'stroke-width="0(\.0+)?"', b):
            stroke += 1
            m = re.search(r'stroke-width="([0-9.]+)"', b)
            if m:
                sw[num(m.group(1))] += 1
        if re.search(r'<(animate|animateTransform|animateMotion|set)\b', b, re.I):
            anim += 1
    hard_pct = 100 * hard / n; grad_pct = 100 * grad / n; stroke_pct = 100 * stroke / n
    palette = 'monotone' if hard_pct <= 5 and grad_pct <= 5 else ('multicolor' if hard_pct >= 50 or grad_pct >= 50 else 'mixed')
    construction = 'stroke' if stroke_pct >= 80 else ('fill' if stroke_pct <= 20 else 'mixed')
    return {'icon_viewbox_px': num(vb.most_common(1)[0][0]) if vb else None,
            'icons_own_size_pct': round(100 * sum(1 for i in icons if i['own']) / n, 1),
            'icons_currentcolor_pct': round(100 * cc / n, 1), 'icons_hardcoded_color_pct': round(hard_pct, 1),
            'icons_gradient_pct': round(grad_pct, 1), 'icons_stroke_based_pct': round(stroke_pct, 1),
            'icons_animated_n': anim, 'stroke_width_mode': sw.most_common(1)[0][0] if sw else None,
            'median_icon_bytes': int(statistics.median(sizes)), 'mean_icon_bytes': int(round(statistics.mean(sizes))),
            'measured_palette': palette, 'icon_construction': construction}


def fingerprints(icons):
    """One hash per icon that has path data: exact, and rounded to one decimal. Returns (exact list, rounded list)."""
    ex, rd = [], []
    for i in icons:
        paths = re.findall(r'<path\b[^>]*?\sd="([^"]*)"', i['body'], re.I)
        if not paths:
            continue
        exact = '|'.join(' '.join(p.split()) for p in paths)
        rounded = re.sub(r'-?\d+\.\d+', lambda m: f'{float(m.group()):.1f}', exact)
        ex.append(hashlib.sha1(exact.encode()).hexdigest()[:16])
        rd.append(hashlib.sha1(rounded.encode()).hexdigest()[:16])
    return ex, rd


def style_variants(names):
    """Suffixes that vary a drawing: a suffix token is a style if at least 20 % of names carry it and at least half of
    the base names carrying it have two or more suffixes. Needs at least two styles to be reported."""
    last = collections.Counter(n.rsplit('-', 1)[-1] for n in names if '-' in n)
    base_suffix = collections.defaultdict(set)
    for n in names:
        if '-' in n:
            b, s = n.rsplit('-', 1)
            base_suffix[b].add(s)
    styles = set()
    for s, c in last.items():
        if c < STYLE_CHECK_MIN_SHARE * len(names):
            continue
        bases = [b for b, ss in base_suffix.items() if s in ss]
        if sum(1 for b in bases if len(base_suffix[b]) >= 2) >= 0.5 * len(bases) and len(bases) >= 2:
            styles.add(s)
    return sorted(styles) if len(styles) >= 2 else []


def base_names(names, styles):
    """Names with the style suffix removed (the set of distinct base names)."""
    out = set()
    for n in names:
        b = n
        if styles and '-' in n and n.rsplit('-', 1)[1] in styles:
            b = n.rsplit('-', 1)[0]
        out.add(b)
    return out


def remix_overlap(base, remix):
    """Share of this set's base names that also occur among the Remix Icon base names."""
    if not base or not remix:
        return None
    return round(100 * len(set(base) & remix) / len(base), 1)


def overlap(result, pkg_of, basis_key, min_fp=OVERLAP_MIN_FINGERPRINTS):
    """For each set: largest share of its fingerprints that occur in one other set of a different package.
    result maps set_id to a dict with the fingerprint list under basis_key. Returns set_id -> (pct or None, other set_id)."""
    index = collections.defaultdict(set)
    for sid, m in result.items():
        for h in set(m.get(basis_key, [])):
            index[h].add(sid)
    out = {}
    for sid, m in result.items():
        fps = m.get(basis_key, [])
        if len(fps) < min_fp:
            out[sid] = (None, '')
            continue
        counts = collections.Counter()
        for h in fps:
            for other in index[h]:
                if other != sid and pkg_of.get(other) != pkg_of.get(sid):
                    counts[other] += 1
        if not counts:
            out[sid] = (0.0, '')
            continue
        # most shared set; on a tie the smaller set_id wins, so the result does not depend on hash order
        other, c = min(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        out[sid] = (round(100 * c / len(fps), 1), other)
    return out


def best_overlap(result, pkg_of):
    """Overlap on the exact and on the rounded basis; the higher one is reported. Returns set_id -> (pct, with, basis)."""
    ov_ex = overlap(result, pkg_of, 'fp_exact')
    ov_rd = overlap(result, pkg_of, 'fp_rounded')
    out = {}
    for sid in result:
        a, aw = ov_ex.get(sid, (None, ''))
        b, bw = ov_rd.get(sid, (None, ''))
        if a is None and b is None:
            out[sid] = (None, '', '')
        elif (b or 0) > (a or 0):
            out[sid] = (b, bw, 'rounded_1dp')
        else:
            out[sid] = (a, aw, 'exact')
        if out[sid][0] == 0:  # release convention: no partner name when the share is 0 %
            out[sid] = (0.0, '', out[sid][2])
    return out
