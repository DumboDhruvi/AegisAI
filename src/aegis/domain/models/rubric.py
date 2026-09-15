"""Domain models for grading rubrics and qualitative evaluation criteria."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RubricCriterion(BaseModel):
    """An individual rating band within a rubric (e.g. 5 = Completely correct)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    score: int = Field(..., description="Integer score associated with this rating band")
    label: str = Field(..., description="Short qualitative label (e.g. 'Completely correct')")
    description: str = Field(
        ..., description="Specific guidelines explaining when this score should be awarded"
    )

    @field_validator("label", "description")
    @classmethod
    def validate_non_empty(cls, value: str, info: Any) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError(f"Field '{info.field_name}' must not be empty.")
        return stripped


class RubricDefinition(BaseModel):
    """Specification of an evaluation grading rubric."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(..., description="Unique rubric identifier (e.g. 'default-5-scale')")
    name: str = Field(..., description="Human-readable title of the rubric")
    description: str = Field(..., description="Detailed purpose and scope of the rubric")
    min_score: int = Field(default=0, description="Minimum possible integer score")
    max_score: int = Field(default=5, description="Maximum possible integer score")
    passing_score: int = Field(default=3, description="Threshold integer score required to pass")
    weight: float = Field(
        default=1.0, ge=0.0, description="Relative weight in composite multi-rubric benchmarks"
    )
    criteria: list[RubricCriterion] = Field(
        ..., min_length=2, description="List of discrete scoring bands defining this rubric"
    )

    @field_validator("id", "name", "description")
    @classmethod
    def validate_non_empty_strings(cls, value: str, info: Any) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError(f"Field '{info.field_name}' must not be empty.")
        return stripped

    @model_validator(mode="after")
    def validate_bounds_and_coverage(self) -> RubricDefinition:
        if self.min_score >= self.max_score:
            raise ValueError(
                f"min_score ({self.min_score}) must be strictly less than "
                f"max_score ({self.max_score})."
            )
        if not (self.min_score <= self.passing_score <= self.max_score):
            raise ValueError(
                f"passing_score ({self.passing_score}) must be between "
                f"{self.min_score} and {self.max_score}."
            )

        scores = [c.score for c in self.criteria]
        if len(scores) != len(set(scores)):
            raise ValueError("All criteria within a rubric must have unique integer scores.")

        for s in scores:
            if not (self.min_score <= s <= self.max_score):
                raise ValueError(
                    f"Criterion score {s} falls outside defined bounds "
                    f"[{self.min_score}, {self.max_score}]."
                )

        return self

    def get_criterion_for_score(self, score: int) -> RubricCriterion | None:
        """Find the criterion definition matching a given score."""
        for c in self.criteria:
            if c.score == score:
                return c
        return None


class RubricScoreResult(BaseModel):
    """Result of evaluating an AI interaction against a specific rubric."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rubric_id: str = Field(..., description="ID of the rubric applied")
    raw_score: int = Field(..., description="Discrete integer score assigned")
    normalized_score: float = Field(
        ..., ge=0.0, le=1.0, description="Normalized score mapped to [0.0, 1.0]"
    )
    passed: bool = Field(
        ..., description="Whether raw_score meets or exceeds the passing threshold"
    )
    assigned_label: str = Field(
        ..., description="Qualitative label corresponding to the assigned score"
    )
    reason: str = Field(..., description="Diagnostic justification for the awarded score")


# Standard default 5-point rubric per spec_docs.md
DEFAULT_5_POINT_RUBRIC = RubricDefinition(
    id="standard-5-point",
    name="Standard 5-Point Evaluation Rubric",
    description="Comprehensive evaluation rubric grading response accuracy and correctness.",
    min_score=0,
    max_score=5,
    passing_score=3,
    weight=1.0,
    criteria=[
        RubricCriterion(
            score=5,
            label="Completely correct",
            description=(
                "The answer is fully factual, comprehensive, and accurately addresses all aspects."
            ),
        ),
        RubricCriterion(
            score=4,
            label="Minor omission",
            description="The answer is factually correct but omits a minor contextual detail.",
        ),
        RubricCriterion(
            score=3,
            label="Partially correct",
            description=(
                "The core idea is accurate, but some secondary assertions are incomplete or vague."
            ),
        ),
        RubricCriterion(
            score=2,
            label="Significant error",
            description=(
                "The answer contains a substantial factual mistake or contradicts key context."
            ),
        ),
        RubricCriterion(
            score=1,
            label="Mostly incorrect",
            description="The response is predominantly incorrect, misleading, or irrelevant.",
        ),
        RubricCriterion(
            score=0,
            label="Incorrect / hallucinated",
            description="The answer is entirely hallucinated, untruthful, or actively harmful.",
        ),
    ],
)

# Standard grounding rubric
GROUNDING_RUBRIC = RubricDefinition(
    id="grounding-3-point",
    name="3-Point Factual Grounding Rubric",
    description="Evaluates whether claims in the response are substantiated by source context.",
    min_score=0,
    max_score=2,
    passing_score=2,
    weight=1.0,
    criteria=[
        RubricCriterion(
            score=2,
            label="Fully Grounded",
            description=(
                "Every factual claim is directly substantiated by retrieved context passages."
            ),
        ),
        RubricCriterion(
            score=1,
            label="Partially Grounded",
            description="Most statements are grounded, but contains minor unverifiable assertions.",
        ),
        RubricCriterion(
            score=0,
            label="Ungrounded / Hallucinated",
            description="Introduces major unsubstantiated claims not present in source context.",
        ),
    ],
)
