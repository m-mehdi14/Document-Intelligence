"""Configuration for the Document Intelligence demo."""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App settings."""

    # Paths (relative to project root)
    project_root: Path = Path(__file__).resolve().parent.parent
    docs_path: Path = Path("sample_docs")
    index_path: Path = Path("data/chroma_db")
    uploads_path: Path = Path("data/uploads")

    # Embedding model (runs locally, no API key)
    embedding_model: str = "all-MiniLM-L6-v2"

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 128

    # RAG
    top_k: int = 5
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:latest"
    use_ollama: bool = True  # If False or Ollama unavailable, return retrieved chunks only

    @property
    def docs_dir(self) -> Path:
        return self.project_root / self.docs_path

    @property
    def index_dir(self) -> Path:
        return self.project_root / self.index_path

    @property
    def uploads_dir(self) -> Path:
        return self.project_root / self.uploads_path


settings = Settings()
