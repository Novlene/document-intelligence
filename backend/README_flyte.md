# Document Intelligence on Flyte 2

The ingestion pipeline of [Document Intelligence](../README.md) (OCR, LLM classification, indexing), rebuilt as Flyte 2 tasks.

## Why

In the FastAPI version, `process_document` runs parse, classify and index in one function. If the LLM call fails
(Groq rate limit, timeout), the document is marked `FAILED` and must be re-processed from the OCR step.

With Flyte 2, each step is its own task with its own retries and its own saved output:

| Task | Reuses | Retries |
|---|---|---|
| `parse` | `parser.parse_document` (pdfplumber + Tesseract OCR fallback) | none (fails fast if no pages) |
| `classify` | `classifier.classify_document` (Groq LLM, JSON output) | 3, 5 min timeout |
| `index` | `rag.index_document` (ChromaDB, page-level citation metadata) | 2 |
| `ingest_document` | tasks calling tasks, plain Python | |

If `classify` fails, only `classify` is retried. The OCR result is kept and OCR is not run again.

## Setup

```
pip install flyte sentence-transformers
```

Put these in `backend/.env`:

```
GROQ_API_KEY=your_groq_key
LLM_MODEL=openai/gpt-oss-120b
```

- `GROQ_API_KEY`: needed by `classify`.
- `LLM_MODEL`: the Groq model used by `classify`. Groq removed `llama-3.3-70b-versatile` on 16 August 2026
  (404 `model_not_found`), so I use `openai/gpt-oss-120b`. No code change is needed, only this variable.
- No Hugging Face key is needed for this pipeline: the `index` task computes embeddings locally
  (`HuggingFaceEmbeddings`, model `all-MiniLM-L6-v2`, the same model as the API version). The first run downloads the model.
  I switched to local embeddings because the Hugging Face Inference API answered `402 Payment Required`.

## Run (from `backend/`)

```
python flyte_pipeline.py ../sample_docs/AI_ML_Interview_Prep.pdf
```

## Failure demo

```
python flyte_pipeline.py ../sample_docs/AI_ML_Interview_Prep.pdf --fail-classify 2
```

`classify` fails twice with a simulated `429 Too Many Requests`, is retried, then succeeds.
`[parse] START` appears only once, so OCR is not run again. The run ends with the final result
(`doc_id`, `page_count`, `classification`, `chunks_indexed`). See `demo_run_log.txt`.

On Windows, if printing the result fails with a `UnicodeEncodeError`, run `set PYTHONIOENCODING=utf-8` first.

## Notes

- Runs in Flyte local mode only. I have not run it on a Kubernetes cluster.
- The failure is simulated (a counter in `flyte_pipeline.py`), not a real Groq outage.
- `demo_run_log.txt` is a real run: real OCR on a 4-page PDF, real Groq call, local embeddings, ChromaDB (13 chunks indexed).
  Only the `classify` failures are simulated.
- The FastAPI app is unchanged. This pipeline reuses its code as is.
