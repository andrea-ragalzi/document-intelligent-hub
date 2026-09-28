---
name: plan
description: Analyze a natural-language request and prepare a focused implementation plan plus a copy-ready TASK.md draft. Explicit invocation only.
disable-model-invocation: true
---

Read-only planning phase.

Follow `AGENTS.md` and, for the relevant area, `backend/AGENTS.md` or `frontend/AGENTS.md`.

Do not modify repository files, including `TASK.md`. Do not spawn agents, use MCP, switch models or tools spontaneously, or proceed to another phase automatically.

1. Accept the developer's natural-language request. `/plan` does not require a populated `TASK.md`.
2. Read only the relevant requirements, code, tests, configuration, and documentation needed to understand the request.
3. Reconstruct the current flow and identify the files and symbols likely involved.
4. Separate verified facts from hypotheses. Look for evidence that could disprove the first proposed solution.
5. Choose the simplest solution supported by evidence.
6. Identify meaningful risks and regressions.
7. Produce a plan of at most 5 implementation steps and targeted verification.
8. Do not implement, refactor, or expand the request beyond its scope.

Respond with these sections, in order:

## Goal

## Current flow

## Evidence

## Risks

## Plan

## Verification

## Unknowns

## TASK.md draft

In the final section, provide the complete contents of `TASK.md` inside a single fenced Markdown code block, ready to copy without editing.

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
- Do not use inline labels such as `**Goal:**`.
- Do not add commentary inside the code block.
- Do not modify `TASK.md`; `/plan` only proposes its contents.
- The developer manually copies the block into `TASK.md` only after approving the plan.

Stop and wait for approval before `/implement`.
