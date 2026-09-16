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
  "initiative": "feature/hybrid-search-001",
  "action": {"type": "message", "kind": "task_assigned"}
}
```

Use `action.kind` values `task_assigned`, `handoff`, `test_requested`, `test_failed`, `test_passed`, `review_requested`, `review_rejected`, `review_approved`, or `task_completed`. Use `action.type` `message`, `implementation`, or `qa_verdict` as appropriate. Use `okf/status/<initiative>` with `active`, `blocked`, or `complete` for lifecycle updates. Put code, logs, lengthy reasoning, and durable decisions in repository artifacts; AgentBus messages link to them.

## Deterministic event consumption

Every real unit of work has one unique, namespaced `initiative`, such as `rag/retrieval-assessment-001`, `feature/hybrid-search-001`, or `bug/file-filter-001`. Mateo creates it and includes it in every handoff. A new independent thread must be told its active initiative when it cannot determine it unambiguously from AgentBus state. Never reuse an initiative.

`agentbus_poll` in AgentBus 0.23.0 is an at-least-once, topic-wide poll: it returns only `PUBLISHED` events with `event_id > since_id`; it does not filter `payload.to` or `initiative`, and it has no persistent consumer cursor or acknowledgement facility. Each agent therefore records its own last consumed **global event id** and polls `okf/handoff` after that id. It may act only when all four conditions hold:

1. `payload.to` exactly matches the agent id.
2. `initiative` exactly matches the expected active initiative.
3. `event_id` is newer than that agent's last consumed global event id.
4. The event status is `PUBLISHED`.

Advance the recorded cursor only after the poll results have been examined; retain the highest returned global id so unrelated events are not repeatedly reconsidered. A matching event is consumed only when its work is accepted. If multiple events match an agent and initiative, the agent reports the ambiguity to Mateo and does not guess.

Replies retain the incoming `initiative`, specify an explicit `payload.to`, and set `causation_id` to the exact consumed `event_id`. A reply never invents a causal parent. The John failure occurred because he selected stale smoke-test event 2 merely because it mentioned him; topic ordering alone cannot identify the intended task.

Smoke-test events use a distinct `smoke/*` initiative, for example `smoke/agentbus-001`. Real work never reuses a smoke initiative, and real agents ignore `smoke/*` unless explicitly running a smoke test. A small `read_inbox(agent, initiative, after_event_id)` MCP wrapper remains recommended to apply the recipient and initiative filters consistently, but is not implemented here because AgentBus 0.23.0 does not provide it.

## Zed

The tracked `.zed/settings.json` registers AgentBus as a project-local stdio MCP context server using `./.agentbus-venv/bin/agentbus`. Open this repository as the Zed worktree after installing the pinned environment. Codex threads that Zed exposes to configured MCP servers can then share this repository's AgentBus event store.

AgentBus cannot wake or resume an existing Zed-hosted Codex thread. Its autonomous Codex adapter requires a separate `codex` CLI and starts headless `codex exec` processes; that executable is not installed on this machine, so no headless runners are enabled. Handoffs are persisted and visible, but Andrea starts or resumes the corresponding Zed thread.

## End-to-end Zed AgentBus test

Reopen this repository in Zed after installing the pinned environment so the project context server is loaded. Use three independent Codex threads; do not copy conversation context between them. This fresh test uses `rag/retrieval-assessment-002`; do not reuse old events. Each participant records its last consumed global event id before polling and acts only on the event matching its recipient and this initiative.

### Mateo thread

Give the first thread this exact instruction:

> You are Mateo. Read agents/mateo.md. Start the new initiative `rag/retrieval-assessment-002`. Use AgentBus MCP to publish a `PUBLISHED` handoff to Sarah asking her to inspect the current RAG retrieval architecture and identify the three highest-value improvement opportunities. Include that initiative. Do not perform Sarah's work yourself.

Expected result: an AgentBus event addressed to Sarah is persisted.

### Sarah thread

Give a separate thread this exact instruction:

> You are Sarah. Read agents/sarah.md. Your active initiative is `rag/retrieval-assessment-002`. Poll AgentBus after your cursor, filter for `payload.to: "sarah"` and that initiative, and consume the single matching `PUBLISHED` Mateo event. Inspect the relevant RAG/retrieval code. Do not modify code. Publish a `PUBLISHED` assessment to John with the same initiative and `causation_id` set to Mateo's exact event id.

Expected result: Sarah discovers Mateo's request without its contents being copied into her conversation, then publishes the second event, addressed to John. Its `initiative` remains `rag/retrieval-assessment-002` and its `causation_id` is Mateo's event id.

### John thread

Give a third thread this exact instruction:

> You are John. Read agents/john.md. Your active initiative is `rag/retrieval-assessment-002`. Poll AgentBus after your cursor, filter for `payload.to: "john"` and that initiative, and consume the single matching `PUBLISHED` Sarah event. Do not act on any `smoke/*` event. Independently assess Sarah's findings without modifying implementation, then publish a `PUBLISHED` verdict to Sarah with the same initiative and `causation_id` set to Sarah's exact event id.

Expected result: John publishes the third event, addressed to Sarah, with the same initiative and causation pointing to Sarah's first event. Sarah then consumes that single matching event and publishes the fourth, final `task_completed` event to Mateo, preserving the initiative and setting causation to John's event id.

### Sarah final handoff

Resume the Sarah thread with this instruction:

> You are Sarah. Continue the active initiative `rag/retrieval-assessment-002`. Poll AgentBus after your updated cursor, filter for `payload.to: "sarah"` and that initiative, and consume the single matching `PUBLISHED` John verdict. Publish the final `PUBLISHED` `task_completed` handoff to Mateo with the same initiative and `causation_id` set to John's exact event id.

Verify the persisted graph with:

```bash
.agentbus-venv/bin/agentbus poll --workspace "$PWD" --topic okf/handoff --since-id <cursor-before-test> --limit 100
```

It must prove this exact four-event chain before calling the test successful: Mateo → Sarah → John → Sarah → Mateo, all with `initiative: rag/retrieval-assessment-002`, and each event after the first with `causation_id` equal to the preceding event's exact `event_id`. AgentBus is the shared storage and coordination layer; the threads do not share conversational memory. AgentBus persists work for inactive threads but does not wake them. Autonomous wake or spawn requires a supported process-level runner such as the separate Codex CLI, so no Codex runner is configured while `codex` is unavailable in `PATH`.

## Runtime files

`.agentbus/swarm.yaml`, `.agentbus/roles.yaml`, `requirements-agentbus.txt`, agent definitions, and this guide are reproducible configuration. `.agentbus-venv/`, the SQLite event store, tokens, logs, process state, identities, wake files, and runner state are local-only and ignored by Git. Never commit those runtime files or secrets.
