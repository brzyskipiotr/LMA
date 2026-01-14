from app.schemas import ExtractedFact, VerificationResult, RedFlag, ScoreCard

# PVGIS estimates for Polish cities (kWh/kWp/year)
POLAND_YIELD = {
    "warszawa": 1050, "krakow": 1080, "gdansk": 1000,
    "wroclaw": 1060, "poznan": 1040, "lodz": 1045,
    "szczecin": 1010, "lublin": 1070, "default": 1030
}

REQUIRED_FIELDS = ["project_location_text", "declared_power_kwp", "system_type"]
IMPORTANT_FIELDS = ["declared_yield_kwh_per_kwp", "capex_pln", "roof_area_m2"]


def get_fact_value(facts: list[ExtractedFact], field: str):
    for f in facts:
        if f.field == field and f.value is not None:
            return f.value, f.evidence
    return None, []


def verify_yield(facts: list[ExtractedFact]) -> VerificationResult | None:
    declared, evidence = get_fact_value(facts, "declared_yield_kwh_per_kwp")
    location, _ = get_fact_value(facts, "project_location_text")

    if not declared:
        return None

    declared = float(declared)
    loc_lower = str(location).lower() if location else ""
    expected = next((v for k, v in POLAND_YIELD.items() if k in loc_lower), POLAND_YIELD["default"])

    delta = ((declared - expected) / expected) * 100
    result = "OK" if abs(delta) < 10 else ("MARGINAL" if abs(delta) < 15 else "OUTLIER")

    return VerificationResult(
        check_id="CHK-YIELD",
        check_type="PVGIS_YIELD",
        inputs={"declared": declared, "expected": expected, "location": location or "unknown"},
        result=result,
        delta_pct=round(delta, 1),
        why=f"Declared yield {declared} vs expected {expected} kWh/kWp ({delta:+.1f}%)",
        pages_to_verify=[e.page_no for e in evidence]
    )


def verify_area_power(facts: list[ExtractedFact]) -> VerificationResult | None:
    area, area_ev = get_fact_value(facts, "roof_area_m2")
    power, power_ev = get_fact_value(facts, "declared_power_kwp")

    if not area or not power:
        return None

    ratio = float(area) / float(power)
    result = "OK" if 4 <= ratio <= 10 else ("MARGINAL" if 3 <= ratio <= 12 else "OUTLIER")

    pages = list(set(e.page_no for e in area_ev + power_ev))

    return VerificationResult(
        check_id="CHK-AREA",
        check_type="AREA_POWER_RATIO",
        inputs={"area_m2": area, "power_kwp": power, "ratio": round(ratio, 2)},
        result=result,
        delta_pct=None,
        why=f"Area ratio {ratio:.1f} m²/kWp (typical: 5-8 m²/kWp)",
        pages_to_verify=pages
    )


def generate_flags(facts: list[ExtractedFact], verifications: list[VerificationResult]) -> list[RedFlag]:
    flags = []
    found = {f.field for f in facts if f.value is not None}

    # Missing required
    for field in REQUIRED_FIELDS:
        if field not in found:
            flags.append(RedFlag(
                flag_id=f"RF-MISSING-{field[:8].upper()}",
                severity="HIGH",
                category="DATA_COMPLETENESS",
                title=f"Missing: {field.replace('_', ' ')}",
                description=f"Required field '{field}' not found in document.",
                pages_to_verify=[1, 2],
                recommended_action="Request document with complete data."
            ))

    # Missing important
    for field in IMPORTANT_FIELDS:
        if field not in found:
            flags.append(RedFlag(
                flag_id=f"RF-MISSING-{field[:8].upper()}",
                severity="MEDIUM",
                category="DATA_COMPLETENESS",
                title=f"Missing: {field.replace('_', ' ')}",
                description=f"Important field '{field}' not found.",
                pages_to_verify=[],
                recommended_action="Consider requesting this data."
            ))

    # Verification flags
    for v in verifications:
        if v.result == "OUTLIER":
            flags.append(RedFlag(
                flag_id=f"RF-{v.check_id}",
                severity="HIGH",
                category="FEASIBILITY",
                title=f"Issue: {v.check_type}",
                description=v.why,
                pages_to_verify=v.pages_to_verify,
                recommended_action="Manual verification required."
            ))
        elif v.result == "MARGINAL":
            flags.append(RedFlag(
                flag_id=f"RF-{v.check_id}",
                severity="MEDIUM",
                category="FEASIBILITY",
                title=f"Warning: {v.check_type}",
                description=v.why,
                pages_to_verify=v.pages_to_verify,
                recommended_action="Verification recommended."
            ))

    return flags


def calculate_scorecard(facts: list[ExtractedFact], verifications: list[VerificationResult], flags: list[RedFlag]) -> ScoreCard:
    found = {f.field for f in facts if f.value is not None}

    # Evidence coverage
    all_fields = REQUIRED_FIELDS + IMPORTANT_FIELDS
    coverage = int(len(found & set(all_fields)) / len(all_fields) * 100)

    # Consistency
    consistency = 100 - sum(20 for f in flags if f.category == "DATA_COMPLETENESS" and f.severity == "HIGH")
    consistency = max(0, consistency)

    # Feasibility
    feasibility = 100
    for v in verifications:
        if v.result == "OUTLIER":
            feasibility -= 25
        elif v.result == "MARGINAL":
            feasibility -= 10
    feasibility = max(0, feasibility)

    avg = (coverage + consistency + feasibility) / 3
    light = "GREEN" if avg >= 70 else ("YELLOW" if avg >= 45 else "RED")

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
    verifications = []

    v = verify_yield(facts)
    if v:
        verifications.append(v)

    v = verify_area_power(facts)
    if v:
        verifications.append(v)

    flags = generate_flags(facts, verifications)
    scorecard = calculate_scorecard(facts, verifications, flags)

    return verifications, flags, scorecard
