"""Data models for Wiki Mode."""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class WikiConfig(BaseModel):
    """Configuration for wiki generation."""
    output_dir: Path = Field(default=Path("wiki"))
    collection_name: str = Field(default="praxis")
    chroma_path: str = Field(default="data/chroma")
    embedding_model: str = Field(default="nomic-embed-text")
    ollama_url: str = Field(default="http://localhost:11434")
    llm_model: str = Field(default="claude-sonnet-4-20250514")
    max_chunks_per_page: int = Field(default=10)
    min_similarity: float = Field(default=0.3)


class WikiPage(BaseModel):
    """A single wiki page representing one concept."""
    slug: str
    title: str
    content: str
    sources: list[str] = Field(default_factory=list)
    layers: list[str] = Field(default_factory=list)
    links_to: list[str] = Field(default_factory=list)
    linked_from: list[str] = Field(default_factory=list)
    chunk_ids: list[str] = Field(default_factory=list)
    generation_timestamp: Optional[str] = None


class ConceptCluster(BaseModel):
    """A cluster of related chunks representing a single concept."""
    concept_name: str
    slug: str
    chunk_ids: list[str] = Field(default_factory=list)
    chunks: list[dict] = Field(default_factory=list)
    layer_sources: list[str] = Field(default_factory=list)
