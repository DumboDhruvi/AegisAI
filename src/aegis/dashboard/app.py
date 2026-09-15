"""AegisAI Enterprise Reliability & Evaluation Dashboard (Module 14).

Streamlit multi-tab diagnostic interface displaying:
- Overview (Reliability, Faithfulness, Correctness, Relevance, Robustness, Hallucination)
- Runs (Historical evaluation executions)
- Failed Tests (Diagnostic drill-down & reproduction)
- Models (Model pricing and latency characteristics)
- Benchmarks (Comparative multi-model trade-offs & Pareto frontier)
- Agents (Autonomous agent trajectory evaluations & tool trace efficiency)
- Regression (Baseline comparison & automated quality gate diffing)
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from aegis.services.dashboard_data import DashboardDataService


def render_dashboard(service: DashboardDataService | None = None) -> None:
    """Render the comprehensive AegisAI Streamlit dashboard."""
    data_service = service or DashboardDataService()

    st.set_page_config(
        page_title="AegisAI Reliability Platform",
        page_icon="🛡️",
        layout="wide",
    )

    st.title("🛡️ AegisAI — Enterprise AI Reliability & Evaluation Platform")
    st.markdown(
        "Continuous Evaluation, Grounding, Robustness, Benchmarking, and Regression Testing."
    )

    # 1. Executive Summary Metric Banner
    overview = data_service.get_overview()
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Reliability", f"{overview.overall_reliability * 100:.1f}%")
    col2.metric("Faithfulness", f"{overview.faithfulness * 100:.1f}%")
    col3.metric("Correctness", f"{overview.correctness * 100:.1f}%")
    col4.metric("Relevance", f"{overview.relevance * 100:.1f}%")
    col5.metric("Robustness", f"{overview.robustness * 100:.1f}%")
    col6.metric("Hallucination", f"{overview.hallucination_rate * 100:.1f}%")

    st.divider()

    # 2. Tabs
    tab_names = [
        "Overview",
        "Runs",
        "Failed Tests",
        "Models",
        "Benchmarks",
        "Agents",
        "Regression",
    ]
    tabs = st.tabs(tab_names)

    # Tab 1: Overview
    with tabs[0]:
        st.subheader("Platform Health & Reliability Overview")
        st.write(
            f"Evaluated **{overview.total_evaluations}** test cases. "
            f"**{overview.passed_evaluations}** passed quality gates "
            f"({overview.passed_evaluations / overview.total_evaluations * 100:.1f}% pass rate)."
        )
        overview_data = {
            "Dimension": [
                "Faithfulness",
                "Correctness",
                "Relevance",
                "Robustness",
                "Safety (1 - Hallucination)",
            ],
            "Score": [
                overview.faithfulness,
                overview.correctness,
                overview.relevance,
                overview.robustness,
                1.0 - overview.hallucination_rate,
            ],
        }
        df_overview = pd.DataFrame(overview_data)
        st.bar_chart(df_overview.set_index("Dimension"))

    # Tab 2: Runs
    with tabs[1]:
        st.subheader("Evaluation Execution History")
        runs = data_service.get_runs()
        df_runs = pd.DataFrame(runs)
        st.dataframe(df_runs, use_container_width=True)

    # Tab 3: Failed Tests
    with tabs[2]:
        st.subheader("Diagnostic Failure Drill-Down")
        failed_tests = data_service.get_failed_tests()
        if not failed_tests:
            st.success("Zero failed evaluations detected across recent runs.")
        else:
            for item in failed_tests:
                with st.expander(f"⚠️ {item['run_id']}: {item['prompt'][:60]}..."):
                    st.markdown(f"**Target Model:** `{item['model']}`")
                    st.markdown(
                        f"**Failed Metric:** `{item['failed_metric']}` "
                        f"(Score: `{item['score']:.2f}`, Target: `{item['target_threshold']:.2f}`)"
                    )
                    st.markdown(f"**Retrieved Context:**\n> {item['retrieved_context']}")
                    st.markdown(f"**Actual Answer:**\n> {item['actual_answer']}")
                    st.error(f"**Diagnostic Root Cause:** {item['diagnostic']}")

    # Tab 4: Models
    with tabs[3]:
        st.subheader("Model Latency & Pricing Profiles")
        models = data_service.get_models()
        df_models = pd.DataFrame(models)
        st.dataframe(df_models, use_container_width=True)

    # Tab 5: Benchmarks
    with tabs[4]:
        st.subheader("Multi-Model Comparative Benchmarking & Pareto Frontier")
        benchmarks = data_service.get_benchmarks()
        df_bench = pd.DataFrame(benchmarks)
        st.dataframe(df_bench, use_container_width=True)
        st.info(
            "💡 Highlight: GPT-4o delivers top quality; GPT-4o-mini provides Pareto efficiency."
        )

    # Tab 6: Agents
    with tabs[5]:
        st.subheader("Autonomous Agent Trajectory Evaluations")
        agents = data_service.get_agents()
        df_agents = pd.DataFrame(agents)
        st.dataframe(df_agents, use_container_width=True)

    # Tab 7: Regression
    with tabs[6]:
        st.subheader("Baseline Diffing & Regression Quality Gates")
        regressions = data_service.get_regression_baselines()
        df_regr = pd.DataFrame(regressions)
        st.dataframe(df_regr, use_container_width=True)


if __name__ == "__main__":
    render_dashboard()
