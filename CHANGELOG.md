# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning is [semantic](https://semver.org/).

## [Unreleased]

### Fixed
- **The documented install failed on the pip a fresh venv gives you.**
  `python -m venv` provides whichever pip shipped with your Python, and an older
  3.10 point release still bundles pip 21.2. Editable installs of a
  `pyproject.toml` project need pip 21.3 or newer (PEP 660), so following the
  README verbatim ended at

      ERROR: ... Directory cannot be installed in editable mode
      (A "pyproject.toml" file was found, but editable mode currently
       requires a setuptools-based build.)

  which blames setuptools for what is really pip's age. CI never saw it: it runs
  `python -m pip install --upgrade pip` first, and the README did not. The
  documented path and the tested path have to be the same path. All four install
  blocks now upgrade pip, as CI always did. Non-editable `pip install .` was
  unaffected.
- The rule that a hazard module must be named after its `key` was written down
  nowhere. Discovery is by module name, so `key="my_peril"` has to live in
  `my_peril.py`. Every shipped example happens to match, so it only bit someone
  choosing their own filename, who got a `KeyError` instead. Now stated in the
  README, the walkthrough and the registry docstring.
- `P(at least one)` could still print 1.0000 at low `--sims`. At 500 draws a
  probability of 4e-4 is unmeasurable, so zero "no event" simulations is routine
  and the estimate lands exactly on 1, reading as certainty once again. The
  quickstart now says so where it happens: 0 of N is a resolution limit, not
  impossibility.
- Em and en dashes replaced with plain hyphens throughout.

## [0.2.0] - 2026-09-25

The first release that is actually published. Minor rather than patch because
the hazard specs moved package, which breaks any import written against 0.1.0.

0.1.0 is recorded below for provenance but is deliberately left untagged: it was
never released publicly, and it carries the packaging defect fixed here, so a
checkout of it fails at its own documented quickstart.

### Added
- CI tests every Python version `requires-python` admits -- 3.10 through 3.14 --
  rather than stopping at 3.12 while the metadata promised `>=3.10`. Windows and
  macOS move to 3.13. A badge nobody verifies is worse than no badge.
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
- A weekly `schedule` and a `workflow_dispatch` trigger on the CI workflow, so
  a full-history secret scan is reachable at all. gitleaks-action scopes its
  scan by event and a push or pull request run walks only its own commits, so
  nothing was ever scanning what was already in the repository.
- A Status section in the README.
- A comment on `test_monte_carlo_requires_explicit_probabilities` explaining
  that its wrong-arity call is deliberate. CodeQL reports it, the alert is
  dismissed as "used in tests", and the only way to satisfy the scanner in code
  is to restore the default probabilities -- i.e. to reintroduce the defect.
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
- **The quickstart told first-time readers to use a probability of 1.000.**
  Isotonic calibration saturates beyond its outermost bin, so the headline
  occurrence probability came back as exactly 1 -- printed with `<- use this`
  beside it, and fed straight into the Monte Carlo, which made every number
  downstream degenerate. `OccurrenceModel.predict_latest` has always raised a
  `RuntimeWarning` for precisely this case, but `examples/01_quickstart.py`
  opened with a blanket `warnings.filterwarnings("ignore")` that hid it: the
  project's own honesty mechanism, silenced in the one place a newcomer looks.
  The filter now covers third-party deprecations only, the saturation is
  explained where it occurs, and an uncalibrated refit supplies the probability
  the simulation actually uses.
- `P(at least one)` printed to three decimals, so 0.9995 rendered as "1.000" and
  read as certainty through rounding alone. Now four decimals, with the
  complement beside it.
- "MONTE CARLO" was printed twice for any hazard with no bundled index series.
- `--help` documented neither option.
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
- **CI was red on `main` from the first push.** gitleaks-action builds its scan
  range as `<first commit of the push>^..<last commit>`. On a repository's very
  first push that first commit is the root commit, which has no parent, so git
  exited with `unknown revision` and the scan failed before inspecting anything.
  No secret was involved. All five test legs passed; `ci-complete` then failed
  because the security job had, which is the aggregate check working correctly.
  The condition cannot recur, since a root commit is pushed exactly once, so the
  next push to `main` clears it. Confirmed locally with gitleaks v8.18.4 -- the
  version `.pre-commit-config.yaml` pins -- a full-history scan of every commit
  against the existing `.gitleaks.toml` reports no leaks.

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
