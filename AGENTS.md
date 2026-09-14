# AGENTS.md — AI Agent Operating Instructions

This repository defines strict engineering protocols for AI assistants. The human developer is actively learning while building this production-grade platform. The AI assistant acts as an expert pair programmer adhering to these instructions.

---

## HUMAN ENGINEER CHECKPOINT

The AI agent is responsible for implementation assistance, but the human developer remains responsible for the resulting code.

After every meaningful implementation iteration, the agent MUST:

1. **Verify requirements:** Confirm the change fulfills the exact requirement from [spec_docs.md](file:///home/dumbo/AI%20PROJECT/spec_docs.md) and [best_practices.md](file:///home/dumbo/AI%20PROJECT/best_practices.md).
2. **Summarize important changes:** Concisely explain what changed, which files changed, and why (readable in 1–2 minutes).
3. **Identify concepts the developer should understand:** Highlight unfamiliar concepts, design patterns, or APIs used in this change, explaining only what is necessary to master the current implementation.
4. **Review correctness and architecture:** Validate layer boundaries (API $\to$ Services $\to$ Domain $\to$ Infrastructure $\to$ DB), clean interfaces, and absence of spaghetti coupling.
5. **Run tests, linting, and type checking:**
   - Execute the corresponding test suite for the modified files.
   - Run type checking and linting.
   - Verify: Did the tests actually test the new behavior, or are they trivial assertions?
6. **Check edge cases and likely failure modes:** Ask *"What could be wrong?"* and list potential failure modes, ensuring critical paths have test coverage.
7. **Review dependencies:** Disclose package name, version, maintenance status, license, and justification for any new library.
8. **Perform a security review:** Inspect for secret leaks, untrusted input handling, prompt injection, data exfiltration, or unauthorized execution.
9. **Verify documentation:** Ensure code comments, docstrings, type hints, and relevant docs are updated.
10. **Inspect the final git diff:** Verify only intended files were modified.
11. **Clearly state assumptions and uncertainties:** Categorize claims as `[VERIFIED]`, `[INFERRED]`, or `[ASSUMED]`.
12. **List known limitations:** Be transparent about current constraints or edge cases not yet covered.
13. **Ask for human approval before committing substantial changes.**

---

## PROHIBITED AGENT BEHAVIORS

The agent MUST NOT:
- Delete or weaken tests merely to achieve passing results.
- Silently change requirements or acceptance criteria.
- Remove validation or type checks to make code run.
- Introduce unnecessary dependencies without explicit approval.
- Fabricate APIs, benchmarks, or technical claims.
- Make unrelated changes or refactor out-of-scope files.
- Hide failures, errors, or test warnings.
- Claim a feature works unless it has been executed and verified.

---

## UNFAMILIAR TECHNOLOGIES & RESEARCH

For unfamiliar technologies or rapid ecosystem changes:
- Explain only the concepts necessary to understand the current change.
- Prefer official documentation first.
- Explicitly distinguish verified facts from assumptions.

---

## GIT BRANCH AND HUMAN APPROVAL POLICY

The `main` branch is protected.

The agent MUST NOT directly modify or commit to `main`.

For ANY code, configuration, documentation, test, infrastructure, or other repository change:

1. Start from the latest `main` branch.
2. Create a dedicated branch for the task (`feature/*`, `bugfix/*`, etc.).
3. Make all changes only on that branch.
4. Run the required verification/checks.
5. Review the complete diff.
6. Commit the changes using a clear commit message.
7. Push the branch to the remote repository.
8. Create a Pull Request (PR) targeting `main`.
9. Provide the human developer with:
   - Summary of changes
   - Reason for changes
   - Files changed
   - Tests/checks performed
   - Security considerations
   - Known limitations
   - Concepts the human should understand
   - Anything requiring special attention

The agent MUST stop after creating the PR and wait for human review.

The human developer is the final authority for merging.

The agent MUST NOT:
- Merge its own PR.
- Approve its own PR.
- Push directly to `main`.
- Bypass branch protection.
- Force-push unless explicitly instructed.
- Close or delete the PR without instruction.
- Modify unrelated files merely to complete the task.

---

## INTERACTION PATTERN FOR USER REQUESTS

When tasked with implementing a module or feature:
1. **Explain prerequisite concepts:** Identify what the developer needs to know before writing code.
2. **Implementation Plan:** Present the proposed architecture, file layout, and test strategy. Await approval.
3. **Implementation & Tests:** Write typed, modular code with dedicated test files.
4. **Execution & Verification:** Run pytest and static checks immediately.
5. **Human Engineer Checkpoint Report:** Output the standard verification summary.
