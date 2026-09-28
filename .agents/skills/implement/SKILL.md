---
name: implement
description: Implement the approved TASK.md incrementally with minimal, verified changes. Explicit invocation only.
disable-model-invocation: true
---

Bounded write phase.

Follow `AGENTS.md` and the instructions for the relevant area. Do not spawn agents or start another phase automatically.

Read `TASK.md` first.

If `TASK.md` is missing, empty, materially ambiguous, lacks an approved plan or verification, or conflicts with a newer explicit developer instruction, stop.

Before editing, briefly state:

- the task goal;
- the current approved plan step;
- the files expected to change;
- the verification required for that step.

Implement only the current approved step.

Prefer the smallest correct patch. Use TDD when appropriate. Do not expand scope, redesign the architecture, introduce dependencies, or refactor unrelated code unless the approved task explicitly requires it.

Do not modify `TASK.md`.

After every non-trivial implementation step, run the verification agreed for that step before continuing.

If required verification cannot be run, stop and report the missing prerequisite. Do not silently substitute another check.

If implementation evidence shows the approved plan is wrong or incomplete, stop and request a new `/plan`.

If two attempts at the same problem fail, stop and recommend `/diagnose` or `/diagnose-rag` rather than continuing to guess.

When the current approved work is complete, report:

- what changed;
- tests/checks run;
- documentation updated when relevant;
- remaining uncertainty.

Then stop. The developer decides whether to continue implementation or move to OpenCode review.
