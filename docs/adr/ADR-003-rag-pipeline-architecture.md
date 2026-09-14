# ADR-003: RAG Architecture — Pluggable Vector Store & Offline Reproducibility

- **Status:** Accepted
- **Date:** 2026-09-14
- **Decision Makers:** Human Engineer & AegisAI Assistant

## Context
Module 2 specifies the core RAG pipeline:
`Documents -> Parser -> Chunker -> Embeddings -> pgvector -> Retriever -> LLM`.
Every response must return:
- `answer`
- `retrieved_documents`
- `metadata / sources`

In typical AI projects, testing RAG pipelines directly against live cloud APIs (OpenAI/Anthropic) and running database servers makes automated tests brittle, slow, non-deterministic, and costly.

## Decision
1. **Separation via Protocols (`typing.Protocol`):**
   - Defined abstract contracts for `VectorStore`, `EmbeddingProvider`, and `LlmProvider`.
   - Domain logic and pipeline orchestration depend strictly on these interfaces rather than concrete third-party SDKs.
2. **Deterministic Offline Adapters for Testing:**
   - Implemented `InMemoryVectorStore` using cosine similarity for sub-millisecond local execution and unit tests.
   - Implemented `DeterministicEmbeddingProvider` utilizing unit-normalized hashing and term frequency to generate deterministic semantic embeddings without external API keys or models.
   - Implemented `MockLlmProvider` for deterministic grounding verification.
3. **Chunking & Traceability:**
   - `TextChunker` creates sliding-window chunks (`chunk_size`, `chunk_overlap`) and preserves precise character offsets (`start_char`, `end_char`) and document-level metadata for downstream source attribution.

## Consequences
- **Positive:**
  - 100% offline, reproducible unit and integration tests executing in under 1 second.
  - Zero external credentials required for local CI/CD pipelines.
  - Pluggable architecture ready to connect to PostgreSQL/pgvector and live LLM APIs.
- **Trade-offs:**
  - In-memory store does not scale to millions of vectors (pgvector will be used for large persistence).
