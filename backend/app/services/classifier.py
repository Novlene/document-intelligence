import json
from langchain_groq import ChatGroq
from app.core.config import settings

CLASSIFICATION_PROMPT = """You are a document classification system. Analyze the following document text and return ONLY a valid JSON object (no markdown, no preamble, no explanation) with this exact structure:

{{
  "doc_type": "invoice|contract|report|letter|form|resume|presentation|academic|other",
  "topic": "short topic description",
  "language": "detected language (ISO code, e.g. en, fr, ar)",
  "sensitivity": "public|internal|confidential",
  "has_tables": true/false,
  "has_handwriting": true/false,
  "has_images": true/false,
  "is_scanned": true/false,
  "summary": "2-3 sentence summary of the document content",
  "key_entities": ["list", "of", "names", "orgs", "dates", "found"],
  "tags": ["list", "of", "relevant", "tags"]
}}

Document text (first pages):
---
{text}
---

Return ONLY the JSON object."""


def classify_document(full_text: str, has_tables: bool, is_scanned: bool) -> dict:
    llm = ChatGroq(
        model=settings.llm_model,
        groq_api_key=settings.groq_api_key,
        temperature=0,
    )

    # Limit text to avoid token overflow
    truncated_text = full_text[:8000]

    prompt = CLASSIFICATION_PROMPT.format(text=truncated_text)

    response = llm.invoke(prompt)
    content = response.content.strip()

    # Strip markdown code fences if present
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        result = {
            "doc_type": "other",
            "topic": "unknown",
            "language": "unknown",
            "sensitivity": "internal",
            "has_tables": has_tables,
            "has_handwriting": False,
            "has_images": False,
            "is_scanned": is_scanned,
            "summary": "Classification failed, manual review needed.",
            "key_entities": [],
            "tags": [],
        }

    # Override with ground-truth values from parser
    result["has_tables"] = has_tables
    result["is_scanned"] = is_scanned

    return result