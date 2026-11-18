#!/bin/sh
# Collects the measured values again from the public sources (see README). Caches are in collect/work/.
# usage (from the repository root): sh collect/run_collect.sh
set -e
cd "$(dirname "$0")"
python3 1_iconify.py
python3 2_seed.py
python3 3_npm.py
python3 3c_icon_content.py
python3 4_web.py
python3 5_git.py
python3 6_merge.py
python3 7_compare.py
