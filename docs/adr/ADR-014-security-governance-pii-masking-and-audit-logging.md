# ADR-014: Security Governance, PII and Secret Masking, RBAC, and Immutable Audit Logging

- **Status:** Accepted
- **Date:** 2026-09-16
- **Decision Makers:** Human Engineer & AegisAI Assistant

## Context
Module 13 specifies enterprise-grade security and data governance controls for the AegisAI platform. Generative AI evaluation involves sensitive internal documents, user queries, and model responses:
1. **Secrets & PII Infiltration:** Developers and users may inadvertently submit API keys (OpenAI, AWS, GitHub), SSNs, phone numbers, or emails in evaluation datasets or test queries.
2. **Adversarial Prompt Injection:** Attackers can attempt goal hijacking, jailbreaking, or system prompt exfiltration.
3. **Access Control (RBAC):** Users must not access or evaluate documents beyond their assigned clearance level (`PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, `RESTRICTED`).
4. **Audit Trail & Retention:** Compliance frameworks (SOC 2, GDPR, HIPAA) mandate logging all access events and enforcing strict data retention and purging schedules.

## Decision
1. **Domain Models (`src/aegis/domain/models/security.py`):**
   - `PiiType`: Entity classification (`EMAIL`, `PHONE`, `SSN`, `CREDIT_CARD`, `API_KEY`, `IP_ADDRESS`).
   - `PiiDetection`: Span-level detection finding with start/end character offsets and redacted replacement tokens.
   - `AccessLevel`: Hierarchical clearance level.
   - `AuditAction`: Categorical audited action (`INGEST`, `EVALUATE`, `QUERY`, `EXPORT`, `PURGE`, `ACCESS_DENIED`).
   - `AuditLogEntry`: Immutable event log with actor identity, resource ID, classification, and execution status.
   - `DataRetentionPolicy`: Configurable expiration thresholds for prompts, traces, and audit records.
   - `SecurityScanResult`: Consolidated verdict with sanitized text and injection detection flags.
2. **Services (`src/aegis/services/security_governance.py`):**
   - `SecurityGovernanceService`: High-throughput regex PII scanner, non-destructive reverse-offset masking, prompt injection defense, RBAC clearance validator, and data retention purger.
3. **Documentation (`docs/security/governance_policy.md`):**
   - Documents what data enters the system, clearance levels, logged events, and retention rules.
4. **FastAPI Endpoints (`src/aegis/api/routes/security.py`):**
   - `POST /api/v1/security/scan`
   - `POST /api/v1/security/authorize`
   - `GET /api/v1/security/audit-logs`
   - `GET /api/v1/security/retention-policy`
   - `POST /api/v1/security/retention-purge`

## Consequences
- **Positive:**
  - Complete PII and credential sanitization before storage or evaluation.
  - Granular RBAC and immutable audit logging for enterprise security compliance.
  - Zero-dependency regex scanners provide sub-millisecond execution overhead.
- **Trade-offs:**
  - High-volume audit logging requires periodic retention policy enforcement to prevent database growth.
