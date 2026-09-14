"""Service for loading and validating evaluation datasets from various formats."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from aegis.domain.models.evaluation_case import (
    DatasetValidationResult,
    EvaluationCase,
    EvaluationDataset,
    RejectedCase,
)


class DatasetLoader:
    """Loads and validates evaluation datasets from files, strings, and in-memory structures."""

    @classmethod
    def load_from_records(
        cls,
        records: Sequence[Any],
        dataset_name: str = "default_dataset",
        dataset_version: str = "v1",
    ) -> tuple[DatasetValidationResult, EvaluationDataset]:
        """Validate a sequence of raw dictionary records.

        Args:
            records: Sequence of raw dictionaries representing evaluation test cases.
            dataset_name: Name assigned to the generated EvaluationDataset.
            dataset_version: Version assigned to the generated EvaluationDataset.

        Returns:
            A tuple containing (DatasetValidationResult, EvaluationDataset).
        """
        valid_cases: list[EvaluationCase] = []
        rejected_cases: list[RejectedCase] = []
        seen_ids: set[str] = set()

        for index, raw_item in enumerate(records):
            if not isinstance(raw_item, dict):
                rejected_cases.append(
                    RejectedCase(
                        raw_identifier=f"record-{index}",
                        raw_data={"raw_value": str(raw_item)},
                        errors=["Record must be a JSON object (key-value dictionary)."],
                    )
                )
                continue

            raw_id = raw_item.get("id")
            str_id = str(raw_id).strip() if raw_id is not None else None

            # Check for duplicate IDs
            if str_id and str_id in seen_ids:
                rejected_cases.append(
                    RejectedCase(
                        raw_identifier=str_id,
                        raw_data=raw_item,
                        errors=[f"Duplicate case ID '{str_id}' detected at index {index}."],
                    )
                )
                continue

            try:
                case = EvaluationCase(**raw_item)
                valid_cases.append(case)
                seen_ids.add(case.id)
            except ValidationError as exc:
                error_messages = [
                    f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
                    for err in exc.errors()
                ]
                rejected_cases.append(
                    RejectedCase(
                        raw_identifier=str_id,
                        raw_data=raw_item,
                        errors=error_messages,
                    )
                )

        validation_result = DatasetValidationResult(
            valid_cases=valid_cases,
            rejected_cases=rejected_cases,
            total_count=len(records),
        )

        dataset = EvaluationDataset(
            name=dataset_name,
            version=dataset_version,
            cases=valid_cases,
        )

        return validation_result, dataset

    @classmethod
    def load_from_json_string(
        cls,
        json_content: str,
        dataset_name: str = "dataset_from_json",
        dataset_version: str = "v1",
    ) -> tuple[DatasetValidationResult, EvaluationDataset]:
        """Load and validate test cases from a JSON or JSONL formatted string."""
        content = json_content.strip()
        if not content:
            result = DatasetValidationResult(valid_cases=[], rejected_cases=[], total_count=0)
            dataset = EvaluationDataset(name=dataset_name, version=dataset_version, cases=[])
            return result, dataset

        # Try parsing as standard JSON array first if it looks like one
        if content.startswith("["):
            try:
                parsed = json.loads(content)
                if not isinstance(parsed, list):
                    raise ValueError("Top-level JSON structure must be a list of records.")
                return cls.load_from_records(
                    records=parsed,
                    dataset_name=dataset_name,
                    dataset_version=dataset_version,
                )
            except (json.JSONDecodeError, ValueError) as err:
                syntax_error_cases = [
                    RejectedCase(
                        raw_identifier=None,
                        raw_data={"content_preview": content[:100]},
                        errors=[f"JSON syntax error: {str(err)}"],
                    )
                ]
                result = DatasetValidationResult(
                    valid_cases=[], rejected_cases=syntax_error_cases, total_count=1
                )
                dataset = EvaluationDataset(name=dataset_name, version=dataset_version, cases=[])
                return result, dataset

        # Otherwise parse as line-delimited JSON (JSONL)
        records: list[dict[str, Any]] = []
        rejected: list[RejectedCase] = []

        for line_num, line in enumerate(content.splitlines(), start=1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                item = json.loads(line_str)
                if isinstance(item, dict):
                    records.append(item)
                else:
                    rejected.append(
                        RejectedCase(
                            raw_identifier=f"line-{line_num}",
                            raw_data={"raw_line": line_str},
                            errors=["JSONL entry is not a JSON object."],
                        )
                    )
            except json.JSONDecodeError as err:
                rejected.append(
                    RejectedCase(
                        raw_identifier=f"line-{line_num}",
                        raw_data={"raw_line": line_str},
                        errors=[f"Line {line_num} JSONDecodeError: {err.msg}"],
                    )
                )

        validation_result, dataset = cls.load_from_records(
            records=records,
            dataset_name=dataset_name,
            dataset_version=dataset_version,
        )

        # Merge line syntax rejection errors with schema validation rejections
        all_rejected = rejected + list(validation_result.rejected_cases)
        final_result = DatasetValidationResult(
            valid_cases=validation_result.valid_cases,
            rejected_cases=all_rejected,
            total_count=len(records) + len(rejected),
        )

        return final_result, dataset

    @classmethod
    def load_from_file(
        cls,
        file_path: str | Path,
        dataset_name: str | None = None,
        dataset_version: str = "v1",
    ) -> tuple[DatasetValidationResult, EvaluationDataset]:
        """Load and validate an evaluation dataset from a local JSON or JSONL file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Evaluation dataset file not found: {path}")

        name = dataset_name or path.stem
        raw_text = path.read_text(encoding="utf-8")
        return cls.load_from_json_string(
            json_content=raw_text,
            dataset_name=name,
            dataset_version=dataset_version,
        )
