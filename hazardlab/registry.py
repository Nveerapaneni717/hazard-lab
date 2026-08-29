"""Hazard registry -- discover built-in specs and register your own.

Two ways to add a hazard:

1. Drop a module in `hazardlab/hazards/` defining a module-level `SPEC`. Best
   if you cloned the repo, which is the intended path for learning from it.

2. Call `register(spec)` at runtime. Best if you installed hazard-lab as a
   dependency and keep your specs in your own project, where they belong.

       from hazardlab import HazardSpec, register, get_hazard
       register(my_spec)
       get_hazard("my_peril")
"""
from __future__ import annotations

import importlib
import pkgutil

from hazardlab.spec import HazardSpec

_PACKAGE = "hazardlab.hazards"

# Specs added at runtime by register(). Kept separate from the built-ins so a
# user spec can never be silently mistaken for one that ships with the library.
_REGISTERED: dict[str, HazardSpec] = {}


def _builtin_names() -> tuple[str, ...]:
    pkg = importlib.import_module(_PACKAGE)
    return tuple(sorted(m.name for m in pkgutil.iter_modules(pkg.__path__)))


def available(include_registered: bool = True) -> tuple[str, ...]:
    """Every hazard that can be loaded, built-in and registered."""
    names = set(_builtin_names())
    if include_registered:
        names |= set(_REGISTERED)
    return tuple(sorted(names))


def register(spec: HazardSpec, *, overwrite: bool = False) -> HazardSpec:
    """Add a spec at runtime. Validated before it is accepted.

    Raises if the key is already taken, unless `overwrite=True`. Silently
    shadowing a built-in is exactly the kind of surprise that costs someone an
    afternoon, so it has to be asked for explicitly.
    """
    if not isinstance(spec, HazardSpec):
        raise TypeError(f"expected a HazardSpec, got {type(spec).__name__}")
    problems = spec.validate()
    if problems:
        raise ValueError(f"spec '{spec.key}' is invalid: " + "; ".join(problems))
    if not overwrite:
        if spec.key in _REGISTERED:
            raise KeyError(f"'{spec.key}' is already registered; pass overwrite=True")
        if spec.key in _builtin_names():
            raise KeyError(
                f"'{spec.key}' is a built-in hazard; pass overwrite=True to shadow it"
            )
    _REGISTERED[spec.key] = spec
    return spec


def unregister(key: str) -> None:
    """Remove a runtime-registered spec. Built-ins are untouched."""
    _REGISTERED.pop(key, None)


def get_hazard(key: str) -> HazardSpec:
    """Load a hazard spec by key. Registered specs take precedence."""
    if key in _REGISTERED:
        return _REGISTERED[key]
    if key not in _builtin_names():
        raise KeyError(
            f"unknown hazard '{key}'. Available: {', '.join(available())}. "
            "To add your own, drop a module in hazardlab/hazards/ or call "
            "hazardlab.register(spec)."
        )
    mod = importlib.import_module(f"{_PACKAGE}.{key}")
    spec = getattr(mod, "SPEC", None)
    if not isinstance(spec, HazardSpec):
        raise TypeError(f"{_PACKAGE}.{key} must define a module-level SPEC: HazardSpec")
    problems = spec.validate()
    if problems:
        raise ValueError(f"hazard '{key}' spec is invalid: " + "; ".join(problems))
    return spec
