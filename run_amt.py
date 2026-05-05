#!/usr/bin/env python3
"""
run_amt.py — Run the AMT.engine pipeline on a single TTL file.

Clones AMT.engine from GitHub into a local cache, installs its three
dependencies (rdflib, pyshacl, pyvis) into your active Python environment,
and runs the full pipeline:

    validate (SHACL) → reason → export TTL + Cypher + HTML

Usage
-----
    python run_amt.py path/to/input.ttl
    python run_amt.py path/to/input.ttl --outdir results/
    python run_amt.py path/to/input.ttl --update      # pull latest amt.engine
    python run_amt.py path/to/input.ttl --ref v0.2.0  # pin to a tag/branch/sha

Requires Python ≥ 3.10 and git on PATH. Dependencies are installed into
the Python that runs this script — use a venv if you want isolation.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
AMT_REPO_URL = "https://github.com/n4o-rse/amt-engine.git"
AMT_DEFAULT_REF = "main"
AMT_DEPS = ["rdflib>=7.0", "pyshacl>=0.25", "pyvis>=0.3"]

SCRIPT_DIR = Path(__file__).resolve().parent
CACHE_DIR = SCRIPT_DIR / ".amt-cache"
REPO_DIR = CACHE_DIR / "amt-engine"
DEPS_MARKER = CACHE_DIR / ".deps-installed"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def run(cmd, **kwargs) -> None:
    """Run a subprocess, streaming output, raising on non-zero exit."""
    cmd = [str(c) for c in cmd]
    print(f"  $ {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True, **kwargs)


def ensure_repo(ref: str, update: bool) -> None:
    """Clone amt.engine into the cache, or update if requested."""
    if not REPO_DIR.exists():
        print(f"[1/3] Cloning {AMT_REPO_URL} ...")
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--depth", "1", AMT_REPO_URL, REPO_DIR])
    elif update:
        print("[1/3] Updating cached amt.engine ...")
        run(["git", "-C", REPO_DIR, "fetch", "--all", "--tags"])
    else:
        print(f"[1/3] Using cached amt.engine at {REPO_DIR}")

    run(["git", "-C", REPO_DIR, "checkout", ref],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if update:
        subprocess.run(
            ["git", "-C", str(REPO_DIR), "pull", "--ff-only"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )


def ensure_deps() -> None:
    """Install rdflib / pyshacl / pyvis into the active Python (once)."""
    if DEPS_MARKER.exists():
        # Quick sanity check: are the imports actually available? If someone
        # nuked their env between runs, the marker lies — re-install.
        try:
            for mod in ("rdflib", "pyshacl", "pyvis"):
                __import__(mod)
            print("[2/3] Dependencies already installed")
            return
        except ImportError:
            print("[2/3] Marker present but imports missing — reinstalling")

    else:
        print(f"[2/3] Installing dependencies into {sys.executable}")
        print(f"      ({', '.join(AMT_DEPS)})")

    run([sys.executable, "-m", "pip", "install", "--quiet", *AMT_DEPS])
    DEPS_MARKER.touch()


def run_pipeline(input_file: Path, outdir: Path) -> None:
    """Invoke amt.runner — the full-pipeline entry point of AMT.engine.

    Each run gets its own timestamped subfolder: out/run-YYYYMMDD-HHMMSS/.
    This sidesteps amt.runner's behaviour of wiping its output directory
    before writing — every run lives in a fresh folder, so previous runs
    are preserved and runs against different input files don't collide.

    A symlink (POSIX) or copy (Windows) called `out/latest` always points
    at the most recent run.
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = outdir / f"run-{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"[3/3] Running pipeline on {input_file.name} ...")
    # Run from inside the repo so amt's relative imports + ontology paths work,
    # exactly as if you'd cloned it and run the runner by hand.
    run(
        [
            sys.executable, "-m", "amt.runner", input_file,
            "-o", run_dir.resolve(),
        ],
        cwd=REPO_DIR,
    )

    _update_latest_pointer(outdir, run_dir)

    print(f"\n✓ Outputs written to {run_dir.resolve()}")
    print(f"  (also accessible via {outdir.resolve() / 'latest'})")
    for p in sorted(run_dir.glob(f"{input_file.stem}.*")):
        print(f"    - {p.name}")


def _update_latest_pointer(outdir: Path, run_dir: Path) -> None:
    """Make `out/latest` point at the run we just produced.

    Uses a symlink on POSIX, a directory junction copy on Windows. Failure
    is non-fatal — the pointer is convenience, not correctness.
    """
    latest = outdir / "latest"
    try:
        if latest.is_symlink() or latest.exists():
            if latest.is_symlink() or latest.is_file():
                latest.unlink()
            else:
                # Plain directory copy from a previous Windows run.
                import shutil
                shutil.rmtree(latest)
        # Use a relative target so the pointer survives moving outdir/.
        latest.symlink_to(run_dir.name, target_is_directory=True)
    except (OSError, NotImplementedError):
        # Windows without dev-mode / admin → no symlinks. Fall back to a copy.
        try:
            import shutil
            if latest.exists():
                shutil.rmtree(latest)
            shutil.copytree(run_dir, latest)
        except Exception as e:
            print(f"      (could not update '{latest.name}' pointer: {e})")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run AMT.engine pipeline on a TTL file (clone-and-cache).",
    )
    p.add_argument("input", type=Path, help="AMT-compatible Turtle (.ttl) file")
    p.add_argument(
        "--outdir", type=Path, default=Path("out"),
        help="Output directory (default: ./out)",
    )
    p.add_argument(
        "--ref", default=AMT_DEFAULT_REF,
        help=f"Git ref of amt.engine to use (default: {AMT_DEFAULT_REF})",
    )
    p.add_argument(
        "--update", action="store_true",
        help="Pull the latest amt.engine before running",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()

    if not args.input.exists():
        print(f"FAIL  Input file not found: {args.input}", file=sys.stderr)
        return 2

    try:
        ensure_repo(args.ref, args.update)
        ensure_deps()
        run_pipeline(args.input.resolve(), args.outdir)
    except subprocess.CalledProcessError as e:
        print(f"\nFAIL  step failed (exit {e.returncode})", file=sys.stderr)
        return e.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
