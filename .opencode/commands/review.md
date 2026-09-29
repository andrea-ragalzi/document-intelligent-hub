---
description: Independently review architecture, maintainability and canonical quality checks
agent: review
subtask: false
---

Review as the primary `review` agent in this thread. Do not delegate, spawn agents or
invoke skills. Remain read-only unless the developer explicitly asks for fixes; the
configured review role denies edits, so fixes belong in an implementation session.

## Scope and evidence

Read the current developer request and applicable `AGENTS.md` files. For a Zed handoff,
read approved `TASK.md` first and stop if it is missing, empty, ambiguous or conflicts
with newer instructions. For direct Codex work, use the current prompt as scope.

Establish a baseline with `git status --short`, complete staged/unstaged diffs and all
task-relevant untracked files. Read surrounding code and callers, not just changed lines.
Verify every acceptance criterion and challenge whether tests could pass despite a defect.

Apply the independent-review checklist and BLOCKER / IMPORTANT / OPTIONAL definitions
in root `AGENTS.md`. In particular inspect layer placement, dependency injection,
duplicate implementations, unnecessary abstractions, obsolete code, large files/functions,
weakened tests/gates, missing regression tests, unrelated changes, error handling,
authentication/tenant isolation and established backend/frontend conventions.
For changed files over 400 lines or functions over 100 lines, explicitly assess ownership
and cohesion. A size exception permits existing debt, not growth or additional responsibilities.

## Independent verification

Inspect changed Makefile/scripts/configuration/tests before executing them. Report any
unexpected source-writing, dependency-installing or external side effects as a BLOCKER.
Run focused tests where useful, then independently run **`make quality` at the repository
root**, even for test-only or documentation-only changes. The implementer's log is not
independent evidence. No fast path skips this gate. Also run task-specific integration
checks required by `docs/development-quality.md`.

Use `bash.workdir` for the repository root with `make quality`; backend focused checks
use absolute `backend/` with `poetry run`, frontend focused checks use absolute `frontend/`
with npm scripts. Do not use `cd`, command overrides, fix/write/update flags, shell
redirection, Git mutations, environment substitution or dependency installation.
Normal ignored coverage/cache/build artifacts from approved checks are expected.

Never edit existing tests, add reviewer tests, fix production code, change configuration
or adjust expected values during read-only review. Preserve failing evidence, describe
missing regressions for the implementer, and return `CHANGES_REQUIRED` when a required
check fails or is blocked. Expensive LLM/API evaluations require explicit authorization.

Inspect final status against the baseline. `PASS` requires all acceptance criteria,
independent passing checks, no BLOCKER/IMPORTANT finding and no prohibited edits.
Architectural violations and avoidable maintainability regressions fail review even if
tests pass. Do not repeat passing checks without relevant changes or new evidence.

## Report

- **Verdict:** PASS or CHANGES_REQUIRED.
- **Findings:** severity, file/line, impact and concrete correction; or None.
- **Architecture/maintainability:** ownership, reuse, obsolete code and size assessment.
- **Validation:** commands actually executed, results, and material blocked checks.
- **Reviewer changes:** None (apart from normal ignored check artifacts).
