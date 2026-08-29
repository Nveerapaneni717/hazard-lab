"""Impact translation -- severity class to economic / physical consequence.

Kept deliberately thin. Impacts are conditional means indexed on severity, so
the severity distribution drives essentially all downstream variation. If you
disagree with the severity mix, every number here moves with it and nothing in
the model pushes back. `sensitivity()` exists to make that explicit.
"""
from __future__ import annotations

import pandas as pd

from hazardlab.spec import HazardSpec


def impact_table(spec: HazardSpec) -> pd.DataFrame:
    """The spec's impact assumptions, laid out for inspection."""
    rows = []
    for cls in spec.severity_classes:
        cp = spec.class_params[cls]
        row = {
            "severity": cls,
            "peak_mean": cp.peak[0],
            "duration_months": cp.duration_months,
        }
        for name in spec.impact_names:
            mean, sd = cp.impacts.get(name, (0.0, 0.0))
            row[f"{name}_mean"] = mean
            row[f"{name}_sd"] = sd
        rows.append(row)
    return pd.DataFrame(rows)


def sensitivity(spec: HazardSpec, impact: str) -> pd.DataFrame:
    """How far does one class of misclassification move an impact?

    Reports the step between adjacent class means against the within-class
    standard deviation. When the step is several sd wide, severity assignment
    dominates every other source of uncertainty in the model -- which is the
    honest answer to "how sensitive is this?".
    """
    if impact not in spec.impact_names:
        raise KeyError(f"unknown impact '{impact}'. Known: {list(spec.impact_names)}")
    classes = list(spec.severity_classes)
    rows = []
    for i, cls in enumerate(classes):
        mean, sd = spec.class_params[cls].impacts.get(impact, (0.0, 0.0))
        step = None
        if i + 1 < len(classes):
            nxt, _ = spec.class_params[classes[i + 1]].impacts.get(impact, (0.0, 0.0))
            step = nxt - mean
        rows.append({
            "severity": cls,
            "mean": mean,
            "sd": sd,
            "step_to_next_class": step,
            "step_in_sd_units": round(abs(step) / sd, 2) if (step and sd) else None,
        })
    return pd.DataFrame(rows)
