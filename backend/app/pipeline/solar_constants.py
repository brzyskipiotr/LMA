"""
Solar constants and optimal angles by country/region.
Used as fallback when PVGIS API is unavailable.

Optimal tilt angle rule of thumb: angle ≈ latitude
These values are for fixed south-facing installations optimized for annual yield.
"""

# Optimal tilt angles by country (degrees from horizontal)
# Source: PVGIS data, industry standards
OPTIMAL_ANGLES = {
    # Central Europe
    "PL": 35,  # Poland
    "DE": 33,  # Germany
    "CZ": 34,  # Czech Republic
    "SK": 34,  # Slovakia
    "AT": 34,  # Austria
    "CH": 35,  # Switzerland
    "HU": 34,  # Hungary

    # Western Europe
    "FR": 33,  # France
    "BE": 35,  # Belgium
    "NL": 36,  # Netherlands
    "LU": 35,  # Luxembourg
    "GB": 37,  # United Kingdom
    "IE": 38,  # Ireland

    # Southern Europe
    "ES": 30,  # Spain
    "PT": 30,  # Portugal
    "IT": 30,  # Italy
    "GR": 28,  # Greece
    "HR": 32,  # Croatia
    "SI": 33,  # Slovenia

    # Northern Europe
    "SE": 40,  # Sweden
    "NO": 42,  # Norway
    "FI": 42,  # Finland
    "DK": 38,  # Denmark
    "EE": 39,  # Estonia
    "LV": 39,  # Latvia
    "LT": 38,  # Lithuania

    # Eastern Europe
    "RO": 33,  # Romania
    "BG": 32,  # Bulgaria
    "UA": 35,  # Ukraine

    # Default for unknown
    "DEFAULT": 35,
}

# Typical specific yield (kWh/kWp/year) by country
# For validation when PVGIS is unavailable
TYPICAL_YIELD = {
    # Central Europe
    "PL": (950, 1100),   # Poland: 950-1100 kWh/kWp
    "DE": (900, 1050),   # Germany
    "CZ": (950, 1080),   # Czech Republic
    "AT": (1000, 1150),  # Austria

    # Western Europe
    "FR": (1000, 1400),  # France (varies north-south)
    "BE": (900, 1000),   # Belgium
    "NL": (900, 1000),   # Netherlands
    "GB": (850, 1000),   # United Kingdom

    # Southern Europe
    "ES": (1400, 1800),  # Spain
    "PT": (1400, 1700),  # Portugal
    "IT": (1200, 1600),  # Italy
    "GR": (1400, 1700),  # Greece

    # Northern Europe
    "SE": (850, 1000),   # Sweden
    "NO": (800, 950),    # Norway
    "FI": (800, 950),    # Finland
    "DK": (900, 1050),   # Denmark

    # Default range for Europe
    "DEFAULT": (900, 1400),
}


def get_optimal_angle(country_code: str) -> int:
    """Get optimal tilt angle for a country."""
    return OPTIMAL_ANGLES.get(country_code.upper(), OPTIMAL_ANGLES["DEFAULT"])


def get_typical_yield_range(country_code: str) -> tuple[int, int]:
    """Get typical yield range (min, max) for a country."""
    return TYPICAL_YIELD.get(country_code.upper(), TYPICAL_YIELD["DEFAULT"])


def estimate_angle_from_latitude(lat: float) -> float:
    """
    Estimate optimal tilt angle from latitude.
    Rule of thumb: optimal angle ≈ latitude for annual optimization.
    Adjusted slightly for winter/summer balance.
    """
    # For latitudes 35-60° (most of Europe), angle ≈ lat - 2 to lat + 2
    if lat < 25:
        return lat + 5  # Tropics: steeper to shed rain
    elif lat > 55:
        return lat - 5  # High latitudes: slightly less steep
    else:
        return lat  # Mid-latitudes: angle ≈ latitude
