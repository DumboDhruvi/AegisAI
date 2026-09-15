"""Unit tests for ObservabilityTracer service (Module 12)."""

from __future__ import annotations

from pathlib import Path

import pytest

from aegis.domain.models.agent import ToolCall
from aegis.domain.models.observability import (
    EvaluationTraceRecord,
    TraceFilter,
)
from aegis.domain.models.rag import DocumentChunk, RetrievedDocument
from aegis.services.observability_tracer import ObservabilityTracer


def test_tracer_record_and_get() -> None:
    """Test in-memory trace recording and retrieval."""
    tracer = ObservabilityTracer()
    record = EvaluationTraceRecord(
        run_id="run-1",
        request_id="req-1",
        model_name="gpt-4o",
        prompt="Explain vector search",
        answer="Vector search uses cosine similarity.",
        passed=True,
    )
    tracer.record_trace(record)

    retrieved = tracer.get_trace("run-1")
    assert retrieved is not None
    assert retrieved.run_id == "run-1"
    assert tracer.get_trace("unknown") is None


def test_tracer_disk_persistence(tmp_path: Path) -> None:
    """Test disk persistence and reload of traces."""
    tracer = ObservabilityTracer(storage_dir=tmp_path)
    record = EvaluationTraceRecord(
        run_id="run-disk-1",
        request_id="req-disk-1",
        model_name="gpt-4o-mini",
        prompt="What is AegisAI?",
        answer="AegisAI is an evaluation platform.",
        cost_usd=0.001,
        tokens={"total": 50},
        latency_ms={"total": 200.0},
    )
    tracer.record_trace(record)
    assert (tmp_path / "run-disk-1.json").exists()

    reloaded = ObservabilityTracer(storage_dir=tmp_path)
    reloaded_record = reloaded.get_trace("run-disk-1")
    assert reloaded_record is not None
    assert reloaded_record.model_name == "gpt-4o-mini"
    assert reloaded_record.cost_usd == 0.001


def test_tracer_query_filtering() -> None:
    """Test filtering traces by model name, passed status, cost, and latency."""
    tracer = ObservabilityTracer()
    rec1 = EvaluationTraceRecord(
        run_id="run-pass-1",
        request_id="req-1",
        model_name="gpt-4o",
        prompt="P1",
        answer="A1",
        passed=True,
        cost_usd=0.010,
        latency_ms={"total": 150.0},
    )
    rec2 = EvaluationTraceRecord(
        run_id="run-fail-1",
        request_id="req-2",
        model_name="gpt-4o-mini",
        prompt="P2",
        answer="A2",
        passed=False,
        cost_usd=0.002,
        latency_ms={"total": 450.0},
    )
    rec3 = EvaluationTraceRecord(
        run_id="run-pass-2",
        request_id="req-3",
        model_name="gpt-4o",
        prompt="P3",
        answer="A3",
        passed=True,
        cost_usd=0.015,
        latency_ms={"total": 800.0},
    )
    tracer.record_trace(rec1)
    tracer.record_trace(rec2)
    tracer.record_trace(rec3)

    # Filter only failed runs
    failed = tracer.query_traces(TraceFilter(passed=False))
    assert len(failed) == 1
    assert failed[0].run_id == "run-fail-1"

    # Filter by model name
    gpt4 = tracer.query_traces(TraceFilter(model_name="gpt-4o"))
    assert len(gpt4) == 2

    # Filter by min latency
    slow = tracer.query_traces(TraceFilter(min_latency_ms=400.0))
    assert len(slow) == 2


def test_tracer_summary_aggregation() -> None:
    """Test summary operational metrics computation."""
    tracer = ObservabilityTracer()
    empty_summary = tracer.get_trace_summary()
    assert empty_summary.total_traces == 0
    assert empty_summary.failure_rate == 0.0

    rec1 = EvaluationTraceRecord(
        run_id="r1",
        request_id="q1",
        model_name="m1",
        prompt="p1",
        answer="a1",
        passed=True,
        latency_ms={"total": 200.0},
        tokens={"total": 100},
        cost_usd=0.002,
    )
    rec2 = EvaluationTraceRecord(
        run_id="r2",
        request_id="q2",
        model_name="m1",
        prompt="p2",
        answer="a2",
        passed=False,
        latency_ms={"total": 400.0},
        tokens={"total": 200},
        cost_usd=0.004,
    )
    tracer.record_trace(rec1)
    tracer.record_trace(rec2)

    summary = tracer.get_trace_summary()
    assert summary.total_traces == 2
    assert summary.failed_traces == 1
    assert summary.failure_rate == 0.50
    assert summary.mean_latency_ms == 300.0
    assert summary.total_tokens == 300
    assert summary.total_cost_usd == 0.006


def test_reproduce_evaluation_payload() -> None:
    """Test diagnostic reproduction payload extraction for debugging failed runs."""
    tracer = ObservabilityTracer()
    chunk = DocumentChunk(
        chunk_id="c-1",
        document_id="doc-1",
        content="Ground truth context chunk",
        chunk_index=0,
        start_char=0,
        end_char=26,
    )
    retrieved = RetrievedDocument(chunk=chunk, similarity_score=0.91)
    tool = ToolCall(name="calculator", arguments={"expr": "2+2"}, output="4")

    record = EvaluationTraceRecord(
        run_id="run-failed-eval",
        request_id="req-fail-42",
        model_name="gpt-4o",
        prompt="Calculate ROI",
        retrieved_documents=[retrieved],
        tool_calls=[tool],
        answer="ROI is 15%",
        evaluation_results={"faithfulness": 0.60, "correctness": 0.95},
        passed=False,
    )
    tracer.record_trace(record)

    payload = tracer.reproduce_evaluation("run-failed-eval")
    assert payload["run_id"] == "run-failed-eval"
    assert payload["prompt"] == "Calculate ROI"
    assert payload["retrieved_context_count"] == 1
    assert payload["retrieved_contexts"][0] == "Ground truth context chunk"
    assert payload["tool_call_count"] == 1
    assert "faithfulness" in payload["failed_metrics"]
    assert "correctness" not in payload["failed_metrics"]

    with pytest.raises(KeyError, match="not found"):
        tracer.reproduce_evaluation("nonexistent-run")
