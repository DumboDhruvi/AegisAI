"""Integration tests for FastAPI RAG endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aegis.api.main import app

client = TestClient(app)


def test_rag_ingest_and_query_flow() -> None:
    """Ensure documents can be ingested via API and subsequently queried."""
    ingest_payload = {
        "documents": [
            {
                "id": "doc-api-policy",
                "content": "All employees receive 25 days of paid annual leave.",
                "metadata": {"source": "hr-handbook", "category": "benefits"},
            }
        ]
    }

    # 1. Ingest
    ingest_res = client.post("/api/v1/rag/ingest", json=ingest_payload)
    assert ingest_res.status_code == 201
    ingest_data = ingest_res.json()
    assert ingest_data["status"] == "success"
    assert ingest_data["chunks_indexed"] >= 1
    assert ingest_data["total_stored_chunks"] >= 1

    # 2. Query
    query_payload = {
        "question": "How many days of paid annual leave do employees receive?",
        "top_k": 2,
    }
    query_res = client.post("/api/v1/rag/query", json=query_payload)
    assert query_res.status_code == 200
    query_data = query_res.json()

    # Verify 3 required elements
    assert "answer" in query_data
    assert "retrieved_documents" in query_data
    assert "metadata" in query_data

    assert len(query_data["answer"]) > 0
    assert len(query_data["retrieved_documents"]) >= 1
    assert query_data["retrieved_documents"][0]["chunk"]["document_id"] == "doc-api-policy"
    assert "hr-handbook" in query_data["retrieved_documents"][0]["chunk"]["metadata"]["source"]


def test_rag_ingest_empty_list_returns_400() -> None:
    """Ensure submitting empty documents list yields 400."""
    res = client.post("/api/v1/rag/ingest", json={"documents": []})
    assert res.status_code == 400
    assert "empty document list" in res.json()["detail"]


def test_rag_query_empty_question_returns_400() -> None:
    """Ensure empty query question yields 400."""
    res = client.post("/api/v1/rag/query", json={"question": "   "})
    assert res.status_code == 400
    assert "cannot be empty" in res.json()["detail"]


def test_rag_stats_endpoint() -> None:
    """Ensure stats endpoint returns stored chunks count."""
    res = client.get("/api/v1/rag/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total_chunks" in data
    assert data["total_chunks"] >= 0
