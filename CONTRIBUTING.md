# Contributing

Contributions are welcome, particularly new hazard specs and the missing
validation machinery listed in [`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md).

## Setup

```bash
python -m venv .venv && .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

`pre-commit install` matters: it runs secret scanning before anything reaches
your history, which is far easier than removing it afterwards.

## Before opening a pull request

```bash
ruff check .
pytest -q
python examples/01_quickstart.py --sims 500
```

## What makes a good contribution here

**A new hazard spec.** One file in `hazards/`, following
[`examples/02_add_a_hazard.md`](examples/02_add_a_hazard.md). Say in `notes`
whether the catalogue is real or illustrative, and cite the source. A spec with
a real catalogue and honest placeholder impacts is more useful than one with
invented numbers throughout.

**Anything from the limitations list.** The walk-forward backtest harness is the
single most valuable missing piece, followed by a calibration/coverage test.

**A defect you found.** Especially one that produces plausible-looking numbers —
those are the dangerous ones, and this project has shipped three.

## What to avoid

- **Personal or machine-specific data.** No absolute paths, usernames, machine
  names, credentials or email addresses. CI scans for secrets; the rest is on
  review.
- **Large binaries.** Data is fetched from source. The only bundled data is a
  16 KB public-domain sample so the quickstart runs offline. Pre-commit blocks
  anything over 512 KB.
- **Hardcoding peril knowledge into `hazardlab/`.** If the engine needs to know
  something about your peril, that is a signal the `HazardSpec` needs a new
  field, not that the engine needs an `if`.
- **Silent failure.** Prefer raising with an explanation. `MonteCarloEngine`
  requiring explicit probabilities is the house style: it is better to be
  stopped than to be quietly given a default.

## Style

Ruff enforces the mechanical parts (line length 100, import order). Beyond that:
write comments that explain *why*, especially where the code resists an obvious
simplification. Several comments in this repository exist because the obvious
simplification is exactly what broke it the first time.

## AI assistance

This project was built with substantial AI assistance and there is no
expectation that contributions avoid it. Do say so in the pull request
description if a change is largely model-generated, and satisfy yourself that
it is correct before submitting — the review burden is yours either way.
