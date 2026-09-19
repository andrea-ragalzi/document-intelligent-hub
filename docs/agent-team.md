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
| Mateo | Tech lead / router | One relevant owner, John, Alice, or Alex |
| Sarah | RAG engineer | John |
| Lucía | Backend / data / auth engineer | John |
| Maya | Frontend / product engineer | John |
| John | Independent QA / evaluation | Same owner on one failure; otherwise COMPLETE |
| Alice | Independent RAG theory / research analyst | On demand only |
| Alex | Security / adversarial reviewer | On demand only |

The core team is Mateo, Sarah, Lucía, Maya, and John. Alice and Alex are dormant
until a bounded analysis or meaningful security review is explicitly justified.
The normal path is `Mateo → one implementation owner → John → COMPLETE`, so it
normally uses two or three model runs. Do not broadcast work to unrelated agents.

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

## Objective-led specialist handoffs

Mateo assigns an outcome, not a recipe. A normal Mateo → Sarah/Lucía/Maya
implementation handoff carries a non-empty `execution.implementation_handoff`
object with `problem`, `evidence`, `objective`, `invariants`, `non_goals`,
`success_criteria`, and `context`; the existing `implementation_owner` and
`budget_profile` provide ownership and budget. `optional_hypotheses` may suggest
directions but is explicitly non-binding. This is a repository convention inside
AgentBus's supported arbitrary JSON `--payload`, not an AgentBus schema change.

The owner independently chooses the algorithm, internal order, decomposition,
architecture, heuristics, and thresholds. The owner may reject a suggested
approach if evidence contradicts it, a simpler approach meets the criteria, an
invariant is threatened, or another approach is better supported; explain the
choice while preserving the stated objective and constraints.

Only `binding_constraints` may prescribe an implementation detail. Each entry
must contain `constraint` and `binding_reason`. A reason is permitted only for
an existing repository/API contract, deterministic mechanical work, Andrea's
explicit request, a recorded deliberation decision, a security invariant, or a
specialist-requested ambiguity resolution. This is an agent contract: the gate
does not attempt to infer whether free-form text contains an implementation recipe.
For a deliberation decision, record the selected direction, rejected
alternatives, evidence, and remaining flexibility; the specialist still owns
implementation unless the decision itself fixes the mechanism.

Use this compact form for a normal implementation assignment:

```yaml
execution:
  implementation_owner: sarah
  budget_profile: normal
  docs_impact: none | update_required
  docs_targets: [<required only when impact is update_required>]
  implementation_handoff:
    problem: <what is failing or missing>
    evidence: [<observations, tests, or metrics>]
    objective: <required outcome>
    invariants: [<must remain true>]
    non_goals: [<explicitly out of scope>]
    success_criteria: [<John-evaluable outcomes>]
    context: [<paths, artifacts, rejected approaches>]
    optional_hypotheses: [<clearly non-binding direction>]
    binding_constraints:
      - constraint: <only a truly binding detail>
        binding_reason: <contract, decision, security invariant, or request>
```

For a direct Mateo → John evaluation request, use
`execution.independent_evaluation` with `mode: independent_criteria`,
`objective`, `invariants`, and `success_criteria`. For a direct Mateo → Alex
review request, use `execution.independent_security_review` with
`mode: adversarial_counterexample_search`, `threat_or_invariant`,
`changed_surface`, and `acceptance_criteria`. These are role contracts; John and
Alex remain responsible for independent and adversarial evaluation.

Alice's hypotheses remain theory and experiment context. Mateo selects a bounded
objective; Sarah chooses the implementation; John independently evaluates the
criteria rather than Sarah's explanation. John receives success criteria and
invariants, not a request to prove an implementation correct. Alex receives the
threat/invariant, changed surface, and security criteria, and searches for
counterexamples rather than confirming a claimed safety rationale.

## Definition of Done and documentation

Every initiative evaluates `docs_impact` as `none` or `update_required`. For an
update, name `docs_targets`; the owner updates them and marks `docs_updated: true`
when handing work to John. The gate will not wake John for an implementation
handoff with required documentation still missing. John must not pass if changed
behavior, API, configuration, architecture, developer workflow, or operational
procedure leaves affected documentation inconsistent. Definition of Done is:
code, tests, and affected documentation agree.

Sarah, Lucía, and Maya use TDD by default: test, expected failure where practical,
implementation, green, then refactor. They own implementation tests and affected
documentation. Mateo owns architecture/ADR documentation; use small ADRs for
important decisions and supersede an old ADR when a decision changes. Agent
Infrastructure owns AgentBus/team documentation. Lucía owns CI/CD, Docker, and
deployment documentation for now. Do not create Git, DevOps, hacker, or cracker
agents: deterministic finalization uses `git diff --check`, required checks,
`git status`, and commit metadata. A normal commit needs no LLM, and pushing,
merging, or releasing still requires explicit authorization.

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

### Capability execution model

The execution contract is intentionally small: deterministic route, one
`implementer`, one independent `verifier`, then completion. `router`,
`analysis(domain=rag)`, and `security_review` are optional capabilities used
only when semantic arbitration, unresolved diagnosis, or a security boundary
requires them. Runner files may retain human-readable producer aliases for the
Zed UI, but `.agentbus/dispatch.py` authorizes by the runner's capability.

Each real handoff must carry `execution.workspace_path`; it is the authoritative
worktree for that initiative. The gate resolves it, verifies the branch and
optional base SHA, runs `poetry check --directory <workspace>/backend`, and
only then invokes AgentBus. The native command receives `agentbus run
--workspace <workspace>`, while the Codex adapter receives `codex exec -C
<workspace>`. A missing or invalid environment produces `INFRASTRUCTURE_FAILURE`
without consuming initiative budget or retrying. Worktrees therefore never
fall back to the control repository.

The project toolchain remains Poetry-based. Dependencies are installed and
locked outside model execution; preflight only verifies the declared project
configuration and requires a worktree-specific Poetry environment. Bootstrap a new
worktree once with `.agentbus/bootstrap-worktree.sh <worktree>`; it uses
configures a worktree-local Poetry virtualenv path and runs
`poetry install --no-root`, so each worktree has an isolated environment and
no dependency installation occurs during a model run.

AgentBus 0.23.0 runs one-shot Codex turns through its native `codex` adapter. `.agentbus/swarm.yaml` starts wake workers and each worker invokes the native `agentbus run --once` path through the small `.agentbus/dispatch.py` policy gate. The gate is needed because 0.23.0 workers cannot filter nested payload fields or enforce a team-wide initiative budget. It never replaces AgentBus routing or the runner.

Implementer, verifier, router, analysis and security-review runners select their capability in YAML; human names are only producer aliases. Defaults remain Luna low, with the explicitly configured Alice analysis alias retaining Luna high. Mateo's router runner uses `--sandbox read-only`: it may inspect, reason, and publish coordination events, but cannot edit application files. This per-run selection leaves the interactive Codex default untouched. The gate writes local usage records under `.agentbus/team-runtime/usage.jsonl`, containing the event, initiative, capability, selected model, effort, and exit code.

An autonomous handoff must be `PUBLISHED`, addressed to its target, newer than that agent's gate cursor, have a non-smoke initiative (unless `execution.smoke_test: true`), and include:

```yaml
execution:
  autonomous: true
  expected_initiative: <same initiative>
  budget_profile: simple | normal | high_risk | cross_cutting
  implementation_owner: sarah | lucia | maya
```

Mateo selects and persists the profile at initiative creation. Each profile separates an immediately usable base from a protected QA-fix reserve: `simple` and `normal` allow 3 base runs plus a 2-run reserve (5 absolute maximum); `high_risk` allows 4 base runs plus a 2-run reserve (6 absolute maximum). `cross_cutting` allows 5 base runs plus the same 2-run reserve (7 absolute maximum), and requires `cross_cutting_ownership_domains` to name at least two of `sarah`, `lucia`, and `maya`; it is only for work spanning two ownership domains, such as Sarah + Lucía + John, Lucía + Maya + John, or Sarah + Lucía + John + Alex. Difficulty alone does not qualify: a difficult single-owner task remains `normal` or `high_risk`. Declaring multiple domains under a smaller profile does not enlarge its base budget. A cross-cutting specialist-to-specialist handoff must be between declared domains and set `cross_cutting_handoff: true`.

The reserve unlocks once, and only when John publishes a valid concrete verification failure to the recorded implementation owner: same initiative, exact causation, `verification_failure: true`, non-empty summary, and an unused fix cycle. Its two runs are exclusively that owner’s fix and John’s re-verification; Mateo, Alex, other specialists, retries, and unrelated handoffs cannot consume it. A John pass closes the initiative without unlocking the reserve. A second verification failure is `BLOCKED` to Mateo/Andrea. Handoff and retry caps remain unchanged. Once persisted, a profile cannot change through AgentBus; an increase requires Andrea/manual approval. The gate does not invoke Codex after budget exhaustion; it publishes `BLOCKED` with `reason: budget_exhausted` to Mateo. Quota, rate, and account-limit errors publish `BLOCKED` with `reason: quota_exhausted` and do not retry.

Mateo alone may request a one-run override by adding `execution.model_override` with `requested_by: mateo`, `scope: one_run`, an approved reason, and exactly one allowed target: Luna at medium effort, Terra at low effort, or Sol at low effort. The gate creates an ephemeral runner config for that one invocation and then returns to Luna low. It never escalates after a failure.

Routing stays deliberately narrow: Mateo normally starts one-owner work; Sarah,
Lucía, and Maya receive from Mateo or John. An owner hands directly to John, and
John may return exactly one concrete failure to that same owner. John PASS writes
`okf/status/<initiative>: complete` to Andrea without another Mateo run. A
specialist-to-specialist handoff is accepted only for a genuinely cross-cutting
initiative using the existing `cross_cutting` metadata. John runs only when
`execution.qa_mode: reasoning`; mechanical checks are local automation. Alex is
reserved for auth/authz, tenant isolation, sensitive document boundaries,
migrations, prompt injection, poisoned evidence, secrets, trust boundaries,
CI/deployment security, and architecture-critical review.

Alice is a permanent on-demand RAG Theory / Research Analyst. Ordinary RAG work
does not wake Alice. Mateo explicitly invokes her read-only analysis only after
unclear root cause, multiple failed experiments, material Sarah/John disagreement,
or a costly/new architecture needing independent analysis. Alice returns competing
hypotheses, falsifiers, and the cheapest discriminating experiment to Mateo for a
decision; she never implements or opens a peer-to-peer workflow. One bounded
analysis turn is the norm and the existing initiative budget remains the hard cap.
Alice is the sole default Luna-high agent; Mateo chooses when to invoke her.

## Deliberation Mode

Mateo opens Deliberation Mode only when the normal workflow is blocked, its fix cycle is exhausted, root cause is disputed, architecture crosses ownership domains, or independent verdicts materially disagree. Select the smallest group, normally at most four relevant participants. Deliberation does not create a separate budget: every turn consumes the initiative's existing budget and escalation rules.

Round 1 is blind and independent: Mateo sends each participant the same problem and evidence in separate recipient-scoped handoffs. Participants must not inspect, request, or use another initial position; they submit diagnosis, evidence, strongest alternative, falsifier, recommended action, and confidence only to Mateo. AgentBus 0.23.0 storage is topic-wide, so this is a deterministic consumption contract rather than cryptographic payload isolation. Mateo may share material divergences for one critique round only, then synthesizes the bounded next step: selected hypothesis, rejected alternatives, uncertainty, next experiment, and success/failure criteria. Use `okf/status/<initiative>` states `IDLE`, `RUNNING`, `WAITING_QA`, `WAITING_REVIEW`, `DELIBERATING`, `BLOCKED`, `COMPLETE`, or `QUOTA_BLOCKED`; Alice additionally uses `ANALYZING` and `WAITING_DECISION`.

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

Expected result: John publishes the third event as `okf/status/<initiative>` with
`status: complete`, addressed to Andrea, with the same initiative and causation
pointing to Sarah's event. This deterministic completion does not wake Mateo.

Verify the persisted graph with:

```bash
.agentbus-venv/bin/agentbus poll --workspace "$PWD" --topic okf/handoff --since-id <cursor-before-test> --limit 100
```

It must prove this exact chain before calling the test successful: Mateo → Sarah
→ John PASS → `COMPLETE`, all with `initiative: rag/retrieval-assessment-002`,
and each derived event carrying the exact preceding `causation_id`. AgentBus is
the shared storage and coordination layer; deterministic completion consumes no
Mateo model run.

## Runtime files

`.agentbus/swarm.yaml`, `.agentbus/roles.yaml`, `requirements-agentbus.txt`, agent definitions, and this guide are reproducible configuration. `.agentbus-venv/`, the SQLite event store, tokens, logs, process state, identities, wake files, and runner state are local-only and ignored by Git. Never commit those runtime files or secrets.
