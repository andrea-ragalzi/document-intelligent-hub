# AI development workflow

`/plan → /implement → OpenCode /review`

Open the trusted repository in Zed. Use **Ask** with `/plan`, review the draft, and manually copy it into `TASK.md`. Use **Write** with `/implement` to complete the approved plan. Then manually open a fresh OpenCode thread, select **Nemotron** (`opencode/nemotron-3-ultra-free`), and run `/review` for `PASS` or `CHANGES_REQUIRED`.

Optional support: `/diagnose`, `/diagnose-rag` (**Diagnose**) and `/understand` (**Ask**). There is no automatic handoff or nested reviewer.

## Where instructions live

- [AGENTS.md](../AGENTS.md) and area instructions: repository rules.
- [Zed skills](../.agents/skills/): phase behavior.
- [tasks.json](tasks.json): reusable manual commands via `task: spawn`.
- [review.md](../.opencode/commands/review.md): independent read-only architecture and quality review.
- [opencode.json](../.opencode/opencode.json): tool permissions; all source/test/config edits denied.

Every implementation and independent review runs root `make quality`, including small
test-only changes. Reviewers inspect architecture and maintainability as well as tests;
BLOCKER/IMPORTANT findings or failed/blocked gates yield `CHANGES_REQUIRED`.

Reviewers cannot add or modify tests. Request fixes or missing regressions in the findings;
implementation happens in a separate write session. Permissions are not an OS sandbox:
allowed tests/scripts execute repository code and create normal cache/coverage/build
artifacts. Inspect changed check scripts before running them. Manual Zed tasks do not
inherit agent permissions.

## Runtime and checks

Zed ACP uses OpenCode **1.18.33** with V1 `agent`, `permission`, `bash`, and `subtask: false`. Shell `opencode` resolves to **2.0.16**. Diagnose ACP using its actual executable's `--version`, `debug config`, and `debug agent review`; the shell binary is not equivalent. After configuration changes, restart ACP and open a fresh thread.

Backend checks run through Poetry in `backend/`; frontend checks use npm scripts in `frontend/`. OpenCode supplies the directory through `bash.workdir`. Start with `Backend: current test` (an open backend test), a relevant RAG task, or a frontend test filter.

`Quality: full` runs `make quality`; area quality tasks use its backend/frontend targets.
Focused tasks are iteration aids, not substitutes for the completion gate. The uninstalled
basedpyright task and duplicate full-suite/security runs have been removed. See
[the quality contract](../docs/development-quality.md) for prerequisites, limits and
additional integration checks. Public RAG evaluation can incur API costs and still requires
explicit authorization.
