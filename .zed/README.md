# Zed: human-in-the-loop AI development

Open the repository root as a trusted worktree and use the **Zed Agent**. Skills in `.agents/skills/` provide `/plan`, `/implement`, `/diagnose`, `/finish`, and specialized `/diagnose-rag`, `/debug`, and `/understand`. They are manually invoked only (`disable-model-invocation: true`); none starts the next phase. OpenCode owns the only `/review` action; open a fresh OpenCode thread manually, select `opencode/nemotron-3-ultra-free`, then run `/review` in that thread. Zed does not launch OpenCode. `TASK.md` is the source of truth for approved work; the developer manually copies an approved `/plan` draft into it. The root `AGENTS.md` and instructions for the relevant areas remain authoritative.

Select **Ask** for planning and finishing. Select **Diagnose** for read-only investigation; it can read/search, use diagnostics, terminal, and skills, but cannot edit files or spawn subagents. For an approved step, select **Write** and invoke `/implement`. Zed asks for confirmation before running agent terminal commands; the terminal can still write to the project, so inspect proposed commands. Tasks run manually in Zed's terminal, do not use LLMs, and do not inherit agent permissions. Profiles and skills apply to Zed Agent. OpenCode's `review` primary agent has structurally enforced read-only permissions and runs `/review` in the current OpenCode thread without a child session.

Natural-language request
→ Zed Ask + `/plan`
→ developer manually copies the approved `TASK.md` draft
→ Zed Write + `/implement`
→ Zed Diagnose + `/diagnose` if needed
→ Manually open OpenCode + select Nemotron + `/review` in the same thread
→ Zed Ask + `/finish`

Run the agreed verification after each non-trivial implementation step before proceeding; stop if a prerequisite is unavailable. The OpenCode reviewer only reports findings and does not fix them. Review `git diff` yourself. After two failed attempts at the same problem, stop implementation and return to diagnosis.

Open the Command Palette and choose `task: spawn` to run a task. Run `Environment: verify Poetry, Python, Node, npm` first; it stops at the first missing executable rather than selecting another package manager. Use `Backend: install (Poetry lock)` (`poetry install`) and `Frontend: install (npm lock)` (`npm ci`) to install from the existing lockfiles. `Quality: fast` runs backend Ruff/MyPy/Pylint/complexity checks and frontend lint/format/type checks. `Quality: full` additionally runs backend basedpyright, all backend tests and focused security regression tests, frontend tests, and the frontend build. `basedpyright` is not declared in the backend Poetry dependencies; its task and the full gate will stop until that prerequisite is available in the Poetry environment. Do not substitute a different checker without approval. For `Backend: current test`, first open a Python test under `backend/tests/`. Regular backend tests follow `pytest.ini`, which excludes `firebase_emulator`; the targeted RAG tasks and `RAG: evaluation tests` use deterministic suites.

`RAG: public eval (LLM/API cost)` runs the real public suite. It may incur API charges and adds reports/history as described in `backend/evaluation/README.md`; run it only by explicit decision. `Frontend: quality` runs lint, format check, and type check; `Quality: frontend` uses the existing script, which also runs tests. `Quality: backend` groups Ruff, MyPy, Pylint, and complexity checks; tests remain separate for targeted feedback. `Backend: security tests` runs existing security/auth tests, not a dependency vulnerability or secrets scan. No task starts another task automatically.
