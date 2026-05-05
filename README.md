# amt-runner

A small wrapper script that runs the [AMT.engine](https://github.com/n4o-rse/amt-engine)
pipeline on a single Turtle file — **validate → reason → export everything** —
without requiring you to clone or install the engine yourself.

This repo is meant as a **demo template**: clone it, drop in your own `.ttl` file,
run the script, get the full set of outputs in `out/`. Use it as a starting point
for your own AMT-based projects.

## What it does

`run_amt.py` is a self-contained Python script that:

1. **Clones AMT.engine** from GitHub into a local cache (`.amt-cache/`)
2. **Installs three dependencies** (`rdflib`, `pyshacl`, `pyvis`) into your active Python — once
3. **Runs `amt.runner`** — the engine's own full-pipeline entry point — into a fresh, timestamped folder:
   - SHACL validation against the AMT shapes
   - Fuzzy-logic reasoning (n-ary role chains, inverse roles)
   - Consistency check
   - Export to Turtle, Neo4j Cypher, two CSVs (nodes/edges), interactive HTML graph
   - A Markdown run report documenting the whole run

Each run gets its own subfolder under `out/`, so previous runs are preserved
and runs against different input files don't collide.

## Requirements

- Python ≥ 3.10
- `git` on your `PATH`

## A note on Python environments

The script installs `rdflib`, `pyshacl`, and `pyvis` into whatever Python you
use to run it. If you don't want them in your global Python, create a venv
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

The first run downloads AMT.engine and installs its three dependencies. Allow
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
[2/3] Installing dependencies into /path/to/python
      (rdflib>=7.0, pyshacl>=0.25, pyvis>=0.3)
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

Your file needs to follow the AMT vocabulary — Concepts, Roles, weighted edges,
and (optionally) RoleChainAxioms or InverseRoleAxioms. The bundled
[`animals.ttl`](animals.ttl) is the most complete worked example; for the formal
specification see the [AMT.engine README](https://github.com/n4o-rse/amt-engine).

## Options

| Flag | Default | Effect |
|---|---|---|
| `--outdir DIR` | `out/` | Parent directory for run subfolders |
| `--ref REF` | `main` | Pin AMT.engine to a tag, branch, or commit SHA |
| `--update` | off | `git pull` the cached engine before running |

Pinning to a release tag is the right move for reproducible pipelines:

```bash
python run_amt.py animals.ttl --ref v0.2.0
```

## Repository layout

```
amt-runner/
├── run_amt.py          # the wrapper script
├── animals.ttl         # demo input
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
wrapper picks it up automatically.

The script also avoids the heavyweight `pip install -e .` that an editable
install would require. It just installs the three runtime dependencies into
your active Python and runs `python -m amt.runner` from inside the cloned
repo — exactly what you'd do if you cloned and ran the engine by hand. If
you want isolation, put the script in a venv yourself.

## Related

- [AMT.engine](https://github.com/n4o-rse/amt-engine) — the reasoning engine itself
- [Academic Meta Tool](http://academic-meta-tool.xyz/) — the underlying framework
- [AMT webviewer (CAA2026-amt)](https://github.com/leiza-scit/CAA2026-amt) — JS
  visualisation that consumes the same TTL format

A GitHub Pages publication of `animals.html` and similar examples is planned
once the corresponding setup is in place in the engine repository.

## License

MIT. See [LICENSE](LICENSE).

## Acknowledgements

AMT.engine is developed within
[**mainzed**](https://www.mainzed.org/) — Mainzer Zentrum für Digitalität
in den Geistes- und Kulturwissenschaften — at
[Hochschule Mainz, i3mainz](https://i3mainz.hs-mainz.de/)
and the [Leibniz-Zentrum für Archäologie (LEIZA)](https://www.leiza.de/).
