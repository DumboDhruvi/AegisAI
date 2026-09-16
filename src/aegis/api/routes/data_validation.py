"""FastAPI routes for Pre-Indexing Data Validation and Poison Detection (Module 10)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from aegis.domain.models.data_validation import (
    BatchValidationReport,
    DocumentValidationResult,
)
from aegis.domain.models.rag import Document
from aegis.services.data_validator import DataValidator

router = APIRouter(prefix="/validation", tags=["Data Validation"])

_validator = DataValidator()


@router.post(
    "/validate-document",
    response_model=DocumentValidationResult,
    status_code=status.HTTP_200_OK,
    summary="Validate single document",
    description=(
        "Runs schema, metadata, quality, staleness, duplicate, "
        "and poisoning checks before indexing."
    ),
)
async def validate_document(document: Document) -> DocumentValidationResult:
    """Validate a single document for ingestion."""
    try:
        return _validator.validate_document(document)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document validation failed: {e}",
        ) from e


@router.post(
    "/validate-batch",
    response_model=BatchValidationReport,
    status_code=status.HTTP_200_OK,
    summary="Validate batch of documents",
    description=(
        "Validates an array of candidate documents, detecting intra-batch duplicates and poison."
    ),
)
async def validate_batch(documents: list[Document]) -> BatchValidationReport:
    """Validate a batch of candidate documents."""
    try:
        return _validator.validate_batch(documents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch validation failed: {e}",
        ) from e


@router.get(
    "/rules",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get validation rules configuration",
    description="Returns active thresholds, required metadata keys, and allowed classifications.",
)
async def get_validation_rules() -> dict[str, Any]:
    """Retrieve active validation rule configuration."""
    return {
        "required_metadata_keys": _validator.required_metadata_keys,
        "min_content_length": _validator.min_content_length,
        "max_content_length": _validator.max_content_length,
        "min_word_count": _validator.min_word_count,
        "max_age_days": _validator.max_age_days,
        "allowed_classifications": _validator.allowed_classifications,
        "registered_hash_count": len(_validator.seen_hashes),
    }


@router.post(
    "/reset-registry",
    response_model=dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Reset duplicate hash registry",
    description="Clears all recorded content hashes in the in-memory duplicate detector.",
)
async def reset_registry() -> dict[str, str]:
    """Reset duplicate detection registry."""
    _validator.reset_registry()
    return {"status": "success", "message": "Duplicate hash registry cleared."}
