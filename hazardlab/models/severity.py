"""Severity layer - P(class | event occurred), blended with the observed prior."""
from __future__ import annotations

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

from hazardlab.spec import HazardSpec


class SeverityModel:
    """Multinomial logistic regression over the spec's severity classes.

    The empirical prior is derived from the spec's own event catalogue, so it
    can never drift out of step with the catalogue the way a hardcoded table can.
    """

    def __init__(self, spec: HazardSpec, C: float = 0.5):
        self.spec = spec
        self.C = C
        self.pipeline: Pipeline | None = None
        self.le = LabelEncoder()

    def fit(self, X: pd.DataFrame, y: pd.Series) -> SeverityModel:
        known = list(self.spec.severity_classes)
        mask = y.isin(known)
        if mask.sum() == 0:
            raise ValueError("no rows with a known severity class")
        y_enc = self.le.fit_transform(y[mask])
        self.pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, C=self.C, random_state=42)),
        ]).fit(X[mask.values].values, y_enc)
        return self

    def predict_latest(self, X: pd.DataFrame) -> dict[str, float]:
        if self.pipeline is None:
            return self.spec.empirical_probs()
        proba = self.pipeline.predict_proba(X.tail(1).values)[0]
        raw = dict(zip(self.le.inverse_transform(range(len(proba))), proba, strict=True))
        prior = self.spec.empirical_probs()
        out = {c: float(raw.get(c, prior.get(c, 0.0))) for c in self.spec.severity_classes}
        total = sum(out.values()) or 1.0
        return {k: v / total for k, v in out.items()}


def blend(model_probs: dict[str, float], prior: dict[str, float],
          model_weight: float = 0.5) -> dict[str, float]:
    """Shrink a model distribution toward the observed prior.

    With a couple of dozen historical events the model side rests on very few
    observations, so shrinkage is doing real work here. Weight is explicit --
    there is deliberately no default that differs between callers.
    """
    if not 0.0 <= model_weight <= 1.0:
        raise ValueError("model_weight must be in [0, 1]")
    keys = set(model_probs) | set(prior)
    out = {k: model_weight * model_probs.get(k, 0.0)
              + (1 - model_weight) * prior.get(k, 0.0) for k in keys}
    total = sum(out.values()) or 1.0
    return {k: v / total for k, v in out.items()}
