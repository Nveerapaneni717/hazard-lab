# Adding a new hazard

You will write one file. You will not touch the engine.

Worked example: **European windstorm**, indexed on peak gust (m/s).

## 1. Decide four things

| Question | Windstorm answer |
|---|---|
| What single number measures intensity? | peak gust, m/s |
| Does a bigger number mean worse? | yes → `higher_is_worse=True` |
| What are the class boundaries? | 30 / 38 / 46 / 55 m/s |
| What does the event cost? | insured loss, € bn |

If you cannot answer the first one, you do not have a hazard spec yet — you have
several. Split them.

## 2. Write `hazardlab/hazards/euro_windstorm.py`

```python
from hazardlab.spec import ClassParams, HazardSpec, HistoricalEvent

EVENTS = tuple(
    HistoricalEvent(y, y, gust) for y, gust in [
        (1990, 52.0), (1999, 58.0), (2007, 44.0), (2013, 41.0),
        (2018, 46.0), (2020, 43.0), (2022, 51.0), (2023, 39.0),
        # ... your catalogue. More blocks is better; 20+ before you quote
        # return periods at all.
    ]
)

CLASS_PARAMS = {
    "Moderate": ClassParams(
        peak=(33.0, 2.0, 30.0, 38.0),        # (mean, sd, lower, upper)
        duration_months=1,
        impacts={"insured_loss_eur_bn": (0.4, 0.2)},
    ),
    "Severe":  ClassParams((41.0, 2.0, 38.0, 46.0), 1, {"insured_loss_eur_bn": (1.8, 0.8)}),
    "Extreme": ClassParams((50.0, 2.5, 46.0, 55.0), 1, {"insured_loss_eur_bn": (6.0, 2.5)}),
    "Historic":ClassParams((60.0, 4.0, 55.0, 80.0), 1, {"insured_loss_eur_bn": (18.0, 7.0)}),
}

SPEC = HazardSpec(
    key="euro_windstorm",
    name="European windstorm",
    index_name="PeakGust",
    index_units="m/s",
    description="Extratropical cyclone windstorm over northwest Europe.",
    severity_classes=("Moderate", "Severe", "Extreme", "Historic"),
    severity_thresholds={"Moderate": 30.0, "Severe": 38.0,
                         "Extreme": 46.0, "Historic": 55.0},
    events=EVENTS,
    class_params=CLASS_PARAMS,
    sources={"era5": "https://cds.climate.copernicus.eu/"},
    impact_names=("insured_loss_eur_bn",),
    higher_is_worse=True,
    notes="Catalogue is illustrative; recalibrate impacts before use.",
)
```

## 3. Check it

```bash
python -c "from hazardlab.registry import get_hazard; s=get_hazard('euro_windstorm'); \
print(s.empirical_counts()); print(s.empirical_probs())"
```

`get_hazard` runs `spec.validate()` and refuses to return an incoherent spec.
It catches inverted peak bounds, classes with no parameters, means outside their
own bounds, and unknown severity labels.

## 4. Run it

```bash
python examples/01_quickstart.py --hazard euro_windstorm
```

---

## Things that will bite you

**Severity is derived, not stored.** Leave `HistoricalEvent.severity` as `None`
and let `classify()` do it. Hand-labelling is how the original El Niño catalogue
came to disagree with its own data on 16 of 22 events.

**Lower-is-worse indices need `higher_is_worse=False`,** and then your
thresholds are *upper* bounds. See `hazardlab/hazards/indian_monsoon.py`. Flood depth, loss
ratios and rainfall percentiles all fall in this category.

**The truncated normal on peak intensity is a within-class smoother.** Its bounds
are the class boundaries, so it cannot add information the class label does not
already carry. If your peril has a genuine parametric tail — Gutenberg-Richter
for earthquakes, a Pareto for large losses — replace the peak draw rather than
tuning the normal.

**Your catalogue determines your prior.** `hazardlab/hazards/earthquake.py` ships a global
M8+ sample, so its empirical prior assigns *zero* probability to Moderate and
Strong events. That is arithmetically correct and physically nonsense. Use a
regional catalogue with a stated completeness threshold.

**More classes is not better.** Each one needs enough historical events to
estimate a frequency. Five classes over twenty events means four events per
class; the tail class will rest on one.

## When you have it working

Read [`KNOWN_LIMITATIONS.md`](../KNOWN_LIMITATIONS.md) and check which of those
limitations your hazard inherits. Most of them are structural and will apply to
you too.
