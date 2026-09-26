"""Quickstart: the full pipeline on the bundled El Nino sample. No network needed.

    python examples/01_quickstart.py
    python examples/01_quickstart.py --hazard indian_monsoon

Read this top to bottom -- it is the whole library in about sixty lines.
"""
from __future__ import annotations

import argparse
import warnings

# Quieten third-party deprecation chatter only. This project's own warnings must
# get through: a blanket filterwarnings("ignore") hid the saturation warning
# below, which is the single most important thing this example has to say.
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

from hazardlab.features.builder import annual_maxima, build_features, build_target
from hazardlab.impact.translator import sensitivity
from hazardlab.io.series import load_sample
from hazardlab.models.monte_carlo import MonteCarloEngine
from hazardlab.models.occurrence import OccurrenceModel
from hazardlab.models.return_period import ReturnPeriodAnalyzer
from hazardlab.registry import available, get_hazard

# Which bundled series belongs to which hazard. Only ONI ships with the repo;
# the rest are yours to supply, and this mapping is where you say so.
SERIES_FOR = {
    "elnino": "oni",
    "atlantic_hurricane": None,
    "earthquake": None,
    "convective_storm": None,
    "indian_monsoon": None,
}


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Run the whole hazard-lab pipeline against one hazard spec.",
        epilog="Only 'elnino' ships with an index series, so only it can fit the "
               "occurrence and return-period layers. Every other hazard runs the "
               "Monte Carlo and impact layers on a stated base rate.",
    )
    ap.add_argument("--hazard", default="elnino", choices=available(),
                    help="which shipped hazard spec to run (default: elnino)")
    ap.add_argument("--sims", type=int, default=10_000,
                    help="Monte Carlo iterations (default: 10000)")
    args = ap.parse_args()

    spec = get_hazard(args.hazard)
    print(f"HAZARD  {spec.name}   index={spec.index_name} ({spec.index_units})")
    print(f"        {len(spec.events)} events in catalogue")
    prior = spec.empirical_probs()
    print(f"        observed prior: {({k: round(v, 3) for k, v in prior.items()})}\n")

    # ---- 1. occurrence and 2. return periods ---------------------------
    # These two layers need an OBSERVED SERIES of the spec's own index. The spec
    # is portable; the data is not. Only ONI is bundled here, so only `elnino`
    # can run them out of the box -- for any other hazard you supply the series.
    #
    # Applying a spec to the wrong series is not a harmless no-op: point the
    # inverted-scale monsoon spec at ONI and every period counts as an event,
    # the target collapses to one class, and the fit fails. That is the library
    # telling you something true.
    p_next = None
    if SERIES_FOR.get(args.hazard):
        series = load_sample(SERIES_FOR[args.hazard])
        X_all = build_features(series, spec)
        y = build_target(series, spec, horizon=6)
        idx = X_all.index.intersection(y.index)
        X_fit, y_fit = X_all.loc[idx], y.loc[idx]

        occ = OccurrenceModel().fit(X_fit, y_fit)

        # Fit on labelled rows, but PREDICT from the most recent features
        # available. The last `horizon` periods have no label yet -- precisely
        # the window in which an event may be developing. Predicting from the
        # last LABELLED row instead silently hands you a stale vintage. The
        # project this library came from presented a March-vintage probability
        # in August, while the index had already tripled.
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", RuntimeWarning)
            p_next = occ.predict_latest(X_all)
            p_stale = occ.predict_latest(X_fit)
        saturated = any(issubclass(w.category, RuntimeWarning) for w in caught)

        print("OCCURRENCE")
        print(f"        {occ.report()}")
        print(f"        latest features {X_all.index[-1].date()} -> P = {p_next:.3f}")
        print(f"        last labelled   {idx[-1].date()} -> P = {p_stale:.3f}   <- stale vintage")

        if saturated:
            # A probability of exactly 1 is not a forecast, and handing one to a
            # first-time reader labelled "use this" is worse than useless. Isotonic
            # calibration is a step function: anything past its outermost bin comes
            # back as exactly 0 or 1. Refit uncalibrated for a number that can
            # actually be carried into the simulation below.
            p_saturated = p_next
            raw = OccurrenceModel(calibrate=False).fit(X_fit, y_fit)
            p_next = raw.predict_latest(X_all, warn_saturated=False)
            print()
            print(f"        ^ P = {p_saturated:.3f} is SATURATION, not certainty."
                  " Isotonic")
            print("          calibration is a step function, so anything beyond its")
            print("          outermost bin returns exactly 0 or 1. Read it as 'off")
            print("          the top of the fitted range'. KNOWN_LIMITATIONS.md, 3.")
            print(f"        uncalibrated logistic -> P = {p_next:.3f}   <- use this instead")
            print("          (OccurrenceModel(calibrate=False)). Still unvalidated:")
            print("          no backtest exists. KNOWN_LIMITATIONS.md, sections 1-2.")
        print()

        rp = ReturnPeriodAnalyzer(spec).fit(annual_maxima(series))
        print(f"RETURN PERIODS   GEV shape xi = {rp.shape():.3f}")
        print(rp.table(return_periods=(10, 100, 1000), n_boot=200).to_string(index=False))
        print()
    else:
        print("OCCURRENCE / RETURN PERIODS")
        print(f"        skipped: no {spec.index_name} series is bundled for "
              f"'{args.hazard}'.")
        print("        Supply one and these layers run unchanged:")
        print("            from hazardlab import load_csv, build_features")
        print("            series = load_csv('my_index.csv')   # date,value")
        print(f"        Sources for this hazard: {', '.join(spec.sources) or 'see the spec'}\n")

    # ---- 3. Monte Carlo ------------------------------------------------
    # Probabilities are explicit and required -- there is no default to fall
    # through to. Passing the observed prior for severity is a choice: it is
    # defensible and transparent, but it carries no forward-looking information.
    assumed = None
    if p_next is None:
        # No fitted probability available, so state the assumption out loud
        # rather than letting a placeholder masquerade as an estimate.
        p_next = round(len(spec.events) / 75.0, 3)   # crude base rate
        assumed = (f"ASSUMED base rate {p_next:.3f} ({len(spec.events)} events / 75 "
                   "periods): no fitted occurrence probability exists here.")
    mc = MonteCarloEngine(
        spec,
        occurrence_probs={2026: round(p_next, 3), 2027: round(p_next, 3)},
        severity_probs=prior,
        n_sims=args.sims,
    )
    mc.run()
    s = mc.summary()
    print("MONTE CARLO")
    if assumed:
        print(f"        {assumed}")
    for period, v in s["periods"].items():
        print(f"        {period}: P(occurrence) = {v['p_occurrence']:.3f}")
    # Four decimals, and the complement alongside. At three, 0.9995 prints as
    # "1.000" and reads as certainty -- the same false impression the saturated
    # calibration gives, arriving this time purely from rounding.
    p_any = s["p_at_least_one"]
    print(f"        P(at least one) = {p_any:.4f}   (P(none) = {1 - p_any:.4f})")
    n_none = round((1 - p_any) * args.sims)
    if n_none == 0:
        # 0 of N is a resolution limit, not impossibility. Without saying so the
        # line reads as certainty again: the same false impression the saturated
        # calibration gives, arriving this time from sample size.
        print(f"          0 of {args.sims:,} simulations had no event, which is a")
        print(f"          resolution limit: {args.sims:,} draws cannot measure a")
        print(f"          probability below about {1 / args.sims:.1e}. Read it as")
        print('          "too rare for this many draws", not as impossible.')
    print(f"        peak {spec.index_name} quantiles = {mc.quantiles('peak_intensity')}")
    print("        (model-internal quantiles, NOT validated coverage)\n")

    # ---- 4. impacts ----------------------------------------------------
    if spec.impact_names:
        first = spec.impact_names[0]
        print(f"IMPACT SENSITIVITY  ({first})")
        print(sensitivity(spec, first).to_string(index=False))
        print("\n        'step_in_sd_units' is the honest answer to 'how much does")
        print("        severity misclassification matter?'. Where it exceeds ~2,")
        print("        the class label dominates every other uncertainty here.")


if __name__ == "__main__":
    main()
