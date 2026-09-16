# AegisAI — Enterprise AI Reliability & Evaluation Platform

[![CI/CD Pipeline](https://github.com/DumboDhruvi/AegisAI/actions/workflows/ci.yml/badge.svg)](https://github.com/DumboDhruvi/AegisAI/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type Checked: mypy](https://img.shields.io/badge/mypy-strict-blue.svg)](https://mypy.readthedocs.io/)
[![Coverage: 94%](https://img.shields.io/badge/coverage-94%25-brightgreen.svg)](https://github.com/DumboDhruvi/AegisAI)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**AegisAI** is an enterprise-grade platform designed for rigorous **TEVV (Testing, Evaluation, Verification, and Validation)** of Retrieval-Augmented Generation (RAG) and autonomous AI agent systems prior to and during production deployment.

---

## 🚀 Key Capabilities & Modules

AegisAI implements all **15 sequential enterprise modules** defined in the system specification:

| Module | Name | Key Capabilities |
| :---: | :--- | :--- |
| **M1** | **Evaluation Datasets** | Strict schema validation, tag-based slicing, duplicate ID detection, and error quarantine. |
| **M2** | **RAG Application** | Document parser, recursive chunker, deterministic/OpenAI embeddings, and vector similarity retrieval. |
| **M3** | **Evaluation Engine** | Deterministic & LLM-as-a-judge scoring for Faithfulness, Answer Relevance, and Context Precision. |
| **M4** | **Rubric System** | Configurable N-point scoring rubrics, customizable criterion weighting, and descriptive failure rationales. |
| **M5** | **Grounding & Hallucination** | Atomic claim extraction, citation verification, and unsupported claim penalty scoring. |
| **M6** | **Robustness Testing** | Synthetic noise injection, typo generation, distractor chunks, missing information, and prompt injections. |
| **M7** | **Agent Evaluation** | Multi-step agent trajectory evaluation, tool call schema validation, loop detection, and efficiency metrics. |
| **M8** | **Benchmarking** | Multi-model comparative benchmarks, Pareto-optimal frontier analysis (quality vs. latency vs. cost). |
| **M9** | **Regression Testing** | Historical baseline snapshots, tolerance margin comparisons, and automated quality gate alerts. |
| **M10** | **Data Validation** | Pre-indexing sanitization, non-printable binary check, duplicate detection, staleness checks, and RBAC isolation. |
| **M11** | **CI/CD Quality Gates** | Automated pull request evaluation gates, failure thresholds, and standalone CI runner CLI. |
| **M12** | **Observability & Tracing** | Full evaluation trace spans, latency profiling, token accounting, and diagnostic replay capabilities. |
| **M13** | **Security & Governance** | PII & developer secret masking (regex + reverse offset), indirect prompt injection quarantine, and audit logging. |
| **M14** | **Interactive Dashboard** | 7-tab Streamlit dashboard: Overview, Runs, Failed Tests, Models, Benchmarks, Agents, Regression. |
| **M15** | **Cloud Deployment** | Multi-stage Dockerfiles, Docker Compose (API + Dashboard + pgvector), and AWS ECS Fargate architecture. |

---

## 🏗️ Architecture

AegisAI adheres to strict 5-layer clean architecture boundaries:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI REST API & CLI                          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                    Application / Services Layer                        │
│   (EvaluationEngine, RubricEngine, BenchmarkingService, AgentEvaluator)│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                         Pure Domain Layer                              │
│   (Immutable Pydantic Models, Evaluation Metrics, Governance Rules)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                       Infrastructure Layer                             │
│   (InMemory / PgVectorStore, LLM Providers, Embedding Adapters)        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                    Database & External APIs (AWS/RDS)                  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Quickstart

### Option 1: Docker Compose (Recommended)
Spin up the complete system (PostgreSQL with `pgvector`, FastAPI backend, and Streamlit Dashboard) with a single command:

```bash
# Clone the repository
git clone https://github.com/DumboDhruvi/AegisAI.git
cd AegisAI

# Launch all services
docker compose up -d
```

- **API Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **Streamlit Evaluation Dashboard**: [http://localhost:8501](http://localhost:8501)

---

### Option 2: Local Python Environment

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install package with all dependencies
pip install -e ".[dev]"

# Run FastAPI API Server
uvicorn aegis.api.main:app --host 0.0.0.0 --port 8000 --reload

# Run Streamlit Dashboard (in a separate terminal)
streamlit run src/aegis/dashboard/app.py
```

---

## 🧪 Verification & Quality Checks

AegisAI maintains strict automated verification standards with zero warnings:

```bash
# Run code formatting & linting
ruff check src tests
ruff format --check src tests

# Run strict static type checking
mypy src tests

# Run comprehensive test suite with coverage report
pytest --cov=aegis
```

**Current Verification Status:**
- **Unit & Integration Tests**: 257 passing tests (0 failures)
- **Code Coverage**: 94% across all modules
- **Static Typing**: 0 errors across 116 source files (`strict = true`)

---

## 📊 Dashboard Views

The Streamlit dashboard provides 7 specialized analysis tabs:
1. **Overview**: Executive summary, system reliability status, and active test suites.
2. **Runs**: Detailed run histories with score and status distributions.
3. **Failed Tests**: Failure triage, root-cause diagnostic traces, inputs/outputs, and reproduction.
4. **Models**: Multi-model comparison across faithfulness, latency, and token cost.
5. **Benchmarks**: Standard benchmark test suites, leaderboard, and domain filters.
6. **Agents**: Tool call execution accuracy, hallucination rates, and loop detection.
7. **Regression**: Baseline comparisons, tolerance margins, and automated regression alerts.

---

## 📚 Documentation & ADRs

All architectural decisions and engineering knowledge are documented in the repository:
- **[Roadmap & Backlog](docs/roadmap.md)**: Status of all 15 modules.
- **[Engineering Learning Log](docs/learning_log.md)**: Technical takeaways and ecosystem insights for each milestone.
- **[AWS Cloud Architecture](docs/deployment/aws_architecture.md)**: ECS Fargate, ALB, and RDS production setup.
- **[Architectural Decision Records (ADRs)](docs/adr/)**: 16 ADRs covering all architectural decisions.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
