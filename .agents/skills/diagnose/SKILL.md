---
name: diagnose
description: Diagnose an observed failure against the approved task without modifying repository files. Explicit invocation only.
disable-model-invocation: true
---

Read-only phase. First read `TASK.md` and follow `AGENTS.md` and the instructions for the relevant area. If the task is missing, empty, or materially ambiguous, stop. Use it for expected behavior and scope; do not modify it, fix the problem, or expand scope. Do not spawn agents, use MCP, or switch models or tools spontaneously.

Investigate an observed failure using evidence, relevant tests, logs, diagnostics, and non-destructive commands. Reconstruct the call path; distinguish symptoms from root causes and consider evidence against the leading hypothesis. Do not write repository files. Stop when evidence is insufficient rather than guessing.

End with `Observed`, `Root cause` (or state that it is unconfirmed), `Evidence`, and `Next action`. Then stop; the developer decides whether to invoke `/implement`.
