---
description: Review current changes against TASK.md
agent: review
subagent: false
---

Review the current changes against `TASK.md` and follow its scope exactly.

1. Read `TASK.md`.
2. Run and inspect `git status --short`.
3. If staged changes are present, inspect `git diff --cached`.
4. If unstaged changes are present, inspect `git diff`.
5. Inspect untracked files only when they are relevant to `TASK.md`.
6. Inspect only the minimum surrounding code and directly relevant tests needed to review the task.

Do not inventory the repository, inspect unrelated files, report unrelated pre-existing issues, suggest unrelated refactors, modify files, commit, or push.

Return exactly these sections:

## Verdict
PASS or CHANGES_REQUIRED

## Findings
Concrete `TASK.md`-related findings only, or None

## Validation
Executed: ...
Inspected: ...
Not run: ...
