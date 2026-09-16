# ADR-011: Pre-Indexing Data Validation, Ingestion Filtering, and Poison Detection

- **Status:** Accepted
- **Date:** 2026-09-16
- **Decision Makers:** Human Engineer & AegisAI Assistant

## Context
Module 10 addresses data quality and security prior to document ingestion into vector storage. In modern RAG pipelines, bad input data directly degrades generation quality and creates severe security risks:
1. **Schema Defects:** Empty or tiny strings, corrupted binary encoding, and disproportionately long texts degrade chunking and vector index precision.
2. **Missing Metadata:** Omission of `source`, `timestamp`, or `title` prevents reliable evidence attribution, grounding verification, and auditability.
3. **Duplicate Documents:** Ingesting duplicate or near-identical texts inflates index size and dilutes retrieval relevance scores.
4. **Stale Information:** Expired or outdated documentation causes models to answer with superseded policies or outdated facts.
5. **Indirect Prompt Injection & Poisoning:** Adversarial actors or poisoned web sources can embed hidden instructions (e.g. `ignore previous instructions`, `exfiltrate data`) into indexed documents, taking over the downstream generator.
6. **Authorization Mismatches:** Ingesting documents with restricted classifications into public or internal stores risks data leakage.

## Decision
1. **Domain Models (`src/aegis/domain/models/data_validation.py`):**
   - `ValidationSeverity`: `ERROR`, `WARNING`, `INFO`.
   - `ValidationCategory`: `SCHEMA`, `METADATA`, `DUPLICATE`, `QUALITY`, `STALENESS`, `POISONING`, `AUTHORIZATION`.
   - `ValidationIssue`: Structured finding with category, severity, error code, message, and field name.
   - `DocumentValidationResult`: Document-level verdict (`ACCEPTED`, `REJECTED`, `QUARANTINED`), SHA-256 hash, and issue list.
   - `BatchValidationReport`: Aggregated batch statistics, per-document outcomes, and quality summary.
2. **Service (`src/aegis/services/data_validator.py`):**
   - Implemented `DataValidator` executing a multi-stage validation pipeline:
     - Schema & length bounds
     - Binary encoding / non-printable character ratio
     - Required metadata presence and allowed source domain verification
     - Content SHA-256 duplicate detection with registry management
     - Quality checks: minimum word counts and degenerate repetition / lexical diversity
     - Staleness checks: configurable age thresholds evaluated against document timestamps
     - Authorization checks: allowed access classification enforcement
     - Malicious instructional injection / poisoning detection with quarantine isolation
3. **FastAPI Endpoints (`src/aegis/api/routes/data_validation.py`):**
   - `POST /api/v1/validation/validate-document`
   - `POST /api/v1/validation/validate-batch`
   - `GET /api/v1/validation/rules`
   - `POST /api/v1/validation/reset-registry`

## Consequences
- **Positive:**
  - Robust defense-in-depth: prevents toxic, corrupted, and adversarial data from ever entering the vector store.
  - Transparent audit trail: every ingested document receives a granular validation report.
  - Quarantines prompt injection attacks instead of silently passing them to generation.
- **Trade-offs:**
  - Ingestion latency slightly increases due to regex pattern matching and hash computation, though overhead remains negligible (<1ms per document) compared to embedding generation.
