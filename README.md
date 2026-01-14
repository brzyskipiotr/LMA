# GreenLoan Validator

**AI-powered document analysis for green loan origination**

> Submitted to [LMA EDGE Hackathon 2026](https://lmaedgehackathon.devpost.com/) — Category: **Greener Lending**

---

## The Problem

Banks and financial institutions face significant challenges when originating green loans for photovoltaic (PV) installations:

- **Manual document review** — Loan officers spend hours extracting data from PDF offers, technical specs, and applications
- **Greenwashing risk** — Overstated yield projections can lead to non-performing loans when actual energy production falls short
- **Data inconsistency** — Key figures scattered across multiple documents with no automated cross-validation
- **Compliance burden** — EU Taxonomy and green bond standards require robust evidence trails

## Our Solution

**GreenLoan Validator** automates the due diligence process for PV green loans:

1. **Upload PDF** — Drop any PV-related document (offers, specs, grid applications)
2. **AI Extraction** — Gemini 2.5 Flash extracts structured facts with evidence citations
3. **PVGIS Validation** — Cross-reference declared yields against EU JRC satellite data
4. **Risk Assessment** — Automatic red flags for outliers, missing data, and inconsistencies
5. **Decision Support** — Traffic light scorecard (GREEN/YELLOW/RED) for quick decisions

### Key Features

| Feature | Description |
|---------|-------------|
| **Evidence Grounding** | Every extracted value links to page number + exact quote |
| **PVGIS Sanity Check** | Compare declared kWh/kWp against satellite-based estimates for the exact location |
| **Implied Yield Detection** | Calculate specific yield from annual MWh if not explicitly stated |
| **Red Flag Engine** | Automatic alerts for missing fields, optimistic projections, unusual ratios |
| **PII Anonymization** | Regex-based masking before sending to external APIs |
| **International Support** | Works with documents in any language, supports EU-wide geocoding |

---

## Technical Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│   Frontend  │────▶│   Backend   │────▶│  External APIs  │
│  React/Vite │     │   FastAPI   │     │                 │
└─────────────┘     └─────────────┘     │  • Gemini 2.5   │
                           │            │  • Nominatim    │
                    ┌──────┴──────┐     │  • EU PVGIS     │
                    │             │     └─────────────────┘
               ┌────┴────┐  ┌─────┴─────┐
               │   PDF   │  │ Verification│
               │ Parser  │  │   Engine    │
               │ PyMuPDF │  │             │
               └─────────┘  └─────────────┘
```

### Tech Stack

- **Frontend:** React 18 + TypeScript + Tailwind CSS + Vite
- **Backend:** Python 3.12 + FastAPI + Pydantic
- **AI/ML:** Google Gemini 2.5 Flash (document understanding)
- **Geocoding:** OpenStreetMap Nominatim (with file cache)
- **Solar Data:** EU JRC PVGIS 5.2 API (satellite-based irradiance)
- **PDF Processing:** PyMuPDF (text extraction + OCR fallback)

---

## Business Value

### For Banks & Lenders

- **80% faster** document review vs manual processing
- **Reduce greenwashing risk** with satellite-validated yield checks
- **Audit trail** — every decision backed by page-level evidence
- **Scalable** — process hundreds of applications without adding headcount

### For the Green Lending Market

- **Standardization** — consistent evaluation criteria across institutions
- **Transparency** — clear methodology for yield validation
- **EU Taxonomy alignment** — evidence-based green classification

### Market Opportunity

- €300B+ green loan market in Europe (2024)
- Growing regulatory pressure for robust green due diligence
- Banks seeking automation to meet ESG commitments at scale

---

## PVGIS Yield Validation

The core innovation is cross-referencing declared yields against EU satellite data:

```
Document claims: 1,200 kWh/kWp/year in Warsaw
                          ↓
         Geocode "Warsaw" → 52.23°N, 21.07°E
                          ↓
         PVGIS API → Expected: 1,046 kWh/kWp/year
                          ↓
         Delta: +14.7% → MEDIUM severity flag
                          ↓
         "Yield assumption looks optimistic"
```

### Severity Thresholds

| Delta | Result | Action |
|-------|--------|--------|
| < 10% | OK | Proceed |
| 10-15% | MEDIUM | Review methodology |
| > 15% | HIGH | Request justification |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google Gemini API key ([Get one here](https://aistudio.google.com/apikey))

### Installation

```bash
# Clone repository
git clone https://github.com/brzyskipiotr/LMA.git
cd LMA

# Backend setup
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Frontend setup
cd ../frontend
npm install
```

### Running

```bash
# Terminal 1: Backend
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

Open **http://localhost:5173**

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Upload PDF, returns full analysis report |
| `GET` | `/api/page/{doc_id}/{page_no}` | Get page image for verification |

### Response Schema

```json
{
  "document": {
    "doc_id": "DOC-20260114-abc123",
    "filename": "pv_offer.pdf",
    "pages": 6,
    "sha256": "..."
  },
  "facts": [
    {
      "field": "declared_power_kwp",
      "value": 49.68,
      "unit": "kWp",
      "confidence": 0.95,
      "evidence": [{"page_no": 1, "snippet": "System size: 49.68 kWp"}]
    }
  ],
  "verifications": [
    {
      "check_type": "PVGIS_YIELD_SANITY",
      "result": "MARGINAL",
      "severity": "MEDIUM",
      "delta_pct": 12.5,
      "why": "Declared yield 1180 kWh/kWp is 12.5% above PVGIS estimate"
    }
  ],
  "red_flags": [
    {
      "severity": "MEDIUM",
      "title": "Yield assumption looks optimistic",
      "description": "...",
      "recommended_action": "Request yield methodology"
    }
  ],
  "scorecard": {
    "evidence_coverage": 83,
    "consistency": 100,
    "feasibility": 75,
    "traffic_light": "YELLOW"
  }
}
```

---

## Project Structure

```
LMA/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI endpoints
│   │   ├── config.py            # Environment config
│   │   ├── schemas.py           # Pydantic models
│   │   └── pipeline/
│   │       ├── pdf_processor.py    # PDF → text + images
│   │       ├── gemini_analyzer.py  # AI fact extraction
│   │       ├── verification.py     # Sanity checks + scoring
│   │       ├── geocoding.py        # Nominatim integration
│   │       ├── pvgis.py            # EU PVGIS API client
│   │       ├── anonymize.py        # PII redaction
│   │       └── solar_constants.py  # EU country data
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Main application
│   │   ├── types.ts             # TypeScript interfaces
│   │   └── components/
│   │       ├── ScoreCard.tsx       # Traffic light dashboard
│   │       ├── FactsTable.tsx      # Extracted data display
│   │       ├── RedFlags.tsx        # Risk alerts
│   │       ├── PVGISPanel.tsx      # Yield validation view
│   │       └── PageViewer.tsx      # Document evidence viewer
│   └── package.json
│
└── README.md
```

---

## Roadmap

- [ ] Multi-document analysis (cross-reference offer vs application)
- [ ] Integration with LMA ACORD data standards
- [ ] Batch processing API for portfolio screening
- [ ] Export to credit decision systems
- [ ] Mobile-responsive UI

---

## License

Apache 2.0 — See [LICENSE](LICENSE)

---

## Acknowledgments

- **[EU JRC PVGIS](https://re.jrc.ec.europa.eu/pvg_tools/)** — Photovoltaic Geographical Information System
- **[OpenStreetMap Nominatim](https://nominatim.org/)** — Geocoding service
- **[Google Gemini](https://ai.google.dev/)** — Document understanding AI

---

*Built with urgency and passion at the LMA EDGE Hackathon 2026*
