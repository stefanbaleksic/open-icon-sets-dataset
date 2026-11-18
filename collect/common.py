"""Shared settings and HTTP helper for the collection scripts (standard library only)."""
import json, os, re, time, urllib.request, urllib.error, urllib.parse
from datetime import datetime, timezone, date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
# ICON_WORK lets the evidence check read saved snapshots instead of live caches.
WORK = os.environ.get('ICON_WORK') or os.path.join(HERE, 'work')
SEED = os.environ.get('ICON_SEED') or os.path.join(HERE, 'seed')
os.makedirs(WORK, exist_ok=True)

# Snapshot definition (same as the release: UTC days, cut-off at the end of the collection day)
COLLECTION_DAY = date(2026, 11, 16)
CUTOFF = datetime(2026, 11, 16, 23, 59, 59, tzinfo=timezone.utc)
CUTOFF_ISO = '2026-11-16T23:59:59Z'
# Download windows (fixed, inclusive)
DL30 = ('2026-10-17', '2026-11-15')
DL30_PREV = ('2026-09-17', '2026-10-16')
DL365 = ('2025-11-17', '2026-11-15')
JSDELIVR_WINDOW = ('2026-10-16', '2026-11-14')
USER_AGENT = 'icon-sets-dataset-collector/3 (+https://github.com/stefanbaleksic/icon-sets-dataset)'

def get_json(url, retries=5, timeout=60):
    """GET a JSON document. Returns None on 404. Backs off on 429 and 5xx."""
    delay = 3
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(delay); delay *= 2; continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if attempt < retries - 1:
                time.sleep(delay); delay *= 2; continue
            raise
    return None

def q(name):
    """URL-encode an npm package name, keeping the scope slash encoded (%2F)."""
    return urllib.parse.quote(name, safe='')

def utc_day(iso):
    """Convert an ISO-8601 timestamp with offset to the UTC calendar day (YYYY-MM-DD)."""
    return datetime.fromisoformat(iso.replace('Z', '+00:00')).astimezone(timezone.utc).strftime('%Y-%m-%d')

# Semantic version tag: v1.2.3 or 1.2.3 (no pre-release suffix).
SEMVER = re.compile(r'^v?(\d+)\.(\d+)\.(\d+)$')
