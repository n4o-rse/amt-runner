#!/usr/bin/env python3
"""
main.py — the development pipeline of amt-runner.

This is the maintenance entry point of the repository: version check and
offline tests. It does *not* replace ``run_amt.py``, which is the product and
stays untouched by everything in here.

    python main.py                     all steps, in order
    python main.py --list              print steps and exit
    python main.py --only tests        one step
    python main.py --from tests        this step and everything after
    python main.py --skip meta         everything but this step
    python main.py --dry-run           print the plan, run nothing
    python main.py --strict            warnings become errors (what CI runs)

    python main.py --only smoke        network step: run_amt.py end to end
    python main.py --only drift        network step: bundled examples vs the engine's

Every step is also runnable on its own, e.g. ``python py/step_tests.py``.
The combined output is written to ``build/pipeline_report.txt``. The default
run touches no network: the two network steps ``smoke`` and ``drift`` are
verbs of their own and never run unless asked for with ``--only``.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY_DIR = ROOT / "py"
REPORT = ROOT / "build" / "pipeline_report.txt"

# (name, script, what it checks)
STEPS: list[tuple[str, str, str]] = [
    ("meta",  "step_meta.py",  "version, date and changelog agree across all files"),
    ("tests", "step_tests.py", "offline pytest suite in tests/ (needs git, no network)"),
]
NAMES = [s[0] for s in STEPS]

# Steps that need the network: only ever started by name, never by default,
# --from or --skip.
NETWORK_STEPS: list[tuple[str, str, str]] = [
    ("smoke", "step_smoke.py", "network: run_amt.py animals.ttl end to end (clones the engine)"),
    ("drift", "step_drift.py", "network: bundled examples against the engine's examples/"),
]
NETWORK_NAMES = [s[0] for s in NETWORK_STEPS]


def select(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    if args.only:
        return [s for s in STEPS + NETWORK_STEPS if s[0] == args.only]
    chosen = list(STEPS)
    if args.from_step:
        start = NAMES.index(args.from_step)
        chosen = [s for s in chosen if NAMES.index(s[0]) >= start]
    if args.skip:
        chosen = [s for s in chosen if s[0] not in args.skip]
    return chosen


def run_step(name: str, script: str, strict: bool, log) -> tuple[int, float]:
    env = dict(os.environ)
    # Without this, check marks and arrows fail at the pipe on Windows.
    env["PYTHONIOENCODING"] = "utf-8"
    env["AMT_DEV_STRICT"] = "1" if strict else "0"
    started = time.perf_counter()
    proc = subprocess.Popen(
        [sys.executable, str(PY_DIR / script)],
        cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        emit(f"     {line.rstrip()}", log)
    code = proc.wait()
    return code, time.perf_counter() - started


def emit(line: str, log) -> None:
    print(line)
    if log is not None:
        log.write(line + "\n")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    p = argparse.ArgumentParser(description="Development pipeline of amt-runner")
    p.add_argument("--list", action="store_true", help="print steps and exit")
    p.add_argument("--only", choices=NAMES + NETWORK_NAMES, metavar="STEP",
                   help="run one step (the network steps smoke and drift only run this way)")
    p.add_argument("--from", dest="from_step", choices=NAMES, metavar="STEP",
                   help="run this step and everything after it")
    p.add_argument("--skip", action="append", choices=NAMES, metavar="STEP",
                   help="skip a step (repeatable)")
    p.add_argument("--dry-run", action="store_true", help="print the plan, run nothing")
    p.add_argument("--strict", action="store_true", help="warnings become errors")
    args = p.parse_args(argv)

    if args.list:
        width = max(len(n) for n in NAMES + NETWORK_NAMES)
        for name, script, what in STEPS + NETWORK_STEPS:
            print(f"{name:<{width}}  py/{script:<16} {what}")
        return 0

    chosen = select(args)
    if not chosen:
        print("Nothing selected.")
        return 0

    if args.dry_run:
        print("Plan (dry run, nothing is executed):")
        for i, (name, script, _) in enumerate(chosen, 1):
            print(f"  {i}. {name:<12} py/{script}")
        print(f"strict: {'yes' if args.strict else 'no'}")
        return 0

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    timings: list[tuple[str, float, int]] = []
    with REPORT.open("w", encoding="utf-8") as log:
        for i, (name, script, _) in enumerate(chosen, 1):
            emit(f"[{i}/{len(chosen)}] {name}", log)
            code, secs = run_step(name, script, args.strict, log)
            timings.append((name, secs, code))
            if code != 0:
                emit(f"     step '{name}' failed (exit {code}); stopping.", log)
                break

        total = sum(t[1] for t in timings) or 1.0
        emit("", log)
        emit(f"{'step':<12} {'seconds':>8} {'share':>7}  result", log)
        for name, secs, code in timings:
            emit(f"{name:<12} {secs:>8.1f} {secs / total:>6.0%}  {'ok' if code == 0 else 'FAILED'}", log)
        emit(f"{'total':<12} {total:>8.1f}", log)

    failed = any(code != 0 for _, _, code in timings)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
