"""Integration tests for Robustness FastAPI routes (Module 6)."""

from __future__ import annotations

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from aegis.api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_api_perturb_endpoint_typos(client: TestClient) -> None:
    """Verify POST /api/v1/robustness/perturb with typo category."""
    payload = {
        "text": "PostgreSQL is a relational database management system.",
        "perturbation_type": "typos",
        "typo_rate": 0.2,
    }
    response = client.post("/api/v1/robustness/perturb", json=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["perturbation_type"] == "typos"
    assert data["original_text"] == payload["text"]
    assert data["perturbed_text"] != payload["text"]


def test_api_perturb_endpoint_prompt_injection(client: TestClient) -> None:
    """Verify POST /api/v1/robustness/perturb appends prompt injection."""
    payload = {
        "text": "What is the return policy for defective items?",
        "perturbation_type": "prompt_injection",
    }
    response = client.post("/api/v1/robustness/perturb", json=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["perturbation_type"] == "prompt_injection"
    assert "instructions" in data["perturbed_text"].lower()


def test_api_evaluate_case_endpoint(client: TestClient) -> None:
    """Verify POST /api/v1/robustness/evaluate-case comparative evaluation."""
    payload = {
        "baseline_input": {
            "question": "What is FastAPI?",
            "actual_answer": "FastAPI is a modern asynchronous web framework.",
            "expected_answer": "FastAPI is an async Python web framework.",
            "retrieved_context": ["FastAPI is a modern web framework."],
        },
        "perturbation_type": "typos",
        "max_degradation": 0.5,
    }
    response = client.post("/api/v1/robustness/evaluate-case", json=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["test_case_id"] == "api-rob-case-1"
    assert data["perturbation_type"] == "typos"
    assert "baseline_score" in data
    assert "perturbed_score" in data
    assert "robustness_passed" in data


def test_api_evaluate_suite_endpoint(client: TestClient) -> None:
    """Verify POST /api/v1/robustness/evaluate-suite runs multiple perturbations."""
    payload = {
        "baseline_inputs": [
            {
                "question": "What is Python?",
                "actual_answer": "Python is an interpreted programming language.",
                "expected_answer": "Python is a high-level programming language.",
                "retrieved_context": ["Python is an interpreted programming language."],
            }
        ],
        "perturbation_types": ["typos", "missing_info"],
        "max_degradation": 0.5,
    }
    response = client.post("/api/v1/robustness/evaluate-suite", json=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["total_tests"] == 2
    assert "robustness_score" in data
    assert "breakdown_by_type" in data
    assert len(data["comparisons"]) == 2
