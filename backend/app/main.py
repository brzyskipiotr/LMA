from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json

from app.config import UPLOAD_DIR
from app.schemas import AnalysisReport
from app.pipeline.pdf_processor import process_pdf
from app.pipeline.gemini_analyzer import extract_facts_from_text, extract_facts_from_images
from app.pipeline.verification import run_verification

app = FastAPI(title="GreenLoan Validator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files supported")

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 50MB)")

    # Process PDF
    doc_meta, page_info, page_texts = process_pdf(content, file.filename)

    # Check if pages have good text
    has_good_text = sum(1 for p in page_info if p.has_text) > len(page_info) * 0.5

    # Extract facts
    if has_good_text:
        facts = extract_facts_from_text(page_texts)
    else:
        facts = extract_facts_from_images(doc_meta.doc_id, page_info)

    # If text extraction failed, try images
    if not facts and has_good_text:
        facts = extract_facts_from_images(doc_meta.doc_id, page_info)

    # Run verification
    verifications, flags, scorecard = run_verification(facts)

    report = AnalysisReport(
        document=doc_meta,
        page_info=page_info,
        facts=facts,
        verifications=verifications,
        red_flags=flags,
        scorecard=scorecard
    )

    # Save report
    report_path = UPLOAD_DIR / doc_meta.doc_id / "report.json"
    report_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    return report


@app.get("/api/reports/{doc_id}")
async def get_report(doc_id: str):
    path = UPLOAD_DIR / doc_id / "report.json"
    if not path.exists():
        raise HTTPException(404, "Report not found")
    return json.loads(path.read_text())


@app.get("/api/page/{doc_id}/{page_no}")
async def get_page(doc_id: str, page_no: int):
    path = UPLOAD_DIR / doc_id / "pages" / f"{page_no:03d}.png"
    if not path.exists():
        raise HTTPException(404, "Page not found")
    return FileResponse(path, media_type="image/png")
