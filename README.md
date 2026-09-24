# hazard-lab

[![CI](https://github.com/Nveerapaneni717/hazard-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/Nveerapaneni717/hazard-lab/actions/workflows/ci.yml)
[![CodeQL](https://github.com/Nveerapaneni717/hazard-lab/actions/workflows/codeql.yml/badge.svg)](https://github.com/Nveerapaneni717/hazard-lab/actions/workflows/codeql.yml)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A small, readable skeleton for **probabilistic catastrophe modelling** — occurrence,
severity, extreme value, Monte Carlo, impact — that is not tied to any one peril.

You describe a hazard once, in a single declarative file. Everything else runs unchanged.

```python
from hazardlab.registry import get_hazard

spec = get_hazard("elnino")            # or atlantic_hurricane, earthquake,
                                       # convective_storm, indian_monsoon
```

---

> ### ⚠️ AI-augmented project
>
> **This repository was built with substantial AI assistance.** The methodology,
> the domain judgement, the choice of what to model and the review of what came
> back are the author's. A large language model was used extensively for
> implementation, refactoring, documentation and adversarial review of the
> numbers.
>
> Read the code before you rely on it. That is good advice for any repository;
> it is not optional here. [`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md)
> documents what this model does *badly*, on purpose.

---

## Why this exists

It began as an actuarial study of El Niño for a seminar of the Institute of
Actuaries of India. The interesting part turned out not to be El Niño — it was
that the *shape* of the problem is the same for hurricanes, earthquakes,
convective storms and monsoon failure:

> How often does it happen · how bad is it when it does · how bad can it
> plausibly get · what does that cost

So the peril-specific knowledge was pulled out into a `HazardSpec`, and what
remains is a teaching-grade engine you can point at something else.

**This is a methodology walkthrough, not a production model.** A commercial
catastrophe model is built by specialist teams over many years, each component
its own research programme. What is offered here is the shape of the problem
and a reproducible path through it.

## Install and run

```bash
git clone https://github.com/Nveerapaneni717/hazard-lab.git && cd hazard-lab
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .                                   # add "[dev]" for tests and linting
python examples/01_quickstart.py
```

`pip install -e .` rather than `pip install -r requirements.txt`: the latter
installs the dependencies but not `hazard-lab` itself, so `import hazardlab`
would fail from a fresh clone.

The quickstart needs no network — a public-domain NOAA ONI series is bundled.

```
python examples/01_quickstart.py --hazard indian_monsoon
```

## Status

Tested on **Linux, Windows and macOS**, Python **3.10 / 3.11 / 3.12**, from a
clean clone in both editable and non-editable installs. CI runs the full suite,
a secret scan, a dependency audit and CodeQL on every push and pull request.

| | |
|---|---|
| Tests | 39, covering the models, the specs and every fixed defect |
| Hazards | 5 shipped — one worked example, four templates |
| Runtime dependencies | 4 (numpy, pandas, scipy, scikit-learn) |
| Network calls | none; a public-domain sample is bundled |

Version 0.1.0. The API is young and may change; `CHANGELOG.md` records what did.

## Swapping the hazard

This is the whole point. A hazard is one file in `hazardlab/hazards/`:

```python
from hazardlab.spec import ClassParams, HazardSpec, HistoricalEvent

SPEC = HazardSpec(
    key="my_peril",
    name="Something that goes wrong",
    index_name="Index", index_units="whatever you measure",
    description="...",
    severity_classes=("Minor", "Major", "Severe"),
    severity_thresholds={"Minor": 1.0, "Major": 2.0, "Severe": 3.0},
    events=(HistoricalEvent(1998, 1998, 2.4), ...),
    class_params={"Minor": ClassParams((1.4, .2, 1.0, 2.0), 6, {"loss_usd_bn": (5, 2)}), ...},
    impact_names=("loss_usd_bn",),
    higher_is_worse=True,
)
```

Drop it in `hazardlab/hazards/`, and `get_hazard("my_peril")` finds it. `spec.validate()`
runs automatically and tells you what is incoherent before anything else does.

**Installed hazard-lab as a dependency rather than cloning it?** Keep your specs
in your own project and register them at runtime — no need to edit site-packages:

```python
from hazardlab import register, get_hazard, MonteCarloEngine

register(my_spec)                  # validated on the way in
spec = get_hazard("my_peril")
```

Full walkthrough: [`examples/02_add_a_hazard.md`](examples/02_add_a_hazard.md)

### Shipped hazards

| key | index | direction | status |
|---|---|---|---|
| `elnino` | ONI (°C anomaly) | higher is worse | **worked example**, real catalogue |
| `atlantic_hurricane` | seasonal ACE | higher is worse | template |
| `earthquake` | moment magnitude | higher is worse | template |
| `convective_storm` | severe-day count | higher is worse | template |
| `indian_monsoon` | AISMR % of LPA | **lower is worse** | template, inverted scale |

`indian_monsoon` exists to prove the engine is not quietly assuming that bigger
means worse. If you are modelling flood depth, loss ratio, or anything where
small is bad, start from that file.

## Architecture

```
hazardlab/
  spec.py                  HazardSpec — the only peril-aware object
  registry.py              discovery: get_hazard("elnino")
  io/series.py             load an index series (bundled / CSV / your own frame)
  features/builder.py      causal features from any index series
  models/occurrence.py     P(event) — calibrated logistic regression
  models/severity.py       P(class | event) — multinomial + shrinkage to prior
  models/return_period.py  GEV block maxima → return levels
  models/monte_carlo.py    occurrence → severity → conditional impacts
  impact/translator.py     severity → consequence, and its sensitivity
  hazards/               one file per peril
examples/                  runnable quickstart + how to add a hazard
```

The dependency arrow only ever points one way: `hazardlab/hazards/` knows about
`hazardlab/`, never the reverse.

## What it deliberately does not do

No backtest harness. No validated predictive intervals. No fitted impact
functions. These are absences with reasons, written down in
[`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md) — several are framed as exercises,
because working out *why* a model is wrong teaches more than reading one that
claims it is right.

## Licence and attribution

MIT — see [`LICENSE`](LICENSE).

Author: **Nishanth Veerapaneni**. Originally presented to the Institute of
Actuaries of India, August 2026. Bundled ONI data is NOAA Climate Prediction
Center output, a US Government work in the public domain.

Contributions welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md). Security policy:
[`SECURITY.md`](SECURITY.md).
