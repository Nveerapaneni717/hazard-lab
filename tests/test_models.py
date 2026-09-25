"""Model-layer behaviour, including guards against the defects this repo fixed."""
import numpy as np
import pandas as pd
import pytest

from hazardlab.features.builder import annual_maxima, build_features, build_target
from hazardlab.io.series import load_sample
from hazardlab.models.monte_carlo import MonteCarloEngine
from hazardlab.models.occurrence import OccurrenceModel
from hazardlab.models.return_period import ReturnPeriodAnalyzer
from hazardlab.models.severity import blend
from hazardlab.registry import get_hazard


@pytest.fixture(scope="module")
def spec():
    return get_hazard("elnino")


@pytest.fixture(scope="module")
def oni():
    return load_sample("oni")


# --- regression: simulation must not run on defaults ------------------------
def test_monte_carlo_requires_explicit_probabilities(spec):
    """The original engine defaulted to p=0.65/0.55 and a catalogue built from
    those defaults was mistaken for fitted output. There is now no default."""
    # The missing arguments below are the whole point, so CodeQL reports "wrong
    # number of arguments in a class instantiation" here and the alert is
    # dismissed as "used in tests". Do not silence it by giving MonteCarloEngine
    # default probabilities -- that is precisely the defect this guards against.
    with pytest.raises(TypeError):
        MonteCarloEngine(spec)                       # no probabilities at all
    with pytest.raises(ValueError):
        MonteCarloEngine(spec, occurrence_probs={}, severity_probs={"Weak": 1.0})
    with pytest.raises(ValueError):
        MonteCarloEngine(spec, occurrence_probs={2026: 0.5}, severity_probs={})


def test_monte_carlo_rejects_out_of_range_and_incomplete_inputs(spec):
    with pytest.raises(ValueError):
        MonteCarloEngine(spec, occurrence_probs={2026: 1.4},
                         severity_probs=spec.empirical_probs())
    with pytest.raises(ValueError):
        MonteCarloEngine(spec, occurrence_probs={2026: 0.5},
                         severity_probs={"Weak": 1.0})   # missing classes


def test_monte_carlo_reproduces_its_inputs(spec):
    p = spec.empirical_probs()
    mc = MonteCarloEngine(spec, occurrence_probs={2026: 0.65, 2027: 0.40},
                          severity_probs=p, n_sims=6000, seed=7)
    mc.run()
    s = mc.summary()
    assert s["periods"][2026]["p_occurrence"] == pytest.approx(0.65, abs=0.02)
    assert s["periods"][2027]["p_occurrence"] == pytest.approx(0.40, abs=0.02)
    # default is independence, so P(both) ~= product
    assert s["p_all_periods"] == pytest.approx(0.65 * 0.40, abs=0.03)


def test_period_dependence_changes_joint_probability(spec):
    kw = dict(occurrence_probs={2026: 0.5, 2027: 0.5},
              severity_probs=spec.empirical_probs(), n_sims=6000, seed=3)
    indep = MonteCarloEngine(spec, **kw)
    indep.run()
    dep = MonteCarloEngine(spec, period_dependence=0.8, **kw)
    dep.run()
    assert dep.summary()["p_all_periods"] > indep.summary()["p_all_periods"]


def test_simulated_peaks_respect_class_bounds(spec):
    mc = MonteCarloEngine(spec, occurrence_probs={2026: 1.0},
                          severity_probs=spec.empirical_probs(), n_sims=3000, seed=11)
    cat = mc.run()
    for cls, cp in spec.class_params.items():
        vals = cat.loc[cat.severity == cls, "peak_intensity"].dropna()
        if len(vals):
            assert vals.min() >= cp.peak[2] - 1e-6
            assert vals.max() <= cp.peak[3] + 1e-6


# --- regression: GEV must use all block maxima ------------------------------
def test_gev_shape_is_bounded_for_oni(spec, oni):
    """Filtering block maxima to 'event years' flipped xi from -0.24 to +0.29 and
    put the 1000-year ONI at 9.7 C. Fit on all blocks; the tail is bounded."""
    rp = ReturnPeriodAnalyzer(spec).fit(annual_maxima(oni))
    assert rp.shape() < 0                      # Weibull-type, bounded upper tail
    assert 1.5 < rp.return_level(10) < 2.5
    assert 2.5 < rp.return_level(100) < 3.5
    assert 3.0 < rp.return_level(1000) < 4.5   # emphatically not 9.7


def test_gev_refuses_too_few_blocks(spec):
    with pytest.raises(ValueError):
        ReturnPeriodAnalyzer(spec).fit(pd.Series(np.arange(10, dtype=float)))


def test_return_period_table_is_monotonic(spec, oni):
    rp = ReturnPeriodAnalyzer(spec).fit(annual_maxima(oni))
    t = rp.table(return_periods=(10, 50, 100, 500), n_boot=60)
    levels = t[f"{spec.index_name}_level"].tolist()
    assert levels == sorted(levels)


# --- features must be causal ------------------------------------------------
def test_features_do_not_use_the_future(spec, oni):
    """Truncating the series must not change features on the surviving dates."""
    full = build_features(oni, spec)
    trunc = build_features(oni.iloc[:-24], spec)
    common = full.index.intersection(trunc.index)
    assert len(common) > 100
    pd.testing.assert_frame_equal(full.loc[common], trunc.loc[common])


def test_target_drops_the_unlabelled_tail(spec, oni):
    y = build_target(oni, spec, horizon=6)
    assert y.index.max() < oni.index.max()     # no fabricated 'no event' labels
    assert set(y.unique()) <= {0, 1}


# --- severity blending ------------------------------------------------------
def test_blend_is_a_distribution_and_respects_weight():
    model = {"A": 1.0, "B": 0.0}
    prior = {"A": 0.0, "B": 1.0}
    assert blend(model, prior, 1.0)["A"] == pytest.approx(1.0)
    assert blend(model, prior, 0.0)["A"] == pytest.approx(0.0)
    mid = blend(model, prior, 0.5)
    assert mid["A"] == pytest.approx(0.5)
    assert sum(mid.values()) == pytest.approx(1.0)


def test_blend_rejects_bad_weight():
    with pytest.raises(ValueError):
        blend({"A": 1.0}, {"A": 1.0}, 1.5)


# --- guard: a spec applied to the wrong series ------------------------------
def test_single_class_target_raises_a_useful_error(spec, oni):
    """Pointing an inverted-scale spec at a rising index makes every period an
    'event'. sklearn's own error is opaque; ours names the likely cause."""
    monsoon = get_hazard("indian_monsoon")     # higher_is_worse=False, threshold 96
    y = build_target(oni, monsoon, horizon=6)  # every ONI value is <= 96
    assert y.nunique() == 1
    X = build_features(oni, monsoon)
    idx = X.index.intersection(y.index)        # features lose the first 12 rows
    X, y = X.loc[idx], y.loc[idx]
    with pytest.raises(ValueError, match="only one class"):
        OccurrenceModel().fit(X, y)
