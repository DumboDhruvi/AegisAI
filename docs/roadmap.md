# AegisAI Roadmap & Module Backlog

This roadmap tracks implementation progress for the 15 sequential modules defined in [spec_docs.md](file:///home/dumbo/AI%20PROJECT/spec_docs.md).

## Module Status Overview

| ID  | Module                      | Status      | Target Milestone | Notes                                           |
| --- | --------------------------- | ----------- | ---------------- | ----------------------------------------------- |
| —   | Project Scaffolding & Setup | DONE        | Foundation       | Git, venv, pyproject.toml, architecture layout |
| M1  | Evaluation Dataset          | DONE        | Milestone 1      | Schemas, validation, loader, tags, rejection    |
| M2  | RAG Application             | TODO        | Milestone 2      | Ingestion, chunking, embeddings, pgvector       |
| M3  | Evaluation Engine           | TODO        | Milestone 3      | Core metrics (faithfulness, correctness, etc.)  |
| M4  | Rubric System               | TODO        | Milestone 4      | Configurable grading rubrics & weights          |
| M5  | Grounding & Hallucination   | TODO        | Milestone 5      | Evidence attribution, hallucination detection   |
| M6  | Robustness Testing          | TODO        | Milestone 6      | Perturbation, adversarial inputs, out-of-domain |
| M7  | Agent Evaluation            | TODO        | Milestone 7      | Tool call schema, multi-step trace verification |
| M8  | Benchmarking                | TODO        | Milestone 8      | Model comparison & comparative benchmarks       |
| M9  | Regression Testing          | TODO        | Milestone 9      | Baseline diffing, automated quality gates       |
| M10 | Data Validation             | TODO        | Milestone 10     | Input sanitization, poison document detection   |
| M11 | CI/CD                       | TODO        | Milestone 11     | Automated GitHub Actions evaluation pipeline    |
| M12 | Observability               | TODO        | Milestone 12     | Traces, run IDs, metrics, latency & cost        |
| M13 | Security & Governance       | TODO        | Milestone 13     | Prompt injection, PII masking, access control   |
| M14 | Dashboard                   | TODO        | Milestone 14     | Streamlit visualization & diagnostic reports    |
| M15 | Cloud Deployment            | TODO        | Milestone 15     | Docker Compose, AWS infrastructure              |

## Kanban Board

### TODO
- [ ] M1: Evaluation Dataset schema, loader, rejection logic, and test cases

### IN PROGRESS
- [x] Engineering standards established ([best_practices.md](file:///home/dumbo/AI%20PROJECT/best_practices.md), [AGENTS.md](file:///home/dumbo/AI%20PROJECT/AGENTS.md))
- [ ] Project scaffolding & toolchain verification (pytest, ruff, mypy)

### BLOCKED
*None.*

### DONE
- [x] Initialized Git repository
- [x] Created standard architectural folder layout
- [x] Created `.env.example`, `.gitignore`, `pyproject.toml`
