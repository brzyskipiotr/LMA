import httpx
import json
import time
import hashlib
from pathlib import Path
from urllib.parse import quote

from app.config import UPLOAD_DIR
from app.schemas import GeocodingResult

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "GreenLoanValidator/1.0 (LMA Hackathon)"
CACHE_DIR = UPLOAD_DIR / "_geocache"

# Rate limiting
_last_request_time = 0.0


def _get_cache_key(address: str) -> str:
    """Generate cache key from normalized address."""
    normalized = address.lower().strip()
    return hashlib.md5(normalized.encode()).hexdigest()


def _load_cache() -> dict:
    """Load geocoding cache from disk."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / "nominatim_cache.json"
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_cache(cache: dict):
    """Save geocoding cache to disk."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / "nominatim_cache.json"
    cache_file.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def _throttle():
    """Enforce 1 request per second rate limit."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)
    _last_request_time = time.time()


def geocode(address: str) -> GeocodingResult | None:
    """
    Geocode an address using Nominatim (international).
    Returns lat/lon coordinates or None if not found.
    Uses file-based cache and respects 1 req/sec rate limit.
    """
    if not address or len(address.strip()) < 5:
        return None

    # Check cache first
    cache = _load_cache()
    cache_key = _get_cache_key(address)

    if cache_key in cache:
        cached = cache[cache_key]
        if cached is None:
            return None
        return GeocodingResult(**cached)

    # Rate limit
    _throttle()

    # Make request
    try:
        params = {
            "q": address,
            "format": "json",
            "limit": 1,
            "addressdetails": 1
        }
        headers = {"User-Agent": USER_AGENT}

        response = httpx.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        if not data:
            # Cache negative result
            cache[cache_key] = None
            _save_cache(cache)
            return None

        result = data[0]
        address_details = result.get("address", {})

        # Extract country code
        country_code = address_details.get("country_code", "").upper()

        # Determine confidence based on result type
        confidence = 0.9 if result.get("type") in ["building", "house", "residential"] else 0.7

        geocoding_result = GeocodingResult(
            lat=float(result["lat"]),
            lon=float(result["lon"]),
            display_name=result.get("display_name", address),
            country_code=country_code,
            confidence=confidence
        )

        # Cache result
        cache[cache_key] = geocoding_result.model_dump()
        _save_cache(cache)

        return geocoding_result

    except Exception as e:
        print(f"Geocoding error for '{address}': {e}")
        return None


def extract_coordinates_from_address(address: str) -> tuple[float, float, float] | None:
    """
    Extract lat, lon, confidence from address.
    Returns (lat, lon, confidence) or None.
    """
    result = geocode(address)
    if result:
        return (result.lat, result.lon, result.confidence)
    return None
