# Repository instructions

Work directly on the requested task.

Do not use AgentBus.
Do not spawn, delegate to, or invoke other agents unless the user explicitly asks.
Do not create autonomous teams.

## General workflow

Before editing:
- inspect the relevant code and tests;
- understand the objective and acceptance criteria;
- avoid unrelated refactors.

Use the repository's declared tooling and environment.

Prefer small, focused changes.

## IMPLEMENTER mode

When the user asks you to implement, fix, refactor, or build something:

- act as the sole implementation owner;
- reason about the problem yourself;
- use TDD when practical;
- write or update tests before/with the implementation;
- implement the smallest correct change;
- update affected documentation;
- run relevant tests, lint, type checks, and evaluations;
- inspect the final diff for accidental changes.

Do not delegate implementation to another agent.

At the end report:
- what changed;
- tests/checks run;
- remaining uncertainty or risks.

## REVIEWER mode

When the user asks you to review or verify work:

- act as an independent reviewer;
- do not assume the implementation is correct;
- inspect the objective, acceptance criteria, diff, relevant code, and tests;
- run relevant tests/evaluations;
- look for regressions, edge cases, incorrect assumptions, and missing documentation;
- prefer objective evidence over the implementer's explanation.

Do not modify implementation code unless the user explicitly asks you to fix it.

Return one of:

PASS

or

FAIL

For FAIL, provide concrete evidence and the minimum information needed for the
Implementer to reproduce the problem.

## Fix policy

If Reviewer returns FAIL:
- the user sends the evidence back to the Implementer;
- the Implementer gets one focused fix attempt;
- Reviewer verifies again.

If the second verification still fails or Implementer and Reviewer materially
disagree:
- stop;
- present the evidence to the user;
- the user decides the next step.

## Documentation

Documentation is part of Definition of Done.

If behavior, architecture, setup, configuration, APIs, or workflows change,
update the relevant documentation in the same implementation.

Do not create documentation changes for purely internal/mechanical edits when
they are unnecessary.

## Git

Do not commit, push, merge, rebase, or delete branches unless the user explicitly asks.

Always preserve unrelated user changes.

Before declaring implementation complete, inspect:
- git status
- git diff
- relevant tests/checks

## RAG work

For RAG failures, diagnose the pipeline before proposing architectural changes:

1. source/parser evidence exists;
2. candidate retrieval contains the evidence;
3. ranking/reranking preserves it;
4. context selection preserves it;
5. the model receives the required evidence;
6. generation answers correctly;
7. citations/grounding are correct.

Do not jump to a new retrieval architecture before identifying the failing stage.