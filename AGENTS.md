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

## Documentation

Update documentation when the task changes behavior, architecture, APIs, configuration, setup, deployment, or developer workflows.

## Verification

Run checks appropriate to the change, including relevant tests and quality checks.

Before considering work complete:

- inspect `git status`;
- inspect the relevant diff;
- confirm only intended files changed;
- report any verification that could not be performed.

Do not disable valid checks merely to make the task pass.

## Git safety

Do not commit, push, merge, rebase, reset, delete branches, or discard unrelated work unless explicitly requested.

## Final report

Briefly report:

- what changed;
- tests/checks run;
- documentation updated when relevant;
- remaining risks or uncertainty.
