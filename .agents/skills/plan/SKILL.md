---
name: plan
description: Analyze a natural-language request and prepare a focused implementation plan plus a copy-ready TASK.md draft. Explicit invocation only.
disable-model-invocation: true
---

Read-only planning phase.

Follow `AGENTS.md` and, for the relevant area, `backend/AGENTS.md` or `frontend/AGENTS.md`.

Do not modify repository files, including `TASK.md`. Do not spawn agents, use MCP, switch models or tools spontaneously, or proceed to another phase automatically.

Start from the developer's request; an existing `TASK.md` is not required. Inspect only enough relevant code, tests, and documentation to identify the affected flow, files, and realistic risks. Choose the smallest solution supported by evidence; investigate alternatives only when a material uncertainty could change it.

Briefly explain the evidence, risks, and any unresolved assumptions. Ask only about ambiguities that prevent a usable plan. Put the plan and verification once, in the copy-ready `TASK.md` draft below, inside a single fenced Markdown code block.

Use exactly this structure:

# Current Task

## Goal

...

## Requirements

- ...

## Constraints

- ...

## Acceptance Criteria

- ...

## Non-goals

- ...

## Approved Plan

1. ...
2. ...

## Verification

- ...

Rules for the final `TASK.md` draft:

- Keep it concise and implementation-oriented.
- Preserve all explicit developer constraints.
- Do not turn assumptions or unknowns into requirements.
- Keep the approved plan to at most 5 steps.
- Do not add commentary inside the code block.
- Choose targeted checks for the changed behavior and identify conditions requiring broader verification; do not default to whole-project quality gates.

Stop after the draft. The developer approves and manually copies it into `TASK.md` before invoking `/implement`.
