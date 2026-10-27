"""
Step ``smoke`` (network) — the real thing, end to end.

Runs ``python run_amt.py animals.ttl --update`` as the README describes: it
clones AMT.engine from GitHub into ``.amt-cache/`` (or updates the clone, so the
step checks the current engine and not a stale cache), installs the engine's
run-time dependencies into the active Python and writes the outputs to
``build/smoke/``. The step fails when the run fails or an output file is
missing. A different number of inferred edges than the README states (106) is
a warning, so ``--strict`` makes it fail.

Not part of the default run: it needs the network and changes the active
Python environment. Start it with ``python main.py --only smoke``.

Standalone:  python py/step_smoke.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

try:
    from amt_runner_dev_utils import BUILD_DIR, ROOT, Report, child_env
except ImportError:  # imported as py.step_smoke
    from py.amt_runner_dev_utils import BUILD_DIR, ROOT, Report, child_env

OUTDIR = BUILD_DIR / "smoke"
# What the README states for animals.ttl.
EXPECTED_INFERRED = 106
EXPECTED_FILES = [
    "animals.reasoned.ttl", "animals.cypher", "animals.nodes.csv",
    "animals.edges.csv", "animals.html", "animals.report.md",
]


def inferred_edges(output: str) -> int | None:
    """The number in 'reasoning produced N inferred edge(s)', if present."""
    m = re.search(r"reasoning produced (\d+) inferred edge", output)
    return int(m.group(1)) if m else None


def missing_files(run_dir: Path) -> list[str]:
    return [name for name in EXPECTED_FILES if not (run_dir / name).exists()]


def newest_run(outdir: Path) -> Path | None:
    runs = sorted(p for p in outdir.glob("run-*") if p.is_dir())
    return runs[-1] if runs else None


def command() -> list[str]:
    """The call the step makes; ``--update`` so that a cached, older engine is never what gets tested."""
    return [sys.executable, "run_amt.py", "animals.ttl", "--update", "--outdir", str(OUTDIR)]


def main() -> int:
    rep = Report("smoke")
    proc = subprocess.run(
        command(),
        cwd=ROOT, env=child_env(), text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    print(proc.stdout.rstrip())
    if proc.returncode != 0:
        return rep.fail(f"run_amt.py exited with {proc.returncode}")

    run_dir = newest_run(OUTDIR)
    if run_dir is None:
        return rep.fail(f"no run folder in {OUTDIR}")
    gone = missing_files(run_dir)
    if gone:
        return rep.fail("missing output file(s): " + ", ".join(gone))
    rep.ok(f"all {len(EXPECTED_FILES)} output files written")

    n = inferred_edges(proc.stdout)
    if n is None:
        rep.warn("could not find the number of inferred edges in the output")
    elif n != EXPECTED_INFERRED:
        rep.warn(f"{n} inferred edges, the README says {EXPECTED_INFERRED}")
    else:
        rep.ok(f"{n} inferred edges, as the README says")
    return rep.finish()


if __name__ == "__main__":
    sys.exit(main())
