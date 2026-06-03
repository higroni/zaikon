"""Application configuration.

Configuration keys mirror docs/master/MASTER_CONFIG.md.
"""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ZAIKON_", env_file=".env")

    env: str = "development"
    log_level: str = "INFO"
    api_host: str = "127.0.0.1"
    api_port: int = 8100

    base_dir: Path = Path(__file__).resolve().parents[3]
    database_url: str = "sqlite:///./zaikon.db"
    artifact_dir: Path = Path("./data/artifacts")
    upload_dir: Path = Path("./data/uploads")

    default_language: str = "sr"
    enable_cyrillic_latin_normalization: bool = True
    parser_min_confidence: float = 0.70

    import_allowed_extensions: str = ".pdf,.docx,.txt"
    import_recursive: bool = True
    import_skip_duplicates: bool = True
    import_max_file_mb: int = 100

    retrieval_top_k: int = 20
    retrieval_vector_weight: float = 0.45
    retrieval_keyword_weight: float = 0.35
    retrieval_graph_weight: float = 0.20
    reranking_enabled: bool = True
    reranking_top_n: int = 8

    vector_backend: str = "qdrant"
    qdrant_url: str = "http://localhost:6333"
    qdrant_path: Path | None = Path("./data/qdrant_storage")
    
    # Embedding Model Settings
    embedding_model: str = "BAAI/bge-m3"
    embedding_dimensions: int = 1024
    embedding_batch_size: int = 128
    embedding_device: str = "cuda"
    embedding_precision: str = "fp16"
    
    keyword_backend: str = "postgres_fts"

    # LLM Settings
    llm_provider: str = "ollama"
    llm_use_provider: bool = False
    llm_base_url: str = "http://localhost:11434"
    llm_model: str = "mistral:latest"
    llm_temperature: float = 0.1
    llm_top_p: float = 0.9
    llm_max_tokens: int = 2048
    llm_context_window: int = 32768
    llm_system_prompt: str | None = None
    
    # Reranker Settings
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    reranker_batch_size: int = 32
    reranker_device: str = "cuda"
    
    # RAG Chunking Settings
    chunking_strategy: str = "semantic"
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    # RAG Search Settings
    search_type: str = "hybrid"
    search_semantic_weight: float = 0.7
    search_bm25_weight: float = 0.3
    search_top_k: int = 10

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @property
    def allowed_extensions(self) -> set[str]:
        return {
            item.strip().lower()
            for item in self.import_allowed_extensions.split(",")
            if item.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
