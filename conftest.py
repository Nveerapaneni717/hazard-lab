"""Make the repository importable when running from a clone.

`pip install -e .` is the supported path and CI uses it. This exists so that a
bare `pytest` in a fresh clone also works, rather than depending on pytest's
rootdir insertion happening to line up.
"""
import sys
from pathlib import Path

ROOT = str(Path(__file__).resolve().parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
