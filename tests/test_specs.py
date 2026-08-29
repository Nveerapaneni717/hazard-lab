"""Every shipped hazard must be coherent, and the fixed defects must stay fixed."""
import pytest

from hazardlab.registry import available, get_hazard
from hazardlab.spec import ClassParams, HazardSpec, HistoricalEvent


@pytest.mark.parametrize("key", available())
def test_spec_is_valid(key):
    spec = get_hazard(key)          # get_hazard() raises if validate() finds problems
    assert spec.validate() == []
    assert spec.severity_classes
    assert len(spec.events) >= 10


@pytest.mark.parametrize("key", available())
def test_empirical_prior_is_a_distribution(key):
    probs = get_hazard(key).empirical_probs()
    assert abs(sum(probs.values()) - 1.0) < 1e-9
    assert all(0.0 <= v <= 1.0 for v in probs.values())


@pytest.mark.parametrize("key", available())
def test_every_event_classifies_into_a_known_class(key):
    spec = get_hazard(key)
    for ev in spec.events:
        assert spec.classify(ev.peak_intensity) in spec.severity_classes


def test_unknown_hazard_raises():
    with pytest.raises(KeyError):
        get_hazard("not_a_hazard")


# --- regression: the catalogue-drift defect ---------------------------------
def test_1997_el_nino_is_super_not_extreme():
    """Observed ONI peak for 1997-98 is 2.40, which is Super.

    The original project stored 2.8 / Extreme -- a Nino-3.4 SST value in an ONI
    column. Severity is now derived, so the label cannot drift from the data.
    """
    spec = get_hazard("elnino")
    ev = next(e for e in spec.events if e.start_year == 1997)
    assert ev.peak_intensity == pytest.approx(2.40)
    assert spec.classify(ev.peak_intensity) == "Super"


def test_only_one_extreme_el_nino_on_record():
    spec = get_hazard("elnino")
    counts = spec.empirical_counts()
    assert counts["Extreme"] == 1          # 2015-16, peak 2.75


def test_no_event_carries_a_hardcoded_severity_label():
    """Deriving beats storing: nothing in the shipped catalogue is hand-labelled."""
    for key in available():
        for ev in get_hazard(key).events:
            assert ev.severity is None


# --- inverted scale ---------------------------------------------------------
def test_inverted_scale_classifies_downwards():
    """For the monsoon spec a LOWER index is worse."""
    spec = get_hazard("indian_monsoon")
    assert spec.higher_is_worse is False
    assert spec.classify(72.0) == "Drought"
    assert spec.classify(94.0) == "BelowNormal"
    # a severe deficit must not be classified as mild
    assert spec.classify(79.0) == "SevereDeficit"


# --- validation actually rejects bad specs ----------------------------------
def test_validate_catches_inverted_peak_bounds():
    bad = HazardSpec(
        key="bad", name="bad", index_name="X", index_units="u", description="d",
        severity_classes=("A",), severity_thresholds={"A": 1.0},
        events=(HistoricalEvent(2000, 2000, 1.5),),
        class_params={"A": ClassParams((1.5, 0.1, 2.0, 1.0), 3)},   # lo > hi
    )
    assert any("bounds inverted" in e for e in bad.validate())


def test_validate_catches_missing_class_params():
    bad = HazardSpec(
        key="bad", name="bad", index_name="X", index_units="u", description="d",
        severity_classes=("A", "B"), severity_thresholds={"A": 1.0, "B": 2.0},
        events=(HistoricalEvent(2000, 2000, 1.5),),
        class_params={"A": ClassParams((1.5, 0.1, 1.0, 2.0), 3)},   # B missing
    )
    assert any("without simulation params" in e for e in bad.validate())


# --- runtime registration ---------------------------------------------------
def _toy_spec(key="toy_peril"):
    return HazardSpec(
        key=key, name="Toy", index_name="X", index_units="u", description="d",
        severity_classes=("Low", "High"),
        severity_thresholds={"Low": 1.0, "High": 2.0},
        events=tuple(HistoricalEvent(1990 + i, 1990 + i, 1.0 + 0.1 * i) for i in range(12)),
        class_params={"Low": ClassParams((1.4, 0.2, 1.0, 2.0), 3),
                      "High": ClassParams((2.5, 0.3, 2.0, 3.0), 3)},
    )


def test_register_and_retrieve_a_runtime_spec():
    from hazardlab.registry import get_hazard, register, unregister
    try:
        register(_toy_spec())
        assert "toy_peril" in available()
        assert get_hazard("toy_peril").name == "Toy"
    finally:
        unregister("toy_peril")
    assert "toy_peril" not in available()


def test_register_refuses_to_shadow_silently():
    from hazardlab.registry import register, unregister
    try:
        register(_toy_spec())
        with pytest.raises(KeyError):
            register(_toy_spec())                       # already registered
        with pytest.raises(KeyError):
            register(_toy_spec(key="elnino"))           # would shadow a built-in
        register(_toy_spec(), overwrite=True)           # explicit is fine
    finally:
        unregister("toy_peril")


def test_register_rejects_a_bad_spec():
    from hazardlab.registry import register
    bad = HazardSpec(
        key="bad_toy", name="bad", index_name="X", index_units="u", description="d",
        severity_classes=("A",), severity_thresholds={"A": 1.0},
        events=(HistoricalEvent(2000, 2000, 1.5),),
        class_params={"A": ClassParams((1.5, 0.1, 2.0, 1.0), 3)},   # lo > hi
    )
    with pytest.raises(ValueError):
        register(bad)


def test_register_rejects_a_non_spec():
    from hazardlab.registry import register
    with pytest.raises(TypeError):
        register({"key": "nope"})
