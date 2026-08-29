## What this changes

<!-- One or two sentences. What is different after this PR? -->

## Why

<!-- The problem, not the solution. Link an issue if there is one. -->

## Type

- [ ] New hazard spec
- [ ] Bug fix
- [ ] New feature / capability
- [ ] Documentation
- [ ] Tests or tooling

## Checks

- [ ] `ruff check .` passes
- [ ] `pytest -q` passes
- [ ] `python examples/01_quickstart.py --sims 500` runs
- [ ] No absolute paths, usernames, machine names, credentials or personal data
- [ ] No files over 512 KB

## If this adds a hazard spec

- [ ] `notes` says whether the catalogue is real or illustrative
- [ ] Data sources are cited in `sources`
- [ ] `HistoricalEvent.severity` left as `None` so severity is derived
- [ ] `higher_is_worse` is set deliberately

## If this changes model behaviour

- [ ] A test covers the new behaviour
- [ ] `KNOWN_LIMITATIONS.md` updated if this fixes or introduces a limitation

## AI assistance

<!-- Optional. If this change is largely model-generated, say so. There is no
     penalty; it helps reviewers calibrate. You are responsible for correctness
     either way. -->
