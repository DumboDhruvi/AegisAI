"""Integration tests for FastAPI dataset endpoints and health check."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from aegis.api.main import app

client = TestClient(app)


def test_health_check() -> None:
    """Ensure the API health endpoint responds with 200 OK and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"


def test_validate_dataset_records_success() -> None:
    """Ensure valid records submitted via API are accepted and returned."""
    payload = {
        "dataset_name": "api_test_dataset",
        "dataset_version": "v1",
        "records": [
            {
                "id": "case-api-1",
                "question": "What is AegisAI?",
                "expected_answer": "An enterprise AI reliability evaluation platform.",
                "context": ["AegisAI tests, benchmarks, and evaluates AI systems."],
                "tags": ["aegis", "overview"],
            }
        ],
    }

    response = client.post("/api/v1/datasets/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_name"] == "api_test_dataset"
    assert data["total_count"] == 1
    assert data["valid_count"] == 1
    assert data["rejected_count"] == 0
    assert data["is_fully_valid"] is True
    assert len(data["valid_cases"]) == 1
    assert data["valid_cases"][0]["id"] == "case-api-1"


def test_validate_dataset_records_isolates_rejections() -> None:
    """Ensure endpoint isolates rejected cases without crashing."""
    payload = {
        "records": [
            {
                "id": "valid-1",
                "question": "Valid Question?",
                "expected_answer": "Valid Answer",
            },
            {
                "id": "bad-case",
                "question": "Missing expected_answer",
            },
        ]
    }

    response = client.post("/api/v1/datasets/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 2
    assert data["valid_count"] == 1
    assert data["rejected_count"] == 1
    assert data["is_fully_valid"] is False
    assert len(data["rejected_cases"]) == 1
    assert data["rejected_cases"][0]["raw_identifier"] == "bad-case"


def test_validate_dataset_empty_records_returns_400() -> None:
    """Ensure submitting an empty record list yields 400 Bad Request."""
    response = client.post("/api/v1/datasets/validate", json={"records": []})
    assert response.status_code == 400
    assert "empty records list" in response.json()["detail"]


def test_validate_raw_json_endpoint() -> None:
    """Ensure raw JSON string validation endpoint works."""
    raw_json = json.dumps([{"id": "raw-1", "question": "Q raw", "expected_answer": "A raw"}])
    response = client.post(
        "/api/v1/datasets/validate-raw",
        json={"json_content": raw_json, "dataset_name": "raw_test"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid_count"] == 1
    assert data["rejected_count"] == 0


def test_validate_sample_dataset_v1_file() -> None:
    """Ensure the checked-in evaluation/datasets/v1/sample_eval_cases.json is 100% valid."""
    dataset_file = Path("evaluation/datasets/v1/sample_eval_cases.json")
    assert dataset_file.exists()

    content = dataset_file.read_text(encoding="utf-8")
    response = client.post(
        "/api/v1/datasets/validate-raw",
        json={"json_content": content, "dataset_name": "sample_v1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_fully_valid"] is True
    assert data["valid_count"] == 4
    assert data["rejected_count"] == 0
