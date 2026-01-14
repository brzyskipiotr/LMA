import google.generativeai as genai
import json
from pathlib import Path
from PIL import Image

from app.config import GOOGLE_API_KEY, UPLOAD_DIR
from app.schemas import ExtractedFact, Evidence, PageInfo
from app.pipeline.anonymize import anonymize_text, anonymize_pages

PV_FIELDS = """
- project_location_text: project address/location (city, region, country)
- declared_power_kwp: installed power in kWp
- system_type: type (rooftop/ground-mounted)
- declared_yield_kwh_per_kwp: expected yield kWh/kWp/year
- declared_annual_energy_mwh: annual energy production in MWh
- capex_total: total investment cost (with currency: PLN, EUR, USD, etc.)
- capex_currency: currency of capex (PLN, EUR, USD, GBP, etc.)
- roof_area_m2: roof area in m²
- panels_count: number of panels
- module_watt_peak: module power in Wp
- inverter_power_kw: inverter power in kW
- grid_connection_status: grid connection status
- supplier_epc: contractor/supplier name
"""


def extract_facts_from_images(doc_id: str, page_info: list[PageInfo]) -> list[ExtractedFact]:
    """Use Gemini vision to extract facts from page images."""
    if not GOOGLE_API_KEY:
        return []

    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    pages_dir = UPLOAD_DIR / doc_id / "pages"
    images = []

    # Load all page images
    for p in page_info:
        img_path = pages_dir / f"{p.page_no:03d}.png"
        if img_path.exists():
            images.append(Image.open(img_path))

    if not images:
        return []

    prompt = f"""Analyze this PV/photovoltaic document and extract facts.

FIELDS TO EXTRACT:
{PV_FIELDS}

For each field found, return JSON:
- field: field name from the list above
- value: value (number or text)
- unit: unit (kWp, EUR, m², etc.)
- confidence: 0.0-1.0
- evidence: [{{"page_no": page_number, "snippet": "exact quote from document"}}]

RULES:
- Extract ONLY if you find clear evidence in the text
- Snippet must be an EXACT quote from the document
- Return [] if nothing found
- Document may be in any language (Polish, English, German, etc.)

Return ONLY valid JSON array, no explanations."""

    response = model.generate_content([prompt] + images)

    try:
        text = response.text
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        data = json.loads(text.strip())
        facts = []
        for f in data:
            evidence = [Evidence(**e) for e in f.get("evidence", [])]
            value = f.get("value")
            # Normalize array values (e.g., [20, 25] -> "20-25")
            if isinstance(value, list):
                value = "-".join(str(v) for v in value) if value else None
            facts.append(ExtractedFact(
                field=f["field"],
                value=value,
                unit=f.get("unit"),
                confidence=f.get("confidence", 0.5),
                evidence=evidence
            ))
        return facts
    except Exception as e:
        print(f"Gemini extraction error: {e}")
        return []


def extract_facts_from_text(page_texts: list[str]) -> list[ExtractedFact]:
    """Use Gemini to extract facts from text."""
    if not GOOGLE_API_KEY:
        return []

    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    # Anonymize before sending to external API
    anonymized_pages = anonymize_pages(page_texts)
    full_text = "\n\n".join(anonymized_pages)[:30000]  # Limit

    prompt = f"""Analyze this PV/photovoltaic document and extract facts.

DOCUMENT:
{full_text}

FIELDS TO EXTRACT:
{PV_FIELDS}

For each field found, return JSON:
- field: field name from the list above
- value: value (number or text)
- unit: unit (kWp, EUR, m², etc.)
- confidence: 0.0-1.0
- evidence: [{{"page_no": page_number, "snippet": "exact quote from document"}}]

RULES:
- Extract ONLY if you find clear evidence in the text
- Snippet must be an EXACT quote from the document
- Return [] if nothing found
- Document may be in any language (Polish, English, German, etc.)
- Note: Some PII has been redacted with placeholders like [NAME], [EMAIL], etc.

Return ONLY valid JSON array."""

    response = model.generate_content(prompt)

    try:
        text = response.text
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        data = json.loads(text.strip())
        facts = []
        for f in data:
            evidence = [Evidence(**e) for e in f.get("evidence", [])]
            value = f.get("value")
            # Normalize array values (e.g., [20, 25] -> "20-25")
            if isinstance(value, list):
                value = "-".join(str(v) for v in value) if value else None
            facts.append(ExtractedFact(
                field=f["field"],
                value=value,
                unit=f.get("unit"),
                confidence=f.get("confidence", 0.5),
                evidence=evidence
            ))
        return facts
    except Exception as e:
        print(f"Gemini text extraction error: {e}")
        return []
