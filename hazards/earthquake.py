"""Regional earthquake -- TEMPLATE.

Index: moment magnitude (Mw) of the largest event in a period. Mw is
logarithmic, so a linear truncated normal on Mw is a cruder approximation than
it is for a linear index like ONI. For serious work, replace the peak model
with a Gutenberg-Richter tail -- that substitution is a good exercise in why
the peak distribution is a per-hazard choice rather than a library default.

STATUS: illustrative. The catalogue is a small global sample, not a regional one.
"""
from hazardlab.spec import ClassParams, HazardSpec, HistoricalEvent

EVENTS = tuple(
    HistoricalEvent(y, y, v) for y, v in [
        (1960, 9.5), (1964, 9.2), (2004, 9.1), (2011, 9.1),
        (2010, 8.8), (1965, 8.7), (2005, 8.6), (2012, 8.6),
        (2007, 8.4), (2001, 8.4), (2015, 8.3), (2017, 8.2),
    ]
)

CLASS_PARAMS = {
    "Moderate": ClassParams((6.5, 0.25, 6.0, 7.0), 1,
                            {"insured_loss_usd_bn": (2.0, 1.0)}),
    "Strong": ClassParams((7.4, 0.25, 7.0, 8.0), 1,
                          {"insured_loss_usd_bn": (12.0, 6.0)}),
    "Major": ClassParams((8.3, 0.20, 8.0, 8.8), 1,
                         {"insured_loss_usd_bn": (45.0, 20.0)}),
    "Great": ClassParams((9.0, 0.30, 8.8, 9.8), 1,
                         {"insured_loss_usd_bn": (140.0, 60.0)}),
}

SPEC = HazardSpec(
    key="earthquake",
    name="Earthquake (moment magnitude)",
    index_name="Mw",
    index_units="moment magnitude",
    description="Largest-magnitude event per period, classified on the Mw scale.",
    severity_classes=("Moderate", "Strong", "Major", "Great"),
    severity_thresholds={"Moderate": 6.0, "Strong": 7.0, "Major": 8.0, "Great": 8.8},
    events=EVENTS,
    class_params=CLASS_PARAMS,
    sources={"usgs_catalog": "https://earthquake.usgs.gov/earthquakes/search/",
             "isc_bulletin": "http://www.isc.ac.uk/iscbulletin/"},
    impact_names=("insured_loss_usd_bn",),
    higher_is_worse=True,
    notes="TEMPLATE -- swap in a regional catalogue and a Gutenberg-Richter tail.",
)
