"""Local embeddings and ChromaDB vector store."""
from pathlib import Path
import logging
from typing import Any

from backend.config import settings
from backend.ingest import DocumentChunk, iter_documents

logger = logging.getLogger(__name__)

_embedding_model = None
_collection = None


def get_embedding_model():
    """Lazy-load sentence-transformers model (runs 100% locally)."""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer(settings.embedding_model)
    return _embedding_model


def get_client():
    """ChromaDB persistent client."""
    import chromadb
    index_dir = settings.index_dir
    index_dir.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(index_dir))


def get_collection(force_new: bool = False):
    """Get or create ChromaDB persistent collection. If force_new, reset collection."""
    global _collection
    client = get_client()
    if force_new:
        try:
            client.delete_collection("mol_documents")
        except Exception:
            pass
        _collection = None
    if _collection is not None:
        return _collection
    _collection = client.get_or_create_collection(
        name="mol_documents",
        metadata={"description": "MOL Document Intelligence - On-Prem RAG"},
    )
    return _collection


def _chunk_to_metadata(chunk: DocumentChunk) -> dict[str, str | None]:
    return {
        "source_path": chunk.source_path,
        "source_name": chunk.source_name,
        "page_or_sheet": chunk.page_or_sheet,
        "last_modified": chunk.last_modified,
        "folder_tag": chunk.folder_tag,
        "doc_type": chunk.doc_type,
    }


def index_documents(docs_root: Path | None = None) -> dict[str, Any]:
    """Ingest from docs_root (default: settings.docs_dir), embed, and add to ChromaDB. Returns stats."""
    coll = get_collection(force_new=True)
    model = get_embedding_model()
    ids = []
    documents = []
    metadatas = []

    count = 0
    for chunk in iter_documents(docs_root):
        count += 1
        ids.append(f"chunk_{count}_{hash(chunk.source_path) % 10**8}")
        documents.append(chunk.content)
        metadatas.append(_chunk_to_metadata(chunk))

    if not documents:
        return {"chunks_indexed": 0, "message": "No documents found to index."}

    # ChromaDB has a 41k limit per add; batch if needed
    batch_size = 500
    for i in range(0, len(documents), batch_size):
        batch_ids = ids[i : i + batch_size]
        batch_docs = documents[i : i + batch_size]
        batch_meta = metadatas[i : i + batch_size]
        embeddings = model.encode(batch_docs).tolist()
        coll.add(ids=batch_ids, documents=batch_docs, metadatas=batch_meta, embeddings=embeddings)

    return {"chunks_indexed": len(documents), "message": "Indexing complete."}


def search(query: str, top_k: int | None = None, folder: str | None = None, doc_type: str | None = None) -> list[dict]:
    """Semantic search. Optional filter by folder_tag or doc_type."""
    top_k = top_k or settings.top_k
    coll = get_collection()
    model = get_embedding_model()
    q_embedding = model.encode([query]).tolist()

    where = None
    if folder or doc_type:
        where = {}
        if folder:
            where["folder_tag"] = folder
        if doc_type:
            where["doc_type"] = doc_type

    result = coll.query(
        query_embeddings=q_embedding,
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    out = []
    if result["ids"] and result["ids"][0]:
        for i, doc_id in enumerate(result["ids"][0]):
            out.append({
                "content": result["documents"][0][i],
                "metadata": result["metadatas"][0][i] or {},
                "distance": result["distances"][0][i] if result.get("distances") else None,
            })
    return out
