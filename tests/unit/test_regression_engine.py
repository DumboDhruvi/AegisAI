"""Unit tests for RegressionEngine and BaselineStore (Module 9)."""

from __future__ import annotations

from pathlib import Path

import pytest

from aegis.domain.models.regression import (
    BaselineRecord,
    RegressionStatus,
)
from aegis.services.regression_engine import BaselineStore, RegressionEngine


def test_baseline_store_in_memory() -> None:
    """Test BaselineStore in-memory saving, retrieving, and listing."""
    store = BaselineStore()
    assert store.list_baselines() == []

    record = BaselineRecord(
        baseline_id="base-v1",
        dataset_version="golden-v1",
        model_id="gpt-4o-mini",
        metrics={"faithfulness": 0.90, "answer_relevance": 0.85},
    )
    store.save_baseline(record)

    assert store.list_baselines() == ["base-v1"]
    retrieved = store.get_baseline("base-v1")
    assert retrieved is not None
    assert retrieved.baseline_id == "base-v1"
    assert retrieved.metrics["faithfulness"] == 0.90
    assert store.get_baseline("nonexistent") is None


def test_baseline_store_disk_persistence(tmp_path: Path) -> None:
    """Test BaselineStore disk persistence and reload."""
    store = BaselineStore(storage_dir=tmp_path)
    record = BaselineRecord(
        baseline_id="base-disk",
        dataset_version="golden-v1",
        model_id="gpt-4o-mini",
        metrics={"faithfulness": 0.95},
    )
    store.save_baseline(record)

    # Verify file exists on disk
    file_path = tmp_path / "base-disk.json"
    assert file_path.exists()

    # Create new store pointing to same directory
    reloaded_store = BaselineStore(storage_dir=tmp_path)
    assert reloaded_store.list_baselines() == ["base-disk"]
    reloaded_record = reloaded_store.get_baseline("base-disk")
    assert reloaded_record is not None
    assert reloaded_record.metrics["faithfulness"] == 0.95


def test_baseline_store_corrupted_file_handling(tmp_path: Path) -> None:
    """Test graceful handling of invalid JSON files on disk."""
    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text("invalid json content", encoding="utf-8")

    store = BaselineStore(storage_dir=tmp_path)
    # Should skip corrupted file without crashing
    assert store.list_baselines() == []


def test_regression_engine_not_found() -> None:
    """Test that comparing against non-existent baseline raises KeyError."""
    engine = RegressionEngine()
    with pytest.raises(KeyError, match="not found in registry"):
        engine.compare(
            baseline_id="missing-base",
            current_version="v2.0",
            current_metrics={"faithfulness": 0.90},
        )


def test_regression_engine_improvement_and_stable() -> None:
    """Test comparison when metrics improve or remain within stability threshold."""
    store = BaselineStore()
    record = BaselineRecord(
        baseline_id="base-v1",
        dataset_version="v1",
        model_id="gpt-4o-mini",
        metrics={"faithfulness": 0.85, "answer_relevance": 0.80},
    )
    store.save_baseline(record)
    engine = RegressionEngine(baseline_store=store)

    # faithfulness improved (+0.05), answer_relevance stable (-0.02, within 0.05 drop)
    report = engine.compare(
        baseline_id="base-v1",
        current_version="v1.1",
        current_metrics={"faithfulness": 0.90, "answer_relevance": 0.78},
        max_allowed_drop=0.05,
    )

    assert report.has_regression is False
    assert report.passed is True
    assert "QUALITY GATE PASSED" in report.summary

    faith_comp = next(c for c in report.comparisons if c.metric_name == "faithfulness")
    assert faith_comp.status == RegressionStatus.IMPROVEMENT
    assert faith_comp.passed is True
    assert faith_comp.delta == 0.05

    rel_comp = next(c for c in report.comparisons if c.metric_name == "answer_relevance")
    assert rel_comp.status == RegressionStatus.STABLE
    assert rel_comp.passed is True
    assert rel_comp.delta == -0.02


def test_regression_engine_regression_detected() -> None:
    """Test detection of metric regression exceeding allowed drop."""
    store = BaselineStore()
    record = BaselineRecord(
        baseline_id="base-v1",
        dataset_version="v1",
        model_id="gpt-4o-mini",
        metrics={"faithfulness": 0.90, "answer_relevance": 0.85},
    )
    store.save_baseline(record)
    engine = RegressionEngine(baseline_store=store)

    # faithfulness dropped by 0.10 (exceeds default 0.05 tolerance)
    report = engine.compare(
        baseline_id="base-v1",
        current_version="v1.2",
        current_metrics={"faithfulness": 0.80, "answer_relevance": 0.85},
        max_allowed_drop=0.05,
    )

    assert report.has_regression is True
    assert report.passed is False
    assert "QUALITY GATE FAILED" in report.summary

    faith_comp = next(c for c in report.comparisons if c.metric_name == "faithfulness")
    assert faith_comp.status == RegressionStatus.REGRESSION
    assert faith_comp.passed is False
    assert faith_comp.delta == -0.10


def test_regression_engine_missing_metric() -> None:
    """Test that missing metric in current evaluation causes a regression failure."""
    store = BaselineStore()
    record = BaselineRecord(
        baseline_id="base-v1",
        dataset_version="v1",
        model_id="gpt-4o-mini",
        metrics={"faithfulness": 0.90, "answer_relevance": 0.85},
    )
    store.save_baseline(record)
    engine = RegressionEngine(baseline_store=store)

    # Missing answer_relevance completely
    report = engine.compare(
        baseline_id="base-v1",
        current_version="v1.3",
        current_metrics={"faithfulness": 0.92},
    )

    assert report.has_regression is True
    assert report.passed is False
    missing_comp = next(c for c in report.comparisons if c.metric_name == "answer_relevance")
    assert missing_comp.status == RegressionStatus.REGRESSION
    assert missing_comp.passed is False
    assert "CRITICAL: Metric 'answer_relevance' missing" in missing_comp.diagnostic
