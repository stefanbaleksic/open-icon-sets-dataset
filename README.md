# Icon Sets Dataset v3 (draft)

One row per open icon set: 571 sets with icon totals, licence (as Iconify reports it, and as checked against the licence text where possible), repository, npm releases, downloads and icon-content measures. Snapshot cut-off **2026-11-16 23:59:59 UTC**; live collection run on 2026-11-18. Status: **draft, not published, no DOI yet**.

Collected and checked with AI assistance under the author's direction. Not independently reviewed.

## Files

| File | Content |
|---|---|
| `data/icon_sets_v3.csv` | 571 rows, 124 columns. The dataset. |
| `data/data_dictionary.csv` | Every column: type (text or number) and meaning. |
| `data/removed_repackaged_copies.csv` | 5 sets removed from the main table as re-packaged copies, with the reason and the original row number. |
| `data/overlap_blanked.csv` | Rows whose overlap value named a removed set; their overlap fields were blanked (2 rows). |
| `build_input/viewer_v3.html` | The HTML viewer that carries the full dataset. The only source the CSV is built from. |
| `build_input/corrections.csv` | Documented cell corrections (set, column, old value, new value, reason). 5,054 rows. The script stops if an old value does not match. |
| `build_input/manual_removals.csv` | Manual removals with reason. Empty: no manual removals in this release. |
| `scripts/run_all.sh` | Rebuilds `data/` from the viewer, runs every check and writes `SHA256SUMS`. Exit status 0 only if all checks pass. |
| `scripts/extract_from_artifact.py` | Reads the embedded data from the viewer and writes it as CSV plus the data dictionary. |
| `scripts/apply_corrections.py` | Applies the documented corrections. |
| `scripts/clean_repackaged_copies.py` | Applies the copy rule and the manual removals, blanks overlap values that named a removed set, and writes the main table and the removed list. |
| `scripts/write_sha256sums.sh` | Writes `SHA256SUMS` for every file in the release (except the build folder and collection caches). |
| `tests/check_dataset.py` | Consistency checks on `icon_sets_v3.csv`. |
| `tests/test_duplicates.py` | Duplicate checks. |
| `tests/test_collect_utils.py` | Unit tests for the collection helpers: UTC day conversion, cut-off, semantic version tags. |
| `tests/test_icon_measures.py` | Unit tests for the icon-content measures (sizes, colours, strokes, fingerprints, style variants, overlap), with hand-checked examples. |
| `tests/test_docs_numbers.py` | Checks that the figures in the documents match the data, and that the citation version matches the changelog. |
| `tests/validation_report.txt`, `tests/duplicate_report.txt` | Output of the release checks from the last run. The unit-test output goes to `build/reports/` (not tracked, because it contains timings and local paths). |
| `tests/collection_compare.md` | Column-by-column comparison of the collected values with the table. |
| `collect/` | Collection scripts: they collect the measured values again from public sources and write them in the release layout. See `collect/README.md`, `collect/RULES.md` (every rule, with how often it agrees with the release) and `collect/COVERAGE.md` (columns not filled). |
| `collect/icon_measures.py` | Pure functions for the icon-content measures (no network); tested in `tests/test_icon_measures.py`. |
| `.github/workflows/check.yml` | Continuous check: runs `scripts/run_all.sh` and fails if any tracked output differs from the commit. |
| `collect/run_compare_from_evidence.sh` | Rebuilds the collected table and the comparison from `evidence/`, without network access. |
| `evidence/` | Saved outputs of the last live collection run (Iconify, npm, jsDelivr and GitHub-cache, git facts, merged table, identity seed). |
| `SHA256SUMS` | SHA-256 of every file in the release. |
| `CHANGELOG.md` | Versions, changes and the rule for each kind of change (semantic versioning). |
| `LICENSE.md`, `CITATION.cff` | Licences and how to cite. |

## Reproducing the table

From the repository root (Python 3, standard library only, `git` for one check):

```bash
sh scripts/run_all.sh
```

This extracts the data from `build_input/viewer_v3.html`, applies the corrections and the copy rule, runs the release checks, the duplicate tests and the collection unit tests, rebuilds the comparison from `evidence/` and writes `SHA256SUMS`. It needs no network access. The GitHub Actions workflow in `.github/workflows/check.yml` runs the same script on every push and pull request, and fails if any tracked output changes.

To verify a download, compare the files with `SHA256SUMS`:

```bash
sha256sum -c SHA256SUMS
```

To collect the measured values again from the live sources (about two hours, network needed), run `sh collect/run_collect.sh`. Results differ from the release where values move with time, and where the rules differ (see `collect/RULES.md`).

## Rows and sampling frame

- **Iconify** (231 rows): the Iconify catalogue on the collection date, minus sets Iconify hides or files under "Archive / Unmaintained". Two Iconify sets were removed as copies (see below).
- **v1 (not in Iconify)** (9 rows) and **v1 (Iconify set archived or hidden)** (4 rows): design-system and other sets from the earlier hand-made list that Iconify does not carry, or carries as archived or hidden.
- **npm discovery (not in Iconify)** (327 rows): packages found on npm that Iconify does not carry. Three were removed as copies (see below).

**Discovery is not reproduced by the scripts.** The candidate list was built by searching npm and by the author's review of the Iconify catalogue and of the earlier hand-made list. The collection scripts start from the list in the release. A set that the search and review did not find is not in this dataset. The frame is not a census of icon libraries.

## Removal of re-packaged copies

Some sets are mostly made of icons from another set. They are kept in a separate file, not in the main table.

Rule: a set is moved out when at least 70 % of its icons appear in another set in the candidate table (`icon_overlap_max_pct`, `icon_overlap_with`), and that other set has an earlier origin date (the earlier of the repository's first commit and the npm first publish).

Five sets were moved: `famicons` (98.9 % in `ion`), `thesvg` (88.3 % in `simple-icons`), `crewlethq-icons` (74.9 % in `qeetrix-icons`), `xymbols` (74.1 % in `qeetrix-icons`), `maru-icons` (71.3 % in `qeetrix-icons`). The reasons are in `removed_repackaged_copies.csv`.

The rule is a heuristic. Overlap is measured on icon files, so a large shared brand set can produce overlap without copying.

`aws-icons-directory` (70.6 % of its icons appear in `aws-iconic`) is kept. The copy rule does not move it, because the origin dates do not show that `aws-iconic` came first. The author decided to keep it: removing it would not change the dataset materially, and the decision is recorded here.

Where a kept row's overlap value named a removed set, the overlap fields of that row (`icon_overlap_max_pct`, `icon_overlap_with`, `icon_overlap_basis`) are blank, listed in `data/overlap_blanked.csv`. The new maximum over the kept sets needs the icon data, which is not part of this release.

Ids were renumbered after removal. `set_id` is the stable key; `original_id` in the removed file gives the old number.

## Reading the values

- `icons_total` follows Iconify, which counts each style variant (outline, filled, …) as an icon. It is not a count of unique icons.
- `npm_downloads_30d` is set per npm package. Sets that share a package (for example Boxicons, Font Awesome, Unicons) show the same value.
- `iconify_downloads_30d` is the only usage figure that exists for every Iconify set. Downloads are not users.
- `license_check`: `not_checked` means the licence could not be confirmed, not that there is no licence. `not_classified` in `license_type` means no licence was declared or found (4 rows).
- Licence flags are a mapping from `license_type`, not a legal reading. Not legal advice.
- `repo_*` facts describe the whole repository on its default branch before the cut-off. Where several sets share a repository, `sets_from_same_repo` shows how many rows share it, and commit and file counts are not per set. Package-folder counts are in the `pkg_*` columns.
- Author counts are distinct e-mail addresses of commits not made by bot accounts (names ending in `[bot]`). Commit counts include bots.
- Document rules (changelog, contributing, security policy, CI, design files) are written in `collect/RULES.md`.
- A blank `icon_overlap_max_pct` means no overlap is reported against the kept sets: either the overlap was not measured, or the highest overlap was with a removed set (see `data/overlap_blanked.csv`).

## Corrections

`build_input/corrections.csv` lists every corrected cell with its old value (from the viewer, before corrections), new value and reason. It has 5,054 rows, one per cell that the collection scripts measure and that differed from the release. The collection scripts measured 122 release columns; after the corrections the comparison shows 0 differences in those columns (`tests/collection_compare.md`). The rules are in `collect/RULES.md`.

Main groups: moving values refreshed on the day of the live run (downloads, stars, forks); repository dates in UTC (the release had the committer's local day, 126 rows); the bot-account rule for authors; the cut-off package rule for Iconify and npm values; the document rules (changelog, contributing, security, CI, design files); the tarball rules for file counts and types. Two earlier corrections by hand remain: `dou-ui-icons` and the `evicons` last commit.

`collect/make_corrections.py` writes the file from the collected values. `scripts/run_all.sh` applies the committed file and does not need the network.

## Tests

`tests/check_dataset.py` checks identifiers, numeric and date formats, URLs, licence values, npm downloads per package, shared repositories, the copy rule and dictionary coverage. Last run: **0 failures, 0 warnings**.

`tests/test_duplicates.py` checks for duplicates: identical identifiers and names, rows identical apart from the id, sets still in the table that meet the copy rule, that kept and removed sets together make the whole candidate frame without overlap, shared repositories and npm packages, and one Iconify package listed twice. Patterns that are expected are reported as INFO. Last run: **0 failures**, 35 INFO lines.

`tests/test_collect_utils.py` checks the UTC day conversion (including local offsets and the daylight-saving change), the cut-off, and the semantic version pattern. Last run: **15 tests passed**.

`tests/test_icon_measures.py` checks the icon-content measures on small examples whose results are worked out by hand: byte sizes and the mean rounding, colours (black and white excluded), gradients, stroke construction, fingerprints, style variants, and the overlap rules (different packages only, at least 20 fingerprints). Last run: **26 tests passed**.

`tests/test_docs_numbers.py` checks that the counts in README, CHANGELOG, RULES and COVERAGE match the table, the corrections and the test output, that no stale count remains, and that `CITATION.cff` has the version of the latest changelog entry.

`collect/run_compare_from_evidence.sh` rebuilds the collected table from `evidence/` and the comparison with the release. Last run: **41,231 cells compared, 0 differ**.

## Limits

- Collection cut-off 2026-11-16 23:59:59 UTC. The live collection ran on 2026-11-18. Values that move with time (downloads, stars, forks, jsDelivr hits) are the 2026-11-18 values; the other values are the values on the cut-off day.
- **Not measured by the scripts: 17 of 124 columns** (`collect/COVERAGE.md`): licence reading (11 columns), discovery and identity (4 columns: `repo_source`, `npm_package_source`, `release_status`, `in_v1`), and two sources the scripts cannot read (`npm_dependents`, `npm_jsdelivr_hits_30d`). They are curated in this release and are not regenerated by `run_all.sh`.
- **Discovery is not reproduced by the scripts.** The candidate list was built by searching npm and by the author's review of the Iconify catalogue and of the earlier hand-made list. The scripts start from the list in this release.
- Iconify frame: the live catalogue decides which sets are in the frame (hidden or archived sets are left out).
- Iconify is a snapshot per cut-off version; licence declarations in the packages can differ from the publisher's text.
- npm packages are confirmed for 425 rows. A missing package is not evidence that none exists.
- Author counts use e-mail addresses (bot accounts excluded), so one person with several addresses counts several times.
- Licence summaries describe the text and are not legal advice.

## Licence and citation

Data and documentation: CC BY 4.0. Scripts and tests: MIT. See `LICENSE.md`. Author ORCID is in `CITATION.cff`.

No DOI yet. The DOI for Zenodo and Kaggle will be added after the upload, in a commit that updates `README.md` and `CITATION.cff`.

## Changes from v2 (246 rows)

- The table now includes npm-discovery candidates (327 rows kept) and 9 v1 sets not carried by Iconify.
- Five re-packaged copies were moved out of the main table (see above); 571 rows remain. `aws-icons-directory` was considered for removal and kept.
- Repository dates were corrected from the local time zone to UTC (see `build_input/corrections.csv`).
- Collection scripts, evidence snapshots, the release checks, the collection unit tests, `LICENSE.md`, `CITATION.cff`, `SHA256SUMS` and the reproduction script were added.
- The v2.1 column list was not compared cell by cell in this release; the v2.1 files are not part of this package.
