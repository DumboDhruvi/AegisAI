"""Unit tests for embeddings and in-memory vector store."""

from __future__ import annotations

import math

import pytest

from aegis.domain.models.rag import DocumentChunk
from aegis.infrastructure.embeddings import DeterministicEmbeddingProvider
from aegis.infrastructure.vector_store import InMemoryVectorStore


def test_deterministic_embedding_provider_properties() -> None:
    """Ensure embedding provider generates normalized, deterministic vectors."""
    embedder = DeterministicEmbeddingProvider(dimensions=64)
    assert embedder.dimensions == 64

    vec1 = embedder.embed_text("AegisAI evaluation framework")
    vec2 = embedder.embed_text("AegisAI evaluation framework")
    vec3 = embedder.embed_text("Unrelated cooking recipe with tomatoes")

    # Identical text produces identical vectors
    assert vec1 == vec2

    # Vectors are unit normalized (L2 norm == 1.0)
    norm = math.sqrt(sum(v * v for v in vec1))
    assert pytest.approx(norm, rel=1e-4) == 1.0

    # Vectors with shared terms have higher dot product than unrelated texts
    sim_identical = sum(a * b for a, b in zip(vec1, vec2, strict=True))
    sim_unrelated = sum(a * b for a, b in zip(vec1, vec3, strict=True))
    assert sim_identical > sim_unrelated


def test_in_memory_vector_store_add_and_search() -> None:
    """Ensure chunks are indexed and ranked by cosine similarity."""
    embedder = DeterministicEmbeddingProvider(dimensions=64)
    store = InMemoryVectorStore()

    chunk1 = DocumentChunk(
        chunk_id="c1",
        document_id="doc-1",
        content="Python web development with FastAPI and Uvicorn.",
        chunk_index=0,
        start_char=0,
        end_char=48,
    )
    chunk2 = DocumentChunk(
        chunk_id="c2",
        document_id="doc-2",
        content="Planting tomatoes and gardening tips in spring.",
        chunk_index=0,
        start_char=0,
        end_char=47,
    )

    embeddings = embedder.embed_batch([chunk1.content, chunk2.content])
    store.add_chunks([chunk1, chunk2], embeddings)

    assert store.count() == 2

    # Query matching chunk 1
    query_vec = embedder.embed_text("FastAPI web framework in Python")
    results = store.search(query_vec, top_k=1)

    assert len(results) == 1
    assert results[0].chunk.chunk_id == "c1"
    assert results[0].similarity_score > 0.0


def test_in_memory_vector_store_min_score_filtering() -> None:
    """Ensure min_score excludes low similarity matches."""
    embedder = DeterministicEmbeddingProvider(dimensions=64)
    store = InMemoryVectorStore()

    chunk = DocumentChunk(
        chunk_id="c1",
        document_id="d1",
        content="Quantum physics and entanglement.",
        chunk_index=0,
        start_char=0,
        end_char=33,
    )
    store.add_chunks([chunk], embedder.embed_batch([chunk.content]))

    # Query with impossible threshold
    query_vec = embedder.embed_text("banana recipe")
    results = store.search(query_vec, top_k=5, min_score=0.99)
    assert len(results) == 0


def test_in_memory_vector_store_clear() -> None:
    """Ensure clearing the vector store resets count to 0."""
    store = InMemoryVectorStore()
    chunk = DocumentChunk(
        chunk_id="c1", document_id="d1", content="Text", chunk_index=0, start_char=0, end_char=4
    )
    store.add_chunks([chunk], [[0.1, 0.2]])
    assert store.count() == 1

    store.clear()
    assert store.count() == 0
