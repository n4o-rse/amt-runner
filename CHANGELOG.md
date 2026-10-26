# Changelog

All notable changes to amt-runner are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project uses [Semantic Versioning](https://semver.org/). The version
describes `run_amt.py`, not the AMT.engine it runs.

The entries for 0.1.0 and 0.2.0 were reconstructed from the commit history;
each date is that of the commit that delivered the change. The tags `v0.1.0`
and `v0.2.0` were set afterwards on exactly those commits. 0.2.1 is the first
release published on GitHub and archived on Zenodo.

## [Unreleased]

### Added

- The Zenodo DOI `10.5281/zenodo.23669557` (all versions) in `CITATION.cff`,
  and a "Citation" section with the DOI badge in `README.md`. Release 0.2.1
  itself is archived as `10.5281/zenodo.23669558`.

## [0.2.1] - 2026-10-26

0.2.1 changes no behaviour of `run_amt.py`, apart from the new `__version__`
constant. It adds the development pipeline, offline tests, citation metadata
and continuous integration.

### Added

- `__version__` in `run_amt.py` (no new command-line flag).
- `PRIMER.md`: German work plan with the standing rules, the decisions taken so
  far and the numbered steps for this repository.
- `main.py` and `py/`: a development pipeline with the steps `meta` and `tests`
  (`--list`, `--only`, `--from`, `--skip`, `--dry-run`, `--strict`). It needs no
  network. `run_amt.py` stays a single self-contained file.
- `tests/`: offline tests for ref resolution in the cached shallow clone (tip,
  tag and commit outside the shallow history, `--update`, unknown ref), the
  dependency fingerprint, feature detection, argument forwarding and the
  `out/latest` pointer. A local git repository stands in for the engine.
- `.github/workflows/ci.yml`: runs `python main.py --strict` on push to `main`
  and on pull requests, on Ubuntu and Windows with Python 3.10 and 3.13, and
  keeps `build/pipeline_report.txt` of each job as an artefact.
- `CITATION.cff` (authors Florian Thiery and Allard W. Mees, with ORCIDs), `requirements.txt` (development only; the runner itself needs
  just the standard library) and this changelog.

### Changed

- The CI workflow uses `actions/checkout@v5`, `actions/setup-python@v6` and
  `actions/upload-artifact@v5`, which run on Node 24.
- `LICENSE`: the copyright holder reads "Florian Thiery | LEIZA | Research
  Squirrel Engineers Network" (was "NFDI4Objects | Research Software
  Engineering Projects"), the same as in AMT.engine.
- `README.md`: the layout lists every bundled example, the pinning example uses
  the engine commit `41620dd`, and a "Development" section describes `main.py`.
- `.gitignore`: also ignores `build/`, `.pytest_cache/` and `PATCH-README.md`.

## [0.2.0] - 2026-08-29

### Added

- `--minimal`: asks the engine to drop inferred edges that a finer role already
  implies (`amt:SubsumptionAxiom`, AMT.engine 0.3.0 or newer). If the cached
  engine is older, the script says so and names `--update` instead of letting
  the engine fail with an argument error.
- Flags the wrapper does not know are forwarded to `amt.runner` unchanged, so a
  new engine option works here before the wrapper has heard of it.
- Dependencies are installed from the engine's own `requirements.txt`, with the
  previous fixed list as a fallback for older refs. The marker file now stores a
  fingerprint of the file, so a changed requirement list triggers a reinstall.
- Every run prints the engine commit it used.
- `subsumption-demo.ttl` and `subsumption-demo.md`.

### Fixed

- Ref pinning: the cache is checked out detached at `origin/<ref>`, so a local
  branch left over from an earlier run can no longer point at a stale commit.
  A tag or commit that is not in the shallow clone is fetched on demand, and an
  unknown ref ends with a clear message instead of a bare git error.

## [0.1.0] - 2026-05-05

### Added

- First version of `run_amt.py`: clones AMT.engine into `.amt-cache/`, installs
  `rdflib`, `pyshacl` and `pyvis` once, and runs `amt.runner` into a fresh
  `out/run-<timestamp>/` folder, with `out/latest` pointing at the newest run.
- Options `--outdir`, `--ref` and `--update`.
- Bundled examples with a companion `.md` each: `animals`,
  `PotterAttributionExample`, `SKOSconceptExample`.
- README with quickstart, output layout and an expected-output walkthrough.

[Unreleased]: https://github.com/n4o-rse/amt-runner/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/n4o-rse/amt-runner/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/n4o-rse/amt-runner/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/n4o-rse/amt-runner/commit/fc8d18d
