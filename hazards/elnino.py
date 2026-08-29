"""El Nino / ENSO -- the worked example.

Index: Oceanic Nino Index (ONI), the 3-month running mean SST anomaly in the
Nino 3.4 region. Severity thresholds follow NOAA's operational convention.

CATALOGUE PROVENANCE
--------------------
Events are contiguous runs of months with ONI >= 0.5 in the NOAA CPC series,
and `peak_intensity` is the maximum ONI within each run. Severity is DERIVED
from the thresholds below rather than stored as a label.

That matters. An earlier version of this project carried hand-entered peaks,
and 16 of 22 disagreed with the observed series -- including 1997-98 recorded
as 2.8 (Extreme) when the ONI peak is 2.40 (Super); 2.8 appears to have been a
Nino-3.4 SST value pasted into an ONI column. Deriving the labels removes the
whole class of error, and it is why `HazardSpec.classify()` exists.

Regenerate from source with: python examples/rebuild_elnino_catalogue.py
"""
from hazardlab.spec import ClassParams, HazardSpec, HistoricalEvent

# ONI peak of each contiguous El Nino episode, NOAA CPC, 1950-2024.
EVENTS = (
    HistoricalEvent(1951, 1952, 1.15),
    HistoricalEvent(1953, 1954, 0.84),
    HistoricalEvent(1957, 1958, 1.81),
    HistoricalEvent(1958, 1959, 0.62),
    HistoricalEvent(1963, 1964, 1.37),
    HistoricalEvent(1965, 1966, 1.98),
    HistoricalEvent(1968, 1969, 1.13),
    HistoricalEvent(1969, 1970, 0.86),
    HistoricalEvent(1972, 1973, 2.12),
    HistoricalEvent(1976, 1977, 0.86),
    HistoricalEvent(1977, 1978, 0.81),
    HistoricalEvent(1982, 1983, 2.23),
    HistoricalEvent(1986, 1988, 1.70),
    HistoricalEvent(1991, 1992, 1.71),
    HistoricalEvent(1994, 1995, 1.09),
    HistoricalEvent(1997, 1998, 2.40),
    HistoricalEvent(2002, 2003, 1.31),
    HistoricalEvent(2004, 2005, 0.70),
    HistoricalEvent(2006, 2007, 0.94),
    HistoricalEvent(2009, 2010, 1.56),
    HistoricalEvent(2014, 2016, 2.75),
    HistoricalEvent(2018, 2019, 0.97),
    HistoricalEvent(2019, 2020, 0.66),
    HistoricalEvent(2023, 2024, 2.06),
)

# Peak-ONI simulation parameters. NOTE: the truncation bounds are the class
# boundaries, so this is a within-class smoother, not an independently fitted
# distribution. No goodness-of-fit test has been run -- see KNOWN_LIMITATIONS.md.
CLASS_PARAMS = {
    "Weak":     ClassParams((0.70, 0.15, 0.50, 1.00),  7,
                            {"gdp_global_pct": (-0.1, 0.05),
                             "gdp_india_pct": (-0.3, 0.10),
                             "food_price_index_pct": (2.0, 1.0)}),
    "Moderate": ClassParams((1.20, 0.15, 1.00, 1.50), 10,
                            {"gdp_global_pct": (-0.3, 0.10),
                             "gdp_india_pct": (-0.8, 0.20),
                             "food_price_index_pct": (6.0, 2.0)}),
    "Strong":   ClassParams((1.70, 0.15, 1.50, 2.00), 13,
                            {"gdp_global_pct": (-0.6, 0.15),
                             "gdp_india_pct": (-1.5, 0.30),
                             "food_price_index_pct": (12.0, 3.0)}),
    "Super":    ClassParams((2.25, 0.20, 2.00, 2.50), 16,
                            {"gdp_global_pct": (-1.1, 0.25),
                             "gdp_india_pct": (-2.5, 0.50),
                             "food_price_index_pct": (22.0, 5.0)}),
    "Extreme":  ClassParams((2.90, 0.30, 2.50, 4.00), 20,
                            {"gdp_global_pct": (-1.9, 0.40),
                             "gdp_india_pct": (-4.0, 0.80),
                             "food_price_index_pct": (38.0, 8.0)}),
}

SPEC = HazardSpec(
    key="elnino",
    name="El Nino (ENSO warm phase)",
    index_name="ONI",
    index_units="degrees C anomaly, Nino 3.4",
    description=(
        "Periodic warming of the equatorial Pacific that reorganises global "
        "weather. Modelled here as an annual occurrence with a five-class "
        "severity scale on peak ONI."
    ),
    severity_classes=("Weak", "Moderate", "Strong", "Super", "Extreme"),
    severity_thresholds={
        "Weak": 0.5, "Moderate": 1.0, "Strong": 1.5, "Super": 2.0, "Extreme": 2.5,
    },
    events=EVENTS,
    class_params=CLASS_PARAMS,
    sources={
        "oni": "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
        "mei": "https://psl.noaa.gov/enso/mei/data/meiv2.data",
        "soi": "https://www.cpc.ncep.noaa.gov/data/indices/soi",
        "nino_sst": "https://www.cpc.ncep.noaa.gov/data/indices/sstoi.indices",
    },
    impact_names=("gdp_global_pct", "gdp_india_pct", "food_price_index_pct"),
    higher_is_worse=True,
    notes=(
        "Impact parameters are order-of-magnitude figures drawn from published "
        "literature, not fitted estimates. The severity distribution drives all "
        "of them; see hazardlab.impact.translator.sensitivity()."
    ),
)
