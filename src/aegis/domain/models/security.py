"""Domain models for Security, Governance, PII, and Audit Logging (Module 13)."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PiiType(str, Enum):
    """Classification of detected Personally Identifiable Information or secrets."""

    EMAIL = "EMAIL"
    PHONE = "PHONE"
    SSN = "SSN"
    CREDIT_CARD = "CREDIT_CARD"
    API_KEY = "API_KEY"
    IP_ADDRESS = "IP_ADDRESS"


class PiiDetection(BaseModel):
    """Detailed finding of a detected PII entity or secret."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    pii_type: PiiType = Field(..., description="Type of detected sensitive entity")
    text_snippet: str = Field(..., description="Original sensitive text fragment")
    start_char: int = Field(..., ge=0, description="Start character offset")
    end_char: int = Field(..., ge=0, description="End character offset")
    masked_value: str = Field(..., description="Sanitized/redacted replacement token")


class AccessLevel(str, Enum):
    """Hierarchical clearance classification for documents and actors."""

    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


class AuditAction(str, Enum):
    """Class of audited governance operations."""

    INGEST = "INGEST"
    EVALUATE = "EVALUATE"
    QUERY = "QUERY"
    EXPORT = "EXPORT"
    PURGE = "PURGE"
    ACCESS_DENIED = "ACCESS_DENIED"


class AuditLogEntry(BaseModel):
    """Immutable audit record logging who accessed or modified what resource."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    audit_id: str = Field(..., description="Unique audit event identifier")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC event occurrence timestamp",
    )
    actor_id: str = Field(..., description="Identity of user, service, or API key")
    action: AuditAction = Field(..., description="Action performed")
    resource_id: str = Field(..., description="Identifier of accessed resource")
    access_level: AccessLevel = Field(..., description="Access classification of the resource")
    status: str = Field(..., description="SUCCESS or DENIED")
    details: dict[str, Any] = Field(default_factory=dict, description="Audit metadata")


class DataRetentionPolicy(BaseModel):
    """Retention duration rules for compliance and governance."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    raw_prompts_retention_days: int = Field(
        default=30, ge=1, description="Days to retain raw input prompts"
    )
    evaluation_traces_retention_days: int = Field(
        default=90, ge=1, description="Days to retain evaluation execution traces"
    )
    audit_logs_retention_days: int = Field(
        default=365, ge=1, description="Days to retain immutable audit records"
    )
    auto_purge_enabled: bool = Field(
        default=True, description="Whether automatic purging of expired data is active"
    )


class SecurityScanResult(BaseModel):
    """Outcome of automated security, secret, PII, and prompt-injection scanning."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    has_pii: bool = Field(..., description="True if one or more PII entities were detected")
    pii_detections: list[PiiDetection] = Field(
        default_factory=list, description="List of detected PII entities"
    )
    masked_text: str = Field(..., description="Sanitized text with all PII and secrets redacted")
    has_injection: bool = Field(
        ..., description="True if malicious prompt injection pattern was detected"
    )
    injection_signatures: list[str] = Field(
        default_factory=list, description="Matched injection or jailbreak patterns"
    )
    passed: bool = Field(
        ..., description="True if no blocking security violations (e.g. injection) occurred"
    )
