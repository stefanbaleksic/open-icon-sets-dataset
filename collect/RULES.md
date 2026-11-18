# Rules used by the collection scripts

Each rule is what the script does. Before the release was corrected, the collected values agreed with the release in 35,610 of 40,664 non-blank collected cells (87.6 %). The differences are listed by column in `tests/collection_compare.md` before correction. The release was then corrected to the collected values, one correction row per cell, in `build_input/corrections.csv` (5,054 rows). After the correction the comparison shows 0 differences in the 122 compared columns.

## Dates and the cut-off

- Cut-off: 2026-11-16 23:59:59 UTC. Every date is a UTC calendar day (`common.utc_day`). Commits are selected with `git log --before` on the committer date.
- Live collection ran on 2026-11-18. Everything that depends on time is read as it stood on the cut-off, except the values listed under "Values that move" below.
- The earlier release used the committer's local day for repository commit dates. Those are corrected to UTC.
- npm: the tagged `latest` version if it existed on the cut-off day; otherwise the newest stable (`X.Y.Z`) version published by then. The tag history is not in the sources, so a tag moved after the cut-off can give a different version.
- Iconify sets (`@iconify-json/*`): the same version rule. The set's metadata (`info.json`) and icons (`icons.json`) are read from the tarball of that version, so the values are the ones Iconify had on the cut-off day. The live Iconify catalogue has moved on since (for example `codex` was modified on 2026-11-17).

## Iconify (`1_iconify.py`, `3_npm.py`, `6_merge.py`)

| Field | Rule |
|---|---|
| `name`, `author`, `iconify_category`, `iconify_tags`, `grid_px`, `palette`, `iconify_license`, `iconify_license_url` | from `info.json` of the cut-off version |
| `icons_total` | the set's `total` in `info.json` (style variants counted separately) |
| `sample_icons` | the first three samples in `info.json` |
| `icons_aliases_n` | number of entries in `aliases` in `icons.json` of the cut-off version |
| `icons_hidden_n` | icons with `hidden: true` in `icons.json` of the cut-off version |
| `iconify_set_last_modified` | `lastModified` of `icons.json` (UTC day) |
| `iconify_categories_n` | number of categories of the set in the Iconify collection endpoint (live catalogue: this value is not in the package and is not date-checked). 0 for sets outside Iconify |
| `iconify_package_version`, `iconify_package_last_publish` | the cut-off version and its publish day |
| frame | the live catalogue: sets hidden by Iconify or filed under "Archive / Unmaintained" are outside the frame. A set that Iconify hid after the cut-off would be left out by a live run |

## Repository facts (`5_git.py`)

| Field | Rule |
|---|---|
| `repo_commit_sha`, `repo_last_commit_date`, `repo_days_since_last_commit` | last commit on the default branch before the cut-off; days = cut-off day minus commit day (UTC) |
| `repo_activity` | active: last commit 90 days or less before the cut-off; recent: 91 to 365 days; dormant: more than 365 days (agrees with the release in 458 of 458 rows where the repository was read) |
| `repo_commits_total`, `repo_commits_365d` | all commits on the default branch before the cut-off, bots included |
| `repo_authors_total`, `repo_authors_365d` | distinct e-mail addresses of commits not made by bot accounts (names ending in `[bot]`) |
| `repo_top_author_share_365d` | commits of the most frequent non-bot e-mail in 365 days, divided by all non-bot commits in 365 days |
| `repo_has_readme` | root file named README |
| `repo_has_changelog` | a changelog-type file at the root: CHANGELOG, CHANGES, HISTORY, RELEASES or NEWS, any case, optional extra part and extension (agrees with the release in 457 of 458 rows; the remaining row is corrected) |
| `repo_has_contributing` | CONTRIBUTING at the root, in `.github/` or in `docs/` (agrees in 452 of 458) |
| `repo_has_security_policy` | SECURITY at the root, in `.github/` or in `docs/` (agrees in 458 of 458) |
| `repo_has_ci` | GitHub Actions workflow under `.github/workflows/`, or `.travis.yml`, `.gitlab-ci.yml`, `azure-pipelines.yml`, `.circleci/` (agrees in 457 of 458) |
| `repo_has_design_files` | a `.fig`, `.sketch`, `.afdesign`, `.figma`, `.xd`, `.psd` or `.ai` file at the root or in a package folder of the set (agrees in 456 of 458 in the test) |
| `repo_has_icon_font` | a `.woff`, `.woff2`, `.ttf`, `.otf` or `.eot` file anywhere in the tree |
| `repo_svg_files`, `repo_files_total` | `.svg` files and all files in the tree on the default branch |
| `repo_semver_tags`, `repo_latest_semver_tag`, `repo_latest_semver_tag_date` | tags `vX.Y.Z` or `X.Y.Z` on or before the cut-off, dated by the tagged commit (UTC) |
| package folder (`pkg_*`) | the same counts, restricted to commits that touch the package folder |

## Icon contents (`3c_icon_content.py`, `6_merge.py`)

The definitions are in `data/data_dictionary.csv`. The measures are pure functions in `collect/icon_measures.py`, tested in `tests/test_icon_measures.py`. The script reads each set's icons as they stood on the cut-off day, from the cut-off version's package.

| Field | Rule |
|---|---|
| Iconify sets | the icons in `icons.json` of the cut-off version; hidden icons are left out; the body is the icon's `body`. `iconify_version` is the `version` in `info.json` |
| other sets | the `.svg` files of the cut-off tarball, except sprite sheets (file names starting with `sprite`); the body is the content between the `<svg>` tag and `</svg>` |
| `median_icon_bytes`, `mean_icon_bytes` | median and mean length of the body in UTF-8 bytes; the mean is rounded to the nearest byte |
| `icon_viewbox_px` | the most common viewBox height |
| `icons_own_size_pct` | share of icons with their own width or height. Sets outside Iconify have no set default, so it is 0.0 for them |
| `icons_currentcolor_pct` | share of icons whose body contains `currentColor` (any case) |
| `icons_hardcoded_color_pct` | share with a `fill`, `stroke` or `stop-color` that is a hex value, `rgb()`, `hsl()` or a colour name; black and white, `none`, `currentColor`, `inherit` and `url()` do not count |
| `icons_gradient_pct` | share containing a linear or radial gradient |
| `icons_stroke_based_pct`, `stroke_width_mode` | share with a stroke other than `none` and not of width 0; the most common stroke width among them |
| `icons_animated_n` | icons with `animate`, `animateTransform`, `animateMotion` or `set` |
| `measured_palette` | monotone when at most 5 % of icons have hard-coded colours and at most 5 % have gradients; multicolor when at least half of the icons have either; otherwise mixed |
| `icon_construction` | stroke when at least 80 % of icons are stroke-based; fill when at most 20 %; otherwise mixed |
| `style_variants`, `style_variants_n`, `unique_base_names` | a name suffix after the last hyphen is a style when at least 20 % of names carry it and at least half of the base names carrying it have two or more suffixes; at least two styles are needed. `unique_base_names` counts the names without the style suffix |
| `icons_fingerprinted_n`, `icon_overlap_*` | each icon with path data gets two hashes of its path data: exact, and rounded to one decimal. `icon_overlap_max_pct` is the largest share of the set's fingerprinted icons that also occur in one other set of a different package; at least 20 fingerprinted icons are needed. `icon_overlap_basis` is `exact` or `rounded_1dp`, whichever is higher; `icon_overlap_with` names the other set |
| `remix_name_overlap_pct` | share of the set's base names that also occur among the base names of Remix Icon (`ri`) |

The overlap uses only the sets of the table, so it changes when the table changes. On a tie (the same number of shared icons with two sets), the set with the smaller `set_id` is named. Where the release named a different set, the cell is corrected (`icon_overlap_with`, 56 cells).

## npm (`3_npm.py`, `6_merge.py`)

| Field | Rule |
|---|---|
| `npm_versions_total` | number of entries in the registry `versions` object |
| `npm_first_publish`, `npm_last_publish`, `npm_latest_version` | first publish time; the cut-off version and its publish day |
| `npm_has_types` | the `types` or `typings` field of the cut-off version, or a `.d.ts` file in its tarball |
| `npm_file_count_registry` | `dist.fileCount` of the cut-off version |
| `npm_unpacked_size_bytes`, `npm_unpacked_size_measured_bytes` | `dist.unpackedSize`; the sum of file sizes in the tarball |
| `npm_package_files` | files in the tarball |
| `npm_package_svg_files` | `.svg` files in the tarball except sprite sheets (file names starting with `sprite`) |
| `npm_package_font_files` | `.woff`, `.woff2`, `.ttf`, `.otf`, `.eot` files in the tarball |
| `npm_deprecated` | the cut-off version carries a `deprecated` field |
| `npm_provenance` | npm publishes a provenance attestation for the cut-off version |
| `npm_downloads_30d`, `npm_downloads_prev30d`, `npm_downloads_365d` | registry downloads, fixed windows in `common.py` |
| `npm_downloads_change_pct` | 30 days against the previous 30 days, percent, one decimal |
| `release_gap_median_days` | median gap in days between stable releases, when there are at least 10 in 730 days |
| `stable_releases_730d` | stable versions published in the 730 days before the cut-off |

The tarball is read in memory and not stored. Packages whose tarball is larger than 150 MB (Iconify sets: 400 MB) are not opened.

## Web (`4_web.py`)

| Field | Rule |
|---|---|
| `npm_jsdelivr_hits_30d` | jsDelivr statistics: the last 30 days only (not a fixed window) |
| `gh_stars`, `gh_forks`, `gh_created_date` | `ungh.cc` repository record on the day of the run |

## Values that move

Downloads, stars, forks and jsDelivr hits are measured on the day of the run. The comparison treats them as matching within 10 %. The release was corrected to the run-day values for every cell that differed (including the ones within 10 %), so these values are the run-day values, not the cut-off values. Their collection date is 2026-11-18.

## Corrections and what they change

`build_input/corrections.csv` has 5,054 rows, one per cell where the collected value was not blank and differed from the release. Grouped by column:

- Icon contents (20 columns, see "Icon contents" above): 3,272 cells. `median_icon_bytes` (340) and `mean_icon_bytes` (445) follow the dictionary definition; 105 of the mean corrections are Iconify sets that differ by one byte, because the release truncated the mean and the rule rounds it.
- `npm_downloads_365d` (263), `iconify_downloads_365d` (158), `gh_stars` (131), `gh_forks` (52): moving values, run-day values (see above).
- `icons_total_source` (231): the text now says the value is the set's total on the cut-off day.
- `repo_top_author_share_365d` (202), `repo_authors_total` (54), `repo_authors_365d` (16): the bot-account rule.
- `repo_first_commit_date` (66), `repo_last_commit_date` (60), `repo_days_since_last_commit` (58): UTC days.
- `release_gap_median_days` (140), `npm_package_svg_files` (78), `npm_has_types` (22), `npm_versions_total` (23), `npm_last_publish` (28), `npm_first_publish` (8), `stable_releases_730d` (11): the cut-off package rule and the tarball rules above.
- `repo_has_design_files` (30), `repo_has_contributing` (6), `repo_has_changelog` (1), `repo_has_ci` (1): the document rules above.
- `repo_latest_semver_tag_date` (25), `repo_commit_sha` (4), `repo_files_total` (44), `repo_svg_files` (16), other single cells.

Each correction states the old value (from the viewer, before corrections) and the new value; `scripts/apply_corrections.py` stops if an old value does not match.

Reasons for the corrections in `build_input/corrections.csv` that were written earlier are kept. The rest say: collected on 2026-11-18 by `collect/`, and the release value was different.

## Licence columns (curated, not measured)

Eleven columns (`license_type`, `license_check`, `license_restrictions`, `license_evidence`, `license_spdx_confirmed`, `license_osi_approved`, `license_fsf_libre`, `license_attribution_required`, `license_commercial_use`, `license_derivatives_allowed`, `license_share_alike`) come from reading the licence text. The scripts do not read licence texts; they only record the licence fields that registries declare (`iconify_license`, `npm_license_declared`).

Protocol for a future update of these columns:

- The text read is the licence file of the cut-off version of the package, or the repository's licence file at the cut-off commit. Where neither exists, `license_check` says `not_checked`.
- `license_evidence` names the file and the line or section relied on.
- `license_type` uses the categories already in the release: permissive, copyleft, cc_share_alike, creative_commons_attribution, public_domain, custom_restricted, split_or_dual, split_by_asset, not_classified.
- Each change is a correction row with the reason, like every other cell.

The values in this release were not produced by a script and cannot be regenerated by `run_all.sh`.

## Not measured

See `COVERAGE.md`: 17 columns are not filled by the scripts: licence reading (11), discovery and identity (4: `repo_source`, `npm_package_source`, `release_status`, `in_v1`), and two sources the scripts cannot read (`npm_dependents`, `npm_jsdelivr_hits_30d`). Their values stay as curated in the release.
