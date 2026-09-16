# ADR-016: Cloud Deployment & Containerization Architecture

## Status
Accepted

## Date
2026-09-16

## Context
AegisAI requires a reproducible, isolated, and scalable deployment mechanism across both local developer workstations and enterprise production environments on Amazon Web Services (AWS).
The system comprises three primary runtime components:
1. **API Server (`aegis-api`)**: Fast, asynchronous FastAPI backend running Uvicorn with evaluation engines, RAG pipelines, and security scanners.
2. **Interactive UI (`aegis-dashboard`)**: Streamlit-based monitoring and failure triage dashboard with 7 analysis views.
3. **Database & Vector Store**: PostgreSQL database equipped with the `pgvector` vector extension for embedding similarity search.

The solution must satisfy:
- Zero manual host configuration: single-command startup (`docker compose up -d`).
- Minimal attack surface: non-root user execution, hardened multi-stage container builds.
- Production readiness on AWS: seamless migration to ECS Fargate with ALB routing, auto-scaling, and Secrets Manager integration.

## Decision
1. **Multi-Stage Docker Builds**:
   - Both `Dockerfile` (API) and `Dockerfile.dashboard` (Streamlit) adopt a 2-stage build structure:
     - `builder` stage: installs build tools and packages virtual environment `/opt/venv`.
     - `runtime` stage: starts from clean `python:3.10-slim`, copies `/opt/venv`, and discards build toolchains and package cache.
   - Run under dedicated non-privileged user `aegis` (`UID/GID 1000/1000`) rather than root.

2. **Local Multi-Service Orchestration with Docker Compose**:
   - Define `docker-compose.yml` orchestrating `postgres` (`pgvector/pgvector:pg16`), `app` (port 8000), and `dashboard` (port 8501).
   - Use health checks (`pg_isready`, `curl /health`, `curl /_stcore/health`) and `depends_on` conditions (`service_healthy`) to ensure proper startup sequencing.

3. **AWS Production Deployment on Amazon ECS Fargate**:
   - Container images pushed to Amazon Elastic Container Registry (ECR).
   - Compute orchestrated via serverless AWS Fargate tasks within private VPC subnets.
   - Traffic managed by an Application Load Balancer (ALB) performing path-based routing (`/api/*`, `/health`, `/docs` to API; `/*` and `/_stcore/*` to Dashboard).
   - Database provisioned using Amazon RDS PostgreSQL with `pgvector` extension enabled.
   - Secrets managed via AWS Secrets Manager with IAM task execution role integration.

4. **Automated Configuration Validation CLI**:
   - Implement `src/aegis/cli/cloud_deploy.py` to statically check environment variables, parse Compose YAML, and generate ECS task definitions.

## Consequences
### Positive
- **Reproducibility**: Identical container artifacts run in development, testing, and production.
- **Security**: Non-root runtime reduces container breakout risk; Secrets Manager prevents credentials from persisting in images.
- **Maintainability**: Clear separation of concern between API, frontend dashboard, and vector database.

### Negative / Trade-offs
- Docker image build times require careful caching of virtual environments.
- Streamlit and FastAPI require separate healthcheck probes and port mappings.
