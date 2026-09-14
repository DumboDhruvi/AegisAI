"""Unit tests for the RagPipeline service."""

from __future__ import annotations

import pytest

from aegis.domain.models.rag import Document
from aegis.infrastructure.llm import MockLlmProvider
from aegis.services.rag_pipeline import RagPipeline


def test_rag_pipeline_end_to_end() -> None:
    """Ensure end-to-end ingestion and query execution returns all required fields."""
    pipeline = RagPipeline(llm_provider=MockLlmProvider())

    doc = Document(
        id="policy-doc",
        content=(
            "Customers may return items within 30 days of delivery for a full refund. "
            "Returns after 30 days are subject to store credit only."
        ),
        metadata={"source": "https://company.com/returns", "category": "policy"},
    )

    # 1. Ingestion
    chunks_indexed = pipeline.ingest_documents([doc])
    assert chunks_indexed >= 1
    assert pipeline.vector_store.count() == chunks_indexed

    # 2. Query
    response = pipeline.query("What is the return window for full refunds?", top_k=2)

    # 3. Assertions on the 3 required fields from spec_docs.md:
    # - answer
    # - retrieved documents
    # - metadata/sources
    assert response.answer is not None
    assert len(response.answer) > 0
    assert "Based on the provided documentation:" in response.answer

    assert len(response.retrieved_documents) >= 1
    assert response.retrieved_documents[0].chunk.document_id == "policy-doc"
    assert response.retrieved_documents[0].similarity_score > 0.0

    assert "latency_seconds" in response.metadata
    assert response.metadata["retrieved_count"] >= 1
    assert response.sources == ["https://company.com/returns"]


def test_rag_pipeline_ingest_raw_text() -> None:
    """Ensure ingest_raw_text directly ingests plain strings."""
    pipeline = RagPipeline()
    count = pipeline.ingest_raw_text(
        text="AegisAI evaluates AI systems for reliability and hallucination.",
        document_id="aegis-overview",
        metadata={"author": "Team"},
    )
    assert count >= 1
    assert pipeline.vector_store.count() == count


def test_rag_pipeline_rejects_empty_query() -> None:
    """Ensure empty question raises ValueError."""
    pipeline = RagPipeline()
    with pytest.raises(ValueError, match="cannot be empty"):
        pipeline.query("   ")


def test_rag_pipeline_handles_unmatched_query_gracefully() -> None:
    """Ensure pipeline produces no-context answer when vector store is empty."""
    pipeline = RagPipeline()
    response = pipeline.query("Unanswerable question without documents?")

    assert "I do not have enough context" in response.answer
    assert len(response.retrieved_documents) == 0
    assert response.sources == []
