---
name: diagnose
description: Diagnose a failure related to the current approved task without modifying repository files. Explicit invocation only.
disable-model-invocation: true
---

Read-only diagnostic phase.

Follow `AGENTS.md` and the instructions for the relevant area. Do not modify files, spawn agents, or start implementation automatically.

Read `TASK.md` first.

If it is missing, empty, materially ambiguous, or unrelated to the reported failure, stop.

Use the task to establish expected behavior and scope.

Investigate using the smallest useful set of:

- relevant code;
- tests;
- logs;
- diagnostics;
- non-destructive terminal commands.

Reconstruct the failing call path and distinguish symptoms from root causes.

Consider evidence both for and against the leading hypothesis. Do not guess when evidence is insufficient.

Run one discriminating experiment at a time when useful.

Do not fix the problem during diagnosis.

Stop once the root cause is sufficiently established or when the available evidence cannot distinguish the remaining hypotheses.

Respond with:

## Observed

## Expected

## Root cause

State `Unconfirmed` if it has not been demonstrated.

## Evidence

## Next action

The next action may recommend `/implement`, a new `/plan`, or additional evidence.

Then stop.
