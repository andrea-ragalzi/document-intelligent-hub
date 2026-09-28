---
description: Adversarially review and verify the current TASK.md implementation
agent: review
subagent: false
---

Act as an independent adversarial reviewer for the current implementation.

Read `TASK.md` first and follow its approved scope exactly.

Before modifying anything, establish the implementation baseline:

1. inspect `git status --short`;
2. inspect staged changes with `git diff --cached` when present;
3. inspect unstaged changes with `git diff` when present;
4. inspect task-relevant untracked files;
5. inspect only the changed implementation, minimum necessary surrounding code, and directly relevant tests.

Evaluate every requirement and acceptance criterion in `TASK.md`.

Actively try to falsify the implementation.

Look for:

- incorrect behavior;
- plausible regressions;
- unhandled edge cases;
- error-handling failures;
- security or data-integrity problems;
- boundary and isolation failures;
- incorrect assumptions;
- duplicated business rules;
- unnecessary complexity;
- typing and maintainability problems;
- tests that merely mirror the implementation;
- important behavior not independently tested.

Do not rely only on tests written by the implementer.

When useful, independently add or strengthen task-relevant tests, fixtures, or test helpers to probe behavior the implementation may have missed.

Reviewer-written tests should test externally meaningful behavior and edge cases rather than implementation details.

Do not weaken, delete, skip, or rewrite valid existing tests merely to make the implementation pass.

Run the smallest useful set of independent verification commands. Use targeted checks first and broaden only when justified.

Relevant verification may include:

- pytest;
- task-relevant RAG regression suites;
- Ruff;
- MyPy;
- basedpyright;
- Pylint;
- complexity checks;
- frontend tests;
- frontend lint;
- frontend type checking.

Do not run costly LLM/API evaluations unless `TASK.md` requires them or the developer explicitly requests them.

You may modify only tests, test fixtures, and test helpers required for independent verification.

Do not modify:

- production code;
- `TASK.md`;
- application configuration;
- dependencies;
- production documentation.

If an independently created test exposes a production bug, do not fix the production code. Return `CHANGES_REQUIRED`.

Temporary probes that have no lasting regression value should be removed before the final verdict. Useful regression tests may remain.

Before the verdict, inspect the final status and diff again and distinguish:

- implementation changes that existed before review;
- tests added or changed by the reviewer.

A `PASS` requires:

- every acceptance criterion supported by concrete evidence;
- no material task-related finding;
- relevant independent verification passing;
- no production-code changes made by the reviewer.

Do not inventory unrelated repository areas, report unrelated pre-existing issues, or suggest unrelated refactors.

Return exactly:

## Verdict
PASS or CHANGES_REQUIRED

## Findings
Concrete TASK.md-related findings only, or None

## Independent tests
Added or changed:
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
- test files intentionally left in the worktree, or None