import json
import uuid
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.models.schemas import ProcessingStatus, DocumentRecord, DocumentClassification
from app.services.parser import parse_document
from app.services.classifier import classify_document
from app.services.rag import index_document

# In-memory store (simple, file-backed for persistence)
_documents: dict[str, DocumentRecord] = {}
_store_file = settings.upload_dir / "documents.json"


def _load_store():
    global _documents
    if _store_file.exists():
        data = json.loads(_store_file.read_text(encoding="utf-8"))
        for doc_id, rec in data.items():
            _documents[doc_id] = DocumentRecord(**rec)


def _save_store():
    data = {doc_id: rec.model_dump() for doc_id, rec in _documents.items()}
    _store_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_document(doc_id: str) -> DocumentRecord | None:
    return _documents.get(doc_id)


def list_documents() -> list[DocumentRecord]:
    return list(_documents.values())


def create_document_record(filename: str, original_name: str) -> DocumentRecord:
    doc_id = str(uuid.uuid4())
    record = DocumentRecord(
        doc_id=doc_id,
        filename=filename,
        original_name=original_name,
        status=ProcessingStatus.PENDING,
        created_at=datetime.utcnow().isoformat(),
    )
    _documents[doc_id] = record
    _save_store()
    return record


def process_document(doc_id: str, file_path: Path):
    """Full pipeline: parse -> classify -> index. Updates status as it goes."""
    record = _documents[doc_id]

    try:
        # 1. Parse
        record.status = ProcessingStatus.PARSING
        _save_store()

        pages = parse_document(file_path, doc_id)
        record.page_count = len(pages)

        if not pages:
            raise ValueError("No pages could be extracted from this document.")

        # 2. Classify
        record.status = ProcessingStatus.CLASSIFYING
        _save_store()

        full_text = "\n\n".join(p["text"] for p in pages)
        has_tables = any(p["has_tables"] for p in pages)
        is_scanned = full_text.strip() == "" or len(full_text) < 50

        classification_dict = classify_document(full_text, has_tables, is_scanned)
        record.classification = DocumentClassification(**classification_dict)

        # 3. Index for RAG
        record.status = ProcessingStatus.INDEXING
        _save_store()

        index_document(doc_id, record.original_name, pages)

        record.status = ProcessingStatus.INDEXED
        _save_store()

    except Exception as e:
        record.status = ProcessingStatus.FAILED
        record.error = str(e)
        _save_store()


_load_store()