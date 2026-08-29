"""Generic feature builder for any hazard index series.

Give it a dated series of the spec's index and it produces lags, momentum,
persistence, threshold flags and seasonality. Nothing here knows what the index
means, which is the point -- the same builder serves ONI, ACE, Mw or rainfall.

A NOTE ON LEAKAGE, because this is where it usually enters
----------------------------------------------------------
`build_features` is causal by construction: every column at time t uses only
information at or before t. Two things it deliberately does NOT do, because
both leak and both were present in the project this library was extracted from:

1. It does not impute with a statistic of the whole series (a global median
   computed over all time uses the future to fill the past). Missing values are
   forward-filled only, and rows that remain incomplete are dropped.
2. It does not align auxiliary series with `reindex(method="nearest")`, which
   can pull a future observation backwards. Use `merge_asof`-style backward
   alignment via `attach_auxiliary()` instead.

If your index is itself a centred moving average (ONI is a 3-month centred
mean), the value at t already embeds t+1. That is a property of the published
index, not of this code -- but you should say so out loud when you report skill.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from hazardlab.spec import HazardSpec


def build_features(
    series: pd.Series,
    spec: HazardSpec,
    lags: tuple[int, ...] = (1, 2, 3, 6, 12),
    momentum: tuple[int, ...] = (3, 6, 12),
    seasonal: bool = True,
) -> pd.DataFrame:
    """Build a causal feature matrix from a single dated index series."""
    if not isinstance(series.index, pd.DatetimeIndex):
        raise TypeError("series must have a DatetimeIndex")
    s = series.sort_index().astype(float)
    f = pd.DataFrame(index=s.index)

    for lag in lags:
        f[f"lag{lag}"] = s.shift(lag)
    for w in momentum:
        f[f"change{w}"] = s - s.shift(w)
    f["roll_mean6"] = s.shift(1).rolling(6).mean()
    f["roll_std12"] = s.shift(1).rolling(12).std()

    # Threshold crossings, using the spec's own class boundaries.
    for cls, thr in spec.severity_thresholds.items():
        flag = (s >= thr) if spec.higher_is_worse else (s <= thr)
        f[f"above_{cls.lower()}"] = flag.astype(int)

    on = spec.occurrence_threshold
    active = (s >= on) if spec.higher_is_worse else (s <= on)
    f["consecutive_active"] = _run_length(active)
    f["periods_since_active"] = _since(active)

    if seasonal and getattr(s.index, "month", None) is not None:
        m = s.index.month
        f["month_sin"] = np.sin(2 * np.pi * m / 12)
        f["month_cos"] = np.cos(2 * np.pi * m / 12)

    # Forward-fill only: never a statistic computed across the whole sample.
    f = f.ffill(limit=3).dropna()
    return f


def build_target(series: pd.Series, spec: HazardSpec, horizon: int = 6) -> pd.Series:
    """Binary target: does the hazard become active within the next `horizon` steps?

    Genuinely forward-looking, and the tail (where the future is not yet
    observed) is dropped rather than filled with zeros. Filling it would teach
    the model that "no event" is the answer for exactly the periods where an
    event may be developing.
    """
    s = series.sort_index().astype(float)
    on = spec.occurrence_threshold
    active = (s >= on) if spec.higher_is_worse else (s <= on)
    fwd = active.shift(-1).rolling(horizon, min_periods=horizon).max().shift(-(horizon - 1))
    return fwd.dropna().astype(int)


def attach_auxiliary(
    features: pd.DataFrame, aux: pd.Series, name: str, tolerance_days: int = 45
) -> pd.DataFrame:
    """Join an auxiliary series using BACKWARD alignment only.

    `reindex(method='nearest')` is the tempting one-liner here and it silently
    leaks: for a date with no exact match it may take the next observation,
    which is in the future. This uses merge_asof with direction='backward'.
    """
    left = features.reset_index().rename(columns={features.index.name or "index": "_dt"})
    right = (aux.sort_index().rename(name).reset_index()
             .rename(columns={aux.index.name or "index": "_dt"}))
    merged = pd.merge_asof(
        left.sort_values("_dt"), right.sort_values("_dt"), on="_dt",
        direction="backward", tolerance=pd.Timedelta(days=tolerance_days),
    )
    return merged.set_index("_dt")


def annual_maxima(series: pd.Series) -> pd.Series:
    """Block maxima by calendar year -- the input to the GEV layer."""
    s = series.sort_index().astype(float)
    return s.groupby(s.index.year).max()


def _run_length(flag: pd.Series) -> pd.Series:
    out, run = [], 0
    for v in flag.astype(bool):
        run = run + 1 if v else 0
        out.append(run)
    return pd.Series(out, index=flag.index)


def _since(flag: pd.Series, cap: int = 120) -> pd.Series:
    out, n = [], cap
    for v in flag.astype(bool):
        n = 0 if v else min(n + 1, cap)
        out.append(n)
    return pd.Series(out, index=flag.index)
