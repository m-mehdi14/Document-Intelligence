"""FastAPI app: RAG API + static frontend for Document Intelligence demo."""
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.config import settings
from backend.embed import index_documents, search, get_collection
from backend.rag import answer_query


class QueryRequest(BaseModel):
    query: str
    top_k: int | None = None
    folder: str | None = None
    doc_type: str | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]
    used_llm: bool


class IndexResponse(BaseModel):
    chunks_indexed: int
    message: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure data dirs exist; optionally run indexing on startup if index empty."""
    settings.index_dir.mkdir(parents=True, exist_ok=True)
    settings.docs_dir.mkdir(parents=True, exist_ok=True)
    try:
        coll = get_collection()
        if coll.count() == 0 and settings.docs_dir.exists():
            index_documents()
    except Exception:
        pass
    yield
    # shutdown
    pass


app = FastAPI(
    title="MOL Document Intelligence (On-Prem RAG Demo)",
    description="Local AI-powered document search and Q&A for enterprise documents.",
    version="1.0.0",
    lifespan=lifespan,
)


# ----- API -----

@app.post("/api/query", response_model=QueryResponse)
def api_query(req: QueryRequest) -> QueryResponse:
    """Natural language query; returns answer and source citations."""
    result = answer_query(
        query=req.query,
        top_k=req.top_k,
        folder=req.folder,
        doc_type=req.doc_type,
    )
    return QueryResponse(**result)


@app.get("/api/search")
def api_search(q: str, top_k: int = 5, folder: str | None = None, doc_type: str | None = None):
    """Semantic search only (no LLM). Returns list of matching chunks with metadata."""
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Query 'q' is required.")
    return {"results": search(q, top_k=top_k, folder=folder, doc_type=doc_type)}


@app.post("/api/index", response_model=IndexResponse)
def api_index():
    """Re-run document ingestion and indexing from the configured docs folder."""
    stats = index_documents()
    return IndexResponse(**stats)


@app.get("/api/filters")
def api_filters():
    """Return distinct folder_tag and doc_type for filter dropdowns."""
    try:
        coll = get_collection()
        # Chroma doesn't have distinct; we'd need to scan. Return common demo values.
        return {
            "folders": ["Safety", "Operations", "Environmental", "SOPs", "Reports"],
            "doc_types": ["pdf", "docx", "xlsx", "pptx", "txt"],
        }
    except Exception:
        return {"folders": [], "doc_types": []}


@app.get("/api/health")
def health():
    return {"status": "ok", "message": "On-Prem Document Intelligence API"}


# ----- Static frontend -----

frontend_dir = settings.project_root / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.get("/")
def index():
    """Serve the intranet portal."""
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Document Intelligence API. Mount frontend at / or use /api/query."}


@app.get("/health")
def health_root():
    return health()
