"""RAG Pipeline service orchestrating ingestion, retrieval, and generation."""

from __future__ import annotations

import time
from collections.abc import Sequence
from typing import Any

from aegis.domain.models.rag import Document, RagResponse, RetrievedDocument
from aegis.infrastructure.embeddings import DeterministicEmbeddingProvider, EmbeddingProvider
from aegis.infrastructure.llm import LlmProvider, MockLlmProvider
from aegis.infrastructure.vector_store import InMemoryVectorStore, VectorStore
from aegis.services.chunker import TextChunker
from aegis.services.parser import DocumentParser


class RagPipeline:
    """Complete RAG application pipeline fulfilling M2 specifications."""

    def __init__(
        self,
        chunker: TextChunker | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        vector_store: VectorStore | None = None,
        llm_provider: LlmProvider | None = None,
    ) -> None:
        self.chunker = chunker or TextChunker(chunk_size=400, chunk_overlap=40)
        self.embedding_provider = embedding_provider or DeterministicEmbeddingProvider(
            dimensions=128
        )
        self.vector_store = vector_store or InMemoryVectorStore()
        self.llm_provider = llm_provider or MockLlmProvider()

    def ingest_documents(self, documents: Sequence[Document]) -> int:
        """Parse, chunk, embed, and index a collection of documents."""
        if not documents:
            return 0

        chunks = self.chunker.chunk_documents(documents)
        if not chunks:
            return 0

        contents = [chunk.content for chunk in chunks]
        embeddings = self.embedding_provider.embed_batch(contents)

        self.vector_store.add_chunks(chunks, embeddings)
        return len(chunks)

    def ingest_raw_text(
        self,
        text: str,
        document_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Parse and ingest a raw text string directly."""
        document = DocumentParser.parse_raw_text(
            text=text,
            document_id=document_id,
            metadata=metadata,
        )
        return self.ingest_documents([document])

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        min_score: float = 0.0,
    ) -> list[RetrievedDocument]:
        """Convert query to embedding vector and retrieve matching document chunks."""
        cleaned_query = query.strip()
        if not cleaned_query:
            return []

        query_embedding = self.embedding_provider.embed_text(cleaned_query)
        return self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            min_score=min_score,
        )

    def query(
        self,
        question: str,
        top_k: int = 3,
        min_score: float = 0.0,
    ) -> RagResponse:
        """Execute complete RAG flow: retrieval -> augmentation -> LLM answer generation."""
        cleaned_question = question.strip()
        if not cleaned_question:
            raise ValueError("Query question cannot be empty.")

        start_time = time.perf_counter()

        retrieved = self.retrieve(
            query=cleaned_question,
            top_k=top_k,
            min_score=min_score,
        )

        context_texts = [item.chunk.content for item in retrieved]
        answer = self.llm_provider.generate(
            prompt=cleaned_question,
            context=context_texts,
        )

        elapsed_seconds = round(time.perf_counter() - start_time, 4)

        metadata: dict[str, Any] = {
            "latency_seconds": elapsed_seconds,
            "retrieved_count": len(retrieved),
            "top_k": top_k,
            "min_score": min_score,
        }

        return RagResponse(
            answer=answer,
            retrieved_documents=retrieved,
            metadata=metadata,
        )
