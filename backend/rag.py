"""RAG: retrieve chunks and optionally generate answer via local Ollama."""
import httpx
from backend.config import settings
from backend.embed import search


def _call_ollama(prompt: str, timeout: float = 60.0) -> str | None:
    """Call local Ollama API. Returns None if unavailable."""
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/generate",
                json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
            )
            if r.status_code != 200:
                return None
            data = r.json()
            return data.get("response", "").strip()
    except Exception:
        return None


def build_context(chunks: list[dict]) -> str:
    """Build context string from retrieved chunks with source labels."""
    parts = []
    for i, c in enumerate(chunks, 1):
        meta = c.get("metadata") or {}
        src = meta.get("source_name", "Unknown")
        page = meta.get("page_or_sheet", "")
        parts.append(f"[Source {i}: {src}" + (f", page/sheet {page}" if page else "") + "]\n" + c.get("content", ""))
    return "\n\n---\n\n".join(parts)


def answer_query(query: str, top_k: int | None = None, folder: str | None = None, doc_type: str | None = None) -> dict:
    """
    RAG: retrieve relevant chunks, then (if Ollama available) generate answer.
    Returns: { "answer": str, "sources": list[dict], "used_llm": bool }.
    """
    chunks = search(query, top_k=top_k, folder=folder, doc_type=doc_type)
    sources = []
    for c in chunks:
        meta = c.get("metadata") or {}
        sources.append({
            "source_name": meta.get("source_name"),
            "source_path": meta.get("source_path"),
            "page_or_sheet": meta.get("page_or_sheet"),
            "folder_tag": meta.get("folder_tag"),
            "content_preview": (c.get("content") or "")[:200] + ("..." if len(c.get("content") or "") > 200 else ""),
        })

    if not chunks:
        return {
            "answer": "No relevant documents were found for your query. Try rephrasing or expanding the search.",
            "sources": [],
            "used_llm": False,
        }

    context = build_context(chunks)
    prompt = f"""You are an internal document assistant for MOL Group. Answer ONLY using the following document excerpts. If the excerpts do not contain enough information, say so. Do not make up information. Cite sources by number (e.g. [Source 1]).

Document excerpts:
{context}

Question: {query}

Answer (based only on the excerpts above):"""

    answer = _call_ollama(prompt) if settings.use_ollama else None
    if answer:
        return {"answer": answer, "sources": sources, "used_llm": True}
    # Fallback: return summarized context as answer
    fallback = "The following excerpts from your documents are most relevant:\n\n" + context
    return {"answer": fallback, "sources": sources, "used_llm": False}
