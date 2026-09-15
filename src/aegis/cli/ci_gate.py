"""CLI entrypoint for running CI/CD AI Quality Gates (Module 11)."""

from __future__ import annotations

import argparse
import sys

from aegis.domain.models.cicd import QualityGateThresholds
from aegis.services.cicd_runner import CicdRunner


def main(argv: list[str] | None = None) -> int:
    """Run CI/CD quality gate check from command line."""
    parser = argparse.ArgumentParser(
        description="AegisAI CI/CD AI Evaluation Quality Gate Verification"
    )
    parser.add_argument("--commit", default="HEAD", help="Git commit hash")
    parser.add_argument("--branch", default="main", help="Git branch name")
    parser.add_argument("--pipeline-id", default="local-ci-1", help="CI Pipeline Run ID")
    parser.add_argument(
        "--faithfulness", type=float, default=0.92, help="Observed faithfulness score"
    )
    parser.add_argument(
        "--correctness", type=float, default=0.88, help="Observed correctness score"
    )
    parser.add_argument(
        "--hallucination-rate", type=float, default=0.03, help="Observed hallucination rate"
    )
    parser.add_argument(
        "--latency-p95", type=float, default=1200.0, help="Observed P95 latency in ms"
    )
    parser.add_argument(
        "--min-faithfulness", type=float, default=0.90, help="Min faithfulness threshold"
    )
    parser.add_argument(
        "--min-correctness", type=float, default=0.85, help="Min correctness threshold"
    )
    parser.add_argument(
        "--max-hallucination", type=float, default=0.05, help="Max hallucination threshold"
    )

    args = parser.parse_args(argv)

    thresholds = QualityGateThresholds(
        min_faithfulness=args.min_faithfulness,
        min_correctness=args.min_correctness,
        max_hallucination_rate=args.max_hallucination,
    )

    runner = CicdRunner(thresholds=thresholds)

    current_metrics = {
        "faithfulness": args.faithfulness,
        "correctness": args.correctness,
        "hallucination_rate": args.hallucination_rate,
        "latency_p95_ms": args.latency_p95,
    }

    report = runner.run_pipeline_check(
        pipeline_id=args.pipeline_id,
        git_commit=args.commit,
        branch=args.branch,
        unit_tests_passed=True,
        integration_tests_passed=True,
        current_metrics=current_metrics,
    )

    print("=" * 60)
    print(f" AegisAI CI Quality Gate Report: {report.pipeline_id}")
    print("=" * 60)
    for gate in report.quality_gate_results:
        symbol = "✓" if gate.passed else "✗"
        print(
            f" [{symbol}] {gate.gate_name:<20}: {gate.actual_value:.3f} "
            f"(Target: {gate.target_threshold:.3f}) - {gate.status}"
        )
    print("-" * 60)
    print(f" Summary: {report.summary}")
    print("=" * 60)

    return 0 if report.overall_passed else 1


if __name__ == "__main__":
    sys.exit(main())
