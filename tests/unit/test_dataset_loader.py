"""Unit tests for DatasetLoader service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from aegis.services.dataset_loader import DatasetLoader


def test_load_from_records_all_valid() -> None:
    """Ensure valid records load cleanly with 100% valid result."""
    records = [
        {
            "id": "q-1",
            "question": "What is Python?",
            "expected_answer": "A high-level programming language.",
            "context": ["Python is an interpreted, high-level language."],
            "tags": ["python", "intro"],
        },
        {
            "id": "q-2",
            "question": "What is FastAPI?",
            "expected_answer": "A modern web framework for building APIs with Python.",
            "context": ["FastAPI is a modern, fast web framework."],
            "tags": ["fastapi", "web"],
        },
    ]

    result, dataset = DatasetLoader.load_from_records(
        records, dataset_name="tech-eval", dataset_version="v1"
    )

    assert result.is_fully_valid
    assert result.valid_count == 2
    assert result.rejected_count == 0
    assert result.total_count == 2
    assert len(dataset) == 2
    assert dataset.name == "tech-eval"
    assert dataset.version == "v1"


def test_load_from_records_rejects_malformed_and_non_dict() -> None:
    """Ensure malformed cases and non-dictionary records are rejected with errors."""
    records: list[Any] = [
        # Valid
        {
            "id": "valid-1",
            "question": "Valid Q",
            "expected_answer": "Valid A",
        },
        # Missing expected_answer
        {
            "id": "invalid-no-answer",
            "question": "Where is the answer?",
        },
        # Non-dictionary item
        "just a string, not a dict",
    ]

    result, dataset = DatasetLoader.load_from_records(records)

    assert not result.is_fully_valid
    assert result.valid_count == 1
    assert result.rejected_count == 2
    assert len(dataset) == 1
    assert dataset.cases[0].id == "valid-1"

    # Inspect rejection reasons
    rejection1 = next(r for r in result.rejected_cases if r.raw_identifier == "invalid-no-answer")
    assert any("expected_answer" in err for err in rejection1.errors)

    rejection2 = next(r for r in result.rejected_cases if r.raw_identifier == "record-2")
    assert "Record must be a JSON object" in rejection2.errors[0]


def test_load_from_records_detects_duplicate_ids() -> None:
    """Ensure records with duplicate IDs are rejected."""
    records = [
        {
            "id": "duplicate-id",
            "question": "First instance",
            "expected_answer": "Answer 1",
        },
        {
            "id": "duplicate-id",
            "question": "Second instance with same ID",
            "expected_answer": "Answer 2",
        },
    ]

    result, dataset = DatasetLoader.load_from_records(records)

    assert result.valid_count == 1
    assert result.rejected_count == 1
    assert "Duplicate case ID 'duplicate-id'" in result.rejected_cases[0].errors[0]


def test_load_from_json_string_array() -> None:
    """Ensure valid JSON array string parses correctly."""
    json_data = json.dumps(
        [
            {
                "id": "json-1",
                "question": "JSON Question?",
                "expected_answer": "JSON Answer",
                "context": ["Context chunk"],
            }
        ]
    )

    result, dataset = DatasetLoader.load_from_json_string(json_data, dataset_name="json-set")
    assert result.is_fully_valid
    assert result.valid_count == 1
    assert dataset.cases[0].id == "json-1"


def test_load_from_json_string_syntax_error() -> None:
    """Ensure malformed JSON syntax is caught gracefully."""
    malformed_json = "[{ 'id': 'bad-json' "  # invalid JSON syntax

    result, dataset = DatasetLoader.load_from_json_string(malformed_json)
    assert not result.is_fully_valid
    assert result.valid_count == 0
    assert result.rejected_count == 1
    assert "JSON syntax error" in result.rejected_cases[0].errors[0]


def test_load_from_jsonl_string() -> None:
    """Ensure line-delimited JSON (JSONL) parses and isolates bad lines."""
    jsonl_content = (
        '{"id": "line-1", "question": "Q1", "expected_answer": "A1"}\n'
        '{"id": "line-2", "question": "Q2", "expected_answer": "A2"}\n'
        "invalid json on this line\n"
    )

    result, dataset = DatasetLoader.load_from_json_string(jsonl_content, dataset_name="jsonl-set")
    assert not result.is_fully_valid
    assert result.valid_count == 2
    assert result.rejected_count == 1
    assert result.rejected_cases[0].raw_identifier == "line-3"
    assert len(dataset) == 2


def test_load_from_file(tmp_path: Path) -> None:
    """Ensure loading from a real filesystem path works."""
    file_path = tmp_path / "eval_data.json"
    content = [{"id": "file-1", "question": "Q file", "expected_answer": "A file"}]
    file_path.write_text(json.dumps(content), encoding="utf-8")

    result, dataset = DatasetLoader.load_from_file(file_path)
    assert result.is_fully_valid
    assert result.valid_count == 1
    assert dataset.name == "eval_data"


def test_load_from_file_not_found() -> None:
    """Ensure FileNotFoundError is raised when file does not exist."""
    with pytest.raises(FileNotFoundError):
        DatasetLoader.load_from_file("non_existent_file_path.json")
