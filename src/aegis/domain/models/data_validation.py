"""Domain models for Pre-Indexing Data Validation and Poison Detection (Module 10)."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ValidationSeverity(str, Enum):
    """Severity classification of validation findings."""

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class ValidationCategory(str, Enum):
    """Category of data validation rule check."""

    SCHEMA = "SCHEMA"
    METADATA = "METADATA"
    DUPLICATE = "DUPLICATE"
    QUALITY = "QUALITY"
    STALENESS = "STALENESS"
    POISONING = "POISONING"
    AUTHORIZATION = "AUTHORIZATION"


class ValidationIssue(BaseModel):
    """Detailed finding produced during data validation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    category: ValidationCategory = Field(..., description="Validation rule category")
    severity: ValidationSeverity = Field(..., description="ERROR, WARNING, or INFO")
    code: str = Field(..., description="Machine-readable issue identifier (e.g. MISSING_METADATA)")
    message: str = Field(..., description="Human-readable explanation of the issue")
    field_name: str | None = Field(
        default=None, description="Affected field or metadata key name if applicable"
    )


class DocumentValidationResult(BaseModel):
    """Comprehensive validation result for a single candidate ingestion document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    document_id: str = Field(..., description="Unique document identifier evaluated")
    is_valid: bool = Field(..., description="True if no ERROR severity issues were found")
    status: str = Field(..., description="ACCEPTED, REJECTED, or QUARANTINED")
    content_hash: str = Field(..., description="SHA-256 hash of document content")
    issues: list[ValidationIssue] = Field(
        default_factory=list, description="List of detected validation issues"
    )


class BatchValidationReport(BaseModel):
    """Consolidated validation report for a batch of ingested documents."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_documents: int = Field(..., ge=0, description="Total documents processed in batch")
    valid_documents: int = Field(..., ge=0, description="Count of accepted documents")
    rejected_documents: int = Field(
        ..., ge=0, description="Count of rejected/quarantined documents"
    )
    results: list[DocumentValidationResult] = Field(
        ..., description="Per-document validation outcomes"
    )
    summary: str = Field(..., description="Executive summary of batch data quality")
