"""Hazard registry — discover and load HazardSpec definitions."""
from __future__ import annotations

import importlib
import pkgutil
from functools import cache

from hazardlab.spec import HazardSpec

_PACKAGE = "hazards"


@cache
def available() -> tuple[str, ...]:
    """Names of every hazard spec that can be loaded."""
    pkg = importlib.import_module(_PACKAGE)
    return tuple(sorted(m.name for m in pkgutil.iter_modules(pkg.__path__)))


def get_hazard(key: str) -> HazardSpec:
    """Load a hazard spec by module name, e.g. get_hazard('elnino')."""
    if key not in available():
        raise KeyError(f"unknown hazard '{key}'. Available: {', '.join(available())}")
    mod = importlib.import_module(f"{_PACKAGE}.{key}")
    spec = getattr(mod, "SPEC", None)
    if not isinstance(spec, HazardSpec):
        raise TypeError(f"{_PACKAGE}.{key} must define a module-level SPEC: HazardSpec")
    problems = spec.validate()
    if problems:
        raise ValueError(f"hazard '{key}' spec is invalid: " + "; ".join(problems))
    return spec
