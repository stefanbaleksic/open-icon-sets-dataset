# Changelog

All notable changes to this dataset. Versions follow [Semantic Versioning 2.0.0](https://semver.org/):

- **MAJOR** (for example 4.0.0): a column is removed or renamed, the meaning of a column changes, or a row set changes so that results from earlier versions cannot be compared.
- **MINOR** (for example 3.1.0): rows or columns are added without changing the meaning of existing columns, or a rule is added that only affects new rows.
- **PATCH** (for example 3.0.1): a corrected cell, a fixed typo in the documentation, or a changed script or test that does not change any value in the table.

Pre-release versions use the suffix `-draft` (for example `3.0.0-draft`) until the dataset is published with a DOI. The version in `CITATION.cff` must match the latest entry here.

Every correction to a cell is listed in `build_input/corrections.csv` with the old value, the new value and the reason. A rule change that alters values is always recorded here.

## [3.0.0-draft] - snapshot 2026-11-16 (cut-off 2026-11-16 23:59:59 UTC), live run 2026-11-18

### Added
- 571 rows and 124 columns (v2 had 246 rows).
- Rows from npm discovery (327) and from the v1 list that Iconify does not carry (9) or carries as archived or hidden (4).
- `CITATION.cff`, `LICENSE.md`, `SHA256SUMS`, `scripts/run_all.sh` (reproduces the table and runs every check).
- Collection scripts in `collect/`, saved evidence in `evidence/`, and the rules they use in `collect/RULES.md`.
- Tests: `tests/check_dataset.py`, `tests/test_duplicates.py`, `tests/test_collect_utils.py` (UTC day conversion, cut-off, semantic version tags), `tests/test_icon_measures.py` (icon-content measures on hand-checked examples), `tests/test_docs_numbers.py` (figures in the documents match the data).
- Continuous check (`.github/workflows/check.yml`): runs `scripts/run_all.sh` and fails if any tracked output differs from the commit.

### Changed
- Iconify values (icon totals, samples, aliases, categories, last modification) are read from the set's npm package as it stood on the cut-off day, not from the live catalogue.
- npm package values use the version that was `latest` on the cut-off day, or the newest stable version published by then.
- Repository dates are UTC days. The earlier pipeline used the committer's local day.
- Author counts exclude bot accounts (names ending in `[bot]`).
- Document rules (changelog, contributing, security policy, CI, design files) are defined in `collect/RULES.md`.
- Icon contents (20 columns) are measured by `collect/3c_icon_content.py` following the definitions in `data/data_dictionary.csv` (see `collect/RULES.md`). The earlier npm-only values did not follow that definition and are replaced.

### Removed
- `famicons`, `thesvg`, `crewlethq-icons`, `xymbols`, `maru-icons`: moved to `data/removed_repackaged_copies.csv` as re-packaged copies (at least 70 % of their icons appear in an earlier set).

### Fixed
- `evicons`: last commit at the cut-off is f228acb (2026-11-13), 157 commits (the release had an earlier commit, f7275e6).
- `dou-ui-icons`, `softstroke-svg`: last-commit dates corrected from the author's local time zone to UTC.

### Corrections
- 5,054 cells corrected to the values collected on 2026-11-18 (`build_input/corrections.csv`). Before the correction the collected values agreed with the release in 35,610 of 40,664 non-blank cells (87.6 %). After the correction the release matches the collected values in all 122 compared columns.
- New measured columns: the 20 icon-content columns and `iconify_version`, `repo_activity`, `icons_aliases_n`, `icons_hidden_n`, `iconify_categories_n`, `iconify_set_last_modified`, `npm_deprecated`, `npm_provenance`, `npm_file_count_registry`, `npm_unpacked_size_measured_bytes`, `npm_package_files`, `npm_package_svg_files`, `npm_package_font_files`, `npm_downloads_change_pct`.

### Known limits
- 17 of 124 columns are not filled by the scripts (`collect/COVERAGE.md`): licence reading (11), discovery and identity (4), and two sources the scripts cannot read (`npm_dependents`, `npm_jsdelivr_hits_30d`). Their values are curated.
- The mean icon size is rounded to the nearest byte. The earlier release truncated it, which changes 105 Iconify values by one byte.
- Discovery of candidate sets is not reproduced by the scripts (see README).
