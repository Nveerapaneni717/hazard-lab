# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning is [semantic](https://semver.org/).

## [Unreleased]

### Added
- Runtime hazard registration -- `register(spec)` and `unregister(key)` -- so a
  spec can live in your own project instead of being dropped into site-packages.
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
- Community files: contributing guide, code of conduct, security policy, and
  issue and pull request templates.
- `py.typed`, so type checkers read the annotations in an installed copy.
- A Status section in the README.
- Five tests, covering runtime registration and the single-class guard. 34 -> 39.

### Changed
- **Breaking.** Hazard specs moved from a top-level `hazards` package to
  `hazardlab.hazards`. Installing the project no longer claims the generic
  top-level name `hazards` in site-packages, where it could collide with
  anything else that wants it. Replace `from hazards.x import SPEC` with
  `from hazardlab.hazards.x import SPEC`.
- Install instructions are split into macOS/Linux and Windows PowerShell blocks,
  one command per line. The single block they replace chained with `&&` and
  activated the venv with `source`; Windows PowerShell 5.1 has neither, so the
  first thing most readers copied did not run.
- The quickstart states its data boundary explicitly instead of implying one.

### Fixed
- **A fresh clone did not work.** `requirements.txt` installs the dependencies
  but not the project itself, so `import hazardlab` failed and
  `python examples/01_quickstart.py` put `examples/` on `sys.path` rather than
  the repository root. CI and the README now use `pip install -e .`. The test
  suite had masked this -- pytest inserts the rootdir for itself, so tests passed
  while the documented entry point did not.
- `SECURITY.md` and `.github/dependabot.yml` both claimed Dependabot would
  propose SHA pins for actions referenced by tag. It does not: it follows the
  reference style already in use. Corrected in both, with the manual migration
  path written down instead.
- `SECURITY.md` described the direct dependencies as pinned. They are
  lower-bounded with a major-version cap, which is a weaker guarantee.
- `KNOWN_LIMITATIONS.md` section 10 was headed "Two defects" while describing
  three, and gave the class-separation step as 3-4 within-class standard
  deviations where `sensitivity()` returns 3.0 to 5.0.
- The README described CI as running on "every push and pull request". Both
  workflows are scoped to `main`, so a push to a feature branch runs nothing
  until a pull request opens.

## [0.1.0] - 2026-08-29

The initial extraction. Taken from an actuarial El Niño study presented to the
Institute of Actuaries of India on 22 August 2026, and generalised so the engine
is not tied to any one peril. Dated to the commit that created it, not to the
seminar; the repository was not published until the following month.

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
Three defects, each now covered by a test. The first two were carried over from
the original study; the third was introduced here and caught before release.

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
