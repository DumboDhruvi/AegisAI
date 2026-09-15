# AegisAI Cloud Deployment Architecture (AWS Production)

## 1. Executive Summary

This document specifies the production cloud deployment architecture for **AegisAI**, an enterprise AI reliability and evaluation platform. AegisAI is deployed across resilient, secure, and auto-scaling infrastructure on **Amazon Web Services (AWS)** using containerized microservices managed by **Amazon Elastic Container Service (ECS) with AWS Fargate**.

---

## 2. Container Topology & Components

The AegisAI system consists of three primary containerized components:

```text
                                 ┌───────────────────────────────┐
                                 │   Internet / Client Clients   │
                                 └───────────────┬───────────────┘
                                                 │ HTTPS (443)
                                                 ▼
                                 ┌───────────────────────────────┐
                                 │ Application Load Balancer     │
                                 │ (AWS ALB - Multi-AZ Public)   │
                                 └───────┬───────────────┬───────┘
                     Path: /api/*,       │               │ Path: /*,
                     /health, /docs      │               │ /_stcore/*
                                         ▼               ▼
                       ┌───────────────────┐   ┌───────────────────┐
                       │ ECS Target Group: │   │ ECS Target Group: │
                       │ Aegis FastAPI     │   │ Aegis Dashboard   │
                       │ (Port 8000)       │   │ (Port 8501)       │
                       └─────────┬─────────┘   └─────────┬─────────┘
                                 │                       │
                                 └───────────┬───────────┘
                                             │ Internal VPC
                                             ▼
                               ┌───────────────────────────┐
                               │ Amazon RDS PostgreSQL     │
                               │ with pgvector Extension   │
                               │ (Port 5432 - Private AZs) │
                               └───────────────────────────┘
```

1. **Aegis API (`aegis-api`)**:
   - High-throughput asynchronous FastAPI backend running on Uvicorn.
   - Handles evaluation runs, RAG ingestion, benchmark execution, and diagnostic tracing.
   - Exposed on port `8000`.
   - Healthcheck: `GET /health`.

2. **Aegis Dashboard (`aegis-dashboard`)**:
   - Interactive Streamlit UI offering 7 analytics tabs (Overview, Runs, Failed Tests, Models, Benchmarks, Agents, Regression).
   - Exposed on port `8501`.
   - Healthcheck: `GET /_stcore/health`.

3. **Database & Vector Store (Amazon RDS PostgreSQL with `pgvector`)**:
   - Managed PostgreSQL 16 engine with `pgvector` extension enabled.
   - Multi-AZ deployment for failover and high availability.
   - Stores datasets, evaluation traces, benchmark baselines, audit logs, and vector embeddings.

---

## 3. Network Architecture & Security

### VPC Layout
- **VPC CIDR**: `10.0.0.0/16` across two Availability Zones (`us-east-1a`, `us-east-1b`).
- **Public Subnets**:
  - `10.0.1.0/24` (AZ-a), `10.0.2.0/24` (AZ-b)
  - Hosts the Application Load Balancer (ALB) and NAT Gateways.
- **Private App Subnets**:
  - `10.0.10.0/24` (AZ-a), `10.0.11.0/24` (AZ-b)
  - Hosts ECS Fargate tasks with no direct inbound internet routes.
  - Outbound internet access via NAT Gateways for pulling external model APIs (OpenAI, Gemini, Anthropic).
- **Private Data Subnets**:
  - `10.0.20.0/24` (AZ-a), `10.0.21.0/24` (AZ-b)
  - Hosts Amazon RDS PostgreSQL DB Subnet Group. Isolated from direct public routing.

### Security Groups Hierarchy
1. `sg-alb`: Allows inbound `80/443` from `0.0.0.0/0`.
2. `sg-ecs-tasks`: Allows inbound `8000` and `8501` strictly from `sg-alb`.
3. `sg-rds`: Allows inbound `5432` strictly from `sg-ecs-tasks`.

---

## 4. Secrets & Configuration Management

Sensitive parameters are stored securely in **AWS Secrets Manager** and injected into ECS task definitions at launch:
- `DATABASE_URL`: Master credentials for RDS PostgreSQL.
- `OPENAI_API_KEY`: API key for OpenAI evaluation endpoints.
- `GEMINI_API_KEY`: API key for Google Gemini model evaluation.
- `ANTHROPIC_API_KEY`: API key for Anthropic Claude evaluations.

IAM Execution Role (`ecsTaskExecutionRole`) is granted scoped `secretsmanager:GetSecretValue` permissions only on `arn:aws:secretsmanager:*:*:secret:aegis/*`.

---

## 5. Auto-Scaling & High Availability

- **Target Tracking Scaling**:
  - API Service scales on `ECSServiceAverageCPUUtilization` (Target: 70%).
  - API Service scales on `ALBRequestCountPerTarget` (Target: 1,000 req/min).
  - Minimum capacity: 2 tasks; Maximum capacity: 10 tasks.
- **Zero-Downtime Deployments**:
  - Rolling updates with `minimumHealthyPercent = 100` and `maximumPercent = 200`.
  - Ensures new tasks pass healthcheck checks before traffic draining from old tasks.

---

## 6. Observability & Synthetic Canaries

- **CloudWatch Container Insights**: CPU, Memory, Network I/O metrics aggregated per ECS task.
- **Centralized Logging**: `awslogs` driver sending JSON structured logs to `/ecs/aegis-ai`.
- **Synthetic Canary**: AWS CloudWatch Synthetics canary checking `GET /health` every 60 seconds with P99 latency alerts.
