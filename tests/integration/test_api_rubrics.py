"""Integration tests for Rubric Engine FastAPI routes."""

from __future__ import annotations

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from aegis.api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_list_rubrics_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/rubrics")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    rubric_ids = [r["id"] for r in data]
    assert "standard-5-point" in rubric_ids
    assert "grounding-3-point" in rubric_ids


def test_get_rubric_details_success(client: TestClient) -> None:
    response = client.get("/api/v1/rubrics/standard-5-point")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == "standard-5-point"
    assert data["min_score"] == 0
    assert data["max_score"] == 5
    assert len(data["criteria"]) == 6


def test_get_rubric_details_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/rubrics/unknown-rubric-xyz")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_register_custom_rubric_endpoint(client: TestClient) -> None:
    payload = {
        "id": "code-quality-rubric",
        "name": "Code Quality Scale",
        "description": "Evaluates Python code style and cleanliness.",
        "min_score": 1,
        "max_score": 3,
        "passing_score": 2,
        "weight": 1.5,
        "criteria": [
            {"score": 3, "label": "Production Grade", "description": "Clean, typed, docstrings."},
            {"score": 2, "label": "Working Prototype", "description": "Works with minor flaws."},
            {"score": 1, "label": "Broken Code", "description": "Syntax or runtime error."},
        ],
    }
    response = client.post("/api/v1/rubrics", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["id"] == "code-quality-rubric"

    # Duplicate registration should return 409
    dup_res = client.post("/api/v1/rubrics", json=payload)
    assert dup_res.status_code == status.HTTP_409_CONFLICT


def test_evaluate_with_rubric_endpoint_success(client: TestClient) -> None:
    payload = {
        "rubric_id": "standard-5-point",
        "question": "What is Python?",
        "actual_answer": "Python is a programming language.",
        "expected_answer": "Python is an interpreted programming language.",
    }
    response = client.post("/api/v1/rubrics/evaluate", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["rubric_id"] == "standard-5-point"
    assert "raw_score" in data
    assert "normalized_score" in data
    assert "passed" in data
    assert "assigned_label" in data


def test_evaluate_with_rubric_unknown_id_returns_404(client: TestClient) -> None:
    payload = {
        "rubric_id": "does-not-exist",
        "question": "What is Python?",
        "actual_answer": "Language.",
    }
    response = client.post("/api/v1/rubrics/evaluate", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_evaluate_with_rubric_invalid_input_returns_400(client: TestClient) -> None:
    payload = {
        "rubric_id": "standard-5-point",
        "question": "   ",
        "actual_answer": "Language.",
    }
    response = client.post("/api/v1/rubrics/evaluate", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
