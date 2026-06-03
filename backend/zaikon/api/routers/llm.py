"""
API endpoints for LLM configuration management.
"""
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from zaikon.core.config import get_settings

router = APIRouter(prefix="/api/v1/llm", tags=["llm"])


class LLMConfigUpdate(BaseModel):
    """Schema for updating LLM configuration."""
    llm_use_provider: bool = Field(..., description="Whether to use LLM provider")
    llm_base_url: str = Field(..., description="Ollama server base URL")
    llm_model: str = Field(..., description="Model name to use")
    llm_temperature: float = Field(..., ge=0.0, le=2.0, description="Temperature parameter")
    llm_top_p: float = Field(..., ge=0.0, le=1.0, description="Top-p sampling")
    llm_max_tokens: int = Field(..., ge=256, le=8192, description="Maximum tokens")
    llm_context_window: int = Field(..., ge=2048, le=131072, description="Context window size")
    llm_system_prompt: str | None = Field(None, description="System prompt")


class LLMConfigResponse(BaseModel):
    """Schema for LLM configuration response."""
    llm_use_provider: bool
    llm_base_url: str
    llm_model: str
    llm_temperature: float
    llm_top_p: float
    llm_max_tokens: int
    llm_context_window: int
    llm_system_prompt: str | None


class EmbeddingConfigUpdate(BaseModel):
    """Schema for updating embedding configuration."""
    embedding_model: str = Field(..., description="Embedding model name")
    embedding_dimensions: int = Field(..., ge=128, le=4096, description="Embedding dimensions")
    embedding_batch_size: int = Field(..., ge=1, le=512, description="Batch size")
    embedding_device: str = Field(..., description="Device (cpu/cuda)")
    embedding_precision: str = Field(..., description="Precision (fp16/fp32)")


class EmbeddingConfigResponse(BaseModel):
    """Schema for embedding configuration response."""
    embedding_model: str
    embedding_dimensions: int
    embedding_batch_size: int
    embedding_device: str
    embedding_precision: str


class RerankerConfigUpdate(BaseModel):
    """Schema for updating reranker configuration."""
    reranker_model: str = Field(..., description="Reranker model name")
    reranker_batch_size: int = Field(..., ge=1, le=256, description="Batch size")
    reranker_device: str = Field(..., description="Device (cpu/cuda)")
    reranking_enabled: bool = Field(..., description="Enable reranking")
    reranking_top_n: int = Field(..., ge=1, le=50, description="Top N results to rerank")


class RerankerConfigResponse(BaseModel):
    """Schema for reranker configuration response."""
    reranker_model: str
    reranker_batch_size: int
    reranker_device: str
    reranking_enabled: bool
    reranking_top_n: int


class RAGConfigUpdate(BaseModel):
    """Schema for updating RAG configuration."""
    chunking_strategy: str = Field(..., description="Chunking strategy")
    chunk_size: int = Field(..., ge=100, le=2000, description="Chunk size")
    chunk_overlap: int = Field(..., ge=0, le=500, description="Chunk overlap")
    search_type: str = Field(..., description="Search type (hybrid/semantic/keyword)")
    search_semantic_weight: float = Field(..., ge=0.0, le=1.0, description="Semantic weight")
    search_bm25_weight: float = Field(..., ge=0.0, le=1.0, description="BM25 weight")
    search_top_k: int = Field(..., ge=1, le=100, description="Top K results")


class RAGConfigResponse(BaseModel):
    """Schema for RAG configuration response."""
    chunking_strategy: str
    chunk_size: int
    chunk_overlap: int
    search_type: str
    search_semantic_weight: float
    search_bm25_weight: float
    search_top_k: int


class OllamaModelInfo(BaseModel):
    """Schema for Ollama model information."""
    name: str
    size: int
    modified_at: str


@router.get("/config", response_model=LLMConfigResponse)
async def get_llm_config() -> dict[str, Any]:
    """
    Get current LLM configuration.
    
    Returns:
        Current LLM configuration settings
    """
    settings = get_settings()
    return {
        "llm_use_provider": settings.llm_use_provider,
        "llm_base_url": settings.llm_base_url,
        "llm_model": settings.llm_model,
        "llm_temperature": settings.llm_temperature,
        "llm_top_p": settings.llm_top_p,
        "llm_max_tokens": settings.llm_max_tokens,
        "llm_context_window": settings.llm_context_window,
        "llm_system_prompt": settings.llm_system_prompt,
    }


@router.put("/config", response_model=LLMConfigResponse)
async def update_llm_config(config: LLMConfigUpdate) -> dict[str, Any]:
    """
    Update LLM configuration.
    
    Args:
        config: New LLM configuration
        
    Returns:
        Updated LLM configuration
    """
    settings = get_settings()
    
    # Update settings
    settings.llm_use_provider = config.llm_use_provider
    settings.llm_base_url = config.llm_base_url
    settings.llm_model = config.llm_model
    settings.llm_temperature = config.llm_temperature
    settings.llm_top_p = config.llm_top_p
    settings.llm_max_tokens = config.llm_max_tokens
    settings.llm_context_window = config.llm_context_window
    settings.llm_system_prompt = config.llm_system_prompt
    
    return {
        "llm_use_provider": settings.llm_use_provider,
        "llm_base_url": settings.llm_base_url,
        "llm_model": settings.llm_model,
        "llm_temperature": settings.llm_temperature,
        "llm_top_p": settings.llm_top_p,
        "llm_max_tokens": settings.llm_max_tokens,
        "llm_context_window": settings.llm_context_window,
        "llm_system_prompt": settings.llm_system_prompt,
    }


@router.get("/ollama/models", response_model=list[OllamaModelInfo])
async def get_ollama_models(
    ollama_url: str = Query(..., description="Ollama server URL")
) -> list[dict[str, Any]]:
    """
    Get list of available models from Ollama server.
    
    Args:
        ollama_url: Ollama server URL
        
    Returns:
        List of available models
        
    Raises:
        HTTPException: If unable to connect to Ollama server
    """
    import httpx
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ollama_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            
            models = []
            for model in data.get("models", []):
                models.append({
                    "name": model.get("name", ""),
                    "size": model.get("size", 0),
                    "modified_at": model.get("modified_at", ""),
                })
            
            return models
            
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to connect to Ollama server: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching models: {str(e)}"
        ) from e

# Made with Bob


@router.get("/embedding/config", response_model=EmbeddingConfigResponse)
async def get_embedding_config() -> dict[str, Any]:
    """Get current embedding configuration."""
    settings = get_settings()
    return {
        "embedding_model": settings.embedding_model,
        "embedding_dimensions": settings.embedding_dimensions,
        "embedding_batch_size": settings.embedding_batch_size,
        "embedding_device": settings.embedding_device,
        "embedding_precision": settings.embedding_precision,
    }


@router.put("/embedding/config", response_model=EmbeddingConfigResponse)
async def update_embedding_config(config: EmbeddingConfigUpdate) -> dict[str, Any]:
    """Update embedding configuration."""
    settings = get_settings()
    settings.embedding_model = config.embedding_model
    settings.embedding_dimensions = config.embedding_dimensions
    settings.embedding_batch_size = config.embedding_batch_size
    settings.embedding_device = config.embedding_device
    settings.embedding_precision = config.embedding_precision
    
    return {
        "embedding_model": settings.embedding_model,
        "embedding_dimensions": settings.embedding_dimensions,
        "embedding_batch_size": settings.embedding_batch_size,
        "embedding_device": settings.embedding_device,
        "embedding_precision": settings.embedding_precision,
    }


@router.get("/reranker/config", response_model=RerankerConfigResponse)
async def get_reranker_config() -> dict[str, Any]:
    """Get current reranker configuration."""
    settings = get_settings()
    return {
        "reranker_model": settings.reranker_model,
        "reranker_batch_size": settings.reranker_batch_size,
        "reranker_device": settings.reranker_device,
        "reranking_enabled": settings.reranking_enabled,
        "reranking_top_n": settings.reranking_top_n,
    }


@router.put("/reranker/config", response_model=RerankerConfigResponse)
async def update_reranker_config(config: RerankerConfigUpdate) -> dict[str, Any]:
    """Update reranker configuration."""
    settings = get_settings()
    settings.reranker_model = config.reranker_model
    settings.reranker_batch_size = config.reranker_batch_size
    settings.reranker_device = config.reranker_device
    settings.reranking_enabled = config.reranking_enabled
    settings.reranking_top_n = config.reranking_top_n
    
    return {
        "reranker_model": settings.reranker_model,
        "reranker_batch_size": settings.reranker_batch_size,
        "reranker_device": settings.reranker_device,
        "reranking_enabled": settings.reranking_enabled,
        "reranking_top_n": settings.reranking_top_n,
    }


@router.get("/rag/config", response_model=RAGConfigResponse)
async def get_rag_config() -> dict[str, Any]:
    """Get current RAG configuration."""
    settings = get_settings()
    return {
        "chunking_strategy": settings.chunking_strategy,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
        "search_type": settings.search_type,
        "search_semantic_weight": settings.search_semantic_weight,
        "search_bm25_weight": settings.search_bm25_weight,
        "search_top_k": settings.search_top_k,
    }


@router.put("/rag/config", response_model=RAGConfigResponse)
async def update_rag_config(config: RAGConfigUpdate) -> dict[str, Any]:
    """Update RAG configuration."""
    settings = get_settings()
    settings.chunking_strategy = config.chunking_strategy
    settings.chunk_size = config.chunk_size
    settings.chunk_overlap = config.chunk_overlap
    settings.search_type = config.search_type
    settings.search_semantic_weight = config.search_semantic_weight
    settings.search_bm25_weight = config.search_bm25_weight
    settings.search_top_k = config.search_top_k
    
    return {
        "chunking_strategy": settings.chunking_strategy,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
        "search_type": settings.search_type,
        "search_semantic_weight": settings.search_semantic_weight,
        "search_bm25_weight": settings.search_bm25_weight,
        "search_top_k": settings.search_top_k,
    }
