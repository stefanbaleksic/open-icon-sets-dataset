"""jsDelivr hits (30 days, daily series) and GitHub repository facts via ungh.cc (stars, forks, created).
The GitHub API itself is not used: it refuses unauthenticated requests from the collection environment."""
import csv, json, os
from common import get_json, WORK, SEED, JSDELIVR_WINDOW

seed = list(csv.DictReader(open(os.path.join(SEED, 'identity_seed.csv'), encoding='utf-8')))
pkgs = sorted({r['npm_package'] for r in seed if r['npm_package']})
repos = sorted({r['repo_url'] for r in seed if r['repo_url'].startswith('https://github.com/')})

js = {}
for p in pkgs:
    d = get_json(f'https://data.jsdelivr.com/v1/stats/packages/npm/{p}?period=month')
    if not d: continue
    dates = (d.get('hits') or {}).get('dates') or {}
    lo, hi = JSDELIVR_WINDOW
    days = [k for k in dates if lo <= k <= hi]
    expected = (lambda a, b: (__import__('datetime').date.fromisoformat(b) - __import__('datetime').date.fromisoformat(a)).days + 1)(lo, hi)
    # the series covers the last 30 days only; the value is reported only when the whole window is present
    js[p] = {'npm_jsdelivr_hits_30d': sum(dates[k] for k in days) if len(days) == expected else None}
print(f'jsDelivr: {len(js)} packages')

gh = {}
for url in repos:
    slug = url.replace('https://github.com/', '').rstrip('/')
    d = get_json(f'https://ungh.cc/repos/{slug}')
    if not d: continue
    r = d['repo']
    gh[url] = {'gh_stars': r.get('stars'), 'gh_forks': r.get('forks'), 'gh_created_date': (r.get('createdAt') or '')[:10]}
print(f'ungh: {len(gh)} repositories')
json.dump({'jsdelivr': js, 'github': gh}, open(os.path.join(WORK, 'web.json'), 'w'), indent=1)
