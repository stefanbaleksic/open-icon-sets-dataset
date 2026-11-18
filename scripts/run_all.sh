#!/bin/sh
# Rebuild data/ from the viewer in build_input/, run every check (release, duplicates, collection helpers,
# comparison from evidence/) and record SHA-256 sums. Live collection is not part of this script (see collect/README.md).
# usage (from the repository root): sh scripts/run_all.sh
# Exit status is 0 only if every check passes.
set -u
cd "$(dirname "$0")/.." || exit 1
status=0

echo "1/6 extract the dataset from the viewer"
python3 -I scripts/extract_from_artifact.py build_input/viewer_v3.html build || exit 1

echo "2/6 apply documented corrections, then the copy rule and manual removals"
python3 -I scripts/apply_corrections.py build/data/icon_sets_extracted.csv build_input/corrections.csv build/data/icon_sets_corrected.csv || exit 1
python3 -I scripts/clean_repackaged_copies.py build/data/icon_sets_corrected.csv . || exit 1

echo "3/6 consistency checks"
python3 -I tests/check_dataset.py data/icon_sets_v3.csv > tests/validation_report.txt || status=1
cat tests/validation_report.txt

echo "4/6 duplicate checks"
python3 -I tests/test_duplicates.py data/icon_sets_v3.csv data/removed_repackaged_copies.csv build/data/icon_sets_corrected.csv > tests/duplicate_report.txt || status=1
cat tests/duplicate_report.txt

echo "5/6 unit tests of the collection helpers (UTC day, cut-off, semantic versions) and of the icon measures"
mkdir -p build/reports
python3 -I tests/test_collect_utils.py > build/reports/collect_utils.txt 2>&1 || status=1
tail -3 build/reports/collect_utils.txt
python3 -I tests/test_icon_measures.py > build/reports/icon_measures.txt 2>&1 || status=1
tail -3 build/reports/icon_measures.txt
python3 -I tests/test_docs_numbers.py > build/reports/docs_numbers.txt 2>&1 || status=1
tail -3 build/reports/docs_numbers.txt

echo "6/6 comparison rebuilt from the saved evidence (no network)"
sh collect/run_compare_from_evidence.sh > /dev/null || status=1

sh scripts/write_sha256sums.sh
echo "done: status $status (0 = all checks pass)"
exit $status
