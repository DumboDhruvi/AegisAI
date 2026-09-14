"""FastAPI routes for evaluation dataset validation and ingestion."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from aegis.domain.models.evaluation_case import EvaluationCase, RejectedCase
from aegis.services.dataset_loader import DatasetLoader

router = APIRouter(prefix="/datasets", tags=["Evaluation Datasets"])


class ValidateRecordsRequest(BaseModel):
    """Payload for validating a batch of raw test cases."""

    records: list[dict[str, Any]] = Field(
        ..., description="Array of evaluation case objects to validate"
    )
    dataset_name: str = Field(default="custom_dataset", description="Name of the dataset")
    dataset_version: str = Field(default="v1", description="Version of the dataset")


class ValidateRawJsonRequest(BaseModel):
    """Payload for validating a raw JSON or JSONL string."""

    json_content: str = Field(..., description="Raw JSON array or JSONL string")
    dataset_name: str = Field(default="raw_json_dataset", description="Name of the dataset")
    dataset_version: str = Field(default="v1", description="Version of the dataset")


class DatasetValidationResponse(BaseModel):
    """Structured response detailing valid cases and isolated rejections."""

    dataset_name: str
    dataset_version: str
    total_count: int
    valid_count: int
    rejected_count: int
    is_fully_valid: bool
    valid_cases: list[EvaluationCase]
    rejected_cases: list[RejectedCase]


@router.post(
    "/validate",
    response_model=DatasetValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate evaluation dataset records",
    description=(
        "Validates evaluation test cases against schema rules, isolating any rejected cases."
    ),
)
def validate_dataset_records(request: ValidateRecordsRequest) -> DatasetValidationResponse:
    """Validate a batch of evaluation case records."""
    if not request.records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot validate an empty records list.",
        )

    result, dataset = DatasetLoader.load_from_records(
        records=request.records,
        dataset_name=request.dataset_name,
        dataset_version=request.dataset_version,
    )

    return DatasetValidationResponse(
        dataset_name=dataset.name,
        dataset_version=dataset.version,
        total_count=result.total_count,
        valid_count=result.valid_count,
        rejected_count=result.rejected_count,
        is_fully_valid=result.is_fully_valid,
        valid_cases=result.valid_cases,
        rejected_cases=result.rejected_cases,
    )


@router.post(
    "/validate-raw",
    response_model=DatasetValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate raw JSON/JSONL content",
    description=(
        "Parses and validates a JSON array or JSONL string representing an evaluation dataset."
    ),
)
def validate_raw_json(request: ValidateRawJsonRequest) -> DatasetValidationResponse:
    """Parse and validate raw JSON/JSONL string."""
    if not request.json_content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="json_content must not be empty.",
        )

    result, dataset = DatasetLoader.load_from_json_string(
        json_content=request.json_content,
        dataset_name=request.dataset_name,
        dataset_version=request.dataset_version,
    )

    return DatasetValidationResponse(
        dataset_name=dataset.name,
        dataset_version=dataset.version,
        total_count=result.total_count,
        valid_count=result.valid_count,
        rejected_count=result.rejected_count,
        is_fully_valid=result.is_fully_valid,
        valid_cases=result.valid_cases,
        rejected_cases=result.rejected_cases,
    )
