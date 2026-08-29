"""Atlantic hurricane season -- TEMPLATE.

Index: seasonal Accumulated Cyclone Energy (ACE, 10^4 kt^2). "Occurrence" here
means an above-normal season, so the occurrence threshold is the ACE level you
treat as above-normal, not "a hurricane happened".

STATUS: illustrative starting point. The catalogue below is a short rounded
sample and the loss figures are placeholders. Replace both with NOAA HURDAT2
seasonal ACE and your own calibration before using any output.
"""
from hazardlab.spec import ClassParams, HazardSpec, HistoricalEvent

EVENTS = tuple(
    HistoricalEvent(y, y, v) for y, v in [
        (1995, 227.0), (1998, 182.0), (1999, 177.0), (2003, 176.0),
        (2004, 227.0), (2005, 245.0), (2008, 146.0), (2010, 165.0),
        (2017, 225.0), (2020, 180.0), (2023, 146.0), (2024, 162.0),
    ]
)

CLASS_PARAMS = {
    "AboveNormal": ClassParams((135.0, 12.0, 120.0, 160.0), 5,
                               {"insured_loss_usd_bn": (12.0, 5.0)}),
    "Active": ClassParams((175.0, 12.0, 160.0, 200.0), 5,
                          {"insured_loss_usd_bn": (30.0, 10.0)}),
    "Hyperactive": ClassParams((215.0, 15.0, 200.0, 240.0), 6,
                               {"insured_loss_usd_bn": (65.0, 22.0)}),
    "Extreme": ClassParams((260.0, 25.0, 240.0, 350.0), 6,
                           {"insured_loss_usd_bn": (120.0, 40.0)}),
}

SPEC = HazardSpec(
    key="atlantic_hurricane",
    name="Atlantic hurricane season (ACE)",
    index_name="ACE",
    index_units="10^4 kt^2, seasonal accumulated cyclone energy",
    description="Seasonal Atlantic basin activity measured by accumulated cyclone energy.",
    severity_classes=("AboveNormal", "Active", "Hyperactive", "Extreme"),
    severity_thresholds={"AboveNormal": 120.0, "Active": 160.0,
                         "Hyperactive": 200.0, "Extreme": 240.0},
    events=EVENTS,
    class_params=CLASS_PARAMS,
    sources={"hurdat2": "https://www.nhc.noaa.gov/data/",
             "seasonal_ace": "https://psl.noaa.gov/gcos_wgsp/Timeseries/"},
    impact_names=("insured_loss_usd_bn",),
    higher_is_worse=True,
    notes="TEMPLATE -- rounded sample catalogue, placeholder impacts.",
)
