from app.schemas import ExtractedFact, VerificationResult, RedFlag, ScoreCard, Evidence
from app.pipeline.geocoding import geocode
from app.pipeline.pvgis import get_pvgis_estimate

REQUIRED_FIELDS = ["project_location_text", "declared_power_kwp", "system_type"]
IMPORTANT_FIELDS = ["declared_yield_kwh_per_kwp", "capex_total", "roof_area_m2"]


def get_fact(facts: list[ExtractedFact], field: str) -> ExtractedFact | None:
    """Get fact by field name."""
    for f in facts:
        if f.field == field and f.value is not None:
            return f
    return None


def get_fact_value(facts: list[ExtractedFact], field: str):
    """Get fact value and evidence."""
    fact = get_fact(facts, field)
    if fact:
        return fact.value, fact.evidence
    return None, []


def verify_pvgis_yield(facts: list[ExtractedFact]) -> VerificationResult | None:
    """
    PVGIS Yield Sanity Check (PRD Delta compliant).

    1. Get declared_power_kwp (required)
    2. Get declared_yield_kwh_per_kwp OR compute implied from annual_energy
    3. Geocode location to get lat/lon
    4. Call PVGIS API for expected yield
    5. Compare and generate verification result
    """
    # Get power (required)
    power_fact = get_fact(facts, "declared_power_kwp")
    if not power_fact or not power_fact.value:
        return None

    power_kwp = float(power_fact.value)
    power_evidence = power_fact.evidence

    # Get declared yield OR compute implied
    yield_fact = get_fact(facts, "declared_yield_kwh_per_kwp")
    annual_fact = get_fact(facts, "declared_annual_energy_mwh")

    declared_kwh_per_kwp = None
    yield_evidence = []
    declared_source = None

    if yield_fact and yield_fact.value:
        declared_kwh_per_kwp = float(yield_fact.value)
        yield_evidence = yield_fact.evidence
        declared_source = "DECLARED_YIELD"
    elif annual_fact and annual_fact.value:
        # Implied: annual_mwh * 1000 / kWp
        annual_mwh = float(annual_fact.value)
        declared_kwh_per_kwp = (annual_mwh * 1000) / power_kwp
        yield_evidence = annual_fact.evidence
        declared_source = "IMPLIED_FROM_ANNUAL"

    if declared_kwh_per_kwp is None:
        return None

    # Get location and geocode
    location_fact = get_fact(facts, "project_location_text")
    if not location_fact or not location_fact.value:
        return None

    geo_result = geocode(str(location_fact.value))
    if not geo_result:
        return None

    lat, lon = geo_result.lat, geo_result.lon

    # Call PVGIS
    pvgis_result = get_pvgis_estimate(lat, lon, power_kwp)
    if not pvgis_result:
        return None

    pvgis_kwh_per_kwp = pvgis_result.kwh_per_kwp

    # Calculate delta
    delta_pct = ((declared_kwh_per_kwp - pvgis_kwh_per_kwp) / pvgis_kwh_per_kwp) * 100

    # Determine result and severity
    abs_delta = abs(delta_pct)
    if abs_delta < 10:
        result = "OK"
        severity = "OK"
    elif abs_delta < 15:
        result = "MARGINAL"
        severity = "MEDIUM"
    else:
        result = "OUTLIER"
        severity = "HIGH"

    # Collect all evidence
    all_evidence = list(power_evidence) + list(yield_evidence)
    pages_to_verify = list(set(e.page_no for e in all_evidence))

    # Build why message
    direction = "above" if delta_pct > 0 else "below"
    why = f"Declared yield {declared_kwh_per_kwp:.0f} kWh/kWp is {abs_delta:.1f}% {direction} PVGIS estimate ({pvgis_kwh_per_kwp:.0f} kWh/kWp) for this location."

    return VerificationResult(
        check_id="CHK-YIELD-001",
        check_type="PVGIS_YIELD_SANITY",
        inputs={
            "lat": lat,
            "lon": lon,
            "peakpower_kwp": power_kwp,
            "declared_kwh_per_kwp": round(declared_kwh_per_kwp, 1),
            "declared_source": declared_source,
            "location": str(location_fact.value)
        },
        outputs={
            "pvgis_kwh_per_kwp_estimate": pvgis_kwh_per_kwp,
            "pvgis_annual_kwh": pvgis_result.annual_kwh
        },
        result=result,
        severity=severity,
        delta_pct=round(delta_pct, 1),
        confidence=0.9 if declared_source == "DECLARED_YIELD" else 0.75,
        why=why,
        pages_to_verify=pages_to_verify,
        evidence=all_evidence
    )


def verify_area_power(facts: list[ExtractedFact]) -> VerificationResult | None:
    """Check if roof area vs declared power makes sense."""
    area, area_ev = get_fact_value(facts, "roof_area_m2")
    power, power_ev = get_fact_value(facts, "declared_power_kwp")

    if not area or not power:
        return None

    ratio = float(area) / float(power)

    if 4 <= ratio <= 10:
        result, severity = "OK", "OK"
    elif 3 <= ratio <= 12:
        result, severity = "MARGINAL", "MEDIUM"
    else:
        result, severity = "OUTLIER", "HIGH"

    all_evidence = list(area_ev) + list(power_ev)
    pages = list(set(e.page_no for e in all_evidence))

    return VerificationResult(
        check_id="CHK-AREA-001",
        check_type="AREA_POWER_RATIO",
        inputs={"area_m2": area, "power_kwp": power, "ratio": round(ratio, 2)},
        outputs={"typical_range": "5-8 m²/kWp"},
        result=result,
        severity=severity,
        delta_pct=None,
        confidence=0.85,
        why=f"Area ratio {ratio:.1f} m²/kWp (typical: 5-8 m²/kWp)",
        pages_to_verify=pages,
        evidence=all_evidence
    )


def generate_flags(facts: list[ExtractedFact], verifications: list[VerificationResult]) -> list[RedFlag]:
    """Generate red flags based on facts and verifications."""
    flags = []
    found = {f.field for f in facts if f.value is not None}

    # Missing required fields
    for field in REQUIRED_FIELDS:
        if field not in found:
            flags.append(RedFlag(
                flag_id=f"RF-DC-{field[:8].upper()}",
                severity="HIGH",
                category="DATA_COMPLETENESS",
                title=f"Missing: {field.replace('_', ' ')}",
                description=f"Required field '{field}' not found in document.",
                why_it_matters="Core data needed for loan assessment.",
                pages_to_verify=[1, 2],
                evidence=[],
                recommended_action="Request document with complete data."
            ))

    # Missing important fields
    for field in IMPORTANT_FIELDS:
        if field not in found:
            flags.append(RedFlag(
                flag_id=f"RF-DC-{field[:8].upper()}",
                severity="MEDIUM",
                category="DATA_COMPLETENESS",
                title=f"Missing: {field.replace('_', ' ')}",
                description=f"Important field '{field}' not found.",
                why_it_matters="Recommended for complete assessment.",
                pages_to_verify=[],
                evidence=[],
                recommended_action="Consider requesting this data."
            ))

    # Verification-based flags
    for v in verifications:
        if v.check_type == "PVGIS_YIELD_SANITY" and v.severity in ["MEDIUM", "HIGH"]:
            direction = "optimistic" if v.delta_pct and v.delta_pct > 0 else "pessimistic"
            flags.append(RedFlag(
                flag_id="RF-FS-002",
                severity=v.severity,
                category="FEASIBILITY",
                title=f"Yield assumption looks {direction}",
                description=v.why,
                why_it_matters="May overstate expected production and cashflows." if v.delta_pct and v.delta_pct > 0 else "Conservative estimate may understate project value.",
                pages_to_verify=v.pages_to_verify,
                evidence=v.evidence,
                recommended_action="Request yield methodology and sensitivity analysis."
            ))

        elif v.check_type == "AREA_POWER_RATIO" and v.severity in ["MEDIUM", "HIGH"]:
            flags.append(RedFlag(
                flag_id="RF-FS-001",
                severity=v.severity,
                category="FEASIBILITY",
                title="Power-to-area ratio unusual",
                description=v.why,
                why_it_matters="May indicate sizing issues or data errors.",
                pages_to_verify=v.pages_to_verify,
                evidence=v.evidence,
                recommended_action="Verify roof dimensions and panel layout."
            ))

    return flags


def calculate_scorecard(
    facts: list[ExtractedFact],
    verifications: list[VerificationResult],
    flags: list[RedFlag]
) -> ScoreCard:
    """Calculate final scores."""
    found = {f.field for f in facts if f.value is not None}

    # Evidence coverage
    all_fields = REQUIRED_FIELDS + IMPORTANT_FIELDS
    coverage = int(len(found & set(all_fields)) / len(all_fields) * 100)

    # Consistency
    consistency = 100 - sum(20 for f in flags if f.category == "DATA_COMPLETENESS" and f.severity == "HIGH")
    consistency = max(0, consistency)

    # Feasibility - based on PVGIS delta (PRD Delta spec)
    feasibility = 100
    for v in verifications:
        if v.check_type == "PVGIS_YIELD_SANITY" and v.delta_pct is not None:
            abs_delta = abs(v.delta_pct)
            if abs_delta < 10:
                feasibility = min(feasibility, 100)
            elif abs_delta < 15:
                # Linear scale 60-79
                feasibility = min(feasibility, 80 - int((abs_delta - 10) * 4))
            else:
                # Linear scale 0-59
                feasibility = min(feasibility, max(0, 60 - int((abs_delta - 15) * 2)))
        elif v.check_type == "AREA_POWER_RATIO":
            if v.result == "OUTLIER":
                feasibility = min(feasibility, 50)
            elif v.result == "MARGINAL":
                feasibility = min(feasibility, 75)

    feasibility = max(0, feasibility)

    # Traffic light
    avg = (coverage + consistency + feasibility) / 3
    light = "GREEN" if avg >= 70 else ("YELLOW" if avg >= 45 else "RED")

    # Pages to verify
    pages = set()
    for f in flags:
        pages.update(f.pages_to_verify)

    missing = [f for f in all_fields if f not in found]

    return ScoreCard(
        evidence_coverage=coverage,
        consistency=consistency,
        feasibility=feasibility,
        traffic_light=light,
        pages_to_verify=sorted(pages),
        missing_data=missing
    )


def run_verification(facts: list[ExtractedFact]) -> tuple[list[VerificationResult], list[RedFlag], ScoreCard]:
    """Run all verification checks."""
    verifications = []

    # PVGIS Yield Sanity Check
    v = verify_pvgis_yield(facts)
    if v:
        verifications.append(v)

    # Area/Power Ratio Check
    v = verify_area_power(facts)
    if v:
        verifications.append(v)

    flags = generate_flags(facts, verifications)
    scorecard = calculate_scorecard(facts, verifications, flags)

    return verifications, flags, scorecard
