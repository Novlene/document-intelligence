from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PARSING = "parsing"
    CLASSIFYING = "classifying"
    INDEXING = "indexing"
    INDEXED = "indexed"
    FAILED = "failed"


class PageData(BaseModel):
    page_num: int
    text: str
    image_path: str
    has_tables: bool = False
    table_data: list[dict] = []


class DocumentClassification(BaseModel):
    doc_type: str
    topic: str
    language: str
    sensitivity: str
    has_tables: bool
    has_handwriting: bool
    has_images: bool
    is_scanned: bool
    summary: str
    key_entities: list[str]
    tags: list[str]


class DocumentRecord(BaseModel):
    doc_id: str
    filename: str
    original_name: str
    status: ProcessingStatus = ProcessingStatus.PENDING
    page_count: int = 0
    classification: Optional[DocumentClassification] = None
    error: Optional[str] = None
    created_at: str = ""


class Citation(BaseModel):
    doc_id: str
    doc_name: str
    page_num: int
    chunk_text: str
    page_image_path: str


class ChatMessage(BaseModel):
    role: str
    content: str
    citations: list[Citation] = []


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    doc_ids: Optional[list[str]] = None


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    sources_found: bool


class UploadResponse(BaseModel):
    doc_id: str
    filename: str
    status: ProcessingStatus


class StatusResponse(BaseModel):
    doc_id: str
    status: ProcessingStatus
    page_count: int
    classification: Optional[DocumentClassification] = None
    error: Optional[str] = None