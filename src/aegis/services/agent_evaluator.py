"""Agent trajectory, tool selection, argument correctness, and sequence evaluation (Module 7)."""

from __future__ import annotations

import logging
from typing import Any

from aegis.domain.models.agent import (
    AgentEvaluationResult,
    AgentTrajectory,
    ToolCall,
)

logger = logging.getLogger(__name__)

# Standard tool set specified in spec_docs.md
STANDARD_TOOLS: set[str] = {"search", "calculator", "database", "web_search"}


def _longest_common_subsequence(seq1: list[str], seq2: list[str]) -> int:
    """Calculate the length of the longest common subsequence between two sequences."""
    m, n = len(seq1), len(seq2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i - 1] == seq2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[m][n]


class MockAgentToolRegistry:
    """Executes standard agent tools in simulation mode."""

    @staticmethod
    def execute(name: str, arguments: dict[str, Any]) -> str:
        """Mock execution of search, calculator, database, or web_search."""
        tool_name = name.lower()
        if tool_name == "calculator":
            expr = str(arguments.get("expression", "0"))
            try:
                # Safe evaluation of basic arithmetic
                allowed_chars = set("0123456789+-*/(). %")
                if not all(c in allowed_chars for c in expr):
                    return f"Error: Disallowed characters in expression '{expr}'"
                result = eval(expr, {"__builtins__": {}}, {})
                return str(result)
            except Exception as e:
                return f"Calculator error: {e}"

        elif tool_name == "database":
            query = str(arguments.get("query", ""))
            table = str(arguments.get("table", "records"))
            return f"Database query '{query}' executed on table '{table}': returned 1 match."

        elif tool_name == "search":
            q = str(arguments.get("query", ""))
            return f"Knowledge base search results for: '{q}'."

        elif tool_name == "web_search":
            q = str(arguments.get("query", ""))
            return f"Live web search results for: '{q}'."

        return f"Unknown tool: '{name}'"


class AgentTrajectoryEvaluator:
    """Evaluates agent tool selection, argument accuracy, ordering, efficiency, and completion."""

    def __init__(
        self,
        default_passing_threshold: float = 0.75,
        selection_weight: float = 0.25,
        arguments_weight: float = 0.25,
        sequence_weight: float = 0.20,
        completion_weight: float = 0.20,
        efficiency_weight: float = 0.10,
    ) -> None:
        self._threshold = default_passing_threshold
        self._w_selection = selection_weight
        self._w_args = arguments_weight
        self._w_seq = sequence_weight
        self._w_comp = completion_weight
        self._w_eff = efficiency_weight

    def evaluate_trajectory(
        self,
        trajectory: AgentTrajectory,
        passing_threshold: float | None = None,
    ) -> AgentEvaluationResult:
        """Evaluate an agent execution trace across all dimensions."""
        threshold = self._threshold if passing_threshold is None else passing_threshold
        reasons: list[str] = []

        executed_tools = [step.name.lower() for step in trajectory.steps]

        # 1. Evaluate Tool Selection
        selection_score = self._evaluate_tool_selection(
            executed_tools=executed_tools,
            expected_tools=trajectory.expected_tools,
            reasons=reasons,
        )

        # 2. Evaluate Tool Arguments
        arguments_score = self._evaluate_tool_arguments(
            steps=trajectory.steps,
            expected_arguments=trajectory.expected_arguments,
            reasons=reasons,
        )

        # 3. Evaluate Tool Sequence
        sequence_score = self._evaluate_tool_sequence(
            executed_tools=executed_tools,
            expected_sequence=trajectory.expected_sequence,
            reasons=reasons,
        )

        # 4. Evaluate Unnecessary Steps & Efficiency
        unnecessary_count, efficiency_score = self._evaluate_efficiency(
            steps=trajectory.steps,
            expected_tools=trajectory.expected_tools,
            reasons=reasons,
        )

        # 5. Evaluate Task Completion
        completion_score = self._evaluate_task_completion(
            trajectory=trajectory,
            reasons=reasons,
        )

        # Composite weighted score calculation
        overall_score = round(
            (selection_score * self._w_selection)
            + (arguments_score * self._w_args)
            + (sequence_score * self._w_seq)
            + (completion_score * self._w_comp)
            + (efficiency_score * self._w_eff),
            4,
        )

        passed = overall_score >= threshold and completion_score >= 0.70

        if passed:
            reasons.insert(
                0,
                f"OVERALL PASSED: Agent score {overall_score:.2f} met threshold {threshold:.2f}.",
            )
        else:
            reasons.insert(
                0,
                f"OVERALL FAILED: Agent score {overall_score:.2f} below threshold {threshold:.2f}.",
            )

        return AgentEvaluationResult(
            tool_selection_score=round(selection_score, 4),
            tool_arguments_score=round(arguments_score, 4),
            tool_sequence_score=round(sequence_score, 4),
            task_completion_score=round(completion_score, 4),
            efficiency_score=round(efficiency_score, 4),
            unnecessary_steps_count=unnecessary_count,
            overall_score=overall_score,
            passed=passed,
            diagnostic_reasons=reasons,
        )

    def _evaluate_tool_selection(
        self,
        executed_tools: list[str],
        expected_tools: list[str] | None,
        reasons: list[str],
    ) -> float:
        """Measure tool selection precision and recall against expected tools."""
        if not expected_tools:
            # If no specific expectations provided, verify executed tools belong to standard suite
            if not executed_tools:
                reasons.append("Tool Selection: No tools were executed.")
                return 0.5
            valid_count = sum(1 for t in executed_tools if t in STANDARD_TOOLS)
            score = valid_count / len(executed_tools)
            reasons.append(
                f"Tool Selection: {valid_count}/{len(executed_tools)} tools belong to "
                "standard tool suite."
            )
            return score

        exp_set = {t.lower() for t in expected_tools}
        exec_set = set(executed_tools)

        true_positives = len(exp_set & exec_set)
        recall = true_positives / len(exp_set) if exp_set else 1.0
        precision = true_positives / len(exec_set) if exec_set else 0.0

        f1 = (2 * precision * recall) / (precision + recall) if precision + recall > 0 else 0.0

        reasons.append(
            f"Tool Selection F1: {f1:.2f} (precision: {precision:.2f}, recall: {recall:.2f})."
        )
        return f1

    def _evaluate_tool_arguments(
        self,
        steps: list[ToolCall],
        expected_arguments: dict[str, dict[str, Any]] | None,
        reasons: list[str],
    ) -> float:
        """Verify that arguments passed to tools are well-formed and accurate."""
        if not steps:
            return 1.0

        valid_calls = 0
        total_calls = len(steps)

        for idx, step in enumerate(steps, start=1):
            args = step.arguments
            name = step.name.lower()
            is_valid = True

            # Schema sanity check
            if name in {"search", "web_search"}:
                if "query" not in args or not str(args.get("query", "")).strip():
                    is_valid = False
            elif name == "calculator":
                if "expression" not in args or not str(args.get("expression", "")).strip():
                    is_valid = False
            elif name == "database" and "query" not in args and "table" not in args:
                is_valid = False

            # Specific expected arguments check if provided
            if expected_arguments and name in expected_arguments:
                expected = expected_arguments[name]
                for key, val in expected.items():
                    if args.get(key) != val:
                        is_valid = False

            if is_valid:
                valid_calls += 1
            else:
                reasons.append(f"Tool Arguments: Invalid arguments at step {idx} for '{name}'.")

        score = valid_calls / total_calls
        reasons.append(f"Tool Arguments: {valid_calls}/{total_calls} calls passed schema checks.")
        return score

    def _evaluate_tool_sequence(
        self,
        executed_tools: list[str],
        expected_sequence: list[str] | None,
        reasons: list[str],
    ) -> float:
        """Measure alignment with expected tool invocation ordering."""
        if not expected_sequence:
            # If no expected sequence provided, default to full credit
            return 1.0

        if not executed_tools:
            reasons.append("Tool Sequence: No tools executed to compare against sequence.")
            return 0.0

        exp_seq = [t.lower() for t in expected_sequence]
        lcs_len = _longest_common_subsequence(executed_tools, exp_seq)

        score = lcs_len / len(exp_seq)
        reasons.append(
            f"Tool Sequence: Order alignment score {score:.2f} (LCS: {lcs_len}/{len(exp_seq)})."
        )
        return score

    def _evaluate_efficiency(
        self,
        steps: list[ToolCall],
        expected_tools: list[str] | None,
        reasons: list[str],
    ) -> tuple[int, float]:
        """Detect repeated consecutive identical tool calls or unnecessary steps."""
        if not steps:
            return 0, 1.0

        unnecessary_count = 0
        seen_calls: list[tuple[str, str]] = []

        for idx, step in enumerate(steps, start=1):
            arg_repr = str(sorted(step.arguments.items()))
            call_sig = (step.name.lower(), arg_repr)

            # Duplicate identical call check (spinning in loops)
            if call_sig in seen_calls:
                unnecessary_count += 1
                reasons.append(
                    f"Efficiency: Redundant duplicate call detected at step {idx} ('{step.name}')."
                )

            seen_calls.append(call_sig)

        # Efficiency penalty: 10% penalty per unnecessary step, min 0.0
        efficiency_score = max(0.0, 1.0 - (unnecessary_count * 0.15))
        return unnecessary_count, efficiency_score

    def _evaluate_task_completion(
        self,
        trajectory: AgentTrajectory,
        reasons: list[str],
    ) -> float:
        """Verify that the agent reached a valid terminal answer without unhandled error."""
        if not trajectory.final_answer or not trajectory.final_answer.strip():
            reasons.append("Task Completion: Agent failed to produce a final answer.")
            return 0.0

        # Check if last step produced an unhandled error
        if trajectory.steps and trajectory.steps[-1].error:
            reasons.append(
                f"Task Completion: Final tool step failed with error: {trajectory.steps[-1].error}"
            )
            return 0.3

        reasons.append("Task Completion: Agent reached valid final answer.")
        return 1.0
