import httpx
from app.schemas import PVGISResult
from app.pipeline.solar_constants import estimate_angle_from_latitude

PVGIS_API_URL = "https://re.jrc.ec.europa.eu/api/v5_2/PVcalc"


def get_pvgis_estimate(
    lat: float,
    lon: float,
    peak_power_kwp: float,
    loss: float = 14.0,
    angle: float | None = None,
    aspect: float | None = None
) -> PVGISResult | None:
    """
    Get PV yield estimate from EU JRC PVGIS API.

    Args:
        lat: Latitude
        lon: Longitude
        peak_power_kwp: System size in kWp
        loss: System losses in % (default 14%)
        angle: Panel tilt angle in degrees (None = let PVGIS optimize)
        aspect: Azimuth, 0=South, -90=East, 90=West (None = let PVGIS optimize)

    Returns:
        PVGISResult with annual_kwh, kwh_per_kwp, monthly_kwh
        or None if API call fails
    """
    try:
        params = {
            "lat": lat,
            "lon": lon,
            "peakpower": peak_power_kwp,
            "loss": loss,
            "outputformat": "json",
            "pvtechchoice": "crystSi"  # Crystalline silicon
        }

        # Use optimal angles if not specified
        if angle is None or aspect is None:
            params["optimalangles"] = 1
        else:
            params["angle"] = angle
            params["aspect"] = aspect

        response = httpx.get(PVGIS_API_URL, params=params, timeout=15)
        response.raise_for_status()

        data = response.json()

        # Extract annual production
        totals = data.get("outputs", {}).get("totals", {}).get("fixed", {})
        annual_kwh = totals.get("E_y", 0)  # kWh/year

        # Extract monthly data
        monthly_data = data.get("outputs", {}).get("monthly", {}).get("fixed", [])
        monthly_kwh = [m.get("E_m", 0) for m in monthly_data] if monthly_data else []

        # Calculate kWh per kWp
        kwh_per_kwp = annual_kwh / peak_power_kwp if peak_power_kwp > 0 else 0

        return PVGISResult(
            annual_kwh=round(annual_kwh, 1),
            kwh_per_kwp=round(kwh_per_kwp, 1),
            monthly_kwh=[round(m, 1) for m in monthly_kwh]
        )

    except httpx.HTTPStatusError as e:
        print(f"PVGIS HTTP error: {e.response.status_code}")
        return None
    except Exception as e:
        print(f"PVGIS error: {e}")
        return None


def estimate_yield_for_location(lat: float, lon: float) -> float | None:
    """
    Get expected kWh/kWp/year for a location using 1 kWp reference system.
    Returns the specific yield or None if API fails.
    """
    result = get_pvgis_estimate(lat, lon, peak_power_kwp=1.0)
    if result:
        return result.kwh_per_kwp
    return None
