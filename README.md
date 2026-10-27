# amt-runner

A small wrapper script that runs the [AMT.engine](https://github.com/n4o-rse/amt-engine)
pipeline on a single Turtle file — **validate → reason → export everything** —
without requiring you to clone or install the engine yourself.

This repo is meant as a **demo template**: clone it, drop in your own `.ttl` file,
run the script, get the full set of outputs in `out/`. Use it as a starting point
for your own AMT-based projects.

> **Two things called amt-runner.** This repository is a wrapper that fetches the
> engine and runs it for you. The engine itself also has a command called
> `amt-runner` (`python -m amt.runner`), which is the pipeline this wrapper calls.
> The wrapper is `run_amt.py`; the engine's command needs the engine installed.

## What it does

`run_amt.py` is a self-contained Python script that:

1. **Clones AMT.engine** from GitHub into a local cache (`.amt-cache/`)
2. **Installs its run-time dependencies** (rdflib, pyshacl, pyvis) into your active Python — once, as listed in `[project].dependencies` of the engine's own `pyproject.toml`; the engine's development packages are not installed
3. **Runs `amt.runner`** — the engine's own full-pipeline entry point — into a fresh, timestamped folder:
   - SHACL validation against the AMT shapes
   - Fuzzy-logic reasoning (n-ary role chains, inverse roles, role subsumption)
   - Consistency check
   - Export to Turtle, Neo4j Cypher, two CSVs (nodes/edges), interactive HTML graph
   - A Markdown run report documenting the whole run

Each run gets its own subfolder under `out/`, so previous runs are preserved
and runs against different input files don't collide.

## Requirements

- Python ≥ 3.10
- `git` on your `PATH`

## A note on Python environments

The script installs the engine's dependencies (currently `rdflib`, `pyshacl`
and `pyvis`) into whatever Python you use to run it. If you don't want them in your global Python, create a venv
first:

```bash
python -m venv .venv
# Linux/Mac:
source .venv/bin/activate
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
```

On modern Debian/Ubuntu, installing into the system Python is blocked by
default ([PEP 668](https://peps.python.org/pep-0668/)) — a venv is required there.
On Windows and macOS, installing globally works but a venv is still cleaner.

## Quickstart

```bash
git clone https://github.com/n4o-rse/amt-runner.git
cd amt-runner
python run_amt.py animals.ttl
```

The first run downloads AMT.engine and installs its dependencies. Allow
roughly 30 seconds on Windows, less on Linux/Mac. Subsequent runs are
near-instant.

## How to use this repo

There are three realistic ways to work with `amt-runner`, depending on what
you want to do:

### Just try it out

You want to see what AMT.engine produces for a TTL file. Clone, run, look at
`out/latest/animals.html`. Done. No GitHub account needed.

```bash
git clone https://github.com/n4o-rse/amt-runner.git
cd amt-runner
python run_amt.py animals.ttl
```

### Run AMT on your own data, long-term

You have your own AMT-shaped data and want a stable setup to keep running it.
The cleanest pattern is to create your own repository alongside this one and
copy `run_amt.py` into it — together with your TTL files. This way your data
lives in a repo you control, with its own history, and `run_amt.py` just rides
along as a small piece of glue.

```bash
mkdir my-amt-project
cd my-amt-project
curl -O https://raw.githubusercontent.com/n4o-rse/amt-runner/main/run_amt.py
curl -O https://raw.githubusercontent.com/n4o-rse/amt-runner/main/.gitignore
# add your own TTL files
git init && git add . && git commit -m "Initial commit"
```

You don't need to fork `amt-runner` for this. Forking would mark your repo as
"forked from n4o-rse/amt-runner" on GitHub, which is the wrong signal if your
repo is really about your data, not about contributing to the runner.

### Contribute back to amt-runner

You found a bug in `run_amt.py`, want to add a feature, or improve the README.
This is the case where forking makes sense:

1. Fork `n4o-rse/amt-runner` on GitHub
2. Clone your fork, make changes, commit, push
3. Open a pull request against `n4o-rse/amt-runner:main`

## How outputs are organised

Each run writes to a fresh, timestamped subfolder:

```
out/
├── latest                         → symlink to the most recent run
├── run-20260505-104530/           ← first run, animals.ttl
│   ├── animals.reasoned.ttl
│   ├── animals.cypher
│   ├── animals.nodes.csv
│   ├── animals.edges.csv
│   ├── animals.html
│   └── animals.report.md
├── run-20260505-112614/           ← second run, animals.ttl again
│   └── ...
└── run-20260505-112617/           ← third run, different TTL
    ├── potter.reasoned.ttl
    └── ...
```

This means you can run the script repeatedly, on different inputs, without
losing earlier outputs. Pick `out/latest/` for "show me the last run" or a
specific `run-...` folder when you want to compare two runs side by side.

On Windows without developer mode, `latest` becomes a copy instead of a
symlink — same effect, just a bit more disk usage.

## The bundled example: `animals.ttl`

The repository ships with [`animals.ttl`](animals.ttl), a deliberately rich
example that exercises most of what AMT.engine can do. It models two intertwined
domains:

- A small **biological taxonomy** — `Tiger isSubclassOf Cat isSubclassOf Mammal isSubclassOf Animal`
- A real **family tree** of individuals — Bagheera the tiger is the great-great-grandfather of Mowgli

The interesting part is the cross-over: composing an `isInstanceOf` edge with
an `isSubclassOf` edge yields a new `isInstanceOf` edge. Once the engine knows
"Mowgli isInstanceOf Tiger" and "Tiger isSubclassOf Cat", it derives "Mowgli
isInstanceOf Cat" on its own — and chains that further up to Mammal and Animal.

The example uses four different fuzzy-logic operators, each chosen for what it
actually means in the domain (Gödel for taxonomy transitivity, Product for
grandparenthood, geometric mean for long ancestry chains). See the comments at
the top of `animals.ttl` for the full reasoning.

## Expected output

```
[1/3] Cloning https://github.com/n4o-rse/amt-engine.git ...
      engine ref 'main' at a50822c Merge branch 'main' of ...
[2/3] Installing dependencies into /path/to/python
      (rdflib>=7.0, pyshacl>=0.25, pyvis>=0.3; from the engine's pyproject.toml)
[3/3] Running pipeline on animals.ttl ...
VAL  Validating animals.ttl ...
OK   Validation passed.
LOAD Loading animals.ttl ...
OK   2 Concepts | 7 Roles | 26 Nodes | 46 Edges | 7 Axioms

OK   Consistency check passed.
     reasoning produced 106 inferred edge(s)
OK   wrote out/run-20260505-104530/animals.reasoned.ttl
OK   wrote out/run-20260505-104530/animals.cypher
OK   wrote out/run-20260505-104530/animals.nodes.csv
OK   wrote out/run-20260505-104530/animals.edges.csv
OK   wrote out/run-20260505-104530/animals.html
OK   wrote out/run-20260505-104530/animals.report.md

✓ Outputs written to ./out/run-20260505-104530
  (also accessible via ./out/latest)
    - animals.cypher
    - animals.edges.csv
    - animals.html
    - animals.nodes.csv
    - animals.reasoned.ttl
    - animals.report.md

  To look at the graph, open the AMT Explorer, https://n4o-rse.github.io/amt-engine/explorer/
  and load animals.reasoned.ttl with the folder button (it opens in your browser, nothing is uploaded).
```

The 46 asserted edges expand to **152 total edges** (46 asserted + 106 inferred)
once reasoning runs. That's the whole point of the engine.

### What's in the output files

**`animals.reasoned.ttl`** — the original graph plus inferred edges, each tagged
with provenance pointing at the axiom that produced it:

```turtle
_:i17
    rdf:subject    ex:Mowgli ;
    rdf:predicate  ex:isInstanceOf ;
    rdf:object     ex:Cat ;
    amt:weight     "0.91"^^xsd:decimal ;
    amt:inferred   "true"^^xsd:boolean ;
    amt:provenance ex:TaxonomyChain .
```

**`animals.cypher`** — Neo4j-ready `CREATE` statements. Pipe into `cypher-shell`
or paste into the Neo4j Browser to materialise the graph in a database.

**`animals.nodes.csv` / `animals.edges.csv`** — the same graph in tabular form.
Useful for quick spreadsheet inspection, import into Gephi or other graph
tools, or pandas analysis.

**`animals.html`** — a standalone, interactive graph (powered by pyvis). Open in
any browser; no server needed. Asserted edges appear solid, inferred edges
dashed.

**`animals.report.md`** — a Markdown run-report documenting the run: timestamp,
options, validation status, ontology summary, every inferred edge with its
provenance, list of output files. Designed for the situation where you come
back to an old `out/` folder six months later and want to know exactly what
produced it.

## Using your own data

Drop a Turtle file into the repo root (or anywhere you can reach by path) and
point the script at it:

```bash
python run_amt.py my-data.ttl
python run_amt.py path/to/my-data.ttl --outdir results/
```

Flags the wrapper does not recognise go straight through to `amt.runner`,
so anything the engine's own CLI accepts works here too:

```bash
python run_amt.py my-data.ttl --no-check --height 900px
```

The one exception is `-o` / `--outdir`: that belongs to the wrapper, which
manages the per-run subfolder itself.

Your file needs to follow the AMT vocabulary — Concepts, Roles, weighted edges,
and (optionally) RoleChainAxioms, InverseAxioms or SubsumptionAxioms. The bundled
[`animals.ttl`](animals.ttl) is the most complete worked example; for the formal
specification see the [AMT.engine README](https://github.com/n4o-rse/amt-engine).

## Options

| Flag | Default | Effect |
|---|---|---|
| `--outdir DIR` | `out/` | Parent directory for run subfolders |
| `--minimal` | off | Suppress inferred edges implied by a finer role (needs engine ≥ 0.3.0) |
| `--ref REF` | `main` | Pin AMT.engine to a tag, branch, or commit SHA |
| `--update` | off | Fetch the current engine before running |

Everything else is forwarded to `amt.runner` — `--no-check`, `--no-report`,
`--no-info`, `--height`, and whatever the engine gains next.

Pinning is the right move for reproducible pipelines. Branches, commit SHAs
and tags all work; the engine publishes a tag for every release (`v0.3.1` was
the first one that is archived on Zenodo, `v0.4.0` is the current one). The cache is
cloned shallow, so a ref other than the tip of `main` is not in it at first;
the script notices and fetches the rest of the history on demand rather than
failing:

```bash
python run_amt.py animals.ttl --ref v0.4.0
python run_amt.py animals.ttl --ref 41620dd1e9f57bfbb3f4db543853aec8ecd2a906
```

Pin a tag or a SHA rather than `main` for anything whose results you intend to
cite. The default stays `main`, so a plain run always uses the current engine.

## Keeping the cached engine current

The cache is a disposable mirror of the engine, cloned once and reused. It
does **not** update itself — a cache created months ago keeps running that
version of the engine, silently, until you ask for something it cannot do.
Every run prints the commit it used, which is how you notice.

```bash
python run_amt.py animals.ttl --update
```

`--update` fetches and checks out the current `origin/main`. If a feature
you asked for is missing from the cached engine — `--minimal`, say — the
script says so and names `--update` rather than letting the engine fail with
an argument error. Deleting `.amt-cache/` works too; the next run re-clones.

The cache is always checked out detached at the exact remote commit, so
there is no local branch to fall behind.

Every run prints which commit it used, so the run report and the engine
revision can be matched up later.

## Role subsumption and `--minimal`

AMT.engine 0.3.0 added `amt:SubsumptionAxiom`, for vocabularies whose roles
are *sets* of finer roles — Freksa's semi-interval relations, for instance,
where `ob` = {`<`, `m`, `o`} is contained in `ol` = {`<`, `m`, `o`, `fi`,
`di`}. Without it, a reasoner derives every member of such a chain
independently: all true, all but the finest redundant.

By default the engine spells the hierarchy out, so that a tool consuming the
Cypher or the CSVs without knowing the role hierarchy still sees every edge.
`--minimal` does the opposite: it drops an inferred edge when a finer edge
relates the same pair at no lower weight.

```bash
python run_amt.py subsumption-demo.ttl            # 8 asserted → 18 edges
python run_amt.py subsumption-demo.ttl --minimal  # 8 asserted → 11 edges
```

Both runs land in their own `out/run-.../` folder, so the two
`subsumption-demo.edges.csv` files can be diffed directly.
[`subsumption-demo.md`](subsumption-demo.md) documents every derivation and
explains why one coarse edge survives `--minimal` while another does not.

Files without subsumption axioms — including `animals.ttl` — produce
identical output in both modes.

## Repository layout

```
amt-runner/
├── run_amt.py          # the wrapper script (self-contained, copy it freely)
├── animals.ttl         # demo input, with animals.md
├── subsumption-demo.ttl  # demo input for --minimal, with subsumption-demo.md
├── PotterAttributionExample.ttl  # demo input, with a companion .md
├── SKOSconceptExample.ttl        # demo input, with a companion .md
├── main.py             # development pipeline (see "Development")
├── py/                 # the steps behind main.py
├── tests/              # offline tests for run_amt.py
├── PRIMER.md           # work plan and decisions (German)
├── CHANGELOG.md
├── CITATION.cff
├── requirements.txt    # development only; run_amt.py needs the standard library
├── .github/workflows/  # ci.yml (main.py --strict on push and pull request),
│                       # network.yml (smoke and drift, weekly and on request)
├── README.md
├── .gitignore
├── .amt-cache/         # created on first run, git-ignored
│   ├── amt-engine/     # cloned engine source
│   └── .deps-installed # marker; prevents reinstalling on every run
└── out/                # created on first run, git-ignored
    ├── latest          # symlink/copy pointing at the most recent run
    └── run-YYYYMMDD-HHMMSS/
        ├── <stem>.reasoned.ttl
        ├── <stem>.cypher
        ├── <stem>.nodes.csv
        ├── <stem>.edges.csv
        ├── <stem>.html
        └── <stem>.report.md
```

## Resetting the cache

If something goes wrong, just nuke the cache:

```bash
rm -rf .amt-cache
```

The next run will re-clone and re-install. The dependencies stay installed in
your Python environment — to remove them, `pip uninstall rdflib pyshacl pyvis`.

To delete old runs:

```bash
rm -rf out/run-*
```

## Why this approach

The script doesn't reimplement the pipeline — it delegates to `amt.runner`,
the engine's own full-pipeline entry point. All this wrapper does is solve
the "how do I get the engine onto my machine and pointed at my file"
problem, plus organising outputs into per-run subfolders so nothing gets
overwritten. When AMT.engine adds a new export format or pipeline step, this
wrapper picks it up automatically — and because unrecognised flags are
forwarded verbatim, a new engine option is usable here before this script
has ever heard of it.

The script also avoids the heavyweight `pip install -e .` that an editable
install would require. It just installs the engine's runtime dependencies into
your active Python and runs `python -m amt.runner` from inside the cloned
repo — exactly what you'd do if you cloned and ran the engine by hand. If
you want isolation, put the script in a venv yourself.

## Development

`run_amt.py` is the product; `main.py` only maintains the repository. It checks
that the version in `run_amt.py`, `CHANGELOG.md` and `CITATION.cff` agree, and
runs the test suite. The tests need `git` but no network: a small local
repository stands in for the engine.

```bash
pip install -r requirements.txt    # pytest
python main.py                     # all steps
python main.py --list              # show the steps
python main.py --only tests        # one step
python main.py --dry-run           # print the plan, run nothing
python main.py --strict            # warnings become errors (use this in CI)
```

GitHub Actions runs `python main.py --strict` on every push to `main` and on
every pull request (`.github/workflows/ci.yml`), on Linux and Windows with
Python 3.10 and 3.13. It needs no network beyond installing `pytest`.

Two more steps need the network and therefore run only when asked for:

```bash
python main.py --only smoke        # run_amt.py animals.ttl end to end; clones the engine
python main.py --only drift        # bundled examples against the engine's examples/
```

`smoke` does what the README describes — it clones the engine into
`.amt-cache/`, installs its requirements into the active Python and writes the
outputs to `build/smoke/` — and fails if a file is missing or the number of
inferred edges for `animals.ttl` is no longer 106. `drift` clones the engine
shallowly into `build/drift/` and compares the bundled examples with the
engine's, ignoring line endings; `subsumption-demo.md` differs on purpose.
With `--strict`, both turn a warning into a failure. A weekly workflow
(`.github/workflows/network.yml`, Sundays) runs both, and it can be started by
hand from the "Actions" tab; GitHub pauses scheduled workflows after 60 days
without repository activity.

The combined output is written to `build/pipeline_report.txt`. Changes are
recorded in [`CHANGELOG.md`](CHANGELOG.md); `PRIMER.md` holds the (German) work
plan and the decisions behind the repository.

## Related

- [AMT.engine](https://github.com/n4o-rse/amt-engine) — the reasoning engine itself
- [Academic Meta Tool](https://n4o-rse.github.io/amt-engine/) — the start page of AMT (also
  <https://w3id.org/amt/>; the vocabulary namespace stays `http://academic-meta-tool.xyz/vocab#`)
- [AMT Explorer](https://n4o-rse.github.io/amt-engine/explorer/) — the engine's web viewer
  (`docs/` in the engine repository); it lets you pick a dataset, switch
  reasoning on and off and download Turtle or Cypher
- [AMT webviewer (CAA2026-amt)](https://github.com/leiza-scit/CAA2026-amt) — a
  related viewer for the Potter attribution example, published at
  <https://leiza-scit.github.io/CAA2026-amt/>

## Citation

If you use amt-runner in your work, please cite it. The citation metadata are in
[`CITATION.cff`](CITATION.cff); GitHub offers them under "Cite this repository".
Every release is archived on Zenodo.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23669557.svg)](https://doi.org/10.5281/zenodo.23669557)

- All versions (always resolves to the latest): <https://doi.org/10.5281/zenodo.23669557>
- Version 0.2.1: <https://doi.org/10.5281/zenodo.23669558>

Use the version DOI when you need to name the exact release your results
came from.

## License

MIT. See [LICENSE](LICENSE).
