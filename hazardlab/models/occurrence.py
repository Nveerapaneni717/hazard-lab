"""Occurrence layer — P(event onset within the forecast horizon).

Hazard-agnostic: it takes a feature matrix and a binary target. The only thing
that varies by peril is how those were built (see hazardlab.features.builder).
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def _base_pipeline(c: float) -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(C=c, max_iter=500, random_state=42)),
    ])


class OccurrenceModel:
    """Regularised logistic regression with isotonic calibration.

    NOTE ON VALIDATION (see KNOWN_LIMITATIONS.md): `cv_auc` is measured with a
    time-ordered TimeSeriesSplit on the *uncalibrated* pipeline. The calibration
    wrapper itself uses stratified folds, so the calibrated probabilities are not
    strictly out-of-sample. Treat the AUC as an optimistic upper bound.
    """

    def __init__(self, C: float = 0.1, n_splits: int = 5, calibrate: bool = True):
        self.C = C
        self.n_splits = n_splits
        self.calibrate = calibrate
        self.pipeline = None
        self.cv_scores: list[float] = []
        self.skipped_folds = 0
        self.feature_names: list[str] = []

    def fit(self, X: pd.DataFrame, y: pd.Series) -> OccurrenceModel:
        n_classes = y.nunique()
        if n_classes < 2:
            only = y.iloc[0] if len(y) else "empty"
            raise ValueError(
                f"the target has only one class ({only!r}), so there is nothing "
                "to learn. The usual cause is a mismatch between your index "
                "series and the spec: check that the series really is the "
                "spec's `index_name`, that its units match `index_units`, and "
                "that `higher_is_worse` points the right way. An inverted-scale "
                "spec applied to a rising index marks every period as an event."
            )
        self.feature_names = list(X.columns)
        base = _base_pipeline(self.C)
        self.pipeline = (
            CalibratedClassifierCV(base, cv=self.n_splits, method="isotonic")
            if self.calibrate else base
        )
        self.pipeline.fit(X.values, y.values)

        self.cv_scores, self.skipped_folds = [], 0
        for tr, te in TimeSeriesSplit(n_splits=self.n_splits).split(X):
            if y.values[te].sum() == 0:
                self.skipped_folds += 1      # reported, not silently dropped
                continue
            m = _base_pipeline(self.C).fit(X.values[tr], y.values[tr])
            self.cv_scores.append(
                roc_auc_score(y.values[te], m.predict_proba(X.values[te])[:, 1])
            )
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if self.pipeline is None:
            raise RuntimeError("model not fitted")
        return self.pipeline.predict_proba(X.values)[:, 1]

    def predict_latest(self, X: pd.DataFrame, warn_saturated: bool = True) -> float:
        """Probability for the most recent row only.

        Warns on saturation. Isotonic calibration is a step function, so it can
        and does return exactly 0.0 or 1.0 when the input falls beyond the
        outermost calibration bin. A probability of exactly 1 is not defensible
        actuarially -- it asserts impossibility of the complement from a few
        dozen events. Treat a saturated value as "off the top of the fitted
        range", not as certainty, and consider `calibrate=False` (which returns
        the uncalibrated logistic probability) when you need a usable number.
        """
        p = float(self.predict_proba(X.tail(1))[0])
        if warn_saturated and p in (0.0, 1.0):
            warnings.warn(
                f"calibrated probability saturated at {p:.1f}: the input lies "
                "beyond the outermost isotonic bin. Report this as 'outside the "
                "calibrated range', not as certainty.",
                RuntimeWarning, stacklevel=2,
            )
        return p

    def cv_auc(self) -> float:
        return float(np.mean(self.cv_scores)) if self.cv_scores else float("nan")

    def report(self) -> dict:
        return {
            "cv_auc": round(self.cv_auc(), 4),
            "folds_scored": len(self.cv_scores),
            "folds_skipped_no_positives": self.skipped_folds,
            "n_features": len(self.feature_names),
            "calibrated": self.calibrate,
        }
