# ADR-002: Evaluation Dataset Schema, Validation, and Partial Rejection Pattern

- **Status:** Accepted
- **Date:** 2026-09-14
- **Decision Makers:** Human Engineer & AegisAI Assistant

## Context
Module 1 requires AegisAI to accept evaluation datasets, validate schemas, reject invalid cases with diagnostics, and produce a verified dataset. Evaluation datasets in AI systems arrive from various sources (JSON exports, crowd-annotated JSONL lines, automated synthetic generators). If a parser fails abruptly on the first malformed line or field, engineers waste significant time diagnosing batches.

## Decision
1. **Pydantic v2 Frozen Domain Models:**
   - `EvaluationCase` is immutable (`frozen=True`) to prevent accidental mutation of benchmark ground truth during evaluation runs.
   - Strict field validators ensure `id`, `question`, and `expected_answer` cannot be empty or solely whitespace.
   - Tags are normalized to lowercase and deduplicated. Empty context chunks are filtered automatically.
2. **Partial Rejection with Diagnostic Isolation (`DatasetValidationResult`):**
   - The loader segregates records into `valid_cases` and `rejected_cases`.
   - `RejectedCase` captures the raw input and field-level error messages so data engineers can fix bad rows without re-running the entire ingestion process.
   - Duplicate ID detection is enforced deterministically.
3. **Multi-Format Ingestion:**
   - Supports both standard JSON arrays and line-delimited JSON (JSONL).

## Alternatives Considered
- **Fail-Fast Exception (`raise on first error`):** Rejected because large evaluation datasets (thousands of rows) would require repeated single-error correction cycles.
- **Unvalidated Raw Dictionaries:** Rejected because type inconsistencies would propagate down into RAG retrieval and metric evaluators.

## Consequences
- **Positive:**
  - Robust batch ingestion; clear visibility into bad data.
  - Immutable test cases eliminate side-effects during concurrent test runs.
- **Trade-offs:**
  - Extra memory overhead to retain `rejected_cases` payloads during validation.
