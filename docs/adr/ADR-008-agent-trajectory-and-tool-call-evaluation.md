# ADR-008: Agent Trajectory Evaluation — Tool Selection, Arguments, Ordering, and Efficiency

- **Status:** Accepted
- **Date:** 2026-09-15
- **Decision Makers:** Human Engineer & AegisAI Assistant

## Context
Module 7 specifies the evaluation framework for autonomous AI agents executing multi-step workflows.
Autonomous agents utilize tool calls (`search()`, `calculator()`, `database()`, `web_search()`) across multi-step execution traces.
Evaluation criteria:
1. **Tool selection:** Did the agent choose the correct tools for the task without extraneous tools?
2. **Tool arguments:** Are the parameters structurally valid according to tool schema and accurate for the subtask?
3. **Tool sequence:** Did the agent invoke tools in a logical, coherent order?
4. **Task completion:** Did the agent reach a terminal solution fulfilling the prompt?
5. **Unnecessary steps:** Are there redundant, looping, or unneeded tool calls degrading efficiency?

## Decision
1. **Domain Models (`src/aegis/domain/models/agent.py`):**
   - `ToolCall`: Captures tool name, input arguments dictionary, output string, and error message.
   - `AgentTrajectory`: Captures task instruction, step-by-step tool trace, final response, expected tools, expected sequence, and expected arguments.
   - `AgentEvaluationResult`: Evaluates five dimensions:
     - `tool_selection_score` (Precision/Recall F1 against expected tools).
     - `tool_arguments_score` (Schema conformance and argument value validity).
     - `tool_sequence_score` (Longest Common Subsequence sequence alignment).
     - `task_completion_score` (Terminal answer presence and execution error absence).
     - `efficiency_score` (Penalty for repeated/redundant calls).
     - `overall_score` (Configurable weighted sum).
2. **Services (`src/aegis/services/agent_evaluator.py`):**
   - `MockAgentToolRegistry`: In-memory sandbox executing `search`, `calculator`, `database`, and `web_search` for simulations.
   - `AgentTrajectoryEvaluator`: Deterministic multi-criteria trace evaluation engine.
3. **FastAPI Endpoints (`src/aegis/api/routes/agent.py`):**
   - `POST /api/v1/agent/evaluate-trajectory`: Evaluates pre-recorded agent traces.
   - `POST /api/v1/agent/simulate-and-evaluate`: Executes tools dynamically and returns evaluation results.

## Consequences
- **Positive:**
  - Granular observability into agent planning, tool usage, argument quality, and trajectory efficiency.
  - Transparent diagnostic reasoning per evaluation dimension.
  - Deterministic and sub-millisecond execution for regression and CI/CD pipelines.
- **Trade-offs:**
  - Complex non-linear sequences (DAGs) are simplified to ordered sequences; LCS provides robust alignment for standard agent chains.
