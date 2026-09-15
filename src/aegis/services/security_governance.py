"""Security, PII detection, masking, RBAC, and audit logging service (Module 13)."""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from aegis.domain.models.security import (
    AccessLevel,
    AuditAction,
    AuditLogEntry,
    DataRetentionPolicy,
    PiiDetection,
    PiiType,
    SecurityScanResult,
)

logger = logging.getLogger(__name__)

PII_REGEX_PATTERNS = {
    PiiType.EMAIL: re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    PiiType.PHONE: re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    PiiType.SSN: re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    PiiType.CREDIT_CARD: re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    PiiType.API_KEY: re.compile(
        r"\b(sk-[a-zA-Z0-9_-]{20,}|AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{36})\b"
    ),
    PiiType.IP_ADDRESS: re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}

INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(rules|safety|guidelines)", re.IGNORECASE),
    re.compile(r"system\s+prompt\s*:", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+in\s+developer\s+mode", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"exfiltrate\s+(secrets|passwords|keys|data)", re.IGNORECASE),
]

ACCESS_LEVEL_HIERARCHY = {
    AccessLevel.PUBLIC: 1,
    AccessLevel.INTERNAL: 2,
    AccessLevel.CONFIDENTIAL: 3,
    AccessLevel.RESTRICTED: 4,
}


class SecurityGovernanceService:
    """Enterprise governance, PII masking, RBAC authorization, and audit logging."""

    def __init__(self, retention_policy: DataRetentionPolicy | None = None) -> None:
        self.retention_policy = retention_policy or DataRetentionPolicy()
        self._audit_logs: list[AuditLogEntry] = []

    def scan_and_mask(self, text: str) -> SecurityScanResult:
        """Detect and mask PII and secrets, and scan for prompt injection."""
        detections: list[PiiDetection] = []

        # Find all PII instances
        for pii_type, regex in PII_REGEX_PATTERNS.items():
            for match in regex.finditer(text):
                matched_snippet = match.group(0)
                detections.append(
                    PiiDetection(
                        pii_type=pii_type,
                        text_snippet=matched_snippet,
                        start_char=match.start(),
                        end_char=match.end(),
                        masked_value=f"[REDACTED_{pii_type.value}]",
                    )
                )

        # Sort detections in reverse offset order to replace cleanly without index shifting
        sorted_detections = sorted(detections, key=lambda d: d.start_char, reverse=True)
        masked_text = text
        for d in sorted_detections:
            masked_text = masked_text[: d.start_char] + d.masked_value + masked_text[d.end_char :]

        # Check prompt injection patterns
        matched_injections: list[str] = []
        for regex in INJECTION_PATTERNS:
            inj_match = regex.search(text)
            if inj_match:
                matched_injections.append(inj_match.group(0))

        has_injection = len(matched_injections) > 0
        passed = not has_injection

        return SecurityScanResult(
            has_pii=len(detections) > 0,
            pii_detections=detections,
            masked_text=masked_text,
            has_injection=has_injection,
            injection_signatures=matched_injections,
            passed=passed,
        )

    def authorize_access(
        self,
        actor_id: str,
        actor_level: AccessLevel,
        resource_id: str,
        resource_level: AccessLevel,
        action: AuditAction = AuditAction.QUERY,
    ) -> bool:
        """Validate access clearance and append an immutable audit log entry."""
        actor_rank = ACCESS_LEVEL_HIERARCHY.get(actor_level, 0)
        resource_rank = ACCESS_LEVEL_HIERARCHY.get(resource_level, 0)
        authorized = actor_rank >= resource_rank

        status = "SUCCESS" if authorized else "DENIED"
        audit_action = action if authorized else AuditAction.ACCESS_DENIED

        self.record_audit(
            actor_id=actor_id,
            action=audit_action,
            resource_id=resource_id,
            access_level=resource_level,
            status=status,
            details={
                "actor_clearance": actor_level.value,
                "resource_classification": resource_level.value,
                "requested_action": action.value,
            },
        )

        return authorized

    def record_audit(
        self,
        actor_id: str,
        action: AuditAction,
        resource_id: str,
        access_level: AccessLevel,
        status: str,
        details: dict[str, Any] | None = None,
    ) -> AuditLogEntry:
        """Record an immutable audit event."""
        entry = AuditLogEntry(
            audit_id=f"audit-{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc),
            actor_id=actor_id,
            action=action,
            resource_id=resource_id,
            access_level=access_level,
            status=status,
            details=details or {},
        )
        self._audit_logs.append(entry)
        return entry

    def get_audit_logs(
        self,
        actor_id: str | None = None,
        action: AuditAction | None = None,
        limit: int = 100,
    ) -> list[AuditLogEntry]:
        """Query audit log history with optional filters."""
        logs = list(self._audit_logs)
        if actor_id is not None:
            logs = [e for e in logs if e.actor_id == actor_id]
        if action is not None:
            logs = [e for e in logs if e.action == action]
        return logs[-limit:]

    def enforce_data_retention(self, policy: DataRetentionPolicy | None = None) -> dict[str, int]:
        """Purge audit logs older than the configured retention policy."""
        active_policy = policy or self.retention_policy
        cutoff_date = datetime.now(timezone.utc) - timedelta(
            days=active_policy.audit_logs_retention_days
        )

        original_count = len(self._audit_logs)
        self._audit_logs = [e for e in self._audit_logs if e.timestamp >= cutoff_date]
        purged_count = original_count - len(self._audit_logs)

        return {
            "purged_audit_logs": purged_count,
            "remaining_audit_logs": len(self._audit_logs),
        }
