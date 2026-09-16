"""FastAPI routes for Security, Governance, PII Masking, and Audit Logging (Module 13)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from aegis.domain.models.security import (
    AccessLevel,
    AuditAction,
    AuditLogEntry,
    DataRetentionPolicy,
    SecurityScanResult,
)
from aegis.services.security_governance import SecurityGovernanceService

router = APIRouter(prefix="/security", tags=["Security & Governance"])

_governance_service = SecurityGovernanceService()


class ScanRequest(BaseModel):
    """Payload to scan text for PII, secrets, and prompt injection."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., min_length=1, description="Input text to scan and sanitize")


class AuthorizationRequest(BaseModel):
    """Payload to check actor clearance against document access metadata."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str = Field(..., min_length=1, description="Actor identity")
    actor_level: AccessLevel = Field(..., description="Actor clearance level")
    resource_id: str = Field(..., min_length=1, description="Target resource identifier")
    resource_level: AccessLevel = Field(..., description="Resource clearance level")
    action: AuditAction = Field(default=AuditAction.QUERY, description="Action to perform")


@router.post(
    "/scan",
    response_model=SecurityScanResult,
    status_code=status.HTTP_200_OK,
    summary="Scan and mask PII / secrets",
    description="Detects PII, API keys, credentials, and prompt injection. Returns masked text.",
)
async def scan_security(payload: ScanRequest) -> SecurityScanResult:
    """Scan and sanitize text."""
    try:
        return _governance_service.scan_and_mask(payload.text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security scan failed: {e}",
        ) from e


@router.post(
    "/authorize",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Validate access clearance",
    description=(
        "Evaluates actor access level against resource classification and logs audit entry."
    ),
)
async def authorize_access(payload: AuthorizationRequest) -> dict[str, Any]:
    """Authorize access and record audit trail."""
    try:
        authorized = _governance_service.authorize_access(
            actor_id=payload.actor_id,
            actor_level=payload.actor_level,
            resource_id=payload.resource_id,
            resource_level=payload.resource_level,
            action=payload.action,
        )
        return {
            "authorized": authorized,
            "status": "SUCCESS" if authorized else "DENIED",
            "actor_id": payload.actor_id,
            "resource_id": payload.resource_id,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authorization check failed: {e}",
        ) from e


@router.get(
    "/audit-logs",
    response_model=list[AuditLogEntry],
    status_code=status.HTTP_200_OK,
    summary="Query audit logs",
    description="Retrieves recorded audit log history with optional filters.",
)
async def get_audit_logs(
    actor_id: str | None = Query(default=None),
    action: AuditAction | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[AuditLogEntry]:
    """Query audit logs."""
    return _governance_service.get_audit_logs(actor_id=actor_id, action=action, limit=limit)


@router.get(
    "/retention-policy",
    response_model=DataRetentionPolicy,
    status_code=status.HTTP_200_OK,
    summary="Get data retention policy",
    description="Returns active retention days for prompts, traces, and audit logs.",
)
async def get_retention_policy() -> DataRetentionPolicy:
    """Retrieve active retention policy."""
    return _governance_service.retention_policy


@router.post(
    "/retention-purge",
    response_model=dict[str, int],
    status_code=status.HTTP_200_OK,
    summary="Enforce data retention purge",
    description="Purges expired records exceeding the compliance retention period.",
)
async def enforce_retention_purge() -> dict[str, int]:
    """Execute retention purge."""
    return _governance_service.enforce_data_retention()
