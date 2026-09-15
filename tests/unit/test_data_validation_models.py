"""Unit tests for Data Validation domain models (Module 10)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aegis.domain.models.data_validation import (
    BatchValidationReport,
    DocumentValidationResult,
    ValidationCategory,
    ValidationIssue,
    ValidationSeverity,
)


def test_validation_issue_instantiation() -> None:
    """Test valid ValidationIssue creation."""
    issue = ValidationIssue(
        category=ValidationCategory.METADATA,
        severity=ValidationSeverity.ERROR,
        code="MISSING_METADATA",
        message="Required metadata key 'source' is missing.",
        field_name="source",
    )
    assert issue.category == ValidationCategory.METADATA
    assert issue.severity == ValidationSeverity.ERROR
    assert issue.code == "MISSING_METADATA"
    assert issue.field_name == "source"


def test_validation_issue_frozen() -> None:
    """Test immutability of ValidationIssue."""
    issue = ValidationIssue(
        category=ValidationCategory.SCHEMA,
        severity=ValidationSeverity.WARNING,
        code="CONTENT_TOO_SHORT",
        message="Short",
    )
    with pytest.raises(ValidationError):
        issue.code = "CHANGED"


def test_document_validation_result() -> None:
    """Test DocumentValidationResult structure."""
    result = DocumentValidationResult(
        document_id="doc-123",
        is_valid=False,
        status="REJECTED",
        content_hash="abc123hash",
        issues=[
            ValidationIssue(
                category=ValidationCategory.SCHEMA,
                severity=ValidationSeverity.ERROR,
                code="CONTENT_TOO_SHORT",
                message="Content length too short.",
            )
        ],
    )
    assert result.document_id == "doc-123"
    assert result.is_valid is False
    assert result.status == "REJECTED"
    assert len(result.issues) == 1


def test_batch_validation_report() -> None:
    """Test BatchValidationReport creation."""
    res = DocumentValidationResult(
        document_id="doc-1",
        is_valid=True,
        status="ACCEPTED",
        content_hash="hash1",
        issues=[],
    )
    report = BatchValidationReport(
        total_documents=1,
        valid_documents=1,
        rejected_documents=0,
        results=[res],
        summary="All valid",
    )
    assert report.total_documents == 1
    assert report.valid_documents == 1
    assert report.rejected_documents == 0
