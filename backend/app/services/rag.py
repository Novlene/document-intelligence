from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.core.config import settings

_embeddings = None
_vectorstore = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
    return _embeddings


def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(
            collection_name="documents",
            embedding_function=get_embeddings(),
            persist_directory=str(settings.chroma_dir),
        )
    return _vectorstore


def index_document(doc_id: str, doc_name: str, pages: list[dict]):
    """Split pages into chunks and index them in ChromaDB with citation metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
    )

    documents = []
    for page in pages:
        if not page["text"].strip():
            continue

        chunks = splitter.split_text(page["text"])
        for chunk in chunks:
            documents.append(Document(
                page_content=chunk,
                metadata={
                    "doc_id": doc_id,
                    "doc_name": doc_name,
                    "page_num": page["page_num"],
                    "page_image_path": page["image_path"],
                }
            ))

    if documents:
        vectorstore = get_vectorstore()
        vectorstore.add_documents(documents)

    return len(documents)


def query_documents(question: str, doc_ids: list[str] | None = None, k: int = 5):
    """Retrieve relevant chunks and generate an answer with citations."""
    vectorstore = get_vectorstore()

    search_kwargs = {"k": k}
    if doc_ids:
        search_kwargs["filter"] = {"doc_id": {"$in": doc_ids}}

    retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)
    docs = retriever.invoke(question)

    if not docs:
        return {
            "answer": "I couldn't find any relevant information in the indexed documents to answer this question.",
            "citations": [],
            "sources_found": False,
        }

    context_parts = []
    citations = []
    for doc in docs:
        context_parts.append(
            f"[Source: {doc.metadata['doc_name']}, Page {doc.metadata['page_num']}]\n{doc.page_content}"
        )
        citations.append({
            "doc_id": doc.metadata["doc_id"],
            "doc_name": doc.metadata["doc_name"],
            "page_num": doc.metadata["page_num"],
            "chunk_text": doc.page_content[:300],
            "page_image_path": doc.metadata["page_image_path"],
        })

    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""You are a helpful document analysis assistant. Answer the user's question based ONLY on the provided context from documents. Be concise and accurate. If the context doesn't contain enough information, say so.

Context from documents:
{context}

Question: {question}

Answer:"""

    llm = ChatGroq(
        model=settings.llm_model,
        groq_api_key=settings.groq_api_key,
        temperature=0,
    )

    response = llm.invoke(prompt)

    return {
        "answer": response.content.strip(),
        "citations": citations,
        "sources_found": True,
    }