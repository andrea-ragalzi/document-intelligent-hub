---
name: implement
description: Apply one step from an already approved plan with a minimal, targeted change. Explicit invocation only.
disable-model-invocation: true
---

Bounded write phase. Follow `AGENTS.md` and the instructions for the relevant area. Do not spawn agents, use MCP, or switch models or tools spontaneously. Do not start another phase automatically.

First read `TASK.md`. Briefly state its current goal, the current approved plan step, and the expected files before editing. If `TASK.md` is missing, empty, or insufficiently defined (including an absent approved plan or verification), stop. Do not modify `TASK.md`. If the step exceeds its scope or the plan proves incorrect, stop, explain the evidence, and request a new `/plan`; do not change the architecture on your own.

Implement only the approved task's current step, with a minimal patch. Use TDD when appropriate, following the repository instructions. Avoid unrequested refactoring, new abstractions when a local change is enough, new dependencies without authorization, new architectures, agentic infrastructure, and out-of-scope changes. Do not commit, push, reset, or rebase.

After every non-trivial implementation step, run the verification agreed for that step successfully before proceeding to another step. If a tool, command, or dependency required for that verification is unavailable, do not substitute an unagreed alternative and do not proceed to the next step. Report the missing prerequisite and stop. A step is not complete until its agreed verification has run successfully.

After two failed attempts at the same problem, stop and request a new diagnosis. After the agreed verification succeeds, report what changed, which targeted checks passed, and any uncertainties. Then stop; the user decides whether to invoke the next phase.
