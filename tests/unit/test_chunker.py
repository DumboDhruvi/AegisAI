"""Unit tests for TextChunker service."""

from __future__ import annotations

import pytest

from aegis.domain.models.rag import Document
from aegis.services.chunker import TextChunker


def test_chunk_document_smaller_than_chunk_size() -> None:
    """Ensure document shorter than chunk size produces exactly one chunk."""
    chunker = TextChunker(chunk_size=100, chunk_overlap=10)
    doc = Document(id="short-doc", content="Short sentence.", metadata={"source": "test"})

    chunks = chunker.chunk_document(doc)
    assert len(chunks) == 1
    assert chunks[0].chunk_id == "short-doc#c0"
    assert chunks[0].content == "Short sentence."
    assert chunks[0].start_char == 0
    assert chunks[0].end_char == len("Short sentence.")
    assert chunks[0].metadata["source"] == "test"


def test_chunk_document_with_sliding_window_overlap() -> None:
    """Ensure long document is sliced into overlapping chunks."""
    chunker = TextChunker(chunk_size=50, chunk_overlap=10)
    # 120 characters of text
    text = "0123456789" * 12
    doc = Document(id="long-doc", content=text)

    chunks = chunker.chunk_document(doc)
    assert len(chunks) > 1

    # First chunk start=0, end=50
    assert chunks[0].start_char == 0
    assert chunks[0].end_char == 50

    # Second chunk step = 50 - 10 = 40, so start=40, end=90
    assert chunks[1].start_char == 40
    assert chunks[1].end_char == 90


def test_chunk_validation_rejects_invalid_parameters() -> None:
    """Ensure invalid chunk_size or chunk_overlap raises ValueError."""
    with pytest.raises(ValueError, match="chunk_size must be positive"):
        TextChunker(chunk_size=0)

    with pytest.raises(ValueError, match="chunk_overlap cannot be negative"):
        TextChunker(chunk_size=100, chunk_overlap=-5)

    with pytest.raises(ValueError, match="strictly less than chunk_size"):
        TextChunker(chunk_size=50, chunk_overlap=50)


def test_chunk_documents_batch() -> None:
    """Ensure batch chunking flattens chunks across all documents."""
    chunker = TextChunker(chunk_size=50, chunk_overlap=10)
    doc1 = Document(id="doc-1", content="First doc text.")
    doc2 = Document(id="doc-2", content="Second doc text.")

    chunks = chunker.chunk_documents([doc1, doc2])
    assert len(chunks) == 2
    assert chunks[0].document_id == "doc-1"
    assert chunks[1].document_id == "doc-2"
