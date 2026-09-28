---
name: plan
description: Analyze a request and prepare a short plan without modifying files. Explicit invocation before implementation.
disable-model-invocation: true
---

Read-only phase. Follow `AGENTS.md` and, for the relevant area, `backend/AGENTS.md` or `frontend/AGENTS.md`. Do not proceed to another phase without the user's explicit invocation. Do not spawn agents, use MCP, or switch models or tools spontaneously.

1. Accept the developer's natural-language request. Read the relevant requirement, code, tests, and documentation; reconstruct the call path and identify the files and symbols involved. `/plan` does not require a populated `TASK.md`.
2. Separate verified facts from hypotheses. Look for evidence that could disprove the first proposed solution, then choose the simplest solution supported by evidence.
3. List risks and regressions, a plan of at most 5 steps, and targeted tests. Do not introduce abstractions when a local change is enough.
4. Do not modify files (including `TASK.md`), implement, or refactor. Stop if the request goes out of scope.

Respond with these sections, in order: `Goal`, `Current flow`, `Evidence`, `Risks`, `Plan`, `Verification`, `Unknowns`, `## TASK.md draft`. In the final section, provide a concise ready-to-copy draft with `Goal`, `Requirements`, `Constraints`, `Acceptance Criteria`, `Non-goals`, `Approved Plan`, and `Verification`. The developer manually copies it into `TASK.md` only after approving the plan. Stop and wait for approval before `/implement`.
