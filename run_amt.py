#!/usr/bin/env python3
"""
run_amt.py — Run the AMT.engine pipeline on a single TTL file.

Fetches AMT.engine from GitHub (cached locally), installs it into an
isolated virtual environment, and runs the full pipeline against an
input file:

    validate (SHACL) → reason → export TTL + Cypher + HTML

Usage
-----
    python run_amt.py path/to/input.ttl
    python run_amt.py path/to/input.ttl --outdir results/
    python run_amt.py path/to/input.ttl --update      # pull latest amt.engine
    python run_amt.py path/to/input.ttl --ref v0.2.0  # pin to a tag/branch/sha

Requires only Python ≥ 3.10 and git on PATH.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
AMT_REPO_URL = "https://github.com/n4o-rse/amt-engine.git"
AMT_DEFAULT_REF = "main"

# Cache lives next to this script — portable, easy to nuke.
SCRIPT_DIR = Path(__file__).resolve().parent
CACHE_DIR = SCRIPT_DIR / ".amt-cache"
REPO_DIR = CACHE_DIR / "amt-engine"
VENV_DIR = CACHE_DIR / "venv"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def venv_bin(name: str) -> Path:
    """Path to an executable inside the cache venv (cross-platform)."""
    if os.name == "nt":  # Windows
        return VENV_DIR / "Scripts" / f"{name}.exe"
    return VENV_DIR / "bin" / name


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
        run(["git", "clone", AMT_REPO_URL, REPO_DIR])
    elif update:
        print("[1/3] Updating cached amt.engine ...")
        run(["git", "-C", REPO_DIR, "fetch", "--all", "--tags"])
    else:
        print(f"[1/3] Using cached amt.engine at {REPO_DIR}")

    # Always checkout the requested ref so --ref is honoured between runs.
    run(["git", "-C", REPO_DIR, "checkout", ref],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if update:
        # Fast-forward if on a branch; quietly skip if HEAD is detached.
        subprocess.run(
            ["git", "-C", str(REPO_DIR), "pull", "--ff-only"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )


def ensure_venv() -> None:
    """Create the cache venv and install amt.engine in editable mode."""
    if venv_bin("amt").exists():
        print(f"[2/3] Using cached venv at {VENV_DIR}")
        return

    print(f"[2/3] Creating venv at {VENV_DIR} and installing amt.engine ...")
    venv.create(VENV_DIR, with_pip=True, clear=False)
    pip = venv_bin("pip")
    run([pip, "install", "--upgrade", "pip", "--quiet"])
    run([pip, "install", "-e", REPO_DIR, "--quiet"])


def reinstall_if_repo_changed() -> None:
    """If the repo HEAD moved since last install, reinstall (cheap with -e)."""
    head_file = CACHE_DIR / ".installed-head"
    head = subprocess.check_output(
        ["git", "-C", str(REPO_DIR), "rev-parse", "HEAD"]
    ).decode().strip()

    if head_file.exists() and head_file.read_text().strip() == head:
        return
    print("      → repo HEAD changed, reinstalling")
    run([venv_bin("pip"), "install", "-e", REPO_DIR, "--quiet"])
    head_file.write_text(head)


def run_pipeline(input_file: Path, outdir: Path) -> None:
    """Invoke the AMT CLI with the full pipeline of flags."""
    outdir.mkdir(parents=True, exist_ok=True)
    stem = input_file.stem
    ttl_out = outdir / f"{stem}.reasoned.ttl"
    cypher_out = outdir / f"{stem}.cypher"
    html_out = outdir / f"{stem}.html"

    print(f"[3/3] Running pipeline on {input_file.name} ...")
    run([
        venv_bin("amt"), input_file,
        "--validate",
        "--reason",
        "--check",
        "--export-ttl", ttl_out,
        "--export-cypher", cypher_out,
        "--export-html", html_out,
    ])
    print(f"\n✓ Outputs written to {outdir.resolve()}")
    for p in (ttl_out, cypher_out, html_out):
        print(f"    - {p.name}")


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
        ensure_venv()
        reinstall_if_repo_changed()
        run_pipeline(args.input.resolve(), args.outdir)
    except subprocess.CalledProcessError as e:
        print(f"\nFAIL  step failed (exit {e.returncode})", file=sys.stderr)
        return e.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
