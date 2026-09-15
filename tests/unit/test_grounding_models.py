"""Unit tests for Grounding and Hallucination domain models (Module 5)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aegis.domain.models.grounding import (
    ClaimStatus,
    ClaimVerification,
    EvidenceCitation,
    ExtractedClaim,
    GroundingReport,
)


def test_claim_status_values() -> None:
    """Verify all expected claim statuses are defined."""
    assert ClaimStatus.SUPPORTED.value == "supported"
    assert ClaimStatus.CONTRADICTORY.value == "contradictory"
    assert ClaimStatus.UNSUPPORTED.value == "unsupported"


def test_extracted_claim_valid() -> None:
    """Verify valid ExtractedClaim creation."""
    claim = ExtractedClaim(
        claim_id="claim-1",
        claim_text="FastAPI is an asynchronous web framework.",
        start_char=0,
        end_char=41,
    )
    assert claim.claim_id == "claim-1"
    assert claim.claim_text == "FastAPI is an asynchronous web framework."
    assert claim.start_char == 0
    assert claim.end_char == 41


def test_extracted_claim_invalid_offsets() -> None:
    """Verify ExtractedClaim rejects start_char > end_char."""
    with pytest.raises(ValidationError):
        ExtractedClaim(
            claim_id="claim-bad",
            claim_text="Invalid span offsets.",
            start_char=50,
            end_char=10,
        )


def test_extracted_claim_empty_text() -> None:
    """Verify ExtractedClaim rejects empty claim text."""
    with pytest.raises(ValidationError):
        ExtractedClaim(claim_id="claim-empty", claim_text="")


def test_evidence_citation_validation() -> None:
    """Verify EvidenceCitation bounds checking."""
    citation = EvidenceCitation(
        context_index=1,
        citation_text="FastAPI natively supports async coroutines.",
        similarity_score=0.88,
    )
    assert citation.context_index == 1
    assert citation.similarity_score == 0.88

    with pytest.raises(ValidationError):
        EvidenceCitation(context_index=-1, citation_text="Negative index", similarity_score=0.5)

    with pytest.raises(ValidationError):
        EvidenceCitation(context_index=0, citation_text="Score too high", similarity_score=1.5)


def test_claim_verification_immutability() -> None:
    """Verify ClaimVerification is frozen."""
    claim = ExtractedClaim(claim_id="c1", claim_text="Python is dynamically typed.")
    verification = ClaimVerification(
        claim=claim,
        status=ClaimStatus.SUPPORTED,
        confidence=0.95,
        evidence=[],
        reason="Context verifies Python type system.",
    )
    assert verification.status == ClaimStatus.SUPPORTED
    with pytest.raises(ValidationError):
        verification.confidence = 0.5


def test_grounding_report_properties() -> None:
    """Verify GroundingReport properties and ratio calculation."""
    claim = ExtractedClaim(claim_id="c1", claim_text="PostgreSQL supports pgvector.")
    verification = ClaimVerification(
        claim=claim,
        status=ClaimStatus.SUPPORTED,
        confidence=1.0,
        evidence=[],
        reason="Context matches.",
    )
    report = GroundingReport(
        total_claims=1,
        supported_claims=1,
        unsupported_claims=0,
        contradictory_claims=0,
        grounding_ratio=1.0,
        hallucination_rate=0.0,
        passed=True,
        claims=[verification],
        summary="All claims grounded.",
    )
    assert report.total_claims == 1
    assert report.grounding_ratio == 1.0
    assert report.passed is True
