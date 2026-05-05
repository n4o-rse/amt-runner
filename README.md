# amt-runner

A small wrapper script that runs the [AMT.engine](https://github.com/n4o-rse/amt-engine)
pipeline on a single Turtle file — **validate → reason → export TTL + Cypher + HTML** —
without requiring you to clone or install the engine yourself.

This repo is meant as a **demo template**: clone it, drop in your own `.ttl` file,
run the script, get a reasoned graph in `out/`. Use it as a starting point for
your own AMT-based projects.

## What it does

`run_amt.py` is a self-contained Python script that:

1. **Clones AMT.engine** from GitHub into a local cache (`.amt-cache/`)
2. **Creates an isolated virtual environment** and installs the engine in editable mode
3. **Runs the full pipeline** on your input file:
   - SHACL validation against the AMT shapes
   - Fuzzy-logic reasoning (n-ary role chains, inverse roles)
   - Consistency check
   - Export to Turtle (with inferred edges), Neo4j Cypher, and a standalone interactive HTML graph

Subsequent runs reuse the cache and finish in about a second.

## Requirements

- Python ≥ 3.10
- `git` on your `PATH`

That's it. The script bootstraps everything else.

## Quickstart

```bash
git clone https://github.com/n4o-rse/amt-runner.git
cd amt-runner
python run_amt.py animals.ttl
```

The first run downloads AMT.engine and its dependencies (`rdflib`, `pyshacl`,
`pyvis`) into `.amt-cache/`. Allow ~30 seconds. Subsequent runs are near-instant.

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
[2/3] Creating venv at .amt-cache/venv and installing amt.engine ...
[3/3] Running pipeline on animals.ttl ...
VAL Validating animals.ttl ...
OK  Validation passed.
LOAD Loading animals.ttl ...
OK  2 Concepts | 7 Roles | 26 Nodes | 46 Edges | 7 Axioms

OK  Consistency check passed.
  -> reasoning produced 106 inferred edge(s)
OK  wrote out/animals.reasoned.ttl
OK  wrote out/animals.cypher
OK  wrote out/animals.html

✓ Outputs written to ./out
    - animals.reasoned.ttl
    - animals.cypher
    - animals.html
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

**`animals.html`** — a standalone, interactive graph (powered by pyvis). Open in
any browser; no server needed. Asserted edges appear solid, inferred edges
dashed.

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
| `--outdir DIR` | `out/` | Where exports are written |
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
└── out/                # created on first run, git-ignored
    ├── animals.reasoned.ttl
    ├── animals.cypher
    └── animals.html
```

## Resetting the cache

If something goes wrong with the engine install, just nuke the cache:

```bash
rm -rf .amt-cache
```

The next run will rebuild it from scratch.

## Why this approach

The script could be a one-liner that calls `pip install git+https://...`, but
that has two costs: it pollutes whatever Python environment you happen to be in,
and it makes pinning a specific engine version awkward. A local cache plus an
isolated venv keeps your system clean and makes the pipeline reproducible.

Conversely, the script could `import amt` directly as a library. That couples
you to the engine's internal API. The CLI is the engine's stable public surface,
so the wrapper invokes it via `subprocess` — when the engine evolves, this
script keeps working.

## Related

- [AMT.engine](https://github.com/n4o-rse/amt-engine) — the reasoning engine itself
- [Academic Meta Tool](http://academic-meta-tool.xyz/) — the underlying framework
- [AMT webviewer (CAA2026-amt)](https://github.com/leiza-scit/CAA2026-amt) — JS
  visualisation that consumes the same TTL format

## License

MIT. See [LICENSE](LICENSE).
