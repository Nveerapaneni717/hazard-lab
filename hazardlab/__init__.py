"""hazard-lab -- a hazard-agnostic skeleton for probabilistic catastrophe modelling.

The public API is re-exported here, so the common imports stay short:

    from hazardlab import HazardSpec, MonteCarloEngine, get_hazard

Everything peril-specific lives in a `HazardSpec` (see the `hazards/` package);
nothing under `hazardlab/` imports peril knowledge.
"""
from hazardlab.features.builder import (
    annual_maxima,
    attach_auxiliary,
    build_features,
    build_target,
)
from hazardlab.impact.translator import impact_table, sensitivity
from hazardlab.io.series import load_csv, load_frame, load_sample
from hazardlab.models.monte_carlo import MonteCarloEngine
from hazardlab.models.occurrence import OccurrenceModel
from hazardlab.models.return_period import ReturnPeriodAnalyzer
from hazardlab.models.severity import SeverityModel, blend
from hazardlab.registry import available, get_hazard, register, unregister
from hazardlab.spec import ClassParams, HazardSpec, HistoricalEvent

__version__ = "0.1.0"

__all__ = [
    # spec
    "HazardSpec",
    "HistoricalEvent",
    "ClassParams",
    # registry
    "get_hazard",
    "available",
    "register",
    "unregister",
    # data and features
    "load_sample",
    "load_csv",
    "load_frame",
    "build_features",
    "build_target",
    "attach_auxiliary",
    "annual_maxima",
    # models
    "OccurrenceModel",
    "SeverityModel",
    "blend",
    "ReturnPeriodAnalyzer",
    "MonteCarloEngine",
    # impact
    "impact_table",
    "sensitivity",
    "__version__",
]
