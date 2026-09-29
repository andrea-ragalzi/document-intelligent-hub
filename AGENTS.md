# Repository instructions

Keep changes focused, minimal, and consistent with the existing architecture.

## Workflow

### Zed

The normal Zed development workflow is:

1. `/plan` analyzes a natural-language request and proposes `TASK.md`.
2. The developer reviews and manually copies the approved draft into `TASK.md`.
3. `/implement` executes the approved task.

`/diagnose`, `/diagnose-rag`, and `/understand` are optional support phases and are invoked explicitly when needed.

For Zed phases operating on an approved task, `TASK.md` is the source of truth. Work only within its scope. If it is missing, empty, ambiguous, or conflicts with a newer explicit developer instruction, stop rather than guessing.

`/plan` does not require an existing `TASK.md`.

### OpenCode

Review is performed independently in OpenCode after implementation.

The OpenCode review workflow and permissions are defined by its own project configuration. Review the approved `TASK.md` and the current repository changes; do not silently expand the task scope.

### Codex

Codex works directly from the developer's current prompt unless explicitly told to use the Zed/TASK.md workflow.

When using Codex directly:

- `TASK.md` is not required;
- the current developer request is the source of truth;
- still follow the repository architecture, testing, quality, and safety rules below.

## Before editing

Inspect only the relevant code, tests, and documentation needed for the task.

Search for existing callers, schemas, helpers, services, hooks and components before
adding an abstraction. State which existing responsibility owns the change.

Preserve unrelated work and existing architectural patterns.

For backend changes, follow `backend/AGENTS.md`.

For frontend changes, follow `frontend/AGENTS.md`.

## Development

Prefer the smallest correct change.

Use TDD for behavior changes when practical:

1. demonstrate the expected behavior with a test;
2. implement the change;
3. run relevant regression tests.

Avoid:

- unrelated refactors;
- duplicated business rules;
- unnecessary abstractions;
- unnecessary dependencies;
- oversized god modules, classes, hooks, or components.

Preserve the repository's typing, linting, formatting, and testing standards.

Remove code, imports and branches made obsolete by your change; check callers before
deleting shared APIs or compatibility exports. Bug fixes require a deterministic
regression test that fails before the fix. Do not weaken assertions, skip tests,
reduce coverage, add blanket suppressions or relax lint/type/quality gates to pass.
Agents must not modify quality configuration merely to make an implementation pass
unless the requested task specifically concerns that configuration.

Handwritten production files over 400 lines require explicit architecture review;
over 600 fail unless a concrete exception is recorded in `quality/size-exceptions.json`.
Existing exceptions are no-growth ceilings, not targets. Never split files mechanically
or compress code to evade limits. Review functions over 100 lines; backend functions
over 200 non-comment lines fail Lizard. See `docs/development-quality.md` for scope.

## Documentation

Update documentation when the task changes behavior, architecture, APIs, configuration, setup, deployment, or developer workflows.

## Verification

Run focused checks while editing, then **`make quality` from the repository root**
before declaring completion, including documentation-only and test-only tasks.
Run additional task-specific integration checks described in `docs/development-quality.md`.

Before considering work complete:

- inspect `git status`;
- inspect the complete staged and unstaged diff and all task-created untracked files;
- confirm only intended files changed;
- report any verification that could not be performed.

Do not disable valid checks merely to make the task pass.

A task is not complete merely because tests pass. The resulting code must also
remain maintainable and consistent with the repository architecture. If required
checks fail or cannot run, report the failure/prerequisite and leave completion unclaimed.

## Independent review

Reviewers remain read-only unless explicitly asked to fix findings. Inspect the full
implementation independently, search related code and callers, and independently run
`make quality`; an implementer's test report is not verification. Normal ignored test,
coverage and build artifacts are permitted; source/config/test edits are not.

Check layer placement, dependency wiring, duplicate logic, unnecessary abstractions,
obsolete code, file/function size, missing regressions, weakened tests/gates, unrelated
changes, error handling, authentication/tenant isolation and backend/frontend conventions.
For each finding give file/line, impact and a concrete correction:

- **BLOCKER**: security/correctness failure, failing required gate, or bypassed verification.
- **IMPORTANT**: architectural violation, avoidable maintainability regression, missing
  regression coverage, or unjustified size/abstraction/duplication.
- **OPTIONAL**: non-blocking improvement within the task's scope.

Return `CHANGES_REQUIRED` for BLOCKER/IMPORTANT findings or blocked required verification,
even when tests pass. `PASS` requires all acceptance criteria and checks, with no such findings.

## Git safety

Do not commit, push, merge, rebase, reset, delete branches, or discard unrelated work unless explicitly requested.

## Final report

Briefly report:

- what changed;
- tests/checks run;
- documentation updated when relevant;
- remaining risks or uncertainty.
