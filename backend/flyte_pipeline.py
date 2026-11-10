"""
Document Intelligence - ingestion pipeline as Flyte 2 tasks.

Same logic as app/services/pipeline.py (parse -> classify -> index),
but each step is a Flyte task, so each one has its own retries and its own
saved output. If `classify` fails (e.g. Groq rate limit), only `classify`
is retried. The OCR output is kept and OCR is NOT run again.

Run from the backend/ folder:

    python flyte_pipeline.py ../sample_docs/AI_ML_Interview_Prep.pdf
    python flyte_pipeline.py ../sample_docs/AI_ML_Interview_Prep.pdf --fail-classify 2
"""
import argparse
import os
import tempfile
import uuid
from datetime import timedelta
from pathlib import Path

import flyte

from app.core.config import settings
from app.services.classifier import classify_document
from app.services.parser import parse_document
from app.services.rag import index_document
import app.services.rag as rag

env = flyte.TaskEnvironment(name="document_intelligence")

_COUNTER = Path(tempfile.gettempdir()) / "flyte_demo_classify_attempts.txt"


def _simulate_rate_limit() -> None:
    """Demo only: make `classify` fail N times, like a Groq 429 error."""
    n = int(os.getenv("DEMO_FAIL_CLASSIFY", "0"))
    if n <= 0:
        return
    done = int(_COUNTER.read_text()) if _COUNTER.exists() else 0
    if done < n:
        _COUNTER.write_text(str(done + 1))
        raise RuntimeError(f"429 Too Many Requests (simulated Groq rate limit, failure {done + 1}/{n})")


@env.task
async def parse(file_path: str, doc_id: str) -> list[dict]:
    """Step 1: PDF/image -> pages (text, OCR fallback, tables, page image)."""
    print(f"[parse] START {file_path}  (this line must appear only ONCE)")
    settings.ensure_dirs()
    pages = parse_document(Path(file_path), doc_id)
    if not pages:
        raise flyte.errors.NonRecoverableError("No pages could be extracted from this document.")
    print(f"[parse] DONE {len(pages)} pages")
    return pages


@env.task(retries=3, timeout=flyte.Timeout(max_runtime=timedelta(minutes=5)))
async def classify(pages: list[dict]) -> dict:
    """Step 2: LLM classification (Groq LLaMA-3.3-70b) -> structured JSON."""
    print("[classify] attempt started")
    _simulate_rate_limit()
    full_text = "\n\n".join(p["text"] for p in pages)
    has_tables = any(p["has_tables"] for p in pages)
    is_scanned = full_text.strip() == "" or len(full_text) < 50
    result = classify_document(full_text, has_tables, is_scanned)
    print(f"[classify] DONE doc_type={result.get('doc_type')}")
    return result


@env.task(retries=2)
async def index(doc_id: str, doc_name: str, pages: list[dict]) -> int:
    """Step 3: chunks + embeddings -> ChromaDB, with page-level citation metadata."""
    print("[index] START")
    # Local embeddings (same model as the API), so the demo does not depend on
    # the Hugging Face Inference API (it answered 402 Payment Required).
    from langchain_huggingface import HuggingFaceEmbeddings
    rag._embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
    n_chunks = index_document(doc_id, doc_name, pages)
    print(f"[index] DONE {n_chunks} chunks")
    return n_chunks


@env.task
async def ingest_document(file_path: str) -> dict:
    """The whole pipeline: just tasks calling tasks, in plain Python."""
    doc_id = str(uuid.uuid4())
    doc_name = Path(file_path).name

    pages = await parse(file_path, doc_id)
    classification = await classify(pages)
    n_chunks = await index(doc_id, doc_name, pages)

    return {
        "doc_id": doc_id,
        "doc_name": doc_name,
        "page_count": len(pages),
        "classification": classification,
        "chunks_indexed": n_chunks,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="path to a PDF or image")
    ap.add_argument("--fail-classify", type=int, default=0,
                    help="demo: make classify fail N times before it succeeds")
    args = ap.parse_args()

    os.environ["DEMO_FAIL_CLASSIFY"] = str(args.fail_classify)
    _COUNTER.unlink(missing_ok=True)

    flyte.init()
    run = flyte.with_runcontext(mode="local").run(ingest_document, str(Path(args.file).resolve()))
    out = run.outputs()
    print("\n=== RESULT ===")
    print(getattr(out, "o0", out))
