# AI development workflow

`/plan → /implement → OpenCode /review`

Open the trusted repository in Zed. Use **Ask** with `/plan`, review the draft, and manually copy it into `TASK.md`. Use **Write** with `/implement` to complete the approved plan. Then manually open a fresh OpenCode thread, select **Nemotron** (`opencode/nemotron-3-ultra-free`), and run `/review` for `PASS` or `CHANGES_REQUIRED`.

Optional support: `/diagnose`, `/diagnose-rag` (**Diagnose**) and `/understand` (**Ask**). There is no automatic handoff or nested reviewer.

## Where instructions live

- [AGENTS.md](../AGENTS.md) and area instructions: repository rules.
- [Zed skills](../.agents/skills/): phase behavior.
- [tasks.json](tasks.json): reusable manual commands via `task: spawn`.
- [review.md](../.opencode/commands/review.md): independent, risk-based review and new-test rules.
- [opencode.json](../.opencode/opencode.json): tool permissions; ordinary test and production edits denied.

Small test-only reviews run one targeted test, then return a verdict when evidence is sufficient. A failing pre-review test stays unchanged and yields `CHANGES_REQUIRED`; broader checks require concrete evidence.

New independent tests use fresh unique filenames under `backend/tests/reviewer_*.py` or `frontend/test/reviewer_*`; writes require no approval. Existing tests, including earlier reviewer files, must never be overwritten or reused. V1 path permissions cannot enforce create-only access within this namespace, so fresh-name discipline remains a reviewer rule. Backend reviewer files run by explicit pytest path. Only temporary probes created during the current review may be removed. Tool permissions are not an OS sandbox: allowed tests/scripts execute code and create normal cache/build artifacts. Manual Zed tasks do not inherit agent permissions.

## Runtime and checks

Zed ACP uses OpenCode **1.18.33** with V1 `agent`, `permission`, `bash`, and `subtask: false`. Shell `opencode` resolves to **2.0.16**. Diagnose ACP using its actual executable's `--version`, `debug config`, and `debug agent review`; the shell binary is not equivalent. After configuration changes, restart ACP and open a fresh thread.

Backend checks run through Poetry in `backend/`; frontend checks use npm scripts in `frontend/`. OpenCode supplies the directory through `bash.workdir`. Start with `Backend: current test` (an open backend test), a relevant RAG task, or a frontend test filter.

`Quality: static (both apps)` runs broad static checks; `Quality: full` adds tests and build checks. These are manual broad gates, not the fast review path. basedpyright availability in Poetry remains a known prerequisite to confirm before using its task/full gate. Regular backend tests exclude `firebase_emulator`. The public RAG evaluation can incur API costs; details are in [the evaluation README](../backend/evaluation/README.md).
