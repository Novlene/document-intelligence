import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.security import verify_api_key, limiter
from app.models.schemas import (
    ChatRequest, ChatResponse, UploadResponse, StatusResponse, ProcessingStatus
)
from app.services.pipeline import (
    create_document_record, process_document, get_document, list_documents
)
from app.services.rag import query_documents

router = APIRouter()


@router.post("/upload", response_model=UploadResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.allowed_ext_list:
        raise HTTPException(400, f"File type {ext} not allowed. Allowed: {settings.allowed_ext_list}")

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.max_file_size_mb:
        raise HTTPException(400, f"File too large ({size_mb:.1f}MB). Max: {settings.max_file_size_mb}MB")

    record = create_document_record(filename="", original_name=file.filename)

    saved_filename = f"{record.doc_id}{ext}"
    file_path = settings.upload_dir / saved_filename
    file_path.write_bytes(contents)
    record.filename = saved_filename

    background_tasks.add_task(process_document, record.doc_id, file_path)

    return UploadResponse(doc_id=record.doc_id, filename=file.filename, status=record.status)


@router.post("/upload/bulk", dependencies=[Depends(verify_api_key)])
@limiter.limit("5/minute")
async def upload_bulk(
    request: Request,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
):
    results = []
    for file in files:
        ext = Path(file.filename).suffix.lower()
        if ext not in settings.allowed_ext_list:
            results.append({"filename": file.filename, "error": f"Type {ext} not allowed"})
            continue

        contents = await file.read()
        size_mb = len(contents) / (1024 * 1024)
        if size_mb > settings.max_file_size_mb:
            results.append({"filename": file.filename, "error": "File too large"})
            continue

        record = create_document_record(filename="", original_name=file.filename)
        saved_filename = f"{record.doc_id}{ext}"
        file_path = settings.upload_dir / saved_filename
        file_path.write_bytes(contents)
        record.filename = saved_filename

        background_tasks.add_task(process_document, record.doc_id, file_path)

        results.append({"doc_id": record.doc_id, "filename": file.filename, "status": record.status})

    return {"results": results}


@router.get("/status/{doc_id}", response_model=StatusResponse, dependencies=[Depends(verify_api_key)])
async def get_status(doc_id: str):
    record = get_document(doc_id)
    if not record:
        raise HTTPException(404, "Document not found")

    return StatusResponse(
        doc_id=record.doc_id,
        status=record.status,
        page_count=record.page_count,
        classification=record.classification,
        error=record.error,
    )


@router.get("/documents", dependencies=[Depends(verify_api_key)])
async def get_all_documents():
    docs = list_documents()
    return {
        "documents": [
            {
                "doc_id": d.doc_id,
                "filename": d.original_name,
                "status": d.status,
                "page_count": d.page_count,
                "classification": d.classification,
            }
            for d in docs
        ]
    }


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit("20/minute")
async def chat(request: Request, body: ChatRequest):
    result = query_documents(body.message, doc_ids=body.doc_ids)
    return ChatResponse(**result)

@router.get("/pages/{filename}")
async def get_page_image(filename: str):
    file_path = settings.pages_dir / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(404, "Page image not found")
    # Prevent path traversal
    if not str(file_path.resolve()).startswith(str(settings.pages_dir.resolve())):
        raise HTTPException(403, "Forbidden")
    return FileResponse(file_path)