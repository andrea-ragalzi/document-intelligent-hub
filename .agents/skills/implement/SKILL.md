---
name: implement
description: Implement the approved TASK.md incrementally with minimal, verified changes. Explicit invocation only.
disable-model-invocation: true
---

Bounded write phase.

Follow `AGENTS.md` and the instructions for the relevant area. Do not spawn agents or start another phase automatically.

Read `TASK.md` first.

If `TASK.md` is missing, empty, materially ambiguous, lacks an approved plan or verification, or conflicts with a newer explicit developer instruction, stop.

Before editing, briefly state the intended changes and targeted verification. Execute the approved plan in order without requesting approval between steps, unless `TASK.md` explicitly requires a checkpoint.

Do not modify `TASK.md`.

Use focused tests during implementation and run all required task checks before finishing. Honor explicit per-step checks; otherwise group checks covering related changes and repeat them only after relevant edits, failures, or new evidence. Do not automatically run broad quality gates.

If required verification cannot be run, stop and report the missing prerequisite. Do not silently substitute another check.

Resolve routine implementation details within the approved scope. If evidence requires changing the goal, scope, or acceptance criteria, stop and request a new `/plan`.

If two attempts at the same problem fail, stop and recommend `/diagnose` or `/diagnose-rag` rather than continuing to guess.

When the approved work is complete, use the repository's final report format and stop. The developer opens OpenCode review manually.
