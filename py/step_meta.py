"""
Step ``meta`` — the places that state the version must agree.

``__version__`` in run_amt.py, ``CITATION.cff`` (version and date-released),
the newest released entry of ``CHANGELOG.md`` and ``RELEASE`` in
``amt_runner_dev_utils.py``.

Standalone:  python py/step_meta.py
"""
from __future__ import annotations

import re
import sys

try:
    from amt_runner_dev_utils import RELEASE, RELEASE_DATE, ROOT, Report
except ImportError:  # imported as py.step_meta
    from py.amt_runner_dev_utils import RELEASE, RELEASE_DATE, ROOT, Report


def _first(pattern: str, text: str) -> str | None:
    m = re.search(pattern, text, flags=re.MULTILINE)
    return m.group(1) if m else None


def main() -> int:
    rep = Report("meta")
    found: dict[str, str | None] = {}

    script = (ROOT / "run_amt.py").read_text(encoding="utf-8")
    found["run_amt.py"] = _first(r'^__version__\s*=\s*"([^"]+)"', script)

    cff_path = ROOT / "CITATION.cff"
    if cff_path.exists():
        cff = cff_path.read_text(encoding="utf-8")
        found["CITATION.cff"] = _first(r'^version:\s*"?([^"\s]+)"?', cff)
        released = _first(r'^date-released:\s*"?(\d{4}-\d{2}-\d{2})"?', cff)
        if released != RELEASE_DATE:
            rep.warn(f"CITATION.cff date-released is {released}, RELEASE_DATE is {RELEASE_DATE}")
    else:
        rep.warn("CITATION.cff is missing")

    log_path = ROOT / "CHANGELOG.md"
    if log_path.exists():
        log = log_path.read_text(encoding="utf-8")
        found["CHANGELOG.md"] = _first(r"^## \[(\d+\.\d+\.\d+)\]", log)
        entry_date = _first(r"^## \[" + re.escape(RELEASE) + r"\] - (\d{4}-\d{2}-\d{2})", log)
        if entry_date != RELEASE_DATE:
            rep.warn(f"CHANGELOG.md dates {RELEASE} as {entry_date}, RELEASE_DATE is {RELEASE_DATE}")
    else:
        rep.warn("CHANGELOG.md is missing")

    found["py/amt_runner_dev_utils.py"] = RELEASE

    width = max(len(k) for k in found)
    for src, ver in found.items():
        print(f"     {src:<{width}}  {ver}")

    if len({v for v in found.values() if v}) > 1 or None in found.values():
        return rep.fail("version mismatch between the files above")
    rep.ok(f"all version sources say {RELEASE}")
    return rep.finish()


if __name__ == "__main__":
    sys.exit(main())
