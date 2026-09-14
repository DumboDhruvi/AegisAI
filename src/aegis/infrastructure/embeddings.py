"""Embedding provider interfaces and implementations."""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Sequence
from typing import Protocol


class EmbeddingProvider(Protocol):
    """Protocol defining the interface for generating vector embeddings."""

    @property
    def dimensions(self) -> int:
        """Return vector dimension size."""
        ...

    def embed_text(self, text: str) -> list[float]:
        """Embed a single text string into a float vector."""
        ...

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed multiple text strings into float vectors."""
        ...


class DeterministicEmbeddingProvider:
    """Deterministic, offline embedding provider for reproducible testing and local development.

    Generates normalized dense vectors using word-level hashing and term frequency.
    Ensures identical strings produce identical vectors and overlapping vocabulary
    produces high cosine similarity without needing external API keys or GPU models.
    """

    def __init__(self, dimensions: int = 128) -> None:
        if dimensions <= 0:
            raise ValueError(f"dimensions must be positive, got {dimensions}")
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def _hash_token(self, token: str) -> int:
        """Hash a token to an index in [0, dimensions - 1]."""
        digest = hashlib.md5(token.encode("utf-8")).hexdigest()
        return int(digest, 16) % self._dimensions

    def embed_text(self, text: str) -> list[float]:
        """Convert a text string into a normalized dense embedding vector."""
        tokens = re.findall(r"\b\w+\b", text.lower())
        if not tokens:
            # Fallback for empty or punctuation-only strings
            vector = [1.0 / math.sqrt(self._dimensions)] * self._dimensions
            return vector

        raw_vector = [0.0] * self._dimensions
        for token in tokens:
            idx = self._hash_token(token)
            raw_vector[idx] += 1.0

        # L2 Normalization so cosine similarity is simply the dot product
        squared_sum = sum(v * v for v in raw_vector)
        norm = math.sqrt(squared_sum) if squared_sum > 0 else 1.0

        return [v / norm for v in raw_vector]

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed a list of text strings."""
        return [self.embed_text(t) for t in texts]
