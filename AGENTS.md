# Repository instructions

Work directly on the requested task.

Before editing:

- inspect the relevant code, tests, and documentation;
- understand the current architecture and existing patterns;
- keep the change focused and preserve unrelated work.

For backend changes, read `backend/AGENTS.md` before editing backend code.

For frontend changes, read `frontend/AGENTS.md` before editing frontend code.

## Development

Use TDD for behavior changes when practical:

1. add or update a test that demonstrates the expected behavior;
2. confirm the failure when fixing a bug;
3. implement the smallest correct change;
4. run the relevant regression tests.

Prefer simple, cohesive code over new abstractions.

Do not:

- introduce unrelated refactors;
- duplicate existing business rules;
- add dependencies without a concrete need;
- create god modules, classes, hooks, or components;
- add substantial new behavior to an already oversized file without first separating a coherent responsibility.

Treat files approaching 600–700 lines as a signal to check responsibilities. Avoid production files growing toward 1,000+ lines. Do not split cohesive code only to satisfy a line-count target.

Preserve the repository's typing, linting, formatting, and testing standards.

## Documentation

Documentation is part of Definition of Done.

Update relevant documentation when behavior, architecture, APIs, configuration, setup, deployment, or workflows change.

## Verification

Before finishing:

- run relevant tests;
- run relevant lint/type/format checks;
- inspect `git status`;
- inspect `git diff`;
- confirm only intended files changed.

Do not disable valid tests or quality checks to make the change pass.

Do not commit, push, merge, rebase, reset, or delete branches unless explicitly requested.

At the end report:

- what changed;
- tests/checks run;
- documentation updated;
- remaining risks or uncertainty.
