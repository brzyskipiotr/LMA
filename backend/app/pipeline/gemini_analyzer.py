import google.generativeai as genai
import json
from pathlib import Path
from PIL import Image

from app.config import GOOGLE_API_KEY, UPLOAD_DIR
from app.schemas import ExtractedFact, Evidence, PageInfo

PV_FIELDS = """
- project_location_text: adres/lokalizacja projektu
- declared_power_kwp: moc instalacji w kWp
- system_type: typ (dachowa/gruntowa)
- declared_yield_kwh_per_kwp: prognozowany uzysk kWh/kWp/rok
- declared_annual_energy_mwh: roczna produkcja energii
- capex_pln: koszt inwestycji w PLN
- roof_area_m2: powierzchnia dachu
- panels_count: liczba paneli
- module_watt_peak: moc modułu Wp
- inverter_power_kw: moc falownika
- grid_connection_status: status przyłączenia do sieci
- supplier_epc: wykonawca/dostawca
"""


def extract_facts_from_images(doc_id: str, page_info: list[PageInfo]) -> list[ExtractedFact]:
    """Use Gemini vision to extract facts from page images."""
    if not GOOGLE_API_KEY:
        return []

    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash-lite")

    pages_dir = UPLOAD_DIR / doc_id / "pages"
    images = []

    # Load all page images
    for p in page_info:
        img_path = pages_dir / f"{p.page_no:03d}.png"
        if img_path.exists():
            images.append(Image.open(img_path))

    if not images:
        return []

    prompt = f"""Przeanalizuj ten dokument PV/fotowoltaiczny i wydobądź fakty.

POLA DO WYDOBYCIA:
{PV_FIELDS}

Dla każdego znalezionego pola zwróć JSON:
- field: nazwa pola z listy
- value: wartość (liczba lub tekst)
- unit: jednostka (kWp, PLN, m2, itp.)
- confidence: 0.0-1.0
- evidence: [{{"page_no": numer_strony, "snippet": "dokładny cytat z dokumentu"}}]

ZASADY:
- Wydobywaj TYLKO jeśli znajdziesz wyraźny dowód w tekście
- Snippet musi być DOKŁADNYM cytatem
- Zwróć [] jeśli nic nie znaleziono

Zwróć TYLKO poprawny JSON array, bez wyjaśnień."""

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
            facts.append(ExtractedFact(
                field=f["field"],
                value=f.get("value"),
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
    model = genai.GenerativeModel("gemini-2.5-flash-lite")

    full_text = "\n\n".join(page_texts)[:30000]  # Limit

    prompt = f"""Przeanalizuj ten dokument PV/fotowoltaiczny i wydobądź fakty.

DOKUMENT:
{full_text}

POLA DO WYDOBYCIA:
{PV_FIELDS}

Dla każdego znalezionego pola zwróć JSON:
- field: nazwa pola z listy
- value: wartość (liczba lub tekst)
- unit: jednostka (kWp, PLN, m2, itp.)
- confidence: 0.0-1.0
- evidence: [{{"page_no": numer_strony, "snippet": "dokładny cytat"}}]

ZASADY:
- Wydobywaj TYLKO jeśli znajdziesz wyraźny dowód
- Snippet = dokładny cytat z dokumentu
- Zwróć [] jeśli nic nie znaleziono

Zwróć TYLKO poprawny JSON array."""

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
            facts.append(ExtractedFact(
                field=f["field"],
                value=f.get("value"),
                unit=f.get("unit"),
                confidence=f.get("confidence", 0.5),
                evidence=evidence
            ))
        return facts
    except Exception as e:
        print(f"Gemini text extraction error: {e}")
        return []
