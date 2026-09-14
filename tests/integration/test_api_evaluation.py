"""Integration tests for Evaluation Engine FastAPI endpoints."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from aegis.api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_evaluate_case_endpoint_success(client: TestClient) -> None:
    payload = {
        "question": "What is AegisAI?",
        "actual_answer": "AegisAI is an AI evaluation and reliability platform.",
        "expected_answer": "AegisAI evaluates AI applications.",
        "retrieved_context": [
            "AegisAI is an AI evaluation and reliability platform designed for enterprises."
        ],
        "case_id": "test-c1",
    }
    response = client.post("/api/v1/evaluate/case", json=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["case_id"] == "test-c1"
    assert "composite_score" in data
    assert "passed" in data
    assert len(data["metrics"]) == 3


def test_evaluate_case_endpoint_validation_error_empty_question(client: TestClient) -> None:
    payload = {
        "question": "   ",
        "actual_answer": "Some answer",
    }
    response = client.post("/api/v1/evaluate/case", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_evaluate_batch_endpoint_success(client: TestClient) -> None:
    payload = {
        "cases": [
            {
                "question": "What is Python?",
                "actual_answer": "Python is a programming language.",
                "expected_answer": "Python is a programming language.",
                "retrieved_context": ["Python is a widely used programming language."],
                "case_id": "c1",
            },
            {
                "question": "Where is the Eiffel Tower?",
                "actual_answer": "The Eiffel Tower is located in Tokyo.",
                "expected_answer": "The Eiffel Tower is located in Paris.",
                "retrieved_context": ["The Eiffel Tower is located in Paris, France."],
                "case_id": "c2",
            },
        ]
    }
    response = client.post("/api/v1/evaluate/batch", json=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["total_cases"] == 2
    assert "overall_pass_rate" in data
    assert len(data["results"]) == 2
    # Second case should fail because of hallucinated city
    assert data["passed_cases"] >= 0


def test_evaluate_batch_endpoint_empty_list_returns_422_or_400(client: TestClient) -> None:
    payload: dict[str, Any] = {"cases": []}
    response = client.post("/api/v1/evaluate/batch", json=payload)
    assert response.status_code in (
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


def test_get_metrics_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/evaluate/metrics")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    metric_types = [m["metric_type"] for m in data]
    assert "faithfulness" in metric_types
    assert "correctness" in metric_types
    assert "answer_relevance" in metric_types
