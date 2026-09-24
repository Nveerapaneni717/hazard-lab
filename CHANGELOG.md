# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning is [semantic](https://semver.org/).

## [Unreleased]

### Added
- CI now tests **Windows and macOS** alongside Linux. The code was verified on
  Windows by hand but nothing guarded it, and most readers of this repo are on
  Windows -- that is where a silent regression would actually hurt.
- A `ci-complete` aggregate job that succeeds only if every other job did.
  Branch protection requires that one name instead of enumerating each matrix
  leg, so changing the matrix can no longer silently block merges when a
  required check name stops existing.
- `.gitleaks.toml`, allowlisting one documented false positive: gitleaks'
  generic-api-key rule matches `key = "..."` and `HazardSpec.key` is a field
  name. Scoped to snake_case identifiers in four paths.
- A Status section in the README.

## [0.1.0] - 2026-08-22

First public release. Extracted from an actuarial El Nino study presented to the
Institute of Actuaries of India, and generalised so the engine is not tied to
any one peril.

### Added
- `HazardSpec`: a declarative description of a peril (index, thresholds, event
  catalogue, per-class simulation and impact parameters). The only peril-aware
  object in the library.
- Hazard registry with discovery by name: `get_hazard("elnino")`.
- Model layers, all peril-agnostic: calibrated logistic occurrence, multinomial
  severity with shrinkage to the observed prior, GEV block-maxima return
  periods, and a Monte Carlo engine.
- Causal feature builder with explicit guards against the two leakage patterns
  that broke the original study.
- Five hazards: `elnino` (worked example, real catalogue) plus templates for
  `atlantic_hurricane`, `earthquake`, `convective_storm` and `indian_monsoon`.
  The last runs on an inverted scale, where a lower index is worse.
- Bundled 16 KB public-domain NOAA ONI sample so the quickstart runs offline.
- 34 tests, several of them regression guards for the defects below.

### Fixed
Three defects carried by the original study, each now covered by a test.

- **Simulation ran on constructor defaults.** A catalogue generated from
  `p=0.65/0.55` defaults was mistaken for fitted output; the headline number
  landed within 0.3pp of the fitted one, so nothing looked wrong while the
  second period and the whole severity mix were placeholders. Probabilities are
  now required arguments with no fallback.
- **Hand-entered catalogue drifted from observations** on 16 of 22 events. Two
  changed class, most visibly 1997-98 stored as ONI 2.8 / Extreme against an
  observed peak of 2.40 / Super. Severity is now derived from thresholds and
  cannot be stored on an event.
- **GEV was fitted to filtered block maxima.** Dropping blocks below the
  occurrence threshold moved the shape parameter from -0.24 (bounded) to +0.29
  (heavy-tailed) and the implied 1000-year ONI from 3.3 to 9.7 degrees C. The
  fit now uses every block.

### Known limitations
No backtest harness, no validated predictive intervals, unfitted impact
functions, and more. All documented in `KNOWN_LIMITATIONS.md` rather than
hidden; several are framed as exercises.
