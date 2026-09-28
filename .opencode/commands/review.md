---
description: Adversarially review and verify the current TASK.md implementation
agent: review
subtask: false
---

Review independently as the primary `review` agent in this thread using the selected model. Do not delegate, spawn child/subagent sessions, or invoke skills.

## Scope and classification

Read `TASK.md` first and applicable repository instructions. Stop if the task is missing, empty, materially ambiguous, or conflicts with newer developer instructions.

Establish the pre-review baseline: `git status --short`, relevant staged/unstaged diffs, and task-relevant untracked files. All tests present at this point belong to the baseline, including implementation-created and untracked tests. Preserve them.

Classify before choosing checks: SMALL TEST-ONLY (localized test assertions/cases, no changed shared fixtures/helpers/configuration or production code) or broader/risk-bearing change. Identify the changed behavior and 1–3 realistic risks against the acceptance criteria. Batch independent reads and reuse evidence.

## Small test-only fast path

1. Inspect the changed test and its setup.
2. Inspect only production behavior needed to understand what the assertion proves.
3. Independently run exactly ONE targeted test first, using its precise node ID/name filter, not the whole file.
4. If it passes, directly demonstrates the acceptance criteria, and inspection finds no plausible material issue, return the verdict. Do not run a final confirmation test.

Do not automatically run the full modified test file, backend suite, unrelated RAG/regression or security suites, Ruff, MyPy, basedpyright, Pylint, complexity checks, or frontend checks. A RAG test location alone is not a risky pipeline change.

Actively challenge whether the assertion proves the intended behavior or could pass despite a defect. The implementer's reported results are not independent verification. Escalate only for concrete evidence or an explicit required task check; briefly identify the trigger and choose checks addressing it.

## Escalation

Triggers: targeted failure, production/shared/core behavior changes, security/auth/isolation/data-integrity impact, cross-cutting RAG impact, insufficient test evidence, suspicious code, or a plausible regression.

For production changes, inspect affected behavior/callers and code quality, run focused regression tests and relevant area checks; broaden for the specific risk. Full suites and broad quality gates are conditional. Stop when acceptance criteria and material risks have sufficient evidence.

A failing pre-review test normally ends the fast path after enough inspection to explain the failure. Do not run unrelated suites to offset that failure.

## Test ownership

If ANY test/assertion/case present before review fails: preserve it unchanged and return `CHANGES_REQUIRED`. Do not modify, repair, weaken, skip, delete, rewrite, or make it match current production behavior. This includes apparently incorrect tests, implementation-created tests, and their fixtures/helpers. Explain the failure; resolution belongs to `/implement`.

Add NEW independent tests only when they materially improve coverage of boundaries, regressions, failure modes, or behavior the implementer did not demonstrate. Do not mirror implementation details.

Always create a new uniquely named independent test file in `backend/tests/reviewer_<unique_name>.py` or `frontend/test/reviewer_<unique_name>.test.ts[x]`. Check that the path is unused before creating it. Never overwrite or reuse an existing reviewer test file, or modify any test that existed before review. Keep new fixtures/helpers in the new file only when required.

Writes in this namespace and allowed test runs proceed automatically without approval. Run backend reviewer files by explicit path because `reviewer_*.py` may not match default pytest discovery. V1 path rules cannot distinguish creation from overwrite, so enforce fresh names before every new file. Do not broaden permissions or write via shell commands to bypass them.

Leave reviewer-created tests with lasting regression value. If one fails, return `CHANGES_REQUIRED` without fixing production code. Remove temporary probes only if they have no lasting value and were created during the current review.

## Execution and verdict

Use `bash.workdir` set to absolute `backend/` with `poetry run`, or absolute `frontend/` with npm scripts. Put only the check command in `command`, without `cd`. Example: `poetry run pytest tests/test_rag_service_unit.py::TestQueryProcessing::test_answer_query_no_relevant_documents`.

Never modify production code, `TASK.md`, configuration, dependencies, or documentation, including through commands or test/helper code. Do not mutate Git state, bypass permissions, install dependencies, use fix/write/update flags or redirection, or substitute environments. Costly LLM/API evaluations require explicit task/developer authorization.

Check final status and inspect any reviewer-created changes against the baseline; do not rerun passing checks without new evidence.

`PASS` requires evidence for every acceptance criterion, passing material independent verification, no material finding, and no prohibited reviewer edits. Otherwise return `CHANGES_REQUIRED`, including when material verification is blocked.

Use exactly the following compact report. Give findings file/line references and impact. Use None where appropriate; under Not run list only material blocked checks, not every unused tool. Do not narrate internal phases.

## Verdict

PASS or CHANGES_REQUIRED

## Findings

...

## Independent tests

Added:

- ...

Result:

- ...

## Validation

Executed:

- ...

Inspected:

- ...

Not run:

- ...

## Reviewer changes

- ...
