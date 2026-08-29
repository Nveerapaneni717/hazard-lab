"""HazardSpec — the single object that makes this library hazard-agnostic.

Everything downstream (occurrence, severity, return periods, Monte Carlo,
impact translation) reads its hazard-specific knowledge from a HazardSpec.
To model a new peril you write one spec; you do not touch the engine.

    from hazardlab.registry import get_hazard
    spec = get_hazard("elnino")        # or "atlantic_hurricane", "earthquake", ...
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field


@dataclass(frozen=True)
class HistoricalEvent:
    """One observed occurrence of the hazard."""

    start_year: int
    end_year: int
    peak_intensity: float
    severity: str | None = None          # None -> derived from thresholds

    @property
    def label(self) -> str:
        if self.start_year == self.end_year:
            return str(self.start_year)
        return f"{self.start_year}-{self.end_year}"


@dataclass(frozen=True)
class ClassParams:
    """Per-severity-class simulation parameters.

    peak:     (mean, sd, lower, upper) for a truncated normal on peak intensity
    duration: mean duration in months (Poisson)
    impacts:  {impact_name: (mean, sd)} drawn as normals conditional on class
    """

    peak: tuple[float, float, float, float]
    duration_months: float
    impacts: Mapping[str, tuple[float, float]] = field(default_factory=dict)


@dataclass(frozen=True)
class HazardSpec:
    """Declarative description of a peril. See hazards/ for worked examples."""

    key: str
    name: str
    index_name: str                       # "ONI", "ACE", "Mw", "AISMR % of LPA"
    index_units: str
    description: str

    severity_classes: Sequence[str]
    # lower bound of each class, ascending; the first is also the occurrence threshold
    severity_thresholds: Mapping[str, float]

    events: Sequence[HistoricalEvent]
    class_params: Mapping[str, ClassParams]

    sources: Mapping[str, str] = field(default_factory=dict)
    impact_names: Sequence[str] = field(default_factory=tuple)
    # a higher index means a worse event for most perils; set False for e.g. rainfall
    higher_is_worse: bool = True
    notes: str = ""

    # ---------------------------------------------------------------- helpers
    @property
    def occurrence_threshold(self) -> float:
        return self.severity_thresholds[self.severity_classes[0]]

    def classify(self, peak: float) -> str:
        """Map a peak intensity onto a severity class name."""
        ordered = sorted(
            self.severity_thresholds.items(), key=lambda kv: kv[1],
            reverse=not self.higher_is_worse,
        )
        chosen = None
        for cls, lo in ordered:
            if (peak >= lo) if self.higher_is_worse else (peak <= lo):
                chosen = cls
        return chosen or "None"

    def empirical_counts(self) -> dict[str, int]:
        """Observed event counts per class, derived from the catalogue."""
        counts = {c: 0 for c in self.severity_classes}
        for ev in self.events:
            cls = ev.severity or self.classify(ev.peak_intensity)
            if cls in counts:
                counts[cls] += 1
        return counts

    def empirical_probs(self) -> dict[str, float]:
        """Observed relative frequency per class. Used as the severity prior."""
        counts = self.empirical_counts()
        total = sum(counts.values())
        if total == 0:
            n = len(self.severity_classes)
            return {c: 1.0 / n for c in self.severity_classes}
        return {c: v / total for c, v in counts.items()}

    def validate(self) -> list[str]:
        """Return a list of problems. Empty list means the spec is coherent."""
        errs: list[str] = []
        if not self.events:
            errs.append("no historical events")
        missing = [c for c in self.severity_classes if c not in self.severity_thresholds]
        if missing:
            errs.append(f"classes without a threshold: {missing}")
        missing_p = [c for c in self.severity_classes if c not in self.class_params]
        if missing_p:
            errs.append(f"classes without simulation params: {missing_p}")
        for cls, cp in self.class_params.items():
            mu, sd, lo, hi = cp.peak
            if sd <= 0:
                errs.append(f"{cls}: peak sd must be positive")
            if lo >= hi:
                errs.append(f"{cls}: peak bounds inverted ({lo} >= {hi})")
            if not (lo <= mu <= hi):
                errs.append(f"{cls}: peak mean {mu} outside bounds [{lo}, {hi}]")
            if cp.duration_months <= 0:
                errs.append(f"{cls}: duration must be positive")
        for ev in self.events:
            if ev.severity and ev.severity not in self.severity_classes:
                errs.append(f"event {ev.label}: unknown severity '{ev.severity}'")
        return errs
