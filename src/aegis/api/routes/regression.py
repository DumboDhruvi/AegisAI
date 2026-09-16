"""FastAPI routes for Regression Testing and Baseline Diffing (Module 9)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from aegis.domain.models.regression import (
    BaselineRecord,
    RegressionReport,
)
from aegis.services.regression_engine import BaselineStore, RegressionEngine

router = APIRouter(prefix="/regression", tags=["Regression Testing"])

_store = BaselineStore()
_engine = RegressionEngine(baseline_store=_store)


class CompareRegressionRequest(BaseModel):
    """Request payload to compare current metrics against a baseline."""

    model_config = ConfigDict(extra="forbid")

    baseline_id: str = Field(..., min_length=1, description="Target baseline snapshot ID")
    current_version: str = Field(..., min_length=1, description="Version or build label")
    current_metrics: dict[str, float] = Field(
        ..., description="Dictionary of metric names to current scores in [0.0, 1.0]"
    )
    max_allowed_drop: float = Field(
        default=0.05, ge=0.0, le=1.0, description="Max permissible drop before regression failure"
    )


@router.get(
    "/baselines",
    response_model=list[str],
    status_code=status.HTTP_200_OK,
    summary="List registered baselines",
    description="Returns a list of all baseline IDs available in the registry.",
)
async def list_baselines() -> list[str]:
    """List baseline identifiers."""
    return _store.list_baselines()


@router.get(
    "/baseline/{baseline_id}",
    response_model=BaselineRecord,
    status_code=status.HTTP_200_OK,
    summary="Get baseline by ID",
    description="Retrieves a specific reference baseline snapshot by identifier.",
)
async def get_baseline(baseline_id: str) -> BaselineRecord:
    """Retrieve a baseline record."""
    record = _store.get_baseline(baseline_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Baseline '{baseline_id}' not found.",
        )
    return record


@router.post(
    "/baseline",
    response_model=dict[str, str],
    status_code=status.HTTP_201_CREATED,
    summary="Save a baseline snapshot",
    description="Stores an evaluation baseline snapshot for future regression diffing.",
)
async def save_baseline(record: BaselineRecord) -> dict[str, str]:
    """Save a baseline record."""
    try:
        _store.save_baseline(record)
        return {"status": "saved", "baseline_id": record.baseline_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save baseline: {e}",
        ) from e


@router.post(
    "/compare",
    response_model=RegressionReport,
    status_code=status.HTTP_200_OK,
    summary="Compare metrics against baseline",
    description="Compares current evaluation metrics against a baseline and detects regressions.",
)
async def compare_regression(payload: CompareRegressionRequest) -> RegressionReport:
    """Execute regression comparison against a baseline snapshot."""
    try:
        return _engine.compare(
            baseline_id=payload.baseline_id,
            current_version=payload.current_version,
            current_metrics=payload.current_metrics,
            max_allowed_drop=payload.max_allowed_drop,
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Regression comparison failed: {e}",
        ) from e
