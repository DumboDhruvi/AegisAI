"""Domain models for evaluation test cases and datasets."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EvaluationCase(BaseModel):
    """Represents a single verified evaluation test case."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(..., description="Unique identifier for the evaluation test case")
    question: str = Field(..., description="The query or prompt submitted to the AI system")
    expected_answer: str = Field(
        ..., description="Ground truth or reference response used to judge correctness"
    )
    context: list[str] = Field(
        default_factory=list,
        description="Reference documents or factual context chunks provided for RAG grounding",
    )
    rubric: dict[str, Any] = Field(
        default_factory=dict,
        description="Scoring criteria, constraints, or weights used to evaluate the answer",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Descriptive tags for categorization, filtering, and sliced testing",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional execution metadata (e.g. difficulty, source, domain)",
    )

    @field_validator("id", "question", "expected_answer")
    @classmethod
    def validate_non_empty(cls, value: str, info: Any) -> str:
        """Ensure critical string fields are not empty or solely whitespace."""
        stripped = value.strip()
        if not stripped:
            raise ValueError(f"Field '{info.field_name}' must not be empty.")
        return stripped

    @field_validator("context")
    @classmethod
    def validate_context_entries(cls, value: list[str]) -> list[str]:
        """Ensure context list does not contain empty or purely whitespace chunks."""
        cleaned = [item.strip() for item in value if item.strip()]
        return cleaned

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        """Normalize tags to lowercase and strip duplicate whitespace."""
        return sorted(list({t.strip().lower() for t in value if t.strip()}))


class RejectedCase(BaseModel):
    """Represents a malformed test case that failed schema or domain validation."""

    model_config = ConfigDict(frozen=True)

    raw_identifier: str | None = Field(
        default=None, description="Identifier extracted from raw data if available"
    )
    raw_data: dict[str, Any] = Field(..., description="The original invalid payload")
    errors: list[str] = Field(..., description="List of validation errors explaining the rejection")


class DatasetValidationResult(BaseModel):
    """Result of loading and validating a raw batch of test cases."""

    model_config = ConfigDict(frozen=True)

    valid_cases: list[EvaluationCase] = Field(
        default_factory=list, description="Cases that passed schema and rule validation"
    )
    rejected_cases: list[RejectedCase] = Field(
        default_factory=list, description="Cases that failed validation with exact error reasons"
    )
    total_count: int = Field(..., description="Total number of evaluated inputs")

    @property
    def is_fully_valid(self) -> bool:
        """Check if all input test cases were valid."""
        return len(self.rejected_cases) == 0

    @property
    def valid_count(self) -> int:
        """Count of valid cases."""
        return len(self.valid_cases)

    @property
    def rejected_count(self) -> int:
        """Count of rejected cases."""
        return len(self.rejected_cases)


class EvaluationDataset(BaseModel):
    """An immutable, versioned collection of validated evaluation cases."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., description="Name of the evaluation dataset")
    version: str = Field(default="v1", description="Dataset version (e.g. v1, v2)")
    cases: list[EvaluationCase] = Field(
        default_factory=list, description="List of validated evaluation cases"
    )

    def get_case(self, case_id: str) -> EvaluationCase | None:
        """Retrieve a test case by unique ID."""
        for case in self.cases:
            if case.id == case_id:
                return case
        return None

    def filter_by_tag(self, tag: str) -> list[EvaluationCase]:
        """Filter cases matching a specific tag."""
        normalized_tag = tag.strip().lower()
        return [case for case in self.cases if normalized_tag in case.tags]

    def __len__(self) -> int:
        return len(self.cases)
