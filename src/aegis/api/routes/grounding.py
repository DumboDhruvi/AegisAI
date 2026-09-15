"""FastAPI routes for Grounding and Hallucination detection (Module 5)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from aegis.domain.models.grounding import ExtractedClaim, GroundingReport
from aegis.services.hallucination_detector import ClaimExtractor, HallucinationDetector

router = APIRouter(prefix="/grounding", tags=["Grounding & Hallucination"])

# Shared singleton service instances (using deterministic / offline fallbacks by default)
_extractor = ClaimExtractor()
_detector = HallucinationDetector(claim_extractor=_extractor)


class ExtractClaimsRequest(BaseModel):
    """Request payload to parse and extract atomic claims from text."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., min_length=1, description="Input text to extract claims from")


class VerifyGroundingRequest(BaseModel):
    """Request payload to verify grounding and detect hallucinations."""

    model_config = ConfigDict(extra="forbid")

    actual_answer: str = Field(..., min_length=1, description="Generated AI response to verify")
    retrieved_context: list[str] = Field(
        ..., description="List of source passages retrieved to substantiate claims"
    )
    question: str | None = Field(
        default=None, description="Original user prompt or question for context"
    )
    threshold: float | None = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum grounding ratio required to pass",
    )


@router.post(
    "/extract-claims",
    response_model=list[ExtractedClaim],
    status_code=status.HTTP_200_OK,
    summary="Extract atomic claims",
    description="Decomposes a response into atomic factual statements with character spans.",
)
async def extract_claims(payload: ExtractClaimsRequest) -> list[ExtractedClaim]:
    """Extract claims from text."""
    try:
        return _extractor.extract_claims(payload.text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract claims: {e}",
        ) from e


@router.post(
    "/verify",
    response_model=GroundingReport,
    status_code=status.HTTP_200_OK,
    summary="Verify grounding and detect hallucinations",
    description="Evaluates all claims in an AI answer against retrieved context passages.",
)
async def verify_grounding(payload: VerifyGroundingRequest) -> GroundingReport:
    """Verify grounding of an answer against retrieved context passages."""
    try:
        return await _detector.verify(
            actual_answer=payload.actual_answer,
            retrieved_context=payload.retrieved_context,
            threshold=payload.threshold,
            question=payload.question,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Grounding verification failed: {e}",
        ) from e
