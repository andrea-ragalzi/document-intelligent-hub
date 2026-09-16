# Local AgentBus team

AgentBus 0.23.0 coordinates this repository's local development team. Install the pinned tool into `.agentbus-venv`; application dependencies remain unchanged.

## Start

From the repository root:

```bash
python3 -m venv .agentbus-venv
.agentbus-venv/bin/pip install -r requirements-agentbus.txt
.agentbus-venv/bin/agentbus init --apply --workspace "$PWD" --producer-id mateo
.agentbus-venv/bin/agentbus up --workspace "$PWD"
```

The tracked swarm starts the filesystem watcher. Zed starts the project MCP server separately when this workspace opens.

## Monitor

```bash
.agentbus-venv/bin/agentbus monitor --workspace "$PWD"
```

For a non-interactive status check:

```bash
.agentbus-venv/bin/agentbus ps --workspace "$PWD"
```

## Stop

```bash
.agentbus-venv/bin/agentbus down --workspace "$PWD"
```

## Agents

| Agent | Role | Normal handoff |
|---|---|---|
| Mateo | Tech lead / architect / orchestrator | Relevant specialist, John, or Alex |
| Sarah | AI / RAG engineer | John, then Mateo |
| Lucía | Backend & data engineer | John; Alex for high-risk review |
| Maya | Frontend / product engineer | John, then Mateo |
| John | QA & RAG evaluation engineer | Owner on failure; Mateo on verdict |
| Alex | Independent reviewer / security gate | Mateo and implementation owner |

Typical flows are `Andrea → Mateo → Sarah → John → Mateo` and `Andrea → Mateo → Lucía → John → Alex → Mateo`. Mateo assigns only the specialists the task actually needs.

## Communication

Use the built-in `okf/handoff` topic for assignments, handoffs, test requests/verdicts, reviews, completion, and blockers. Keep payloads small:

```json
{
  "from": "mateo",
  "to": "sarah",
  "summary": "Inspect the RAG retrieval architecture; do not modify code.",
  "links": ["agents/sarah.md"],
  "initiative": "task-slug",
  "action": {"type": "message", "kind": "task_assigned"}
}
```

Use `action.kind` values `task_assigned`, `handoff`, `test_requested`, `test_failed`, `test_passed`, `review_requested`, `review_rejected`, `review_approved`, or `task_completed`. Use `action.type` `message`, `implementation`, or `qa_verdict` as appropriate. Use `okf/status/<task-slug>` with `active`, `blocked`, or `complete` for lifecycle updates. Put code, logs, lengthy reasoning, and durable decisions in repository artifacts; AgentBus messages link to them.

## Zed

The tracked `.zed/settings.json` registers AgentBus as a project-local stdio MCP context server using `./.agentbus-venv/bin/agentbus`. Open this repository as the Zed worktree after installing the pinned environment. Codex threads that Zed exposes to configured MCP servers can then share this repository's AgentBus event store.

AgentBus cannot wake or resume an existing Zed-hosted Codex thread. Its autonomous Codex adapter requires a separate `codex` CLI and starts headless `codex exec` processes; that executable is not installed on this machine, so no headless runners are enabled. Handoffs are persisted and visible, but Andrea starts or resumes the corresponding Zed thread.

## End-to-end Zed AgentBus test

Reopen this repository in Zed after installing the pinned environment so the project context server is loaded. Use three independent Codex threads; do not copy conversation context between them.

### Mateo thread

Give the first thread this exact instruction:

> You are Mateo. Read agents/mateo.md. Use AgentBus MCP to send Sarah a handoff asking her to inspect the current RAG retrieval architecture and identify the three highest-value improvement opportunities. Do not perform Sarah's work yourself.

Expected result: an AgentBus event addressed to Sarah is persisted.

### Sarah thread

Give a separate thread this exact instruction:

> You are Sarah. Read agents/sarah.md. Use AgentBus to read the latest handoff addressed to Sarah. Inspect the relevant RAG/retrieval code. Do not modify code. Send your assessment or completion status back through AgentBus.

Expected result: Sarah discovers Mateo's request without its contents being copied into her conversation, then publishes her assessment or status. If Sarah requests independent evaluation, that handoff is addressed to John in accordance with her role rules.

### John thread

Give a third thread this exact instruction:

> You are John. Read agents/john.md. Read your AgentBus inbox and act on the newest task addressed to you. Follow your role boundaries strictly.

Expected result: John discovers work through AgentBus rather than conversation context. Ensure a task has first been addressed to John; the CLI smoke test also leaves a harmless Sarah → John evaluation request in the local event store.

This proves shared coordination only after all three independent Zed threads complete the experiment. AgentBus is the shared storage and coordination layer; the threads do not share conversational memory. AgentBus persists work for inactive threads but does not wake them. Autonomous wake or spawn requires a supported process-level runner such as the separate Codex CLI, so no Codex runner is configured while `codex` is unavailable in `PATH`.

## Runtime files

`.agentbus/swarm.yaml`, `.agentbus/roles.yaml`, `requirements-agentbus.txt`, agent definitions, and this guide are reproducible configuration. `.agentbus-venv/`, the SQLite event store, tokens, logs, process state, identities, wake files, and runner state are local-only and ignored by Git. Never commit those runtime files or secrets.
