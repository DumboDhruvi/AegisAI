"""Vector store interfaces and storage implementations."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Protocol

from aegis.domain.models.rag import DocumentChunk, RetrievedDocument


class VectorStore(Protocol):
    """Protocol defining the interface for vector index storage and retrieval."""

    def add_chunks(
        self,
        chunks: Sequence[DocumentChunk],
        embeddings: Sequence[list[float]],
    ) -> None:
        """Store chunks with their corresponding embedding vectors."""
        ...

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 3,
        min_score: float = 0.0,
    ) -> list[RetrievedDocument]:
        """Retrieve the top-k most similar document chunks."""
        ...

    def count(self) -> int:
        """Return total number of stored chunks."""
        ...

    def clear(self) -> None:
        """Clear all stored vectors and chunks."""
        ...


class InMemoryVectorStore:
    """High-performance in-memory vector store using cosine similarity."""

    def __init__(self) -> None:
        self._chunks: dict[str, DocumentChunk] = {}
        self._embeddings: dict[str, list[float]] = {}

    def add_chunks(
        self,
        chunks: Sequence[DocumentChunk],
        embeddings: Sequence[list[float]],
    ) -> None:
        """Index chunks and embedding vectors."""
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Mismatch: received {len(chunks)} chunks but {len(embeddings)} embeddings."
            )

        for chunk, embedding in zip(chunks, embeddings, strict=True):
            self._chunks[chunk.chunk_id] = chunk
            self._embeddings[chunk.chunk_id] = embedding

    @staticmethod
    def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(vec_a) != len(vec_b):
            raise ValueError(f"Vector dimension mismatch: {len(vec_a)} vs {len(vec_b)}")

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b, strict=True))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 3,
        min_score: float = 0.0,
    ) -> list[RetrievedDocument]:
        """Find the top-k chunks with highest cosine similarity to query vector."""
        if not self._chunks:
            return []

        scored_results: list[RetrievedDocument] = []

        for chunk_id, embedding in self._embeddings.items():
            score = self._cosine_similarity(query_embedding, embedding)
            if score >= min_score:
                scored_results.append(
                    RetrievedDocument(
                        chunk=self._chunks[chunk_id],
                        similarity_score=round(score, 4),
                    )
                )

        # Sort descending by similarity score
        scored_results.sort(key=lambda item: item.similarity_score, reverse=True)
        return scored_results[:top_k]

    def count(self) -> int:
        """Return number of stored chunks."""
        return len(self._chunks)

    def clear(self) -> None:
        """Remove all chunks and embeddings."""
        self._chunks.clear()
        self._embeddings.clear()
