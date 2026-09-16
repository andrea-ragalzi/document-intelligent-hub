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

The tracked `.zed/settings.json` registers AgentBus as a project-local stdio MCP context server using `./.agentbus-venv/bin/agentbus`. Open this repository as the Zed worktree after installing the pinned environment. Zed remains the control and monitoring environment.

## Headless Codex runners

AgentBus 0.23.0 runs one-shot Codex turns through its native `codex` adapter. `.agentbus/swarm.yaml` starts six wake workers and each worker invokes the native `agentbus run --once` path through the small `.agentbus/dispatch.py` policy gate. The gate is needed because 0.23.0 workers cannot filter nested payload fields or enforce a team-wide initiative budget. It never replaces AgentBus routing or the runner.

Every runner invokes `codex exec -C <workspace> --ephemeral --json -m gpt-5.6-luna --sandbox workspace-write -c model_reasoning_effort="low" -`. This per-run selection leaves the interactive Codex default untouched. The gate writes local usage records under `.agentbus/team-runtime/usage.jsonl`, containing the event, initiative, agent, selected model, effort, exit code, and `turn.completed` token usage.

An autonomous handoff must be `PUBLISHED`, addressed to its target, newer than that agent's gate cursor, have a non-smoke initiative (unless `execution.smoke_test: true`), and include:

```yaml
execution:
  autonomous: true
  expected_initiative: <same initiative>
  budget_profile: simple | normal | high_risk | cross_cutting
  implementation_owner: sarah | lucia | maya
```

Mateo selects and persists the profile at initiative creation. Each profile separates an immediately usable base from a protected QA-fix reserve: `simple` and `normal` allow 3 base runs plus a 2-run reserve (5 absolute maximum); `high_risk` allows 4 base runs plus a 2-run reserve (6 absolute maximum). `cross_cutting` allows 5 base runs plus the same 2-run reserve (7 absolute maximum), and requires `cross_cutting_ownership_domains` to name at least two of `sarah`, `lucia`, and `maya`; it is only for work spanning two ownership domains, such as Sarah + Lucía + John or Lucía + Maya + John + Alex. Difficulty alone does not qualify: a difficult single-owner task remains `normal` or `high_risk`. Declaring multiple domains under a smaller profile does not enlarge its base budget. A cross-cutting specialist-to-specialist handoff must be between declared domains and set `cross_cutting_handoff: true`.

The reserve unlocks once, and only when John publishes a valid concrete verification failure to the recorded implementation owner: same initiative, exact causation, `verification_failure: true`, non-empty summary, and an unused fix cycle. Its two runs are exclusively that owner’s fix and John’s re-verification; Mateo, Alex, other specialists, retries, and unrelated handoffs cannot consume it. A John pass closes the initiative without unlocking the reserve. A second verification failure is `BLOCKED` to Mateo/Andrea. Handoff and retry caps remain unchanged. Once persisted, a profile cannot change through AgentBus; an increase requires Andrea/manual approval. The gate does not invoke Codex after budget exhaustion; it publishes `BLOCKED` with `reason: budget_exhausted` to Mateo. Quota, rate, and account-limit errors publish `BLOCKED` with `reason: quota_exhausted` and do not retry.

Mateo alone may request a one-run override by adding `execution.model_override` with `requested_by: mateo`, `scope: one_run`, an approved reason, and exactly one allowed target: Luna at medium effort, Terra at low effort, or Sol at low effort. The gate creates an ephemeral runner config for that one invocation and then returns to Luna low. It never escalates after a failure.

Routing stays deliberately narrow: Mateo normally starts work; Sarah, Lucía, and Maya receive from Mateo or John; John receives from Mateo or an implementation specialist and runs only when `execution.qa_mode: reasoning`; Alex accepts review requests only from Mateo or John and only with an allowed `execution.review_scope`. Mateo's worker runs only when `execution.mateo_reasoning_reason` is initial decomposition/routing, ambiguity, ownership conflict, architecture decision, blocked initiative, or an explicit final decision requiring judgment. Mechanical test execution should be performed by local automation and reported directly; it must not wake John merely to interpret a deterministic command. Normal paths are Mateo → Sarah/Lucía/Maya → John → `okf/status/<initiative>: complete` → Andrea. Alex is reserved for auth/authz, tenant isolation, sensitive document boundaries, migrations, security-sensitive behavior, and architecture-critical review.

A routine John pass is not an `okf/handoff` to Mateo. John publishes `okf/status/<initiative>` with `status: complete`, explicit `to: andrea`, the same initiative, and causation set to the verified event. The status event closes and reports the initiative without a Mateo Codex turn. Likewise, a deterministic specialist-to-John route does not relay through Mateo.

John may address an implementation owner only for one concrete verification failure. The handoff must identify the same `implementation_owner`, preserve `causation_id` to the exact owner event John consumed, set `verification_failure: true` with a non-empty `verification_failure_summary`, and declare `fix_cycles_used` below the selected profile limit. The gate records that single cycle. The owner returns only to John, with `fix_cycle: 1` and causation set to John's fix request. A second John-to-owner request is blocked and returned to Mateo; John cannot delegate unrelated work or select a different owner.

For a headless task, Sarah and John publish the substantive handoff with the received initiative and exact `causation_id`, then return `NO-OP` as the final CLI marker. AgentBus treats that marker as an instruction to suppress its synthetic `RUNNER_ACK`, which otherwise lacks the initiative and would violate this repository's event protocol.

The autonomous smoke run `smoke/autonomous-codex-004` verified the worker wake and Sarah's published handoff (events 35 and 36). John's process was started automatically but Codex exited after the account usage limit was reached, so no substantive John result was persisted. Event 38 is the resulting operational error and is not part of a valid initiative chain. Resolve the quota and replace or wrap the native runner acknowledgement path before broadening this rollout: the native acknowledgement can omit `initiative`, and successful suppression currently depends on the headless turn returning the `NO-OP` marker.

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

It must prove this exact four-event chain before calling the test successful: Mateo → Sarah → John → Sarah → Mateo, all with `initiative: rag/retrieval-assessment-002`, and each event after the first with `causation_id` equal to the preceding event's exact `event_id`. AgentBus is the shared storage and coordination layer; the threads do not share conversational memory. The configured workers provide autonomous process-level wake for Sarah and John; the one-shot Codex processes exit after each turn while the workers remain available for later handoffs.

## Runtime files

`.agentbus/swarm.yaml`, `.agentbus/roles.yaml`, `requirements-agentbus.txt`, agent definitions, and this guide are reproducible configuration. `.agentbus-venv/`, the SQLite event store, tokens, logs, process state, identities, wake files, and runner state are local-only and ignored by Git. Never commit those runtime files or secrets.
