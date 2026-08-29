#!/usr/bin/env python3
"""
run_amt.py — Run the AMT.engine pipeline on a single TTL file.

Clones AMT.engine from GitHub into a local cache, installs its dependencies
into your active Python environment, and runs the full pipeline:

    validate (SHACL) → reason → export TTL + Cypher + CSV + HTML + report

Usage
-----
    python run_amt.py path/to/input.ttl
    python run_amt.py path/to/input.ttl --outdir results/
    python run_amt.py path/to/input.ttl --minimal    # drop subsumed edges
    python run_amt.py path/to/input.ttl --update     # pull latest amt.engine
    python run_amt.py path/to/input.ttl --ref v0.3.0 # pin to a tag/branch/sha

Any flag this script does not recognise is passed straight through to
``amt.runner`` — ``--no-check``, ``--no-report``, ``--height 900px`` and so
on all work without this wrapper needing to know about them. The exception
is ``-o`` / ``--outdir``, which belongs to the wrapper: it manages the
per-run subfolder itself.

Requires Python ≥ 3.10 and git on PATH. Dependencies are installed into
the Python that runs this script — use a venv if you want isolation.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
AMT_REPO_URL = "https://github.com/n4o-rse/amt-engine.git"
AMT_DEFAULT_REF = "main"

# Fallback only. Since AMT.engine 0.3.0 the authoritative list lives in the
# engine's own requirements.txt, which is what we install when it is there.
# This list keeps older refs working, and any future engine that drops the
# file.
AMT_FALLBACK_DEPS = ["rdflib>=7.0", "pyshacl>=0.25", "pyvis>=0.3"]

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


def _git(*args, check: bool = True, quiet: bool = False) -> int:
    """Run a git command inside the cached repo. Returns the exit code."""
    cmd = ["git", "-C", str(REPO_DIR), *(str(a) for a in args)]
    kwargs = {}
    if quiet:
        kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    proc = subprocess.run(cmd, **kwargs)
    if check and proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd)
    return proc.returncode


def ensure_repo(ref: str, update: bool) -> None:
    """Clone amt.engine into the cache, or update if requested."""
    if not REPO_DIR.exists():
        print(f"[1/3] Cloning {AMT_REPO_URL} ...")
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--depth", "1", AMT_REPO_URL, REPO_DIR])
    elif update:
        print("[1/3] Updating cached amt.engine ...")
        _git("fetch", "--all", "--tags", check=False, quiet=True)
    else:
        print(f"[1/3] Using cached amt.engine at {REPO_DIR}")

    _checkout(ref)

    if update:
        # Only meaningful on a branch; on a detached HEAD it is a no-op.
        _git("pull", "--ff-only", check=False, quiet=True)

    print(f"      engine ref '{ref}' at {_describe_head()}")


def _checkout(ref: str) -> None:
    """
    Check out ``ref``, deepening the shallow clone if the ref is not in it.

    The initial clone is ``--depth 1``, so it contains exactly one commit.
    Any tag, branch or SHA other than the tip of the default branch is
    therefore simply absent, and a plain checkout fails. Rather than
    surfacing that as an opaque non-zero exit, fetch the missing history
    once and retry.
    """
    if _git("checkout", ref, check=False, quiet=True) == 0:
        return

    print(f"      '{ref}' not in the shallow clone — fetching full history ...")
    # --unshallow fails on a repo that is already complete; that is fine.
    _git("fetch", "--unshallow", "--tags", check=False, quiet=True)
    _git("fetch", "--all", "--tags", check=False, quiet=True)

    if _git("checkout", ref, check=False) != 0:
        raise SystemExit(
            f"FAIL  '{ref}' is not a tag, branch or commit of {AMT_REPO_URL}.\n"
            f"      Check the ref, or delete {CACHE_DIR} and try again."
        )


def _describe_head() -> str:
    """Short description of the checked-out commit, for the run log."""
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO_DIR), "log", "-1", "--format=%h %s"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return out or "unknown commit"
    except (subprocess.CalledProcessError, OSError):
        return "unknown commit"


def _requirements_file() -> Path | None:
    """The engine's own requirements.txt, if the checked-out ref ships one."""
    candidate = REPO_DIR / "requirements.txt"
    return candidate if candidate.exists() else None


def _deps_fingerprint() -> str:
    """
    Identify the dependency set currently in effect.

    Stored in the marker file so that checking out a different engine ref —
    or the engine changing its requirements — triggers a reinstall instead
    of silently reusing whatever happens to be in the environment.
    """
    req = _requirements_file()
    payload = req.read_bytes() if req else "\n".join(AMT_FALLBACK_DEPS).encode()
    return hashlib.sha256(payload).hexdigest()


def ensure_deps() -> None:
    """Install the engine's dependencies into the active Python (once)."""
    fingerprint = _deps_fingerprint()
    req = _requirements_file()

    if DEPS_MARKER.exists() and DEPS_MARKER.read_text().strip() == fingerprint:
        # The marker records what we installed, not what is still there. If
        # someone nuked their env between runs the marker lies — check the
        # imports before trusting it.
        try:
            for mod in ("rdflib", "pyshacl", "pyvis"):
                __import__(mod)
            print("[2/3] Dependencies already installed")
            return
        except ImportError:
            print("[2/3] Marker present but imports missing — reinstalling")
    elif DEPS_MARKER.exists():
        print("[2/3] Engine dependencies changed — reinstalling")
    else:
        print(f"[2/3] Installing dependencies into {sys.executable}")

    if req is not None:
        print(f"      (from the engine's own {req.name})")
        run([sys.executable, "-m", "pip", "install", "--quiet", "-r", req])
    else:
        print(f"      ({', '.join(AMT_FALLBACK_DEPS)})")
        run([sys.executable, "-m", "pip", "install", "--quiet", *AMT_FALLBACK_DEPS])

    DEPS_MARKER.write_text(fingerprint)


def engine_supports(flag: str) -> bool:
    """Whether the checked-out engine's runner accepts ``flag``."""
    runner_py = REPO_DIR / "amt" / "runner.py"
    try:
        return f'"{flag}"' in runner_py.read_text(encoding="utf-8")
    except OSError:
        return True  # can't tell — let the engine reject it with its own error


def run_pipeline(input_file: Path, outdir: Path, engine_args: list[str]) -> None:
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
            *engine_args,
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
def parse_args() -> tuple[argparse.Namespace, list[str]]:
    p = argparse.ArgumentParser(
        description="Run AMT.engine pipeline on a TTL file (clone-and-cache).",
        epilog="Unrecognised flags are forwarded to amt.runner unchanged.",
    )
    p.add_argument("input", type=Path, help="AMT-compatible Turtle (.ttl) file")
    p.add_argument(
        "--outdir", type=Path, default=Path("out"),
        help="Output directory (default: ./out)",
    )
    p.add_argument(
        "--minimal", action="store_true",
        help="Use the engine's SubsumptionAxioms to suppress inferred edges "
             "that a finer role already implies (needs AMT.engine >= 0.3.0)",
    )
    p.add_argument(
        "--ref", default=AMT_DEFAULT_REF,
        help=f"Git ref of amt.engine to use (default: {AMT_DEFAULT_REF})",
    )
    p.add_argument(
        "--update", action="store_true",
        help="Pull the latest amt.engine before running",
    )
    return p.parse_known_args()


def main() -> int:
    args, passthrough = parse_args()

    if not args.input.exists():
        print(f"FAIL  Input file not found: {args.input}", file=sys.stderr)
        return 2

    try:
        ensure_repo(args.ref, args.update)

        engine_args = list(passthrough)
        if args.minimal:
            if not engine_supports("--minimal"):
                print(
                    "FAIL  The cached AMT.engine does not support --minimal.\n"
                    "      It arrived in 0.3.0. Re-run with --update, or pin a\n"
                    "      newer ref with --ref.",
                    file=sys.stderr,
                )
                return 2
            engine_args.append("--minimal")

        ensure_deps()
        run_pipeline(args.input.resolve(), args.outdir, engine_args)
    except subprocess.CalledProcessError as e:
        print(f"\nFAIL  step failed (exit {e.returncode})", file=sys.stderr)
        return e.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
