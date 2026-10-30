"""
Step ``drift`` (network) — the example files bundled here against the engine's.

The runner ships copies of some of AMT.engine's example files so that
``python run_amt.py animals.ttl`` works straight after cloning. This step
fetches the engine's ``examples/`` (shallow clone of ``main``) and compares the
copies, ignoring line endings. A difference is a warning, so ``--strict`` makes
it fail. Files that exist only in the engine are listed but never count.

Not part of the default run: it needs the network. Start it with
``python main.py --only drift``.

Standalone:  python py/step_drift.py
"""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

try:
    from amt_runner_dev_utils import BUILD_DIR, ROOT, Report
except ImportError:  # imported as py.step_drift
    from py.amt_runner_dev_utils import BUILD_DIR, ROOT, Report

ENGINE_URL = "https://github.com/alpaca-fair-framework/amt-engine.git"
CLONE_DIR = BUILD_DIR / "drift" / "amt-engine"

# Files that differ from the engine's on purpose, with the reason.
INTENDED = {
    "subsumption-demo.md": "commands use `python run_amt.py ...` instead of `python -m amt.runner ...`",
    "hextuple-demo.md": "command uses `python run_amt.py ...` instead of `python -m amt.runner ...`, plus a note on engine 0.6.0",
}

SUFFIXES = (".ttl", ".md")


def _text(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def compare(runner_dir: Path, engine_examples: Path) -> dict[str, list[str]]:
    """Compare the bundled examples with the engine's, by file name.

    Returns lists of names under ``same``, ``intended`` (differs on purpose),
    ``different`` (drift), ``missing`` (bundled here but gone from the engine)
    and ``engine_only`` (in the engine, not bundled here; informational).
    """
    result: dict[str, list[str]] = {
        "same": [], "intended": [], "different": [], "missing": [], "engine_only": [],
    }
    bundled_ttl = {p.stem for p in runner_dir.glob("*.ttl")}
    ours = sorted(
        p for p in runner_dir.iterdir()
        if p.is_file() and p.suffix in SUFFIXES and p.stem in bundled_ttl
    )
    for path in ours:
        theirs = engine_examples / path.name
        if not theirs.exists():
            result["missing"].append(path.name)
        elif _text(path) == _text(theirs):
            result["same"].append(path.name)
        elif path.name in INTENDED:
            result["intended"].append(path.name)
        else:
            result["different"].append(path.name)
    ours_names = {p.name for p in ours}
    result["engine_only"] = sorted(
        p.name for p in engine_examples.iterdir()
        if p.is_file() and p.suffix == ".ttl" and p.name not in ours_names
    )
    return result


def _rmtree(path: Path) -> None:
    """Remove a directory tree, including read-only git objects on Windows."""
    def onerror(func, p, _exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)
    if path.exists():
        shutil.rmtree(path, onerror=onerror)


def fetch_engine() -> Path:
    """Shallow clone of the engine's default branch; returns its examples/."""
    _rmtree(CLONE_DIR)
    CLONE_DIR.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", "--depth", "1", "--quiet", ENGINE_URL, str(CLONE_DIR)],
        check=True,
    )
    return CLONE_DIR / "examples"


def main() -> int:
    rep = Report("drift")
    try:
        examples = fetch_engine()
    except (subprocess.CalledProcessError, OSError) as exc:
        return rep.fail(f"could not fetch {ENGINE_URL}: {exc}")

    found = compare(ROOT, examples)
    for name in found["same"]:
        print(f"     same      {name}")
    for name in found["intended"]:
        print(f"     intended  {name}: {INTENDED[name]}")
    for name in found["engine_only"]:
        print(f"     engine only  {name} (not bundled here)")
    for name in found["different"]:
        rep.warn(f"{name} differs from the engine's copy")
    for name in found["missing"]:
        rep.warn(f"{name} is bundled here but no longer in the engine's examples/")
    if not found["different"] and not found["missing"]:
        rep.ok(f"{len(found['same'])} bundled file(s) match the engine, "
               f"{len(found['intended'])} differ on purpose")
    return rep.finish()


if __name__ == "__main__":
    sys.exit(main())
