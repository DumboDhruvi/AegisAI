# AegisAI — Project Specifications

## 1. Project

**AegisAI — AI Reliability & Evaluation Platform**

**Problem:** Build a platform that tests, evaluates, benchmarks, and monitors RAG and agentic AI systems before production. 

## 2. Tech Stack

| Area             | Technology                                    |
| ---------------- | --------------------------------------------- |
| Language         | Python                                        |
| Backend          | FastAPI                                       |
| Schemas          | Pydantic                                      |
| Testing          | pytest                                        |
| LLM              | OpenAI / Gemini / Azure OpenAI-compatible API |
| Embeddings       | Embedding API/model                           |
| Database         | PostgreSQL                                    |
| Vector search    | pgvector                                      |
| Evaluation       | DeepEval                                      |
| Dashboard        | Streamlit                                     |
| Containerization | Docker                                        |
| CI/CD            | GitHub Actions                                |
| Cloud            | AWS                                           |
| Later            | Terraform, LangSmith                          |

## 3. Modules

| ID  | Module                    |
| --- | ------------------------- |
| M1  | Evaluation Dataset        |
| M2  | RAG Application           |
| M3  | Evaluation Engine         |
| M4  | Rubric System             |
| M5  | Grounding & Hallucination |
| M6  | Robustness Testing        |
| M7  | Agent Evaluation          |
| M8  | Benchmarking              |
| M9  | Regression Testing        |
| M10 | Data Validation           |
| M11 | CI/CD                     |
| M12 | Observability             |
| M13 | Security & Governance     |
| M14 | Dashboard                 |
| M15 | Cloud Deployment          |

These modules are intended to be implemented sequentially, not simultaneously. 

## 4. Core Functional Requirements

The system must:

* Accept and validate evaluation datasets.
* Execute AI workflows against test cases.
* Store inputs, outputs, retrieved context, and evaluation results.
* Calculate deterministic and LLM-based metrics.
* Support rubric-based scoring.
* Detect hallucinations and unsupported claims.
* Evaluate RAG grounding.
* Run adversarial/robustness tests.
* Evaluate tool-using agents.
* Compare models/configurations.
* Detect quality regressions.
* Run evaluations through CI.
* Validate ingested data.
* Preserve execution traces for failure analysis. 

## 5. Module Specifications

### M1 — Evaluation Dataset

**Input:** evaluation test cases
**Fields:** ID, question, expected answer, context, rubric, tags.

**Output:** validated dataset.

**Acceptance:** load → validate schema → reject invalid cases → execute tests. 

### M2 — RAG

```text
Documents
→ Parser
→ Chunker
→ Embeddings
→ pgvector
→ Retriever
→ LLM
```

Every response must contain:

```text
answer
retrieved documents
metadata/sources
```



### M3 — Evaluation Engine

**Input:**

```text
question
expected answer
AI answer
retrieved context
```

**Output:**

```text
score
pass/fail
reason
```

Metrics should include correctness, relevance, and faithfulness, with DeepEval added after the basic evaluator works. 

### M4 — Rubric Engine

Support explicit scoring criteria such as:

```text
5 = completely correct
4 = minor omission
3 = partially correct
2 = significant error
1 = mostly incorrect
0 = incorrect/hallucinated
```

Return:

```text
score
reason
evidence
```



### M5 — Grounding / Hallucination

For each generated claim:

```text
Claim
→ Evidence
→ Supported?
→ Confidence
```

Detect unsupported and contradictory claims. 

### M6 — Robustness

Test:

```text
Typos
Ambiguity
Missing information
Conflicting documents
Irrelevant documents
Prompt injection
Out-of-domain queries
```

Compare normal vs adversarial performance. 

### M7 — Agent Evaluation

Agent tools:

```text
search()
calculator()
database()
web_search()
```

Evaluate:

```text
Tool selection
Tool arguments
Tool sequence
Task completion
Unnecessary steps
```



### M8 — Benchmarking

Run identical datasets against multiple models.

Measure:

```text
Accuracy
Faithfulness
Relevance
Hallucination
Latency
Token usage
Cost
```



### M9 — Regression Testing

Store a baseline:

```text
baseline.json
```

Compare every new version against it.

Example:

```text
Baseline faithfulness: 0.93
Current:               0.87

REGRESSION
```



### M10 — Data Validation

Before indexing:

```text
Document
→ Schema validation
→ Metadata validation
→ Duplicate detection
→ Quality checks
→ Authorization check
→ Index
```

Check missing metadata, bad encoding, duplicates, empty content, stale documents, and invalid sources. 

### M11 — CI/CD

```text
Pull Request
→ pytest
→ Integration tests
→ AI evaluation
→ Baseline comparison
→ PASS / FAIL
```

Example quality gates:

```text
Faithfulness >= 0.90
Correctness >= 0.85
Hallucination <= 5%
```



### M12 — Observability

Record:

```text
Request
Model
Prompt
Retrieved documents
Tool calls
Latency
Tokens
Cost
Answer
Evaluation
```

Purpose: reproduce and diagnose failed evaluations. 

### M13 — Security / Governance

Implement:

```text
Secret management
PII detection
Document access metadata
Prompt-injection checks
Audit logs
Data-retention policy
```

Document what data enters the system, who can access it, what is logged, and what is retained. 

### M14 — Dashboard

Streamlit dashboard showing:

```text
Overall reliability
Correctness
Faithfulness
Relevance
Robustness
Hallucination
```

Tabs:

```text
Overview
Runs
Failed Tests
Models
Benchmarks
Agents
Regression
```



### M15 — Cloud

```text
Docker
→ AWS
→ Deployed API
→ Dashboard
```

Terraform comes after the core system works. 

## 6. Development Order

```text
M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8
→ M9 → M10 → M11 → M12 → M13 → M14 → M15
```

For every module:

```text
Requirements
→ Learn
→ Design
→ Implement
→ Unit test
→ Integration test
→ Document
→ Git commit
```



## 7. Project Structure

```text
aegis-ai/
├── docs/
│   ├── 01_product_requirements.md
│   ├── 02_module_breakdown.md
│   ├── 03_system_requirements.md
│   ├── 04_nonfunctional_requirements.md
│   └── modules/
│       ├── M01_evaluation_dataset.md
│       ├── M02_rag_system.md
│       ├── M03_evaluation_engine.md
│       ├── M04_rubrics.md
│       ├── M05_grounding.md
│       ├── M06_robustness.md
│       ├── M07_agents.md
│       ├── M08_benchmarking.md
│       ├── M09_regression.md
│       ├── M10_data_validation.md
│       ├── M11_cicd.md
│       ├── M12_observability.md
│       ├── M13_security.md
│       ├── M14_dashboard.md
│       └── M15_cloud.md
├── src/
├── tests/
├── evaluation/
├── datasets/
├── dashboard/
└── .github/
    └── workflows/
```

The original specification explicitly recommends creating the documentation first and starting implementation with M1. 
