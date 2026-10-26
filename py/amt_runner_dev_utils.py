"""
Shared helpers for the development pipeline (``python main.py``).

This module belongs to the repository's maintenance tooling. ``run_amt.py``
does not import it and stays a single self-contained file, because users are
told to copy that one file into their own projects.

No step reads the system clock; dates come from ``RELEASE_DATE``.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# Release
# --------------------------------------------------------------------------- #
# Must equal __version__ in run_amt.py, `version` in CITATION.cff and the newest
# released entry of CHANGELOG.md. The ``meta`` step checks all four.
RELEASE = "0.2.0"
RELEASE_DATE = "2026-08-29"

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT / "tests"
# build/ is git-ignored; the pipeline report lives here.
BUILD_DIR = ROOT / "build"


def ensure_dirs() -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)


def strict() -> bool:
    """True when ``python main.py --strict`` (or ``AMT_DEV_STRICT=1``) is active."""
    return os.environ.get("AMT_DEV_STRICT") == "1"


class Report:
    """Collects warnings; in strict mode any warning makes the step fail."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.warnings: list[str] = []

    def ok(self, msg: str) -> None:
        print(f"OK   {msg}")

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)
        print(f"WARN {msg}")

    def fail(self, msg: str) -> int:
        print(f"FAIL {msg}")
        return 1

    def finish(self) -> int:
        if self.warnings and strict():
            print(f"FAIL {len(self.warnings)} warning(s) treated as errors (--strict)")
            return 1
        return 0


def child_env(**extra: str) -> dict[str, str]:
    """Environment for child processes: UTF-8 on every platform."""
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env.update(extra)
    return env


def run_python(args: list[str], *, env_extra: dict[str, str] | None = None) -> int:
    """Run ``python <args>`` in the repository root, streaming its output."""
    proc = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        env=child_env(**(env_extra or {})),
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode
