"""Domain models for RAG (Retrieval-Augmented Generation)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Document(BaseModel):
    """Represents an ingested source document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(..., description="Unique document identifier")
    content: str = Field(..., description="Full text content of the document")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary document metadata (e.g. source URL, title, author, timestamp)",
    )

    @field_validator("id", "content")
    @classmethod
    def validate_non_empty(cls, value: str, info: Any) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError(f"Field '{info.field_name}' must not be empty.")
        return stripped


class DocumentChunk(BaseModel):
    """Represents an atomic chunk of a document stored for vector retrieval."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    chunk_id: str = Field(..., description="Unique chunk identifier (e.g. doc-1#c0)")
    document_id: str = Field(..., description="Identifier of the originating document")
    content: str = Field(..., description="Text segment contained in this chunk")
    chunk_index: int = Field(..., ge=0, description="0-indexed position within the document")
    start_char: int = Field(..., ge=0, description="Start character offset in parent document")
    end_char: int = Field(..., ge=0, description="End character offset in parent document")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Chunk-level metadata inherited from document or added during chunking",
    )

    @field_validator("chunk_id", "document_id", "content")
    @classmethod
    def validate_non_empty(cls, value: str, info: Any) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError(f"Field '{info.field_name}' must not be empty.")
        return stripped


class RetrievedDocument(BaseModel):
    """Represents a retrieved document chunk with its similarity score."""

    model_config = ConfigDict(frozen=True)

    chunk: DocumentChunk = Field(..., description="The matching document chunk")
    similarity_score: float = Field(
        ...,
        description="Cosine similarity or relevance score (typically 0.0 to 1.0)",
    )


class RagResponse(BaseModel):
    """Standardized response from the RAG application pipeline.

    Must contain:
    - answer
    - retrieved documents
    - metadata / sources
    """

    model_config = ConfigDict(frozen=True)

    answer: str = Field(..., description="Generated answer from the LLM")
    retrieved_documents: list[RetrievedDocument] = Field(
        default_factory=list,
        description="Exact document chunks retrieved and injected as context",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metadata: model name, latency_seconds, source URLs, token counts",
    )

    @property
    def sources(self) -> list[str]:
        """Convenience property extracting distinct document sources."""
        collected: set[str] = set()
        for item in self.retrieved_documents:
            source = item.chunk.metadata.get("source") or item.chunk.document_id
            if source:
                collected.add(str(source))
        return sorted(list(collected))
