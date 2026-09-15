"""Pre-Indexing Data Validation and Poison Detection Service (Module 10)."""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timezone

from aegis.domain.models.data_validation import (
    BatchValidationReport,
    DocumentValidationResult,
    ValidationCategory,
    ValidationIssue,
    ValidationSeverity,
)
from aegis.domain.models.rag import Document

logger = logging.getLogger(__name__)

DEFAULT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior)\s+(rules|directions|instructions)",
    r"system\s+prompt\s*:",
    r"override\s+(the\s+)?(above|system|safety)",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"bypass\s+all\s+(rules|filters|restrictions|guardrails)",
    r"exfiltrate\s+(data|secrets|credentials|keys)",
]


class DataValidator:
    """Validates ingested source documents prior to chunking and vector indexing."""

    def __init__(
        self,
        required_metadata_keys: list[str] | None = None,
        min_content_length: int = 20,
        max_content_length: int = 500_000,
        min_word_count: int = 5,
        max_age_days: int | None = 365,
        allowed_sources: list[str] | None = None,
        allowed_classifications: list[str] | None = None,
        injection_patterns: list[str] | None = None,
    ) -> None:
        self.required_metadata_keys = required_metadata_keys or [
            "source",
            "timestamp",
            "title",
        ]
        self.min_content_length = min_content_length
        self.max_content_length = max_content_length
        self.min_word_count = min_word_count
        self.max_age_days = max_age_days
        self.allowed_sources = allowed_sources
        self.allowed_classifications = allowed_classifications or [
            "public",
            "internal",
            "confidential",
        ]
        patterns = injection_patterns or DEFAULT_INJECTION_PATTERNS
        self._compiled_injection_regexes = [re.compile(p, re.IGNORECASE) for p in patterns]
        self._seen_hashes: set[str] = set()

    @property
    def seen_hashes(self) -> set[str]:
        """Return the set of recorded content hashes."""
        return set(self._seen_hashes)

    def reset_registry(self) -> None:
        """Reset duplicate detection hash registry."""
        self._seen_hashes.clear()

    def validate_document(
        self, document: Document, register_hash: bool = True
    ) -> DocumentValidationResult:
        """Execute complete validation pipeline on a candidate document."""
        issues: list[ValidationIssue] = []

        # 1. Compute SHA-256 hash
        content_hash = hashlib.sha256(document.content.encode("utf-8")).hexdigest()

        # 2. Schema Validation
        self._check_schema(document, issues)

        # 3. Metadata Validation
        self._check_metadata(document, issues)

        # 4. Duplicate Detection
        self._check_duplicates(content_hash, issues)

        # 5. Content Quality
        self._check_quality(document, issues)

        # 6. Staleness Check
        self._check_staleness(document, issues)

        # 7. Authorization Check
        self._check_authorization(document, issues)

        # 8. Poisoning / Prompt Injection Check
        is_poisoned = self._check_poisoning(document, issues)

        # Determine overall validity and status
        has_error = any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        is_valid = not has_error

        if is_poisoned:
            status = "QUARANTINED"
        elif not is_valid:
            status = "REJECTED"
        else:
            status = "ACCEPTED"
            if register_hash:
                self._seen_hashes.add(content_hash)

        return DocumentValidationResult(
            document_id=document.id,
            is_valid=is_valid,
            status=status,
            content_hash=content_hash,
            issues=issues,
        )

    def validate_batch(
        self, documents: list[Document], register_hashes: bool = True
    ) -> BatchValidationReport:
        """Validate a batch of documents sequentially, detecting intra-batch duplicates."""
        results: list[DocumentValidationResult] = []
        valid_count = 0
        rejected_count = 0

        for doc in documents:
            result = self.validate_document(doc, register_hash=register_hashes)
            results.append(result)
            if result.is_valid:
                valid_count += 1
            else:
                rejected_count += 1

        summary = (
            f"Batch validation complete: {valid_count}/{len(documents)} accepted, "
            f"{rejected_count} rejected or quarantined."
        )

        return BatchValidationReport(
            total_documents=len(documents),
            valid_documents=valid_count,
            rejected_documents=rejected_count,
            results=results,
            summary=summary,
        )

    def _check_schema(self, doc: Document, issues: list[ValidationIssue]) -> None:
        """Validate content length and character integrity."""
        length = len(doc.content.strip())
        if length < self.min_content_length:
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.SCHEMA,
                    severity=ValidationSeverity.ERROR,
                    code="CONTENT_TOO_SHORT",
                    message=(
                        f"Document content length ({length}) is below "
                        f"minimum ({self.min_content_length})."
                    ),
                    field_name="content",
                )
            )
        elif length > self.max_content_length:
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.SCHEMA,
                    severity=ValidationSeverity.ERROR,
                    code="CONTENT_TOO_LONG",
                    message=(
                        f"Document content length ({length}) exceeds "
                        f"maximum ({self.max_content_length})."
                    ),
                    field_name="content",
                )
            )

        # Check binary or corrupted encoding (high non-printable ratio)
        non_printable = sum(1 for c in doc.content if ord(c) < 32 and c not in "\n\r\t")
        if len(doc.content) > 0 and (non_printable / len(doc.content)) > 0.10:
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.SCHEMA,
                    severity=ValidationSeverity.ERROR,
                    code="BAD_ENCODING",
                    message=(
                        "Document content contains an excessive ratio "
                        "of non-printable binary characters."
                    ),
                    field_name="content",
                )
            )

    def _check_metadata(self, doc: Document, issues: list[ValidationIssue]) -> None:
        """Verify required metadata keys and source constraints."""
        for key in self.required_metadata_keys:
            if key not in doc.metadata or not str(doc.metadata[key]).strip():
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.METADATA,
                        severity=ValidationSeverity.ERROR,
                        code="MISSING_METADATA",
                        message=f"Required metadata key '{key}' is missing or empty.",
                        field_name=key,
                    )
                )

        if self.allowed_sources and "source" in doc.metadata:
            source = str(doc.metadata["source"])
            if not any(source.startswith(prefix) for prefix in self.allowed_sources):
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.METADATA,
                        severity=ValidationSeverity.ERROR,
                        code="INVALID_SOURCE",
                        message=f"Source '{source}' is not in allowed sources list.",
                        field_name="source",
                    )
                )

    def _check_duplicates(self, content_hash: str, issues: list[ValidationIssue]) -> None:
        """Check if identical content hash has already been registered."""
        if content_hash in self._seen_hashes:
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.DUPLICATE,
                    severity=ValidationSeverity.ERROR,
                    code="DUPLICATE_CONTENT",
                    message=f"Document content hash '{content_hash[:12]}...' already indexed.",
                    field_name="content",
                )
            )

    def _check_quality(self, doc: Document, issues: list[ValidationIssue]) -> None:
        """Validate word count and textual diversity."""
        words = doc.content.split()
        if len(words) < self.min_word_count:
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.QUALITY,
                    severity=ValidationSeverity.ERROR,
                    code="LOW_WORD_COUNT",
                    message=(
                        f"Document has only {len(words)} words, "
                        f"below required minimum of {self.min_word_count}."
                    ),
                    field_name="content",
                )
            )
            return

        # Check repetitive degenerate text (e.g. single word repeating 70%+ of content)
        unique_words = set(w.lower() for w in words)
        lexical_diversity = len(unique_words) / len(words)
        if len(words) >= 20 and lexical_diversity < 0.15:
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.QUALITY,
                    severity=ValidationSeverity.WARNING,
                    code="LOW_LEXICAL_DIVERSITY",
                    message=(
                        f"Document displays repetitive text pattern "
                        f"(lexical diversity {lexical_diversity:.2f})."
                    ),
                    field_name="content",
                )
            )

    def _check_staleness(self, doc: Document, issues: list[ValidationIssue]) -> None:
        """Detect stale or expired documents using timestamp metadata."""
        if self.max_age_days is None:
            return

        timestamp_val = doc.metadata.get("timestamp") or doc.metadata.get("created_at")
        if not timestamp_val:
            return

        doc_dt: datetime | None = None
        if isinstance(timestamp_val, (int, float)):
            doc_dt = datetime.fromtimestamp(timestamp_val, tz=timezone.utc)
        elif isinstance(timestamp_val, str):
            for fmt in (
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
            ):
                try:
                    parsed = datetime.strptime(timestamp_val, fmt)
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    doc_dt = parsed
                    break
                except ValueError:
                    continue

        if doc_dt:
            age_days = (datetime.now(timezone.utc) - doc_dt).days
            if age_days > self.max_age_days:
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.STALENESS,
                        severity=ValidationSeverity.WARNING,
                        code="STALE_DOCUMENT",
                        message=(
                            f"Document timestamp is {age_days} days old, "
                            f"exceeding max staleness threshold of {self.max_age_days} days."
                        ),
                        field_name="timestamp",
                    )
                )

    def _check_authorization(self, doc: Document, issues: list[ValidationIssue]) -> None:
        """Ensure document access classification matches authorized policy."""
        classification = doc.metadata.get("classification") or doc.metadata.get("access_level")
        if classification:
            classification_str = str(classification).lower()
            if classification_str not in self.allowed_classifications:
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.AUTHORIZATION,
                        severity=ValidationSeverity.ERROR,
                        code="UNAUTHORIZED_CLASSIFICATION",
                        message=(
                            f"Classification '{classification}' is not authorized. "
                            f"Permitted: {', '.join(self.allowed_classifications)}."
                        ),
                        field_name="classification",
                    )
                )

    def _check_poisoning(self, doc: Document, issues: list[ValidationIssue]) -> bool:
        """Scan document content for indirect prompt injection or poisoning signatures."""
        detected = False
        for regex in self._compiled_injection_regexes:
            match = regex.search(doc.content)
            if match:
                detected = True
                matched_snippet = match.group(0)
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.POISONING,
                        severity=ValidationSeverity.ERROR,
                        code="INDIRECT_PROMPT_INJECTION",
                        message=f"Malicious instructional pattern detected: '{matched_snippet}'.",
                        field_name="content",
                    )
                )
        return detected
