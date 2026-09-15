"""Integration tests for Grounding & Hallucination FastAPI endpoints (Module 5)."""

from __future__ import annotations

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from aegis.api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_extract_claims_endpoint(client: TestClient) -> None:
    """Verify POST /api/v1/grounding/extract-claims extracts sentences."""
    payload = {
        "text": (
            "AegisAI evaluates RAG pipelines. It includes an evaluation engine and rubric system."
        )
    }
    response = client.post("/api/v1/grounding/extract-claims", json=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["claim_id"] == "claim-1"
    assert "AegisAI" in data[0]["claim_text"]


def test_extract_claims_rejects_empty_payload(client: TestClient) -> None:
    """Verify validation error on empty text string."""
    response = client.post("/api/v1/grounding/extract-claims", json={"text": ""})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_verify_grounding_endpoint_supported(client: TestClient) -> None:
    """Verify POST /api/v1/grounding/verify passes when answer is grounded."""
    payload = {
        "actual_answer": "PostgreSQL is a relational database. It supports ACID compliance.",
        "retrieved_context": [
            "PostgreSQL is a powerful open-source relational database.",
            "It strictly adheres to ACID compliance guarantees.",
        ],
        "question": "What is PostgreSQL?",
        "threshold": 0.7,
    }
    response = client.post("/api/v1/grounding/verify", json=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["total_claims"] == 2
    assert data["supported_claims"] == 2
    assert data["contradictory_claims"] == 0
    assert data["passed"] is True
    assert data["grounding_ratio"] >= 0.7


def test_verify_grounding_endpoint_hallucinated(client: TestClient) -> None:
    """Verify POST /api/v1/grounding/verify fails when answer is hallucinated."""
    payload = {
        "actual_answer": "Mars has oceans of liquid methane and alien life.",
        "retrieved_context": ["Mars is the fourth planet from the Sun with a thin atmosphere."],
        "question": "Does Mars have life?",
        "threshold": 0.8,
    }
    response = client.post("/api/v1/grounding/verify", json=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["passed"] is False
    assert data["unsupported_claims"] >= 1
