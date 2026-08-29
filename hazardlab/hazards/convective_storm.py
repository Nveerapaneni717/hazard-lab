"""Severe convective storm -- TEMPLATE.

Index: annual count of severe convective days over the region of interest
(hail >= 2 inch, wind >= 65 kt, or a tornado report). SCS is high-frequency and
low-severity per event, so the annual aggregate is the natural unit rather than
a single peak. That makes it a useful contrast with the earthquake spec, where
one event defines the year.

STATUS: illustrative. The counts below are synthetic and shaped for
demonstration only. Replace with NOAA Storm Events extracts.
"""
from hazardlab.spec import ClassParams, HazardSpec, HistoricalEvent

EVENTS = tuple(
    HistoricalEvent(y, y, v) for y, v in [
        (2008, 118), (2009, 96), (2010, 132), (2011, 176), (2012, 104),
        (2013, 88), (2014, 92), (2015, 121), (2016, 138), (2017, 152),
        (2018, 101), (2019, 147), (2020, 129), (2021, 143), (2022, 119),
        (2023, 165), (2024, 141),
    ]
)

CLASS_PARAMS = {
    "Quiet": ClassParams((92.0, 8.0, 80.0, 110.0), 12,
                         {"insured_loss_usd_bn": (8.0, 3.0)}),
    "Normal": ClassParams((122.0, 9.0, 110.0, 140.0), 12,
                          {"insured_loss_usd_bn": (18.0, 6.0)}),
    "Active": ClassParams((150.0, 8.0, 140.0, 165.0), 12,
                          {"insured_loss_usd_bn": (32.0, 10.0)}),
    "VeryActive": ClassParams((190.0, 18.0, 165.0, 240.0), 12,
                              {"insured_loss_usd_bn": (55.0, 18.0)}),
}

SPEC = HazardSpec(
    key="convective_storm",
    name="Severe convective storm (annual severe-day count)",
    index_name="SevereDays",
    index_units="days per year meeting a severe threshold",
    description="Aggregate seasonal convective activity rather than a single peak event.",
    severity_classes=("Quiet", "Normal", "Active", "VeryActive"),
    severity_thresholds={"Quiet": 80.0, "Normal": 110.0,
                         "Active": 140.0, "VeryActive": 165.0},
    events=EVENTS,
    class_params=CLASS_PARAMS,
    sources={"noaa_storm_events": "https://www.ncdc.noaa.gov/stormevents/",
             "spc_climatology": "https://www.spc.noaa.gov/climo/"},
    impact_names=("insured_loss_usd_bn",),
    higher_is_worse=True,
    notes="TEMPLATE -- synthetic counts. Replace with NOAA Storm Events extracts.",
)
