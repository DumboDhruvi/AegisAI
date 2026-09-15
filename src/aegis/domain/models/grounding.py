"""Domain models for Grounding and Hallucination detection (Module 5)."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ClaimStatus(str, Enum):
    """Grounding status of a single factual claim."""

    SUPPORTED = "supported"
    CONTRADICTORY = "contradictory"
    UNSUPPORTED = "unsupported"


class ExtractedClaim(BaseModel):
    """An individual atomic factual claim extracted from an AI response."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    claim_id: str = Field(..., description="Unique identifier for the claim (e.g. 'claim-1')")
    claim_text: str = Field(..., min_length=1, description="Textual proposition of the claim")
    start_char: int | None = Field(
        default=None, ge=0, description="Character start index in the original answer"
    )
    end_char: int | None = Field(
        default=None, ge=0, description="Character end index in the original answer"
    )

    @model_validator(mode="after")
    def validate_offsets(self) -> ExtractedClaim:
        if (
            self.start_char is not None
            and self.end_char is not None
            and self.start_char > self.end_char
        ):
            raise ValueError("start_char cannot exceed end_char.")
        return self


class EvidenceCitation(BaseModel):
    """A citation of evidence from retrieved context passages."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    context_index: int = Field(
        ..., ge=0, description="0-indexed position of the source context chunk"
    )
    citation_text: str = Field(..., min_length=1, description="Substantiating text excerpt")
    similarity_score: float = Field(
        ..., ge=0.0, le=1.0, description="Relevance or alignment score in [0.0, 1.0]"
    )


class ClaimVerification(BaseModel):
    """Verification analysis and evidence attribution for a single claim."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    claim: ExtractedClaim = Field(..., description="The evaluated factual claim")
    status: ClaimStatus = Field(..., description="Grounding determination")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score in the determination [0.0, 1.0]"
    )
    evidence: list[EvidenceCitation] = Field(
        default_factory=list, description="List of citing passages from context"
    )
    reason: str = Field(..., description="Diagnostic justification for verification result")


class GroundingReport(BaseModel):
    """Comprehensive grounding and hallucination analysis report for an AI answer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_claims: int = Field(..., ge=0, description="Total number of evaluated claims")
    supported_claims: int = Field(..., ge=0, description="Count of supported claims")
    unsupported_claims: int = Field(
        ..., ge=0, description="Count of ungrounded / unsupported claims"
    )
    contradictory_claims: int = Field(
        ..., ge=0, description="Count of claims contradicting source context"
    )
    grounding_ratio: float = Field(
        ..., ge=0.0, le=1.0, description="Ratio of supported claims to total claims [0.0, 1.0]"
    )
    hallucination_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Ratio of unsupported + contradictory claims to total claims [0.0, 1.0]",
    )
    passed: bool = Field(
        ..., description="Whether grounding_ratio meets or exceeds passing threshold"
    )
    claims: list[ClaimVerification] = Field(
        default_factory=list, description="Per-claim verification breakdown"
    )
    summary: str = Field(..., description="Executive diagnostic summary of findings")
