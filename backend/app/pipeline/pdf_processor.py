import hashlib
import fitz
from pathlib import Path
from datetime import datetime

from app.config import UPLOAD_DIR
from app.schemas import DocumentMeta, PageInfo


def process_pdf(file_bytes: bytes, filename: str) -> tuple[DocumentMeta, list[PageInfo], list[str]]:
    """Process PDF: extract text, render pages."""
    sha256 = hashlib.sha256(file_bytes).hexdigest()
    doc_id = f"DOC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{sha256[:6]}"

    doc_dir = UPLOAD_DIR / doc_id
    doc_dir.mkdir(parents=True, exist_ok=True)
    (doc_dir / "pages").mkdir(exist_ok=True)

    # Save PDF
    (doc_dir / filename).write_bytes(file_bytes)

    pdf = fitz.open(stream=file_bytes, filetype="pdf")
    page_texts = []
    page_info = []

    for i, page in enumerate(pdf):
        page_no = i + 1

        # Render to PNG
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        pix.save(str(doc_dir / "pages" / f"{page_no:03d}.png"))

        # Extract text
        text = page.get_text()
        page_texts.append(f"--- STRONA {page_no} ---\n{text}")

        page_info.append(PageInfo(
            page_no=page_no,
            has_text=len(text.strip()) > 20,
            char_count=len(text)
        ))

    pdf.close()

    # Save combined text
    (doc_dir / "full_text.txt").write_text("\n\n".join(page_texts), encoding="utf-8")

    meta = DocumentMeta(
        doc_id=doc_id,
        filename=filename,
        sha256=sha256,
        pages=len(page_info),
        created_at=datetime.now()
    )

    return meta, page_info, page_texts
