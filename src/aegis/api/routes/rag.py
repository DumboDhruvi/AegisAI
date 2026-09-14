"""FastAPI routes for RAG application (Ingestion and Querying)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from aegis.domain.models.rag import Document, RagResponse
from aegis.services.rag_pipeline import RagPipeline

router = APIRouter(prefix="/rag", tags=["RAG Application"])

# Global singleton pipeline instance for the application lifecycle
default_pipeline = RagPipeline()


class DocumentInput(BaseModel):
    """Input representation of a document to ingest."""

    id: str = Field(..., description="Unique document identifier")
    content: str = Field(..., description="Document text content")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata dictionary for the document"
    )


class IngestRequest(BaseModel):
    """Request payload for ingesting multiple documents."""

    documents: list[DocumentInput] = Field(
        ..., description="List of documents to chunk, embed, and index"
    )


class IngestResponse(BaseModel):
    """Response returned after ingesting documents."""

    status: str
    chunks_indexed: int
    total_stored_chunks: int


class QueryRequest(BaseModel):
    """Request payload for executing a RAG query."""

    question: str = Field(..., description="The query to search and answer")
    top_k: int = Field(default=3, ge=1, le=20, description="Max document chunks to retrieve")
    min_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Minimum similarity threshold"
    )


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest documents into the RAG vector store",
    description="Parses, chunks, embeds, and indexes documents for semantic retrieval.",
)
def ingest_documents(request: IngestRequest) -> IngestResponse:
    """Ingest a batch of documents into the RAG vector store."""
    if not request.documents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot ingest an empty document list.",
        )

    docs = [Document(id=d.id, content=d.content, metadata=d.metadata) for d in request.documents]

    indexed_count = default_pipeline.ingest_documents(docs)

    return IngestResponse(
        status="success",
        chunks_indexed=indexed_count,
        total_stored_chunks=default_pipeline.vector_store.count(),
    )


@router.post(
    "/query",
    response_model=RagResponse,
    status_code=status.HTTP_200_OK,
    summary="Query the RAG pipeline",
    description="Retrieves relevant document chunks and synthesizes an answer using the LLM.",
)
def query_rag(request: QueryRequest) -> RagResponse:
    """Execute a RAG query with semantic retrieval and answer generation."""
    question = request.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    response = default_pipeline.query(
        question=question,
        top_k=request.top_k,
        min_score=request.min_score,
    )
    return response


@router.get(
    "/stats",
    status_code=status.HTTP_200_OK,
    summary="Get RAG vector store statistics",
)
def get_rag_stats() -> dict[str, Any]:
    """Return current vector index statistics."""
    return {
        "total_chunks": default_pipeline.vector_store.count(),
    }
