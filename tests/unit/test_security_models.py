"""Unit tests for Security domain models (Module 13)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aegis.domain.models.security import (
    AccessLevel,
    AuditAction,
    AuditLogEntry,
    DataRetentionPolicy,
    PiiDetection,
    PiiType,
    SecurityScanResult,
)


def test_pii_detection_creation() -> None:
    """Test valid PiiDetection instantiation."""
    pii = PiiDetection(
        pii_type=PiiType.EMAIL,
        text_snippet="alice@example.com",
        start_char=10,
        end_char=27,
        masked_value="[REDACTED_EMAIL]",
    )
    assert pii.pii_type == PiiType.EMAIL
    assert pii.masked_value == "[REDACTED_EMAIL]"


def test_pii_detection_frozen() -> None:
    """Test immutability of PiiDetection."""
    pii = PiiDetection(
        pii_type=PiiType.PHONE,
        text_snippet="555-123-4567",
        start_char=0,
        end_char=12,
        masked_value="[REDACTED_PHONE]",
    )
    with pytest.raises(ValidationError):
        pii.start_char = 5


def test_audit_log_entry_creation() -> None:
    """Test AuditLogEntry instantiation."""
    entry = AuditLogEntry(
        audit_id="aud-1",
        actor_id="user_admin",
        action=AuditAction.INGEST,
        resource_id="doc-security-1",
        access_level=AccessLevel.CONFIDENTIAL,
        status="SUCCESS",
        details={"ip": "127.0.0.1"},
    )
    assert entry.action == AuditAction.INGEST
    assert entry.status == "SUCCESS"
    assert entry.access_level == AccessLevel.CONFIDENTIAL


def test_retention_policy_defaults() -> None:
    """Test standard retention policy durations."""
    policy = DataRetentionPolicy()
    assert policy.raw_prompts_retention_days == 30
    assert policy.evaluation_traces_retention_days == 90
    assert policy.audit_logs_retention_days == 365
    assert policy.auto_purge_enabled is True


def test_security_scan_result() -> None:
    """Test SecurityScanResult fields."""
    res = SecurityScanResult(
        has_pii=True,
        pii_detections=[],
        masked_text="Clean",
        has_injection=False,
        injection_signatures=[],
        passed=True,
    )
    assert res.has_pii is True
    assert res.passed is True
