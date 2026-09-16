"""Regression testing engine and baseline persistence store (Module 9)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from aegis.domain.models.regression import (
    BaselineRecord,
    RegressionComparison,
    RegressionReport,
    RegressionStatus,
)

logger = logging.getLogger(__name__)


class BaselineStore:
    """Manages persistence and retrieval of versioned baseline evaluation snapshots."""

    def __init__(self, storage_dir: Path | None = None) -> None:
        self._dir = storage_dir
        self._in_memory: dict[str, BaselineRecord] = {}

        if self._dir:
            self._dir.mkdir(parents=True, exist_ok=True)
            self._load_from_disk()

    def save_baseline(self, record: BaselineRecord) -> None:
        """Persist a baseline snapshot to memory and disk."""
        self._in_memory[record.baseline_id] = record
        if self._dir:
            file_path = self._dir / f"{record.baseline_id}.json"
            file_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")

    def get_baseline(self, baseline_id: str) -> BaselineRecord | None:
        """Retrieve a baseline record by its identifier."""
        return self._in_memory.get(baseline_id)

    def list_baselines(self) -> list[str]:
        """Return list of all registered baseline IDs."""
        return sorted(self._in_memory.keys())

    def _load_from_disk(self) -> None:
        """Load any existing baseline JSON files from storage directory."""
        if not self._dir or not self._dir.exists():
            return
        for path in self._dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                record = BaselineRecord.model_validate(data)
                self._in_memory[record.baseline_id] = record
            except Exception as e:
                logger.warning("Failed to load baseline file %s: %s", path, e)


class RegressionEngine:
    """Compares current evaluation metrics against baseline snapshots to prevent quality drops."""

    def __init__(self, baseline_store: BaselineStore | None = None) -> None:
        self._store = baseline_store or BaselineStore()

    @property
    def store(self) -> BaselineStore:
        return self._store

    def compare(
        self,
        baseline_id: str,
        current_version: str,
        current_metrics: dict[str, float],
        max_allowed_drop: float = 0.05,
    ) -> RegressionReport:
        """Compare current metrics against the specified baseline snapshot."""
        baseline = self._store.get_baseline(baseline_id)
        if baseline is None:
            raise KeyError(f"Baseline with ID '{baseline_id}' not found in registry.")

        comparisons: list[RegressionComparison] = []
        has_regression = False

        for metric_name, base_score in baseline.metrics.items():
            curr_score = current_metrics.get(metric_name)
            if curr_score is None:
                # Missing metric in current run is considered a regression failure
                delta = -base_score
                comparisons.append(
                    RegressionComparison(
                        metric_name=metric_name,
                        baseline_score=base_score,
                        current_score=0.0,
                        delta=round(delta, 4),
                        max_allowed_drop=max_allowed_drop,
                        status=RegressionStatus.REGRESSION,
                        passed=False,
                        diagnostic=f"CRITICAL: Metric '{metric_name}' missing in current run.",
                    )
                )
                has_regression = True
                continue

            delta = round(curr_score - base_score, 4)

            if curr_score < (base_score - max_allowed_drop):
                status = RegressionStatus.REGRESSION
                passed = False
                diagnostic = (
                    f"REGRESSION: {metric_name} dropped by {abs(delta):.3f} "
                    f"(baseline: {base_score:.3f} -> current: {curr_score:.3f}). "
                    f"Exceeds max allowed drop of {max_allowed_drop:.3f}."
                )
                has_regression = True
            elif curr_score > base_score:
                status = RegressionStatus.IMPROVEMENT
                passed = True
                diagnostic = (
                    f"IMPROVEMENT: {metric_name} increased by +{delta:.3f} "
                    f"(baseline: {base_score:.3f} -> current: {curr_score:.3f})."
                )
            else:
                status = RegressionStatus.STABLE
                passed = True
                diagnostic = (
                    f"STABLE: {metric_name} delta {delta:+.3f} is within acceptable bounds "
                    f"(baseline: {base_score:.3f} -> current: {curr_score:.3f})."
                )

            comparisons.append(
                RegressionComparison(
                    metric_name=metric_name,
                    baseline_score=base_score,
                    current_score=curr_score,
                    delta=delta,
                    max_allowed_drop=max_allowed_drop,
                    status=status,
                    passed=passed,
                    diagnostic=diagnostic,
                )
            )

        passed_overall = not has_regression

        if passed_overall:
            summary = (
                f"QUALITY GATE PASSED: All {len(comparisons)} metrics stable or improved "
                f"relative to baseline '{baseline_id}'."
            )
        else:
            regressed_names = [
                c.metric_name for c in comparisons if c.status == RegressionStatus.REGRESSION
            ]
            summary = (
                f"QUALITY GATE FAILED: Regression detected in metrics: "
                f"{', '.join(regressed_names)} relative to baseline '{baseline_id}'."
            )

        return RegressionReport(
            baseline_id=baseline_id,
            current_version=current_version,
            has_regression=has_regression,
            passed=passed_overall,
            comparisons=comparisons,
            summary=summary,
        )
