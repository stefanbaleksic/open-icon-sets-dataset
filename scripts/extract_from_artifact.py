"""Read the embedded dataset (COLS, ROWS, MEANING, NUMERIC) from the published
HTML viewer and write it as CSV plus a data dictionary.

usage: python3 -I scripts/extract_from_artifact.py <viewer.html> <out_dir>
"""
import csv, json, os, re, sys
html_path, out = sys.argv[1], sys.argv[2]
html = open(html_path, encoding='utf-8').read()

def js_json(name):
    m = re.search(r'const %s = (.*?);\n' % name, html, re.S)
    if not m: raise SystemExit(f'{name} not found')
    return json.loads(m.group(1))

cols = js_json('COLS'); rows = js_json('ROWS'); meaning = js_json('MEANING')
numeric = set(re.findall(r'"(\w+)"', re.search(r'const NUMERIC = new Set\((\[.*?\])\);', html, re.S).group(1)))
bad = [i for i, r in enumerate(rows) if len(r) != len(cols)]
if bad: raise SystemExit(f'rows with wrong length: {bad[:10]}')
os.makedirs(os.path.join(out, 'data'), exist_ok=True)
with open(os.path.join(out, 'data', 'icon_sets_extracted.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(cols)
    for r in rows: w.writerow(['' if v is None else v for v in r])
with open(os.path.join(out, 'data', 'data_dictionary.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['column', 'type', 'meaning'])
    for c in cols: w.writerow([c, 'number' if c in numeric else 'text', meaning.get(c, '')])
print(f'{len(rows)} rows, {len(cols)} columns written to {out}/data')
