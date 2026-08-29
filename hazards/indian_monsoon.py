"""Indian summer monsoon deficit -- TEMPLATE, and the INVERTED-SCALE example.

Index: All-India Summer Monsoon Rainfall (AISMR) as a percentage of the Long
Period Average. Here a LOWER index is worse, so this spec sets
`higher_is_worse=False`.

It is the deliberate counter-example to every other hazard in this repo, and
the reason `HazardSpec.classify()` takes direction into account rather than
assuming bigger means worse. If you are writing a spec for flood depth, loss
ratio, or anything where small is bad, start from this file.

STATUS: the catalogue is real IITM/IMD AISMR for deficit years. The impact
figures are placeholders -- calibrate before use.
"""
from hazardlab.spec import ClassParams, HazardSpec, HistoricalEvent

# Deficit years: AISMR as % of LPA (lower = worse).
EVENTS = tuple(
    HistoricalEvent(y, y, v) for y, v in [
        (1951, 82), (1965, 82), (1966, 87), (1968, 90), (1972, 75),
        (1974, 88), (1979, 81), (1982, 85), (1986, 91), (1987, 81),
        (2002, 83), (2004, 87), (2009, 79), (2014, 90), (2015, 88),
    ]
)

CLASS_PARAMS = {
    "BelowNormal": ClassParams((93.0, 1.5, 90.0, 96.0), 4,
                               {"kharif_loss_pct": (-5.0, 2.0),
                                "gdp_india_pct": (-0.3, 0.1)}),
    "Deficient": ClassParams((86.0, 2.0, 82.0, 90.0), 4,
                             {"kharif_loss_pct": (-12.0, 3.0),
                              "gdp_india_pct": (-0.9, 0.2)}),
    "SevereDeficit": ClassParams((79.0, 2.0, 75.0, 82.0), 4,
                                 {"kharif_loss_pct": (-22.0, 4.0),
                                  "gdp_india_pct": (-1.8, 0.4)}),
    "Drought": ClassParams((68.0, 3.5, 55.0, 75.0), 4,
                           {"kharif_loss_pct": (-34.0, 6.0),
                            "gdp_india_pct": (-3.2, 0.7)}),
}

SPEC = HazardSpec(
    key="indian_monsoon",
    name="Indian summer monsoon deficit",
    index_name="AISMR",
    index_units="% of long period average (JJAS)",
    description="Monsoon shortfall measured against the long period average.",
    severity_classes=("BelowNormal", "Deficient", "SevereDeficit", "Drought"),
    # Upper bound of each class, because lower is worse.
    severity_thresholds={"BelowNormal": 96.0, "Deficient": 90.0,
                         "SevereDeficit": 82.0, "Drought": 75.0},
    events=EVENTS,
    class_params=CLASS_PARAMS,
    sources={"iitm_aismr": "https://tropmet.res.in/",
             "imd_forecasts": "https://mausam.imd.gov.in/"},
    impact_names=("kharif_loss_pct", "gdp_india_pct"),
    higher_is_worse=False,
    notes="TEMPLATE -- inverted scale. Impacts are placeholders; calibrate before use.",
)
