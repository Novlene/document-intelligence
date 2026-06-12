import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from pathlib import Path
import uuid
import json

from app.core.config import settings


def parse_document(file_path: Path, doc_id: str) -> list[dict]:
    """
    Parse a document and return list of pages with text + image.
    Handles: text PDFs, scanned PDFs, image-only PDFs.
    """
    suffix = file_path.suffix.lower()
    pages = []

    if suffix == ".pdf":
        pages = _parse_pdf(file_path, doc_id)
    elif suffix in [".png", ".jpg", ".jpeg", ".tiff"]:
        pages = _parse_image(file_path, doc_id)

    return pages


def _parse_pdf(file_path: Path, doc_id: str) -> list[dict]:
    pages = []

    # Render all pages as images first
    page_images = convert_from_path(
        str(file_path),
        dpi=200,
        poppler_path=_get_poppler_path()
    )

    with pdfplumber.open(file_path) as pdf:
        for i, plumber_page in enumerate(pdf.pages):
            page_num = i + 1

            # Save page image
            img_filename = f"{doc_id}_page_{page_num}.jpg"
            img_path = settings.pages_dir / img_filename
            page_images[i].save(str(img_path), "JPEG", quality=85)

            # Extract text
            text = plumber_page.extract_text() or ""

            # If no text → scanned page → use OCR
            if len(text.strip()) < 20:
                text = pytesseract.image_to_string(
                    page_images[i],
                    config="--psm 3"
                )

            # Extract tables
            tables = []
            raw_tables = plumber_page.extract_tables()
            for table in raw_tables:
                if table:
                    tables.append(table)

            pages.append({
                "page_num": page_num,
                "text": text.strip(),
                "image_path": f"pages/{img_filename}",
                "has_tables": len(tables) > 0,
                "table_data": tables,
            })

    return pages


def _parse_image(file_path: Path, doc_id: str) -> list[dict]:
    """Parse a standalone image file with OCR."""
    img = Image.open(file_path)

    # Save as page image
    img_filename = f"{doc_id}_page_1.jpg"
    img_path = settings.pages_dir / img_filename
    img.convert("RGB").save(str(img_path), "JPEG", quality=85)

    text = pytesseract.image_to_string(img, config="--psm 3")

    return [{
        "page_num": 1,
        "text": text.strip(),
        "image_path": f"pages/{img_filename}",
        "has_tables": False,
        "table_data": [],
    }]

def _get_poppler_path():
    """Return poppler path for Windows, None for Linux/Mac."""
    import platform
    if platform.system() == "Windows":
        candidates = [
            r"E:\RT4\Release-26.02.0-0\poppler\Library\bin",
            r"C:\poppler\Library\bin",
            r"C:\poppler\bin",
        ]
        for path in candidates:
            if Path(path).exists():
                return path
        return None
    return None