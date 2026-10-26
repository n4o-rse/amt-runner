"""
Step ``tests`` — the offline pytest suite in ``tests/``.

The tests need git on PATH but no network: they build a small local
repository to stand in for the engine.

Standalone:  python py/step_tests.py
"""
from __future__ import annotations

import sys

try:
    from amt_runner_dev_utils import Report, run_python
except ImportError:
    from py.amt_runner_dev_utils import Report, run_python


def main() -> int:
    rep = Report("tests")
    code = run_python(["-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"])
    if code != 0:
        return rep.fail(f"pytest exited with {code}")
    rep.ok("test suite green")
    return rep.finish()


if __name__ == "__main__":
    sys.exit(main())
