#!/bin/sh
# Writes SHA256SUMS for every file in the release (not build/, not itself).
cd "$(dirname "$0")/.." || exit 1
find . -type f \
  ! -path './build/*' ! -path './collect/work/*' ! -path './.git/*' ! -name SHA256SUMS ! -name '*.pyc' \
  | sed 's|^\./||' | LC_ALL=C sort \
  | xargs sha256sum > SHA256SUMS
echo "SHA256SUMS written: $(wc -l < SHA256SUMS) files"
