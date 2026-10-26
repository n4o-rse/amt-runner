"""Make run_amt.py and the pipeline steps in py/ importable."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for entry in (ROOT, ROOT / "py"):
    # py/ is added as a directory, not imported as a package: pytest ships a
    # module called ``py`` that would shadow it.
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))
