#!/bin/sh
# Rebuilds the collected table and the comparison with the release from the saved snapshots in ../evidence/.
# No network access is needed. Output: tests/collection_compare.md (repository root).
# usage (from the repository root): sh collect/run_compare_from_evidence.sh
set -e
cd "$(dirname "$0")"
EV=../evidence
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
for f in iconify_sets.json npm.json web.json git.json icon_content.json.gz; do
  [ -f "$EV/$f" ] || { echo "missing $EV/$f"; exit 1; }
  cp "$EV/$f" "$TMP/$f"
done
cp "$EV/identity_seed.csv" "$TMP/identity_seed.csv"
ICON_WORK="$TMP" ICON_SEED="$TMP" python3 6_merge.py
ICON_WORK="$TMP" ICON_SEED="$TMP" python3 7_compare.py
echo "comparison written to tests/collection_compare.md (from evidence/)"
