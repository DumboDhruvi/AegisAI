# AegisAI — Known Limitations & System Constraints

In accordance with Section 26 of [best_practices.md](file:///home/dumbo/AI%20PROJECT/best_practices.md), this document records known technical constraints, trade-offs, and failure modes across modules.

## Architecture & Evaluation Limitations

1. **LLM-as-a-Judge Variance:**
   - LLM evaluation metrics (semantic similarity, hallucination judgments) are inherently subject to non-deterministic model variation, prompt sensitivity, and alignment biases.
   - *Mitigation:* Always set model temperature to `0.0`, provide few-shot calibration examples in prompts, and pair semantic checks with deterministic schema and regex assertions.

2. **Approximate Vector Recall:**
   - Vector similarity search (e.g. pgvector HNSW / IVFFlat) trades off exact recall for query speed. Extreme top-k queries might miss edge documents under certain index parameters.
   - *Mitigation:* Benchmark retrieval recall across chunk sizes and index parameters during M2/M8.

3. **Context Window & Cost Budgets:**
   - Ingesting large document sets or complex multi-turn agent execution traces can exhaust token limits or induce significant API costs.
   - *Mitigation:* Strict token counting, chunk size enforcement, and configurable cost-limit gates.

4. **Synthetic Dataset Generalization:**
   - Evaluation datasets created offline may not fully capture production user behavior, adversarial typos, or domain shifts.
   - *Mitigation:* Versioned datasets with tagging (M1), robustness testing (M6), and regression suites (M9).
