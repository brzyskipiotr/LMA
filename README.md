# GreenLoan Validator

Narzędzie do automatycznej analizy dokumentów PDF dla kredytów na instalacje PV.

## Quick Start

### 1. Skonfiguruj klucz API Gemini

Skopiuj `.env.example` do `.env` i wklej swój klucz Gemini:

```
GOOGLE_API_KEY=your_gemini_api_key_here
```

Klucz możesz uzyskać: https://aistudio.google.com/apikey

### 2. Uruchom backend

```bash
start_backend.bat
```

Lub ręcznie:
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Uruchom frontend

```bash
start_frontend.bat
```

Lub ręcznie:
```bash
cd frontend
npm install
npm run dev
```

### 4. Otwórz aplikację

http://localhost:5173

## Struktura

```
backend/
  app/
    main.py           - FastAPI endpoints
    schemas.py        - Pydantic models
    pipeline/
      pdf_processor.py    - PDF → tekst + PNG
      gemini_analyzer.py  - Ekstrakcja faktów
      verification.py     - Sanity checks + scoring

frontend/
  src/
    App.tsx           - Main app
    components/       - UI components
```
