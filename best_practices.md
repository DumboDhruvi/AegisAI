# AegisAI — Engineering Standards & Best Practices

## Purpose & Philosophy

This document defines the engineering standards, architecture rules, quality bars, and AI pair-programming protocols for **AegisAI**. 
The goal is dual:
1. **Build a production-grade, highly reliable AI evaluation platform** with no shortcuts or "just make it work" code.
2. **Accelerate learning for the human engineer**, ensuring deep understanding of architecture, design decisions, failure modes, and underlying concepts without becoming a passive code accepter.

---

## Part 1: AegisAI Engineering Standards

### 1. Treat It as a Real Product
Every feature must follow the standard engineering lifecycle:
$$\text{Requirement} \longrightarrow \text{Design} \longrightarrow \text{Implementation} \longrightarrow \text{Tests} \longrightarrow \text{Documentation} \longrightarrow \text{Review} \longrightarrow \text{Release}$$

No "just make it work" code or premature commits without verification.

---

### 2. Clean Architecture Boundaries
Strictly separate concerns into distinct architectural layers:

```
API (FastAPI routes, request/response models)
  ↓
Application / Services (Orchestration, use-cases, workflow management)
  ↓
Domain / Evaluation Logic (Core metrics, rubric logic, scoring, pure business logic)
  ↓
Infrastructure (Vector store clients, LLM clients, external integrations)
  ↓
Database / External APIs (PostgreSQL, pgvector, raw HTTP clients)
```

- **Rule:** Domain & evaluation logic must NEVER import or directly contain database queries, raw HTTP clients, or framework-specific I/O.
- Dependencies point inward; domain logic remains pure, deterministic, and independently testable.

---

### 3. Type Everything (Modern Python Syntax)
- Use **Python 3.12+** modern syntax throughout.
- Explicit type hints on every function parameter and return type:
  ```python
  def evaluate_case(case: EvaluationCase) -> EvaluationResult:
      ...
  ```
- Use `Pydantic v2` (`BaseModel`, `Field`, `ConfigDict`) for all external input validation, configuration, and API schemas.
- Use `typing` primitives (`Sequence`, `Mapping`, `Callable`, `Literal`, etc.) accurately.
- Validate types with static analysis tools (`pyright` / `mypy`) in strict/standard mode.

---

### 4. Configuration, Never Hardcoding
- Never hardcode secrets, API keys, URLs, or tuning constants.
- Manage configuration via `pydantic-settings` loading from `.env` and environment variables.
- Maintain a `.env.example` documenting all required variables with dummy values.
- Never commit `.env` or sensitive credentials to version control.

---

### 5. Comprehensive Testing Strategy
AI systems cannot rely solely on standard software tests or single happy-path runs. Every feature requires:

```
pytest
  ↓
Unit Tests (domain logic, parsing, schema validation, isolated pure functions)
  ↓
Integration Tests (database, pgvector retrieval, external API client adapters with mocks/vcr)
  ↓
RAG Integration Tests (end-to-end ingestion, chunking, retrieval accuracy)
  ↓
AI Evaluation Suite (deterministic metrics + LLM-as-judge runs against versioned datasets)
  ↓
Quality Gate (pass/fail thresholds for CI/CD)
```

- **Rule:** Every new file or function that can be tested MUST have a corresponding test file in `tests/`.
- Every time code is modified, the respective test suite MUST be run to verify no regression.

---

### 6. Evaluation Datasets as Versioned Code Assets
Treat evaluation datasets with the same rigor as production code:

```
evaluation/
├── datasets/
│   ├── v1/
│   ├── v2/
│   └── ...
├── rubrics/
└── baselines/
```

Every evaluation result must capture full lineage:
- `dataset_version`
- `model` & `model_version`
- `prompt_version`
- `embedding_model`
- `retrieval_config` (top-k, chunk size, similarity metric)
- `evaluation_version`
- `timestamp` & `git_commit_sha`

This guarantees exact reproducibility across experiments.

---

### 7. Multi-Dimensional Metrics (Never Rely on One Metric)
A single metric (e.g., accuracy) can mask catastrophic regressions. Always evaluate across:
- **Correctness:** Factual alignment with ground truth.
- **Relevance:** Does the response address the specific prompt?
- **Faithfulness / Grounding:** Is every claim supported by retrieved context?
- **Hallucination Rate:** Frequency of unsupported or fabricated claims.
- **Robustness:** Stability against perturbed, adversarial, or out-of-distribution inputs.
- **Latency & Cost:** Token counts, duration (p50, p95, p99), and API cost per call.

---

### 8. Separate Deterministic & LLM-as-Judge Evaluation
Always prefer deterministic checks when possible:
- JSON schema validation & expected fields
- Exact match / substring / regex checks
- Tool-call validity (function name, arguments schema)
- Latency, token budget, and status code thresholds

Reserve LLM evaluators strictly for subjective or semantic judgment (tone, complex synthesis, semantic similarity). This provides engineering credibility and avoids "an LLM blindly grading an LLM".

---

### 9. Diagnosable Evaluation: Every Result Must Have a Reason
Never store raw scores without explanation:
```python
# Prohibited
score = 0.72

# Required
EvaluationResult(
    score=0.72,
    passed=False,
    reason="Answer omitted the mandatory 30-day return policy condition found in context chunk #2.",
    evidence=[
        "Context: 'Items may be returned within 30 days of purchase.'",
        "Generated Output: 'You can return items anytime.'"
    ]
)
```
The platform must make failures immediately diagnosable and actionable.

---

### 10. Structured Experiment Tracking
Every evaluation run or hyperparameter exploration must have an Experiment record:

- **Experiment ID:** e.g., `EXP-023`
- **Hypothesis:** e.g., *"Increasing retrieval top-k from 3 to 5 improves grounding faithfulness without exceeding 2.5s latency."*
- **Dataset & Config:** e.g., `dataset: rag-v2`, `prompt: prompt-v4`, `retriever: top_k=5`
- **Model:** e.g., `gemini-1.5-pro`
- **Metrics & Comparison:** Baseline vs. Candidate
- **Conclusion & Decision:** Accepted / Rejected with rationale.

---

### 11. Git Workflow, Branch Protection & Human Approval Policy
- **Main branch is protected:** Direct commits or pushes to `main` are strictly prohibited.
- **Workflow for EVERY change:**
  1. Start from latest `main`.
  2. Create a dedicated branch (`feature/*`, `bugfix/*`, `docs/*`, etc.).
  3. Make all changes only on that branch.
  4. Run all verification checks (`pytest`, `ruff`, `mypy`).
  5. Review complete diff.
  6. Commit with clear conventional commit messages.
  7. Push branch to remote.
  8. Create a Pull Request (PR) targeting `main`.
  9. Deliver the Human Engineer Checkpoint report and STOP.
- **Human is the final authority:** The AI assistant must never merge or approve its own PR. Merging is strictly reserved for the human developer.
- Commits follow [Conventional Commits](https://www.conventionalcommits.org/):
  - `feat: add rubric evaluator for M4`
  - `test: add grounding evaluation test cases for M5`
  - `fix: handle empty retrieval results gracefully`
  - `docs: document evaluation schema and ADR-002`
- Never make vague commits (`stuff`, `updates`, `wip`, `fixes`).

---

### 12. Pull-Request Standard & Quality Enforcement
Every meaningful change must pass:
1. Formatting & Linting (`ruff format --check`, `ruff check`)
2. Type checking (`pyright` or `mypy`)
3. Unit & Integration tests (`pytest`)
4. AI evaluation quality gate

CI (GitHub Actions) serves as the automated enforcement mechanism.

---

### 13. Tooling Ecosystem
- **Ruff:** Ultra-fast linting, import sorting, and code formatting.
- **Pytest:** Test discovery, fixtures, parameterization, and assertion reporting.
- **Pyright / Mypy:** Static type checking.
- **Pre-commit:** Git hooks for automated pre-commit linting and type verification.

---

### 14. API Design Standards (FastAPI)
Every API endpoint must provide:
- Strict Pydantic `request` and `response_model` schemas.
- Explicit HTTP status codes (`200`, `201`, `400`, `404`, `422`, `500`).
- Descriptive OpenAPI summary, description, and response documentation.
- Granular, modular routers (e.g., `/evaluations`, `/runs`, `/benchmarks`, `/datasets`). Never bundle everything into one giant endpoint.

---

### 15. Robust Error Handling
- Never use bare `except:` or `except Exception: pass`.
- Catch specific domain exceptions.
- Classify errors (validation errors, upstream API timeouts, parsing failures, internal faults).
- Log errors with full stack traces internally, but sanitize user-facing responses so internal secrets, database schemas, or credentials are never leaked.

---

### 16. Observability & Correlation IDs
Every evaluation run and request must possess a unique trace/run ID (e.g., `run_id = "eval-2026-00123"`).
Full trace captures:
$$\text{Request} \longrightarrow \text{Retrieval} \longrightarrow \text{Model} \longrightarrow \text{Tool Calls} \longrightarrow \text{Response} \longrightarrow \text{Evaluator} \longrightarrow \text{Result}$$

Logs must be structured (JSON/key-value) to facilitate debugging of why a model or retriever failed.

---

### 17. Sensitive Data Protection (No PII / Secret Leaks)
- Never log API keys, bearer tokens, passwords, or customer PII.
- Implement automated redaction filters in logging pipelines.

---

### 18. Security From Day One
- Defense against AI-specific threat vectors:
  - Prompt injection (direct and indirect)
  - Malicious / poisoning document ingestion
  - Data exfiltration / context leakage
  - Unsafe tool execution (sandboxing, strict argument validation)
- Standard application security:
  - Input length and type constraints
  - Rate limiting & authentication
  - Least privilege access for database connections

---

### 19. Dependency Management
- Pin dependencies using modern packaging (`pyproject.toml` with `uv` or `poetry` / `pip-tools`).
- Never leave dependencies unbounded; record locked versions for complete reproducibility.

---

### 20. Reproducible Infrastructure (Docker)
- Fully containerized setup via `Dockerfile` and `docker-compose.yml`:
  - `app` (FastAPI backend)
  - `postgres` with `pgvector`
  - `dashboard` (Streamlit)
- Any developer should be able to run:
  ```bash
  git clone <repo>
  docker compose up -d
  ```
  and have an operational environment.

---

### 21. Engineering Documentation
Every module must have an engineering specification covering:
- Purpose & Stated Requirements
- Architectural Diagram & Data Flow
- Public Interfaces & Pydantic Data Models
- Edge Cases & Known Failure Modes
- Testing Plan & Verification Evidence
- Known Limitations & Security Considerations

---

### 22. Architectural Decision Records (ADRs)
Maintain architectural decisions in `docs/adr/`:
- Format: `ADR-001-<short-title>.md`
- Sections:
  1. **Context:** Problem statement and constraints.
  2. **Decision:** The chosen design or technology.
  3. **Alternatives Considered:** Why alternatives were rejected.
  4. **Consequences:** Positive outcomes, trade-offs, and tech debt.

---

### 23. Threat Model
Maintain `docs/security/threat_model.md`:
- Model: Asset $\longrightarrow$ Threat $\longrightarrow$ Attack Vector $\longrightarrow$ Mitigation $\longrightarrow$ Residual Risk.
- Explicitly cover RAG injection, poisoned embeddings, denial-of-wallet (token exhaustion), and unauthorized vector queries.

---

### 24. Explicit Quality Gates
No arbitrary "looks good" approvals. Hard thresholds enforced in CI:
- **Unit & Integration Test Pass Rate:** 100%
- **Correctness Score:** $\ge 0.85$
- **Faithfulness / Grounding:** $\ge 0.90$
- **Hallucination Rate:** $\le 5\%$
- **Critical Security Tests:** 100% pass

---

### 25. Engineering Backlog & Roadmap
- Track all tasks in `docs/roadmap.md` with:
  - `TODO`
  - `IN PROGRESS`
  - `BLOCKED`
  - `DONE`
- Mirror milestones to GitHub Issues and PRs.

---

### 26. Transparent Limitations
Document known weaknesses in `docs/limitations.md`:
- LLM-as-judge variance and non-determinism.
- Approximate vector recall trade-offs.
- Token limits and context window degradation.
- Differences between synthetic test datasets and production traffic.

Acknowledging limitations is a hallmark of senior engineering.

---

### 27. Semantic Versioning & Release Strategy
- Tag releases using SemVer: `v0.1.0`, `v0.2.0`, `v1.0.0`.
- Maintain `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/).

---

### 28. Scientific Reproducibility
Every evaluation claim must cite full parameters:
```text
Experiment: EXP-024
Dataset: rag-v2 (sha256: 4f8b...)
Model: gemini-1.5-pro (temp: 0.0)
Prompt: prompt-v4 (sha256: 9e1a...)
Retriever: top_k=5, similarity=cosine, chunk_size=512
Evaluator: deepeval-faithfulness-v2
Commit: a81fc2d
Result: Faithfulness = 93.4%
```

---

## Part 2: AI Coding Assistant Operating Protocol

Whenever AI assists with implementation, it MUST adhere strictly to the following 14-step checklist.

### The 14-Step Post-Implementation Checklist

1. **Requirement Check:**
   - Did the implementation satisfy the exact requirement from `spec_docs.md`?
   - Did I solve the requested problem rather than an adjacent one?
   - Did I avoid unstated assumptions?

2. **Change Summary:**
   - What changed? Which files were created/edited?
   - Why was each change made? (Concise 1–2 minute read).

3. **Human Understanding Checkpoint (Crucial for Learning):**
   - Identify new engineering concepts the developer needs to understand.
   - Explain *only* the specific concepts used in this iteration clearly and concisely.

4. **Self Code Review:**
   - Review code for correctness, readability, maintainability, architecture adherence, edge cases, error handling, performance, and security.

5. **Test Verification:**
   - Run the tests! Report status:
     - Existing tests: PASS / FAIL
     - New tests: PASS / FAIL
     - Linting & Type Checking: PASS / FAIL
   - Verify: Did the tests genuinely validate the new behavior, or were they trivial/tautological?

6. **"What Could Be Wrong?" (Adversarial Thinking):**
   - Produce potential failure modes, edge cases, and failure scenarios.
   - Verify tests cover the critical ones.

7. **Dependency Review:**
   - If any package is introduced:
     - Package name & version
     - Why needed & why this package over alternatives
     - License & maintenance status

8. **Security Checkpoint:**
   - Secrets, credentials, PII exposure?
   - Prompt injection, data leakage, unsafe tool usage, untrusted input?
   - High-risk flags: CI/CD, Docker, auth, secrets, deployment.

9. **Architecture Check:**
   - Does this change duplicate logic?
   - Does it violate layer boundaries?
   - Does it create tight coupling or unnecessary dependencies?

10. **Research Verification:**
    - Explicitly classify technology behaviors:
      - `[VERIFIED]` from official documentation.
      - `[INFERRED]` from codebase patterns.
      - `[ASSUMED]` (requires developer attention).

11. **Diff Inspection:**
    - Compare expected changes against `git status` / `git diff`.
    - Flag any unexpected or drifting files.

12. **Goal & Test Integrity Rule:**
    - **NEVER** delete or weaken a test because it fails.
    - **NEVER** remove validation to make tests pass.
    - **NEVER** silently alter acceptance criteria or rewrite unrelated files.

13. **Commit Checkpoint:**
    - Present summary: Requirements (PASS), Tests (PASS), Security (PASS), Architecture (PASS), Documentation (UPDATED), Remaining Limitations.
    - Await human approval before committing.

14. **Learning Log:**
    - Update `docs/learning_log.md` with:
      - What was learned
      - Key architectural decision
      - Any misconceptions or mistakes identified
