"""Unit tests for PerturbationEngine (Module 6)."""

from __future__ import annotations

from aegis.domain.models.evaluation import EvaluationInput
from aegis.domain.models.robustness import PerturbationType
from aegis.services.perturbation_engine import PerturbationEngine


def test_apply_typos_modifies_text() -> None:
    """Verify typo generator modifies characters using keyboard neighbors."""
    engine = PerturbationEngine(seed=123)
    text = "FastAPI provides high performance asynchronous web APIs."
    res = engine.apply_typos(text, typo_rate=0.2)

    assert res.perturbation_type == PerturbationType.TYPOS
    assert res.original_text == text
    assert res.perturbed_text != text
    assert len(res.perturbed_text) == len(text)
    assert res.metadata["modifications"] > 0


def test_apply_typos_empty_string() -> None:
    """Verify empty text produces clean empty result."""
    engine = PerturbationEngine()
    res = engine.apply_typos("")
    assert res.perturbed_text == ""


def test_apply_ambiguity_replaces_entities() -> None:
    """Verify entity replacement with ambiguous terms."""
    engine = PerturbationEngine()
    text = "How does FastAPI interact with PostgreSQL?"
    res = engine.apply_ambiguity(text)

    assert res.perturbation_type == PerturbationType.AMBIGUITY
    assert "FastAPI" not in res.perturbed_text
    assert "PostgreSQL" not in res.perturbed_text
    assert "this system" in res.perturbed_text


def test_apply_missing_info_truncates_clauses() -> None:
    """Verify stripping of conditional clauses."""
    engine = PerturbationEngine()
    text = "How does caching work, when running across multiple worker nodes?"
    res = engine.apply_missing_info(text)

    assert res.perturbation_type == PerturbationType.MISSING_INFO
    assert res.perturbed_text == "How does caching work?"


def test_inject_conflicting_docs() -> None:
    """Verify contradiction prepending in context."""
    engine = PerturbationEngine()
    context = ["PostgreSQL provides strict ACID transactional safety."]
    perturbed = engine.inject_conflicting_docs(context)

    assert len(perturbed) == 2
    assert "CORRECTION" in perturbed[0]
    assert "completely false" in perturbed[0]


def test_inject_irrelevant_docs() -> None:
    """Verify irrelevant distractor document injection."""
    engine = PerturbationEngine(seed=42)
    context = ["Machine learning models evaluate semantic similarity."]
    perturbed = engine.inject_irrelevant_docs(context, count=2)

    assert len(perturbed) == 3
    assert perturbed[0] == context[0]
    # Distractors should contain non-ML topics (photosynthesis, Apollo, bread)
    assert any("Photosynthesis" in d or "Apollo" in d or "sourdough" in d for d in perturbed[1:])


def test_inject_prompt_injection() -> None:
    """Verify prompt injection attack string appending."""
    engine = PerturbationEngine(seed=42)
    text = "Summarize the customer refund policy."
    res = engine.inject_prompt_injection(text)

    assert res.perturbation_type == PerturbationType.PROMPT_INJECTION
    assert (
        "Disregard all prior instructions" in res.perturbed_text
        or "simulation" in res.perturbed_text
    )


def test_generate_out_of_domain() -> None:
    """Verify out-of-domain query generation."""
    engine = PerturbationEngine(seed=42)
    res = engine.generate_out_of_domain("What is AegisAI?")

    assert res.perturbation_type == PerturbationType.OUT_OF_DOMAIN
    assert res.perturbed_text != "What is AegisAI?"
    assert len(res.perturbed_text) > 10


def test_create_robustness_test_case_all_types() -> None:
    """Verify create_robustness_test_case supports every PerturbationType."""
    engine = PerturbationEngine(seed=42)
    base_input = EvaluationInput(
        question="What is FastAPI?",
        actual_answer="FastAPI is a Python web framework.",
        expected_answer="FastAPI is a modern Python framework.",
        retrieved_context=["FastAPI is built on Starlette and Pydantic."],
    )

    for p_type in PerturbationType:
        test_case = engine.create_robustness_test_case(base_input, p_type, case_id=f"tc-{p_type}")
        assert test_case.perturbation_type == p_type
        assert test_case.baseline_input == base_input
        assert test_case.perturbed_input is not None
