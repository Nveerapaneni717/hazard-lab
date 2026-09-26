# Known limitations

Every item here is a real defect or a real absence. Nothing is hidden, and
several are left in place deliberately as exercises - working out why a model is
wrong teaches more than reading one that claims it is right.

Most of these were found by adversarially auditing the original El Niño study
*after* it had been presented and reviewed. That is the honest order of events,
and it is the main reason this file exists.

---

## 1. There is no backtest - the biggest gap

No walk-forward harness exists. The model has never been asked: *refit using
only what was knowable in 1997, or 2015, or 2023 - does the realised outcome
fall inside the predicted distribution?*

Until that exists, every probability here is **indicative, not validated**.

Doing it properly is harder than it looks, and two traps are baked into most
naive attempts:

- imputing with a statistic computed over the whole series (a global median uses
  the future to fill the past), and
- aligning auxiliary series with a nearest-neighbour join, which can pull a
  future observation backwards.

`hazardlab.features.builder` avoids both - see its module docstring. A backtest
built on a leaky feature pipeline will look *better* than it deserves to.

> **Exercise.** Write `hazardlab/validation/walk_forward.py`. Refit at each
> historical origin, store the predicted distribution, and compare against what
> happened. Report a Brier score and a reliability curve.

## 2. The predictive intervals are not calibrated

`MonteCarloEngine.quantiles()` returns quantiles of the model's *own* simulated
distribution. They are internally consistent by construction and have never been
tested against outcomes.

Claiming calibration requires the backtest above plus a coverage test: does the
outcome fall below the predicted P95 about 95% of the time? With a couple of
dozen historical events you would have very few effective observations.

**Present them as a spread of modelled outcomes, not as confidence intervals.**

## 3. Isotonic calibration saturates at 0 and 1

`CalibratedClassifierCV(method="isotonic")` is a step function, so inputs beyond
the outermost bin return *exactly* 0.0 or 1.0. On the bundled ONI series the
latest row returns 1.000.

A probability of exactly 1 is not defensible actuarially - it asserts the
complement is impossible on the basis of a few dozen events.

`OccurrenceModel.predict_latest()` raises a `RuntimeWarning` when this happens,
and `examples/01_quickstart.py` catches it, says so in the output, and refits
without calibration so the number it carries into the simulation is usable. Read it as *"outside the calibrated range"*, not as certainty. Pass
`calibrate=False` when you need a usable number in the tail.

## 4. Reported AUC is an optimistic upper bound

`cv_auc` uses a time-ordered `TimeSeriesSplit` on the **uncalibrated** pipeline.
The shipped predictor is the isotonic-calibrated model, whose internal folds are
*stratified*, not time-ordered - so the calibration layer sees future data.

Folds containing no positive cases are skipped; the count is reported in
`report()["folds_skipped_no_positives"]` rather than silently dropped, which is
what the original code did.

Separately: for a persistent index like ONI, most of the apparent skill is
persistence, not forecasting. A lagged-value benchmark is the comparison that
matters, and it is not implemented.

## 5. Severity is the single latent factor

In the Monte Carlo, everything downstream - peak intensity, duration, every
impact - is drawn conditional on the severity class, and independently of
everything else within that class. There is no copula. A simulation landing at
the top of a class's intensity range does not get a correspondingly worse loss.

Run `hazardlab.impact.translator.sensitivity(spec, impact)`: for the bundled
El Niño spec, the step between adjacent class means is **3.0 to 5.0 within-class
standard deviations**, across all three impact measures. One class of
misclassification moves the answer further than every other source of
uncertainty in the model combined.

**The severity distribution is the model.** If you disagree with it, everything
moves and nothing pushes back.

## 6. Periods are drawn independently by default

`MonteCarloEngine(period_dependence=0.0)` treats consecutive periods as
independent Bernoulli draws.

For ENSO specifically this is not conservative - it is wrong in a known
direction, since La Niña commonly follows a strong El Niño. The parameter exists
so you can set it deliberately; the default is independence because that is what
the record supports least badly, not because it is right.

> **Exercise.** Estimate the transition matrix from the historical catalogue and
> replace the scalar `period_dependence` with it.

## 7. Distributions were chosen, not fitted

No goodness-of-fit testing exists anywhere in this repository.

- **Bernoulli / multinomial** - structurally right for binary and categorical.
- **Truncated normal on peak intensity** - the truncation bounds *are* the class
  boundaries, so it is a within-class smoother, not an independently fitted law.
  It cannot tell you anything the class label does not already carry.
- **Poisson duration** - round-number means from the literature. Poisson also
  forces variance = mean, which is a strong and untested constraint.
- **Normal impacts** - hardcoded (mean, sd) pairs, order-of-magnitude figures.

With a few dozen events you could not fit five class-conditional distributions
with any power anyway. That is the real constraint, and stating the assumption
is better than dressing it up.

## 8. Feature information is narrower than the feature count

The original study used 51 features. Counted by origin, **44 of 51 (86%) were
transformations of the same tropical Pacific state**, and 25 came from the ONI
series alone. Within that block the median pairwise |r| was 0.48, with 13% of
pairs above 0.8.

Genuinely independent information amounted to three sources: the Pacific state,
the Indian Ocean Dipole, and the seasonal cycle.

A feature count measures representational richness, not information content.
It follows that **per-feature attribution is not identifiable** under ridge
shrinkage on collinear inputs - coefficient rankings should be read as *which
families matter*, never as *this variable contributes X%*.

## 9. Impact figures are not fitted

Every impact number in every shipped spec is an order-of-magnitude figure from
published literature or, in the template hazards, an outright placeholder.
None is estimated from data. The four non-El-Niño specs say `TEMPLATE` in their
`notes` field for exactly this reason.

## 10. Three defects that were fixed, recorded because the failure modes generalise

**Simulation ran on default parameters.** The engine used to carry
`p_2026=0.65, p_2027=0.55` as constructor defaults. A catalogue generated from
those defaults was mistaken for fitted output - the headline number happened to
land within 0.3pp of the fitted one, so nothing looked wrong, while the second
period and the entire severity mix were placeholders.

*Fix:* `MonteCarloEngine` now **requires** both probability arguments. There is
no default to fall through to.

**A hand-entered catalogue drifted from the data.** 16 of 22 hardcoded peaks
disagreed with the observed series. Two changed severity class - most visibly
1997-98 recorded as ONI 2.8 / Extreme when the observed peak is 2.40 / Super
(2.8 appears to be a Niño-3.4 SST value pasted into an ONI column). The QC check
that should have caught it tested `> 0.4`, and the error was exactly 0.40.

*Fix:* severity is now **derived** from thresholds via `HazardSpec.classify()`,
never stored as a label. The error class is structurally impossible.

**A third, found while building this library.** An early version of
`ReturnPeriodAnalyzer.fit` filtered block maxima to those above the occurrence
threshold - a tidy-looking line that truncates the maxima distribution. It moved
the GEV shape from ξ = −0.24 (bounded) to ξ = +0.29 (heavy-tailed) and the
implied 1000-year ONI from 3.3 to **9.7 °C**. Physically absurd, and it would
have passed any test that only checked the code ran.

The lesson in all three: the dangerous errors are the ones that produce
*plausible* numbers.
