Poniżej masz kompletny pakiet “wszystko” do wrzucenia do Claude Code: rozszerzony PRD (PV), pełna taksonomia flag, kontrakty JSON, przykładowe wyniki, heurystyki (jawne), backlog z DoD oraz zestaw “demo dataset” (syntetyczny + publiczny wzór), plus gotowe prompty.

PRD: SolarEvidence Pack (PV Green Loan Analyzer, PL-first)
0) Meta

Nazwa robocza: GreenLoan Validator

Cel (hackathon/LMA Edge): przyspieszyć origination + dokumentację + monitoring “green loan / capex loan” na PV poprzez automatyczne wydobycie faktów, szybkie checki wykonalności oraz evidence pack z groundingiem (numery stron).

Wersja: MVP / Hackathon (desktop web app)

Ryzyko modelowe: narzędzie do triage + evidence packaging, nie do decyzji kredytowej.

Poufność: używać dokumentów publicznych lub syntetycznych; zero realnych danych osobowych.

1) Problem (loan workflow)

W procesie kredytu na PV bank/agent dostaje pakiet PDF (wniosek, oferta, projekt, załączniki). Weryfikacja:

jest manualna i wolna,

cierpi na niską jakość PDF (skany, formularze, tabele),

nie ma standaryzacji “co sprawdziliśmy” (brak paczki dowodowej dla audytu/compliance).

Celem jest: w 1–3 min z PDF zrobić: fakty + niespójności + szybkie sanity checks + wskazanie stron do ręcznej weryfikacji.

2) Zakres MVP (Must-have)
2.1 Upload + ingest

Upload PDF

Hash (SHA-256), rozmiar, liczba stron

Podział na strony: render do PNG (np. 200 DPI)

2.2 Ekstrakcja tekstu + OCR fallback

Najpierw: text-layer extraction

Jeśli tekst jest pusty/śmieciowy → OCR dla strony

Każda strona ma ocr_text_raw + quality_metrics

2.3 OCR “review” z obrazem (tylko dla tekstu)

Twoje założenie: obraz jest po to, aby wykryć gdzie OCR się myli, ale nie wyciągamy danych z rysunków/tabel.

Implementacja:

OCR zwraca bbox dla linii/słów

Tworzysz obraz “maskowany” (zostają tylko regiony bbox, reszta zamazana)

Model dostaje: maskowany obraz + ocr_text_raw + bbox mapę

Model zwraca diff: poprawki OCR wyłącznie w obrębie bbox (bez parafrazy)

2.4 Ekstrakcja faktów PV z groundingiem

Model działa na ocr_text_clean (po zastosowaniu diff) i zwraca listę faktów. Każdy fakt musi mieć:

page_no

snippet (cytat)

confidence

2.5 Verification (2 checki, deterministyczne)

Area sanity check: relacja m²/kWp (jeśli są dane) lub roof footprint (adapter geo/dane demo)

PV yield sanity check (PVGIS): roczny uzysk kWh/kWp dla lokalizacji; porównanie z deklaracją (jeśli jest)

2.6 Output: Score + Red Flags + Evidence Pack

3 składowe score (audit-friendly)

Red flags z severity i “pages_to_verify”

Export JSON (opcjonalnie HTML/PDF)

3) Zakres rozszerzony (Nice-to-have)

Batch processing wielu PDF

Generator PDF raportu (“Annex”)

Monitoring post-disbursement (alerty)

Integracja z LOS/case mgmt

Wersjonowanie dokumentów (diff między wersjami)

4) Data Model — pełne kontrakty JSON
4.1 DocumentMeta
{
  "doc_id": "DOC-2026-01-14-0001",
  "sha256": "…",
  "filename": "pv_loan_pack.pdf",
  "pages": 24,
  "created_at": "2026-01-14T09:10:00+01:00",
  "language_guess": "pl"
}

4.2 PageArtifact (pełniejszy)
{
  "page_no": 7,
  "render_path": "pages/page_007.png",
  "has_text_layer": false,
  "text_layer_raw": "",
  "ocr_text_raw": "Moc instalacji: 5O kWp\nAdres: …",
  "ocr_quality": {
    "chars": 420,
    "non_alnum_ratio": 0.08,
    "pl_diacritics_ratio": 0.02,
    "avg_confidence": 0.71
  },
  "ocr_fixes": [
    {
      "bbox": [120, 340, 980, 380],
      "ocr_text": "Moc instalacji: 5O kWp",
      "proposed_text": "Moc instalacji: 50 kWp",
      "issue_type": "OCR_ERROR",
      "confidence": 0.93
    }
  ],
  "ocr_missing": [],
  "ocr_text_clean": "Moc instalacji: 50 kWp\nAdres: …"
}

4.3 ExtractedFact (rozszerzony)
{
  "field": "declared_power_kwp",
  "value": 50.0,
  "unit": "kWp",
  "normalized_value": 50.0,
  "confidence": 0.88,
  "evidence": [
    {
      "page_no": 7,
      "snippet": "Moc instalacji: 50 kWp",
      "source": "text"
    }
  ]
}

4.4 Claim (jeśli chcesz osobną warstwę claimów)
{
  "claim_id": "CL-PV-001",
  "claim_type": "ASSET_PV_POWER",
  "claim_text": "Planowana instalacja PV o mocy 50 kWp.",
  "page_refs": [7],
  "evidence": [{"page_no": 7, "snippet": "Moc instalacji: 50 kWp"}],
  "extract_confidence": 0.88
}

4.5 VerificationResult
{
  "check_id": "CHK-YIELD-001",
  "check_type": "PVGIS_YIELD_SANITY",
  "inputs": {
    "lat": 52.2297,
    "lon": 21.0122,
    "declared_kwh_per_kwp": 1250,
    "pvgis_estimate_kwh_per_kwp": 1050
  },
  "result": "OUTLIER_HIGH",
  "delta_pct": 19.0,
  "confidence": 0.9,
  "why": "Declared yield exceeds PVGIS estimate by ~19% for the location.",
  "pages_to_verify": [18],
  "evidence": [{"page_no": 18, "snippet": "Prognozowany uzysk: 1250 kWh/kWp/rok"}]
}

4.6 RedFlag (pełny standard)
{
  "flag_id": "RF-YIELD-001",
  "severity": "HIGH",
  "category": "FEASIBILITY",
  "title": "Yield assumption looks optimistic",
  "description": "Declared yield is significantly above PVGIS estimate for this location.",
  "why_it_matters": "May overstate cashflow/DSCR assumptions.",
  "pages_to_verify": [18],
  "evidence": [
    {"page_no": 18, "snippet": "Prognozowany uzysk: 1250 kWh/kWp/rok"}
  ],
  "confidence": 0.9,
  "recommended_next_step": "Request yield methodology and sensitivity analysis; validate assumptions with independent estimate."
}

4.7 ScoreCard (final)
{
  "scores": {
    "evidence_coverage": 76,
    "consistency": 63,
    "feasibility": 58
  },
  "traffic_light": "YELLOW",
  "pages_to_verify": [3, 7, 12, 18],
  "missing_data": ["roof_area_m2", "inverter_power_kw"],
  "notes": [
    "This tool supports screening and evidence packaging; final assessment remains with analyst."
  ]
}

4.8 FinalReport
{
  "document": {"doc_id": "DOC-2026-01-14-0001", "pages": 24},
  "facts": [/* ExtractedFact[] */],
  "verifications": [/* VerificationResult[] */],
  "red_flags": [/* RedFlag[] */],
  "scorecard": {/* ScoreCard */},
  "evidence_pack": {
    "highlights": [
      {
        "topic": "Declared PV power",
        "value": "50 kWp",
        "pages": [7],
        "evidence": [{"page_no": 7, "snippet": "Moc instalacji: 50 kWp"}]
      }
    ],
    "pages_to_verify": [3, 7, 12, 18]
  }
}

5) PV Fields — pełna lista pól (z priorytetami)
P0 (MVP absolutny)

project_location_text (adres/miejscowość)

declared_power_kwp

system_type (rooftop/ground/mixed)

declared_yield_kwh_per_kwp (jeśli w PDF)

capex_pln (jeśli w PDF)

timeline_commissioning_date (jeśli w PDF)

P1 (bardzo pożądane)

roof_area_m2 / available_area_m2 (jeśli w PDF)

declared_annual_energy_mwh (jeśli w PDF)

inverter_power_kw

panels_count

module_watt_peak

grid_connection_status (warunki przyłączenia / wniosek / decyzja)

self_consumption_ratio (autokonsumpcja vs eksport)

P2 (post-hackathon)

opex_pln_per_year

maintenance_contract_present (tak/nie)

insurance_present (tak/nie)

permits_present (tak/nie)

supplier_epc (nazwa wykonawcy)

Każde pole: page_no + snippet + confidence.

6) Heurystyki i reguły (jawne, audytowalne)
6.1 Area sanity (m²/kWp)

Jeśli masz roof_area_m2 i declared_power_kwp:

licz m2_per_kwp = roof_area_m2 / declared_power_kwp

flaguj:

LOW jeśli 10–12 m²/kWp (może nietypowa konstrukcja)

HIGH jeśli < 3.5 m²/kWp lub > 15 m²/kWp (podejrzane)

Jeśli brak roof_area_m2: oznacz missing_data i nie wnioskuj.

6.2 Yield sanity (PVGIS)

Jeżeli PDF deklaruje declared_kwh_per_kwp:

porównaj z PVGIS pvgis_kwh_per_kwp

flaguj:

MED jeśli odchylenie 10–15%

HIGH jeśli > 15%

Jeśli PDF deklaruje roczną energię MWh:

implied_kwh_per_kwp = annual_kwh / kwp

i porównaj analogicznie.

6.3 Consistency (wewnątrz dokumentu)

Jeśli w dwóch miejscach różne declared_power_kwp → CRITICAL

Jeśli panels_count * module_wp istotnie odbiega od declared_power_kwp → HIGH

Jeśli inverter_power_kw znacznie > lub << declared_power_kwp bez uzasadnienia → MED/HIGH

7) Red Flags Taxonomy (komplet kodów)
A) DATA COMPLETENESS (DC)

RF-DC-001 Missing location/address

RF-DC-002 Missing declared power (kWp)

RF-DC-003 Missing yield assumptions

RF-DC-004 Missing CAPEX or financials

RF-DC-005 Missing grid connection status/attachments

B) OCR / DOCUMENT QUALITY (DQ)

RF-DQ-001 Low OCR confidence on key pages

RF-DQ-002 Key numeric fields uncertain (manual review)

RF-DQ-003 Suspected text-layer corruption (garbled text)

C) INTERNAL CONSISTENCY (IC)

RF-IC-001 Conflicting power values across pages

RF-IC-002 Panels/modules implied power mismatch

RF-IC-003 Inverter sizing mismatch

RF-IC-004 Timeline dates inconsistent

D) FEASIBILITY (FS)

RF-FS-001 Power-to-area mismatch

RF-FS-002 Yield assumption optimistic vs PVGIS

RF-FS-003 Annual energy inconsistent with kWp

RF-FS-004 System type vs described constraints mismatch

E) COMPLIANCE / PROCESS (CP) (MVP: tylko sygnały)

RF-CP-001 Missing permits statement (if required)

RF-CP-002 Missing insurance/maintenance evidence (if expected by policy)

Każda flaga ma: severity, pages_to_verify, evidence snippets, next steps.

8) UI (ekrany MVP)

Upload + doc meta (hash, pages, status)

Pages view: lista stron + badge “text-layer / OCR / OCR-fix”

Facts table: pole → wartość → confidence → strony (klik otwiera stronę)

Feasibility panel: PVGIS + area sanity (jawne reguły)

Red flags: lista z filtrem severity + “pages to verify”

Evidence pack: “highlight cards” + export JSON (+ opcjonalnie HTML/PDF)

9) Prompty (gotowe, restrykcyjne)
9.1 OCR DIFF (maskowany obraz + OCR text)

System/Developer intent (treść promptu):

Masz poprawić tylko błędy OCR w tekście.

Nie wolno parafrazować, streszczać, poprawiać stylu.

Nie wolno dodawać informacji z wykresów, tabel, obrazków.

Zwróć JSON listę poprawek: bbox + ocr_text + proposed_text + issue_type + confidence.

User prompt (prosty):

Given the masked page image (only OCR text regions visible) and OCR text, identify mismatches and propose corrections ONLY for the mismatched text regions. Return JSON array of fixes. Do not rewrite the whole page. Do not invent numbers.

9.2 FACTS EXTRACTION (tekst po cleanup)

Tylko PV-related fields z listy P0/P1

Każdy fact: page_no + snippet

Jeśli nie ma cytatu/strony: wartość = null i dodaj do missing

10) Backlog + DoD (hackathon)
Sprint 1 (foundation)

 Upload + persist doc meta

 Split pages → PNG

 text-layer extraction + quality scoring

 OCR fallback

 Frontend: upload + pages list

DoD: potrafi przejść PDF i mieć per-strona tekst.

Sprint 2 (core intelligence)

 OCR mask image builder (bbox-based)

 Gemini OCR diff → apply fixes → clean text

 Facts extraction JSON (P0 fields)

 UI: facts table z klikanymi stronami

DoD: zwraca min. 5 faktów z numerami stron.

Sprint 3 (verification + polish)

 PVGIS integration (lub cached demo)

 Area/yield sanity rules

 Red flags taxonomy + generator

 Scorecard + export JSON

 Demo script 3 min + dataset

DoD: end-to-end demo: PDF → score + flags + pages_to_verify + export.

11) Demo dataset (praktyczne, bez danych osobowych)
Opcja A (najbezpieczniejsza): Syntetycznie wypełniony formularz

Bierzesz publiczny blank formularz przyłączenia mikroinstalacji / zgłoszenia PV

Wypełniasz fikcyjnymi danymi firmy (NIP testowy, adres testowy, kwoty fikcyjne)

Generujesz 2 wersje:

“born-digital” (idealny text-layer)

skan/kompresja (OCR challenge)

Opcja B: Publiczny “wzór wypełnienia” (jeśli dostępny)

Używasz wprost “wzorów wypełnienia” publikowanych przez dystrybutorów/instytucje

Plus jeden publiczny załącznik opisowy (np. oferta/założenia)

Minimalny zestaw do demo:

PDF #1: czysty, dużo tekstu (łatwa ekstrakcja)

PDF #2: skan, gorszy OCR (pokazuje przewagę diff)

PDF #3 (opcjonalnie): dokument z “optimistic yield” do odpalenia flagi RF-FS-002

12) Przykładowe wyniki (gotowce do frontendu)
12.1 Facts (przykład)
[
  {"field":"project_location_text","value":"Warszawa, ul. Przykładowa 12","unit":null,"confidence":0.74,
   "evidence":[{"page_no":3,"snippet":"Lokalizacja inwestycji: Warszawa, ul. Przykładowa 12","source":"text"}]},
  {"field":"declared_power_kwp","value":50,"unit":"kWp","confidence":0.88,
   "evidence":[{"page_no":7,"snippet":"Moc instalacji: 50 kWp","source":"text"}]},
  {"field":"system_type","value":"rooftop","unit":null,"confidence":0.66,
   "evidence":[{"page_no":7,"snippet":"Montaż: dach budynku produkcyjnego","source":"text"}]},
  {"field":"declared_yield_kwh_per_kwp","value":1250,"unit":"kWh/kWp/rok","confidence":0.82,
   "evidence":[{"page_no":18,"snippet":"Prognozowany uzysk: 1250 kWh/kWp/rok","source":"text"}]},
  {"field":"capex_pln","value":220000,"unit":"PLN","confidence":0.77,
   "evidence":[{"page_no":12,"snippet":"Koszt inwestycji (CAPEX): 220 000 PLN","source":"text"}]}
]

12.2 Red flags (przykład)
[
  {"flag_id":"RF-FS-002","severity":"HIGH","category":"FEASIBILITY",
   "title":"Yield assumption looks optimistic",
   "description":"Declared yield exceeds PVGIS estimate by ~19% for this location.",
   "why_it_matters":"May overstate expected cashflows/DSCR.",
   "pages_to_verify":[18],
   "evidence":[{"page_no":18,"snippet":"Prognozowany uzysk: 1250 kWh/kWp/rok"}],
   "confidence":0.9,
   "recommended_next_step":"Request yield methodology and sensitivity analysis."},

  {"flag_id":"RF-DC-005","severity":"MEDIUM","category":"DATA_COMPLETENESS",
   "title":"Grid connection evidence missing",
   "description":"No attachment or statement about grid connection conditions found.",
   "why_it_matters":"Project timeline/feasibility depends on grid connection status.",
   "pages_to_verify":[1,2,3,4],
   "evidence":[],
   "confidence":0.7,
   "recommended_next_step":"Request connection conditions / confirmation of application status."}
]

12.3 Scorecard (przykład)
{
  "scores":{"evidence_coverage":76,"consistency":63,"feasibility":58},
  "traffic_light":"YELLOW",
  "pages_to_verify":[3,7,12,18],
  "missing_data":["roof_area_m2","inverter_power_kw"],
  "notes":["Screening & evidence packaging only; final assessment by analyst."]
}

13) Repo skeleton (dokładniej, z modułami i interfejsami)
Backend
backend/
  app/
    main.py
    config.py
    api/
      routes_upload.py
      routes_report.py
    pipeline/
      ingest.py
      render_pages.py
      extract_text_layer.py
      ocr_engine.py
      build_text_mask.py
      llm_ocr_diff.py
      apply_fixes.py
      llm_extract_facts.py
      verify_area.py
      verify_pvgis.py
      flags.py
      scoring.py
      assemble_report.py
    schemas/
      document_meta.py
      page_artifact.py
      extracted_fact.py
      red_flag.py
      verification_result.py
      scorecard.py
      final_report.py
    storage/
      files.py
      cache.py
  requirements.txt

Frontend
frontend/
  src/
    pages/
      Upload.tsx
      Document.tsx
    components/
      PageList.tsx
      FactTable.tsx
      RedFlags.tsx
      EvidencePack.tsx
      FeasibilityPanel.tsx
    api.ts

Jedno pytanie, które determinuje implementację geo (żeby nie ugrzęznąć)

Czy w MVP chcesz:

Idź w (1) bez geo dla MVP. PVGIS + to co w PDF wystarczy na demo. Geo to scope creep i dependency hell.