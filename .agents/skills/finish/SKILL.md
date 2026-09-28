---
name: finish
description: Check the approved task against the final changes and verification, without edits. Explicit invocation only.
disable-model-invocation: true
---

Read-only phase. First read `TASK.md` and follow `AGENTS.md` and the instructions for the relevant area. If the task is missing, empty, or materially ambiguous, stop. Do not modify `TASK.md` or application code; do not spawn agents, use MCP, or start another phase automatically.

Compare `TASK.md`, the final git status and diff (including staged changes and relevant untracked files), and test/check results. Confirm every acceptance criterion and requirement, no unnecessary scope, and that the agreed verification actually ran successfully. Report anything unverified rather than assuming it passed.

End with exactly one outcome: `READY FOR HUMAN COMMIT` or `NOT READY`, with brief reasons. Do not commit; stop.
