# Document Intelligence — Agentic RAG System
## Live Demo
- Frontend: https://document-intelligence-jet.vercel.app
- Backend API: https://document-intelligence-p35u.onrender.com/docs

Note: upload the documents in sample_docs/ via Bulk Upload to populate the knowledge base (backend storage is ephemeral on free tier).

A full-stack web app that ingests messy real-world documents (scanned PDFs, handwritten pages, image-heavy reports, tables), classifies them with an LLM, and powers a chatbot that answers questions with grounded citations showing the exact source page.

## Architecture
frontend (Next.js 16 + TypeScript + Tailwind)

↕ REST API

backend (FastAPI + Python)

├── Parser: pdfplumber + pdf2image + pytesseract (OCR)

├── Classifier: Groq LLaMA-3.3-70b → structured JSON

├── RAG: ChromaDB + HuggingFace embeddings + LangChain

└── Storage: local filesystem + ChromaDB
## Features

- Upload single or bulk documents (PDF, images, text)
- Automatic parsing with OCR fallback for scanned pages
- LLM classification: type, topic, sensitivity, language, entities
- Agentic RAG with inline citations (document + page number)
- Page thumbnails clickable to full-size view
- Real-time processing status per file

## Setup

### Prerequisites
- Python 3.11 64-bit
- Node.js 18+
- Tesseract OCR
- Poppler

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

Create `.env`:'@
GROQ_API_KEY=your_groq_api_key
API_KEY=your_api_key
SECRET_KEY=your_secret_key

Then run:

    uvicorn app.main:app --reload --port 8000

### Frontend

Create .env.local:

    NEXT_PUBLIC_API_URL=http://localhost:8000/api
    NEXT_PUBLIC_API_KEY=your_api_key

Then run:

    cd frontend
    npm install
    npm run dev

Open http://localhost:3000

## Sample Documents

5 sample documents are in sample_docs/. Upload them via Bulk Upload page on first run.

## Security Decisions

### Implemented
- API Key authentication on all endpoints via x-api-key header
- File type validation (PDF, PNG, JPG, TIFF only)
- File size limit (50MB max)
- Path traversal prevention
- Rate limiting (upload: 10/min, chat: 20/min)
- No secrets in code — all keys via environment variables

### Considered but skipped
- Document encryption at rest
- Per-user JWT authentication
- Virus scanning of uploads

### Would add with more time
- JWT-based user auth with document ownership
- AES-256 encryption for stored files
- ClamAV malware scanning
- Full audit trail
- HTTPS enforcement
