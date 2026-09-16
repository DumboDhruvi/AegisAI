"""Unit tests for ClaimExtractor and HallucinationDetector (Module 5)."""

from __future__ import annotations

import json

import pytest

from aegis.domain.models.grounding import ClaimStatus
from aegis.infrastructure.llm import MockLlmProvider
from aegis.services.hallucination_detector import ClaimExtractor, HallucinationDetector


def test_claim_extractor_basic_sentences() -> None:
    """Verify sentence splitting into atomic claims."""
    extractor = ClaimExtractor()
    text = "FastAPI is fast. It uses Pydantic for data validation. Uvicorn runs the server."
    claims = extractor.extract_claims(text)

    assert len(claims) == 3
    assert claims[0].claim_id == "claim-1"
    assert "FastAPI is fast." in claims[0].claim_text
    assert claims[1].claim_id == "claim-2"
    assert "Pydantic" in claims[1].claim_text
    assert claims[2].claim_id == "claim-3"
    assert "Uvicorn" in claims[2].claim_text


def test_claim_extractor_filters_conversational_filler() -> None:
    """Verify conversational greetings and closings are filtered."""
    extractor = ClaimExtractor()
    text = (
        "Hello! Sure thing. AegisAI evaluates enterprise RAG pipelines. "
        "It supports deterministic evaluation. Hope this helps!"
    )
    claims = extractor.extract_claims(text)

    # "Hello!", "Sure thing.", and "Hope this helps!" should be skipped
    assert len(claims) == 2
    assert "AegisAI evaluates enterprise RAG pipelines." in claims[0].claim_text
    assert "It supports deterministic evaluation." in claims[1].claim_text


def test_claim_extractor_empty_input() -> None:
    """Verify empty input returns empty claim list."""
    extractor = ClaimExtractor()
    assert extractor.extract_claims("") == []
    assert extractor.extract_claims("   \n\t  ") == []


@pytest.mark.asyncio
async def test_hallucination_detector_deterministic_supported() -> None:
    """Verify deterministic detector identifies well-grounded claims."""
    detector = HallucinationDetector(default_threshold=0.7)
    context = [
        "AegisAI is a testing platform for retrieval augmented generation. "
        "It provides modular evaluators and strict schema validation."
    ]
    answer = "AegisAI is a testing platform. It provides modular evaluators for RAG."

    report = await detector.verify(actual_answer=answer, retrieved_context=context)

    assert report.total_claims >= 1
    assert report.supported_claims >= 1
    assert report.contradictory_claims == 0
    assert report.grounding_ratio >= 0.7
    assert report.passed is True
    assert len(report.claims[0].evidence) > 0


@pytest.mark.asyncio
async def test_hallucination_detector_deterministic_hallucinated() -> None:
    """Verify detector identifies claims completely absent from context."""
    detector = HallucinationDetector(default_threshold=0.8)
    context = ["PostgreSQL is an open-source relational database."]
    answer = "The Eiffel Tower is located in Paris and was completed in 1889."

    report = await detector.verify(actual_answer=answer, retrieved_context=context)

    assert report.unsupported_claims >= 1
    assert report.grounding_ratio == 0.0
    assert report.hallucination_rate == 1.0
    assert report.passed is False


@pytest.mark.asyncio
async def test_hallucination_detector_deterministic_contradiction() -> None:
    """Verify detector identifies contradictory negation."""
    detector = HallucinationDetector()
    context = ["PostgreSQL supports vector similarity search via pgvector."]
    answer = "PostgreSQL cannot support vector similarity search."

    report = await detector.verify(actual_answer=answer, retrieved_context=context)

    assert report.contradictory_claims >= 1
    assert report.passed is False
    contradictory_verifications = [
        c for c in report.claims if c.status == ClaimStatus.CONTRADICTORY
    ]
    assert len(contradictory_verifications) > 0


@pytest.mark.asyncio
async def test_hallucination_detector_empty_context() -> None:
    """Verify empty context marks all claims unsupported."""
    detector = HallucinationDetector()
    answer = "Python 3.12 introduces improved error messages."

    report = await detector.verify(actual_answer=answer, retrieved_context=[])

    assert report.total_claims == 1
    assert report.unsupported_claims == 1
    assert report.passed is False


@pytest.mark.asyncio
async def test_hallucination_detector_llm_judge() -> None:
    """Verify LLM-as-a-judge claim verification with structured output."""
    mock_payload = {
        "summary": "Answer is fully grounded in the documentation.",
        "claims": [
            {
                "claim_id": "claim-1",
                "status": "supported",
                "confidence": 0.98,
                "evidence": [
                    {
                        "context_index": 0,
                        "citation_text": "AegisAI uses pgvector for embeddings.",
                        "similarity_score": 0.95,
                    }
                ],
                "reason": "Directly confirmed by retrieved passage.",
            }
        ],
    }
    llm = MockLlmProvider(fixed_response=json.dumps(mock_payload))
    detector = HallucinationDetector(llm_provider=llm)

    context = ["AegisAI uses pgvector for embeddings."]
    answer = "AegisAI uses pgvector for embeddings."

    report = await detector.verify(actual_answer=answer, retrieved_context=context)

    assert report.total_claims == 1
    assert report.supported_claims == 1
    assert report.passed is True
    assert report.claims[0].status == ClaimStatus.SUPPORTED
    assert report.claims[0].confidence == 0.98
    assert len(report.claims[0].evidence) == 1
    assert report.claims[0].evidence[0].citation_text == "AegisAI uses pgvector for embeddings."


@pytest.mark.asyncio
async def test_hallucination_detector_llm_fallback_on_invalid_json() -> None:
    """Verify graceful fallback to deterministic evaluation if LLM fails."""
    llm = MockLlmProvider(fixed_response="Invalid Non-JSON response")
    detector = HallucinationDetector(llm_provider=llm)

    context = ["FastAPI is an async framework."]
    answer = "FastAPI is an async framework."

    report = await detector.verify(actual_answer=answer, retrieved_context=context)

    # Should have fallen back to deterministic and still succeeded
    assert report.total_claims == 1
    assert report.supported_claims == 1
    assert report.passed is True
