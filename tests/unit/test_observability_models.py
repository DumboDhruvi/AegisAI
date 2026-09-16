"""Unit tests for Observability domain models (Module 12)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from aegis.domain.models.observability import (
    EvaluationTraceRecord,
    SpanType,
    TraceFilter,
    TraceSpan,
    TraceSummary,
)


def test_trace_span_creation() -> None:
    """Test valid TraceSpan instantiation."""
    now = datetime.now(timezone.utc)
    span = TraceSpan(
        span_id="span-1",
        name="VectorSearch",
        span_type=SpanType.RETRIEVAL,
        start_time=now,
        end_time=now,
        duration_ms=12.4,
        attributes={"top_k": 3},
    )
    assert span.span_id == "span-1"
    assert span.span_type == SpanType.RETRIEVAL
    assert span.duration_ms == 12.4


def test_trace_span_frozen() -> None:
    """Test immutability of TraceSpan."""
    now = datetime.now(timezone.utc)
    span = TraceSpan(
        span_id="span-1",
        name="Inference",
        span_type=SpanType.LLM_INFERENCE,
        start_time=now,
        end_time=now,
        duration_ms=250.0,
    )
    with pytest.raises(ValidationError):
        span.duration_ms = 300.0


def test_evaluation_trace_record_creation() -> None:
    """Test EvaluationTraceRecord serialization and fields."""
    record = EvaluationTraceRecord(
        run_id="run-101",
        request_id="req-999",
        model_name="gpt-4o",
        prompt="What is the refund policy?",
        answer="Refunds are processed within 30 days.",
        evaluation_results={"faithfulness": 0.95, "correctness": 0.90},
        passed=True,
        latency_ms={"retrieval": 15.0, "inference": 320.0, "total": 335.0},
        tokens={"prompt": 45, "completion": 18, "total": 63},
        cost_usd=0.00045,
    )
    assert record.run_id == "run-101"
    assert record.passed is True
    assert record.cost_usd == 0.00045
    assert record.tokens["total"] == 63


def test_trace_summary_metrics() -> None:
    """Test TraceSummary values."""
    summary = TraceSummary(
        total_traces=10,
        failed_traces=1,
        failure_rate=0.10,
        mean_latency_ms=450.5,
        total_tokens=1500,
        total_cost_usd=0.0125,
    )
    assert summary.total_traces == 10
    assert summary.failure_rate == 0.10


def test_trace_filter_creation() -> None:
    """Test TraceFilter default and custom bounds."""
    filter_obj = TraceFilter(passed=False, min_latency_ms=1000.0)
    assert filter_obj.passed is False
    assert filter_obj.min_latency_ms == 1000.0
    assert filter_obj.limit == 100
