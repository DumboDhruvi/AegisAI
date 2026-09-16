# AegisAI Roadmap & Module Backlog

This roadmap tracks implementation progress for the 15 sequential modules defined in [spec_docs.md](file:///home/dumbo/AI%20PROJECT/spec_docs.md).

## Module Status Overview

| ID  | Module                      | Status      | Target Milestone | Notes                                           |
| --- | --------------------------- | ----------- | ---------------- | ----------------------------------------------- |
| —   | Project Scaffolding & Setup | DONE        | Foundation       | Git, venv, pyproject.toml, architecture layout |
| M1  | Evaluation Dataset          | DONE        | Milestone 1      | Schemas, validation, loader, tags, rejection    |
| M2  | RAG Application             | DONE        | Milestone 2      | Ingestion, chunking, embeddings, vector store   |
| M3  | Evaluation Engine           | DONE        | Milestone 3      | Core metrics (faithfulness, correctness, etc.)  |
| M4  | Rubric System               | DONE        | Milestone 4      | Configurable grading rubrics & weights          |
| M5  | Grounding & Hallucination   | DONE        | Milestone 5      | Evidence attribution, hallucination detection   |
| M6  | Robustness Testing          | DONE        | Milestone 6      | Perturbation, adversarial inputs, out-of-domain |
| M7  | Agent Evaluation            | DONE        | Milestone 7      | Tool call schema, multi-step trace verification |
| M8  | Benchmarking                | DONE        | Milestone 8      | Model comparison & comparative benchmarks       |
| M9  | Regression Testing          | NEXT        | Milestone 9      | Baseline diffing, automated quality gates       |
| M10 | Data Validation             | TODO        | Milestone 10     | Input sanitization, poison document detection   |
| M11 | CI/CD                       | TODO        | Milestone 11     | Automated GitHub Actions evaluation pipeline    |
| M12 | Observability               | TODO        | Milestone 12     | Traces, run IDs, metrics, latency & cost        |
| M13 | Security & Governance       | TODO        | Milestone 13     | Prompt injection, PII masking, access control   |
| M14 | Dashboard                   | TODO        | Milestone 14     | Streamlit visualization & diagnostic reports    |
| M15 | Cloud Deployment            | TODO        | Milestone 15     | Docker Compose, AWS infrastructure              |

## Kanban Board

### TODO
- [ ] M9: Baseline storage, regression diffing engine, automated quality gates

### IN PROGRESS
- [x] M8: Comparative Benchmarking (Accuracy, faithfulness, relevance, hallucination, latency, tokens, cost)

### BLOCKED
*None.*

### DONE
- [x] Initialized Git repository
- [x] Created standard architectural folder layout
- [x] Created `.env.example`, `.gitignore`, `pyproject.toml`
- [x] M1: Evaluation Dataset schema, loader, rejection logic, and test cases
- [x] M2: RAG Pipeline with parser, chunker, vector store, and API endpoints
- [x] M3: Evaluation Engine (Faithfulness, Correctness, and Relevance)
- [x] M4: Rubric System (Explicit Scoring Criteria & Customizable Weights)
- [x] M5: Grounding & Hallucination Detection (Atomic Claim Verification & Evidence Attribution)
- [x] M6: Robustness Testing (Synthetic Perturbations & Comparative Adversarial Evaluation)
- [x] M7: Agent Evaluation (Multi-Step Tool Trace & Efficiency Verification)
- [x] M8: Multi-Model Comparative Benchmarking (Quality, Latency, Tokens, and Cost Analysis)
