"""LLM provider interfaces and implementations."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol


class LlmProvider(Protocol):
    """Protocol defining the interface for generating answers from context and prompts."""

    def generate(self, prompt: str, context: Sequence[str]) -> str:
        """Generate an answer given a prompt and retrieved context snippets."""
        ...


class MockLlmProvider:
    """Deterministic LLM provider for unit tests, offline evaluation, and CI pipelines."""

    def __init__(self, fixed_response: str | None = None) -> None:
        self.fixed_response = fixed_response
        self.call_count = 0
        self.last_prompt: str | None = None
        self.last_context: list[str] = []

    def generate(self, prompt: str, context: Sequence[str]) -> str:
        """Generate a response incorporating the question and grounded context."""
        self.call_count += 1
        self.last_prompt = prompt
        self.last_context = list(context)

        if self.fixed_response:
            return self.fixed_response

        if not context:
            return f"I do not have enough context to answer: '{prompt}'."

        # Synthesize a clean grounded answer referencing the top context chunk
        top_context = context[0]
        return f"Based on the provided documentation: {top_context}"
