# Collection scripts

These scripts collect the measured values again from public sources, write them in the release's column layout, and compare them with `data/icon_sets_v3.csv`. The rules are in `RULES.md`. The columns they do not fill are in `COVERAGE.md`.

Standard library only, plus the `git` command. Run from the repository root.

## Three ways to use them

1. **Check the release from the saved evidence (no network, about 10 seconds).** The snapshots of the last live run are in `evidence/`:

   ```bash
   sh collect/run_compare_from_evidence.sh
   ```

   This rebuilds the merged table and `tests/collection_compare.md` from `evidence/` and writes the same output as the last live run.

2. **Collect again from the live sources (about 2 hours, network needed).** Writes the caches to `collect/work/` (not in the repository):

   ```bash
   sh collect/run_collect.sh
   ```

   The first run clones about 420 repositories without blobs (history and trees only). The npm stage makes about 2,500 requests. Values that move with time (downloads, stars, forks, the Iconify catalogue) will differ from the release; `7_compare.py` treats downloads, stars and forks as matching within 10 %, and the others as exact.

3. **Run the unit tests of the helpers (no network):**

   ```bash
   python3 -I tests/test_collect_utils.py
   ```

   These check the UTC day conversion, the cut-off and the semantic version pattern.

`run_all.sh` at the repository root runs the release checks and the unit tests. It does not run live collection.

## Stages

| Script | Source | Output |
|---|---|---|
| `1_iconify.py` | `api.iconify.design/collections` | the Iconify sets of the frame: name, author, licence, total, height, palette, tags, samples |
| `2_seed.py` | `data/icon_sets_v3.csv` | identity inputs only: npm package, repository and package folder of each set |
| `3_npm.py` | npm registry, `api.npmjs.org` downloads | versions, publish dates, licence, dependencies, types, unpacked size, stable releases in 730 days, median release gap, downloads; for `@iconify-json/*` the version as of the cut-off |
| `4_web.py` | `data.jsdelivr.com`, `ungh.cc` | jsDelivr hits (only the last 30 days are available, see below), GitHub stars, forks, creation date |
| `5_git.py` | git history of each repository (blobless clone) | commits, authors, tags and files on the default branch before the cut-off, and the same for the package folder |
| `6_merge.py` | the stages above | `collect/work/collected.csv`, release column layout |
| `7_compare.py` | release and collected table | `tests/collection_compare.md` |

Evidence files in `evidence/` are the outputs of stages 1, 3, 4 and 5 and the merged table of the last live run, plus `identity_seed.csv` (the input of stage 2). `run_compare_from_evidence.sh` reads only these.

## Not reproduced by these scripts

- **Discovery of the candidate sets.** The candidate sets were found by npm search, by reading the Iconify catalogue, and by the author's review of the lists. The scripts take the set list, the npm package and the repository of each set from the release (`2_seed.py`). They do not repeat the search, so a set that is missing from the release is not found by these scripts. The frame is what Iconify packages and what the author found on npm; it is not a census of icon libraries.
- **Licence reading.** `license_type`, `license_check`, `license_evidence` and the licence attributes come from reading licence texts by hand and by text matching. The scripts record the licence as Iconify and npm declare it.
- **Icon contents.** `3c_icon_content.py` reads the icon files of each cut-off version from its npm tarball (about ten minutes). It needs the network like the other stages.
- **GitHub API.** Stars and forks come from `ungh.cc`, a public cache of the GitHub API, because the API refused unauthenticated requests from the collection environment.
- **jsDelivr fixed window.** The jsDelivr statistics endpoint returns the last 30 days only, so the release's fixed window cannot be reproduced; `npm_jsdelivr_hits_30d` is not filled.
- **Tarball contents.** `.d.ts` files, package file counts and SVG counts inside the npm tarball need the tarballs. They are not downloaded.

## Time and cut-off

The cut-off is 2026-11-16 23:59:59 UTC. Git commits are selected with `--before` on the committer date; each date is written as a UTC calendar day. Downloads use the fixed windows in `common.py`.

Values that move with time are collected on the day the script runs. For those the comparison is a refresh, not a replay.

## Differences from the release

`RULES.md` lists the rules and how often each one agrees with the release. `tests/collection_compare.md` lists every cell that differs. Known differences are in `RULES.md` under "Not matched and open".
