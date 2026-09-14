# AegisAI — AI Reliability & Evaluation Platform

AegisAI is an enterprise-grade evaluation, testing, benchmarking, and monitoring platform for RAG and agentic AI systems.

## Project Structure

```text
src/
  aegis/
    api/              # FastAPI routers, request/response models
    services/         # Application orchestration & workflows
    domain/           # Pure domain logic (metrics, evaluation rules)
    infrastructure/   # DB adapters, LLM/embedding clients, vector store
    core/             # Settings, logging, correlation IDs
tests/
  unit/               # Unit test suites (1:1 with source files)
  integration/        # Database, API, and retrieval integration tests
docs/
  adr/                # Architectural Decision Records
  security/           # Threat modeling & security docs
  roadmap.md          # Project backlog and milestones
  limitations.md      # Documented system limitations
  learning_log.md     # Engineering knowledge log
evaluation/
  datasets/           # Versioned evaluation datasets (v1, v2, ...)
  rubrics/            # Evaluation rubrics
  baselines/          # Benchmark baselines
```

## Quickstart

### 1. Setup Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Quality Checks
```bash
ruff check src tests
ruff format --check src tests
mypy src tests
pytest
```
