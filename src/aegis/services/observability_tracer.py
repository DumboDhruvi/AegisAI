"""Observability, distributed tracing, and diagnostic reproduction service (Module 12)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from aegis.domain.models.observability import (
    EvaluationTraceRecord,
    TraceFilter,
    TraceSummary,
)

logger = logging.getLogger(__name__)


class ObservabilityTracer:
    """Manages recording, querying, summarizing, and reproducing evaluation traces."""

    def __init__(self, storage_dir: Path | None = None) -> None:
        self._dir = storage_dir
        self._traces: dict[str, EvaluationTraceRecord] = {}

        if self._dir:
            self._dir.mkdir(parents=True, exist_ok=True)
            self._load_from_disk()

    def record_trace(self, trace: EvaluationTraceRecord) -> None:
        """Store an evaluation trace in memory and optionally on disk."""
        self._traces[trace.run_id] = trace
        if self._dir:
            file_path = self._dir / f"{trace.run_id}.json"
            file_path.write_text(trace.model_dump_json(indent=2), encoding="utf-8")

    def get_trace(self, run_id: str) -> EvaluationTraceRecord | None:
        """Retrieve a trace record by its run ID."""
        return self._traces.get(run_id)

    def query_traces(self, filter_params: TraceFilter | None = None) -> list[EvaluationTraceRecord]:
        """Filter and retrieve recorded traces."""
        records = list(self._traces.values())

        if filter_params:
            if filter_params.model_name is not None:
                records = [r for r in records if r.model_name == filter_params.model_name]
            if filter_params.passed is not None:
                records = [r for r in records if r.passed == filter_params.passed]
            if filter_params.min_cost_usd is not None:
                records = [r for r in records if r.cost_usd >= filter_params.min_cost_usd]
            if filter_params.min_latency_ms is not None:
                min_lat = filter_params.min_latency_ms
                records = [r for r in records if r.latency_ms.get("total", 0.0) >= min_lat]
            records = records[: filter_params.limit]

        return records

    def get_trace_summary(self) -> TraceSummary:
        """Compute aggregated operational metrics across all stored traces."""
        total = len(self._traces)
        if total == 0:
            return TraceSummary(
                total_traces=0,
                failed_traces=0,
                failure_rate=0.0,
                mean_latency_ms=0.0,
                total_tokens=0,
                total_cost_usd=0.0,
            )

        failed_count = sum(1 for r in self._traces.values() if not r.passed)
        total_latency = sum(r.latency_ms.get("total", 0.0) for r in self._traces.values())
        total_tokens = sum(r.tokens.get("total", 0) for r in self._traces.values())
        total_cost = sum(r.cost_usd for r in self._traces.values())

        return TraceSummary(
            total_traces=total,
            failed_traces=failed_count,
            failure_rate=round(failed_count / total, 4),
            mean_latency_ms=round(total_latency / total, 2),
            total_tokens=total_tokens,
            total_cost_usd=round(total_cost, 6),
        )

    def reproduce_evaluation(self, run_id: str) -> dict[str, Any]:
        """Extract a structured diagnostic payload to reproduce and inspect a failed evaluation."""
        trace = self.get_trace(run_id)
        if trace is None:
            raise KeyError(f"Evaluation trace with run_id '{run_id}' not found.")

        retrieved_contexts = [doc.chunk.content for doc in trace.retrieved_documents]
        failed_metrics = {
            metric: score for metric, score in trace.evaluation_results.items() if score < 0.85
        }

        return {
            "run_id": trace.run_id,
            "request_id": trace.request_id,
            "timestamp": trace.timestamp.isoformat(),
            "model_name": trace.model_name,
            "prompt": trace.prompt,
            "retrieved_context_count": len(retrieved_contexts),
            "retrieved_contexts": retrieved_contexts,
            "tool_call_count": len(trace.tool_calls),
            "tool_calls": [t.model_dump() for t in trace.tool_calls],
            "actual_answer": trace.answer,
            "evaluation_results": trace.evaluation_results,
            "passed": trace.passed,
            "failed_metrics": failed_metrics,
            "latency_ms": trace.latency_ms,
            "tokens": trace.tokens,
            "cost_usd": trace.cost_usd,
            "diagnostic_instruction": (
                "Replay prompt and retrieved contexts against the specified model "
                "to isolate root cause of failed metrics."
            ),
        }

    def _load_from_disk(self) -> None:
        """Load stored traces from disk."""
        if not self._dir or not self._dir.exists():
            return
        for path in self._dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                record = EvaluationTraceRecord.model_validate(data)
                self._traces[record.run_id] = record
            except Exception as e:
                logger.warning("Failed to load trace file %s: %s", path, e)
