"""Monte Carlo layer -- occurrence -> severity -> conditional impacts.

Structure: severity is the single latent factor. Everything else is drawn
conditional on the severity class, and independently of everything else within
a class. That is a deliberate simplification and it is the dominant modelling
assumption in this library -- see KNOWN_LIMITATIONS.md.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from hazardlab.spec import HazardSpec


class MonteCarloEngine:
    """Stochastic catalogue generator.

    Occurrence and severity probabilities are REQUIRED arguments. An earlier
    version of this code carried defaults, and a catalogue generated from those
    defaults was mistaken for fitted output for months -- the headline number
    happened to land close to the fitted one, so nothing looked wrong. Passing
    them explicitly makes that class of error impossible.
    """

    def __init__(
        self,
        spec: HazardSpec,
        occurrence_probs: dict,          # {period_label: P(event in that period)}
        severity_probs: dict,            # {class_name: P(class | event)}
        n_sims: int = 10_000,
        seed: int = 42,
        period_dependence: float = 0.0,
    ):
        if not occurrence_probs:
            raise ValueError("occurrence_probs is required, e.g. {2026: 0.65}")
        for k, v in occurrence_probs.items():
            if not 0.0 <= float(v) <= 1.0:
                raise ValueError(f"occurrence probability for {k} out of range: {v}")
        if not severity_probs:
            raise ValueError("severity_probs is required")
        missing = set(spec.severity_classes) - set(severity_probs)
        if missing:
            raise ValueError(f"severity_probs is missing classes: {sorted(missing)}")
        if not -1.0 <= period_dependence <= 1.0:
            raise ValueError("period_dependence must be in [-1, 1]")

        self.spec = spec
        self.occurrence_probs = dict(occurrence_probs)
        self.severity_probs = dict(severity_probs)
        self.n_sims = int(n_sims)
        self.period_dependence = float(period_dependence)
        self.rng = np.random.default_rng(seed)
        self.catalogue: pd.DataFrame | None = None

    def run(self) -> pd.DataFrame:
        spec = self.spec
        classes = list(spec.severity_classes)
        weights = np.array([float(self.severity_probs[c]) for c in classes])
        weights = weights / weights.sum()
        impact_names = list(spec.impact_names)
        periods = list(self.occurrence_probs.items())
        rows = []

        for sim in range(self.n_sims):
            previous = None
            for label, p_occ in periods:
                # Carry-over between periods. Zero (the default) means independent
                # draws. Set it deliberately and document your reasoning: for ENSO
                # the real record shows negative carry-over, since La Nina commonly
                # follows a strong event.
                p_eff = float(p_occ)
                if previous is not None and self.period_dependence:
                    direction = 1.0 if previous else -1.0
                    headroom = min(p_eff, 1.0 - p_eff)
                    p_eff = float(np.clip(
                        p_eff + self.period_dependence * direction * headroom, 0.0, 1.0))

                occurred = bool(self.rng.random() < p_eff)
                row = {"sim_id": sim, "period": label, "occurred": occurred}

                if occurred:
                    cls = str(self.rng.choice(classes, p=weights))
                    cp = spec.class_params[cls]
                    mu, sd, lo, hi = cp.peak
                    peak = float(stats.truncnorm.rvs(
                        (lo - mu) / sd, (hi - mu) / sd, loc=mu, scale=sd,
                        random_state=int(self.rng.integers(0, 2 ** 31 - 1)),
                    ))
                    row["severity"] = cls
                    row["peak_intensity"] = round(peak, 3)
                    row["duration_months"] = int(max(1, self.rng.poisson(cp.duration_months)))
                    for name in impact_names:
                        m, s = cp.impacts.get(name, (0.0, 0.0))
                        val = float(self.rng.normal(m, s)) if s > 0 else float(m)
                        row[name] = round(val, 3)
                else:
                    row["severity"] = "None"
                    row["peak_intensity"] = np.nan
                    row["duration_months"] = 0
                    for name in impact_names:
                        row[name] = 0.0

                rows.append(row)
                previous = occurred

        self.catalogue = pd.DataFrame(rows)
        return self.catalogue

    def summary(self) -> dict:
        if self.catalogue is None:
            raise RuntimeError("call run() first")
        cat = self.catalogue
        out = {"n_sims": self.n_sims, "periods": {}}
        for label in self.occurrence_probs:
            sub = cat[cat.period == label]
            occ = sub[sub.occurred]
            dist = occ.severity.value_counts(normalize=True).to_dict() if len(occ) else {}
            out["periods"][label] = {
                "p_occurrence": round(float(sub.occurred.mean()), 4),
                "severity_given_occurrence": {k: round(float(v), 4) for k, v in dist.items()},
            }
        wide = cat.pivot_table(index="sim_id", columns="period",
                               values="occurred", aggfunc="first")
        out["p_at_least_one"] = round(float(wide.any(axis=1).mean()), 4)
        out["p_all_periods"] = round(float(wide.all(axis=1).mean()), 4)
        return out

    def quantiles(self, column: str, qs=(0.05, 0.25, 0.5, 0.75, 0.95)) -> dict:
        """Quantiles of a simulated column.

        These describe the model's own distribution. They are NOT validated
        predictive intervals: no coverage test has been run against outcomes.
        See KNOWN_LIMITATIONS.md before presenting them as confidence bands.
        """
        if self.catalogue is None:
            raise RuntimeError("call run() first")
        s = self.catalogue[column].dropna()
        return {f"P{int(q * 100):02d}": round(float(s.quantile(q)), 3) for q in qs}
