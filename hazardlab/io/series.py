"""Loading index series -- from a bundled sample, a local file, or a URL.

Deliberately small. Every hazard has its own data quirks, so this offers a
predictable shape (a dated float Series) and leaves parsing to you.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_sample(name: str = "oni") -> pd.Series:
    """Load a bundled sample series so the quickstart runs with no network.

    Bundled data is NOAA CPC output, which is US Government work in the public
    domain. It is a convenience snapshot, not a live feed -- refresh from source
    before drawing any conclusion.
    """
    path = DATA_DIR / f"{name}.csv"
    if not path.exists():
        avail = sorted(p.stem for p in DATA_DIR.glob("*.csv"))
        raise FileNotFoundError(f"no bundled sample '{name}'. Available: {avail}")
    df = pd.read_csv(path, parse_dates=["date"])
    return df.set_index("date")["value"].astype(float)


def load_csv(path: str | Path, date_col: str = "date", value_col: str = "value") -> pd.Series:
    """Load a two-column CSV into a dated float Series."""
    df = pd.read_csv(path, parse_dates=[date_col])
    return df.set_index(date_col)[value_col].astype(float)


def load_frame(df: pd.DataFrame, date_col: str, value_col: str) -> pd.Series:
    """Adapt an existing DataFrame you have already parsed."""
    out = df[[date_col, value_col]].copy()
    out[date_col] = pd.to_datetime(out[date_col])
    return out.set_index(date_col)[value_col].astype(float)
