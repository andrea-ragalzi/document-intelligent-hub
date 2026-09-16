#!/usr/bin/env python3
"""Gate native AgentBus runner launches for the autonomous team.

This is deliberately a small policy layer, not an orchestrator: AgentBus
workers still detect and wake handoffs, and ``agentbus run --once`` still
owns the Codex turn. The gate accepts only explicitly autonomous, deterministic
handoffs and records per-initiative runtime accounting.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent.parent
POLICY_PATH = ROOT / ".agentbus" / "team-policy.yaml"
RUNTIME = ROOT / ".agentbus" / "team-runtime"
BUS = ROOT / ".agentbus-venv" / "bin" / "agentbus"
IMPLEMENTERS = frozenset({"sarah", "lucia", "maya"})


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"expected mapping in {path}")
    return data


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else default


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def wake_for(agent: str) -> Path:
    return ROOT / ".agentbus" / f"WAKE.{agent}.json"


def event_from_store(event_id: int) -> dict[str, Any] | None:
    db = ROOT / ".agentbus" / "events.db"
    if not db.exists():
        return None
    con = sqlite3.connect(db)
    try:
        row = con.execute(
            "SELECT event_id, topic, producer_id, payload, causation_id, status "
            "FROM events WHERE event_id = ?", (event_id,)
        ).fetchone()
    finally:
        con.close()
    if row is None:
        return None
    return {
        "event_id": int(row[0]), "topic": row[1], "producer_id": row[2],
        "payload": json.loads(row[3]), "causation_id": row[4], "status": row[5],
    }


def count_handoffs(initiative: str) -> int:
    db = ROOT / ".agentbus" / "events.db"
    if not db.exists():
        return 0
    con = sqlite3.connect(db)
    try:
        rows = con.execute(
            "SELECT payload FROM events WHERE topic = 'okf/handoff' AND status = 'PUBLISHED'"
        ).fetchall()
    finally:
        con.close()
    total = 0
    for (raw,) in rows:
        payload = json.loads(raw)
        action = payload.get("action") if isinstance(payload, dict) else None
        if payload.get("initiative") == initiative and not (
            isinstance(action, dict) and action.get("type") == "runner_ack"
        ):
            total += 1
    return total


def token_usage(result_path: Path) -> dict[str, Any] | None:
    if not result_path.exists():
        return None
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
        stdout = result.get("result", {}).get("detail", {}).get("stdout", "")
        for line in reversed(str(stdout).splitlines()):
            item = json.loads(line)
            if item.get("type") == "turn.completed":
                return item.get("usage") if isinstance(item.get("usage"), dict) else None
    except (json.JSONDecodeError, AttributeError):
        return None
    return None


def publish_blocked(agent: str, event: dict[str, Any], reason: str) -> None:
    initiative = event["payload"]["initiative"]
    payload = {
        "from": agent,
        "to": "mateo",
        "initiative": initiative,
        "summary": f"BLOCKED: {reason}; pending event_id={event['event_id']} is preserved.",
        "reason": reason,
        "action": {"type": "message", "kind": "blocked"},
    }
    subprocess.run([
        str(BUS), "publish", "--workspace", str(ROOT),
        "--topic", f"okf/status/{initiative}", "--producer-id", agent,
        "--causation-id", str(event["event_id"]),
        "--idempotency-key", f"gate-blocked:{agent}:{event['event_id']}:{reason}",
        "--payload", json.dumps(payload),
    ], check=False, capture_output=True, text=True)


def override_for(execution: dict[str, Any], policy: dict[str, Any]) -> tuple[str, str, bool]:
    default = policy["default_runner"]
    override = execution.get("model_override")
    if override is None:
        return default["model"], default["reasoning_effort"], False
    if not isinstance(override, dict):
        raise ValueError("invalid_model_override")
    if override.get("requested_by") != policy["escalation"]["requested_by"]:
        raise ValueError("invalid_model_override_requester")
    if override.get("scope") != policy["escalation"]["scope"]:
        raise ValueError("invalid_model_override_scope")
    if override.get("reason") not in policy["escalation"]["reasons"]:
        raise ValueError("invalid_model_override_reason")
    pair = {"model": override.get("model"), "reasoning_effort": override.get("reasoning_effort")}
    if pair not in policy["escalation"]["allowed"]:
        raise ValueError("invalid_model_override_target")
    return str(pair["model"]), str(pair["reasoning_effort"]), True


def profile_for(
    execution: dict[str, Any], state: dict[str, Any], policy: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    requested = execution.get("budget_profile")
    existing = state.get("budget_profile")
    profiles = policy["budget_profiles"]
    if existing is not None:
        if requested != existing:
            raise ValueError("budget_profile_change_requires_manual_approval")
        return str(existing), profiles[str(existing)]
    if requested not in profiles:
        raise ValueError("budget_profile_missing_or_invalid")
    state["budget_profile"] = requested
    return str(requested), profiles[str(requested)]


def cross_cutting_domains_for(execution: dict[str, Any], state: dict[str, Any], profile: str) -> set[str]:
    requested = execution.get("cross_cutting_ownership_domains")
    if requested is None:
        if profile == "cross_cutting":
            raise ValueError("cross_cutting_ownership_domains_required")
        return set()
    if not isinstance(requested, list) or len(requested) < 2 or set(requested) - IMPLEMENTERS:
        raise ValueError("cross_cutting_ownership_domains_required")
    domains = set(requested)
    if len(domains) < 2:
        raise ValueError("cross_cutting_ownership_domains_required")
    existing = state.get("cross_cutting_ownership_domains")
    if existing is not None and set(existing) != domains:
        raise ValueError("cross_cutting_ownership_domains_mismatch")
    state["cross_cutting_ownership_domains"] = sorted(domains)
    return domains


def owner_for(execution: dict[str, Any], state: dict[str, Any], domains: set[str]) -> str:
    requested = execution.get("implementation_owner")
    existing = state.get("implementation_owner")
    if existing is not None:
        if requested != existing:
            raise ValueError("implementation_owner_mismatch")
        return str(existing)
    if requested not in IMPLEMENTERS or (domains and requested not in domains):
        raise ValueError("implementation_owner_missing_or_invalid")
    state["implementation_owner"] = requested
    return str(requested)


def validate_fix_route(
    agent: str, event: dict[str, Any], execution: dict[str, Any],
    state: dict[str, Any], limits: dict[str, Any], owner: str, domains: set[str],
) -> str | None:
    payload = event["payload"]
    source = payload.get("from")
    initiative = payload["initiative"]
    if agent in IMPLEMENTERS and source == "john":
        failure_summary = execution.get("verification_failure_summary")
        if event.get("producer_id") != "john" or owner != agent or execution.get("verification_failure") is not True or not isinstance(failure_summary, str) or not failure_summary.strip():
            raise ValueError("invalid_john_fix_request")
        consumed_id = execution.get("john_consumed_event_id")
        if not isinstance(consumed_id, int) or event.get("causation_id") != consumed_id:
            raise ValueError("fix_causation_mismatch")
        consumed = event_from_store(consumed_id)
        if consumed is None or consumed["payload"].get("from") != owner or consumed["payload"].get("to") != "john" or consumed["payload"].get("initiative") != initiative:
            raise ValueError("fix_consumed_event_mismatch")
        used = execution.get("fix_cycles_used")
        if not isinstance(used, int) or used != int(state.get("fix_cycles_used", 0)):
            raise ValueError("fix_cycle_state_mismatch")
        if used >= limits["max_fix_cycles"]:
            raise ValueError("fix_cycle_budget_exhausted")
        state["fix_cycles_used"] = used + 1
        # A valid John failure is the only event that unlocks the protected
        # reserve. It is deliberately a state transition, not a generic
        # "runs remaining" calculation.
        if state.get("fix_reserve_unlocked", False):
            raise ValueError("fix_reserve_already_unlocked")
        state["fix_reserve_unlocked"] = True
        return "implementation_owner_fix"
    elif agent in IMPLEMENTERS and source == "mateo":
        if agent != owner and agent not in domains:
            raise ValueError("implementation_owner_mismatch")
    elif agent in IMPLEMENTERS and source in IMPLEMENTERS:
        if not domains or source not in domains or agent not in domains or execution.get("cross_cutting_handoff") is not True:
            raise ValueError("cross_cutting_handoff_not_eligible")
    elif agent in IMPLEMENTERS:
        raise ValueError("implementer_source_not_allowed")

    if agent == "john" and execution.get("fix_cycle") is not None:
        if execution.get("fix_cycle") != int(state.get("fix_cycles_used", 0)):
            raise ValueError("fix_cycle_state_mismatch")
        request_id = execution.get("fix_request_event_id")
        if not isinstance(request_id, int) or event.get("causation_id") != request_id:
            raise ValueError("fix_causation_mismatch")
        request = event_from_store(request_id)
        if request is None or request["payload"].get("from") != "john" or request["payload"].get("to") != owner or request["payload"].get("initiative") != initiative or request["payload"].get("execution", {}).get("verification_failure") is not True:
            raise ValueError("fix_request_event_mismatch")
        return "john_reverification"
    return None


def codex_command(runner: dict[str, Any]) -> list[str]:
    adapter = runner["adapter"]
    return [
        str(adapter["command"]), "exec", "-C", str(ROOT), "--ephemeral", "--json",
        "-m", str(adapter["model"]), *[str(x) for x in adapter.get("extra_args", [])], "-",
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", required=True)
    parser.add_argument("--runner", required=True)
    parser.add_argument("--print-command", action="store_true")
    args = parser.parse_args()
    policy = load_yaml(POLICY_PATH)
    runner_path = (ROOT / args.runner).resolve()
    runner = load_yaml(runner_path)
    if args.print_command:
        print(" ".join(codex_command(runner)))
        return 0

    wake = load_json(wake_for(args.agent), {})
    event_id = wake.get("event_id")
    if not isinstance(event_id, int):
        return 0
    event = event_from_store(event_id)
    if event is None:
        return 0
    payload = event["payload"]
    execution = payload.get("execution") if isinstance(payload, dict) else None
    state_path = RUNTIME / "state" / f"{payload.get('initiative', 'unknown')}.json"
    cursor_path = RUNTIME / "cursors" / f"{args.agent}.json"
    cursor = load_json(cursor_path, {"last_examined_event_id": 0})

    def reject(reason: str, blocked: bool = False) -> int:
        cursor["last_examined_event_id"] = max(int(cursor.get("last_examined_event_id", 0)), event_id)
        write_json(cursor_path, cursor)
        if blocked and isinstance(payload.get("initiative"), str):
            publish_blocked(args.agent, event, reason)
        return 0

    if event["topic"] != "okf/handoff" or event["status"] != "PUBLISHED":
        return reject("not_published_handoff")
    if payload.get("to") != args.agent or not isinstance(payload.get("initiative"), str):
        return reject("recipient_or_initiative_mismatch")
    if event_id <= int(cursor.get("last_examined_event_id", 0)):
        return reject("stale_event")
    if not isinstance(execution, dict) or execution.get("autonomous") is not True:
        return reject("autonomous_not_requested")
    if execution.get("expected_initiative") != payload["initiative"]:
        return reject("active_initiative_mismatch", blocked=True)
    if payload["initiative"].startswith("smoke/") and execution.get("smoke_test") is not True:
        return reject("smoke_not_explicit", blocked=True)
    if args.agent == "alex":
        if execution.get("review_scope") not in policy["alex_review_scopes"]:
            return reject("alex_review_not_eligible", blocked=True)
    if args.agent == "john" and execution.get("qa_mode") != "reasoning":
        return reject("mechanical_qa_does_not_need_codex")
    if args.agent == "mateo" and execution.get("mateo_reasoning_reason") not in policy["mateo_reasoning_reasons"]:
        return reject("mateo_reasoning_not_required")

    try:
        model, effort, escalated = override_for(execution, policy)
    except ValueError as exc:
        return reject(str(exc), blocked=True)

    state = load_json(
        state_path,
        {
            "runs": 0, "base_runs_used": 0, "fix_reserve_runs_used": 0,
            "fix_reserve_unlocked": False, "escalated_runs": 0,
            "attempts": {}, "fix_cycles_used": 0,
        },
    )
    # Runtime state is ignored and local. Preserve compatibility with an
    # already-created initiative by treating historical runs as base usage.
    state.setdefault("base_runs_used", int(state.get("runs", 0)))
    state.setdefault("fix_reserve_runs_used", 0)
    state.setdefault("fix_reserve_unlocked", False)
    try:
        profile, limits = profile_for(execution, state, policy)
        domains = cross_cutting_domains_for(execution, state, profile)
        owner = owner_for(execution, state, domains)
        reserve_role = validate_fix_route(args.agent, event, execution, state, limits, owner, domains)
    except ValueError as exc:
        write_json(state_path, state)
        return reject(str(exc), blocked=True)
    write_json(state_path, state)
    retry_key = str(execution.get("retry_of") or event_id)
    attempts = state.setdefault("attempts", {}).setdefault(args.agent, {}).get(retry_key, 0)
    if state.get("runs", 0) >= limits["max_agent_runs"] or count_handoffs(payload["initiative"]) >= limits["max_handoffs"]:
        return reject("budget_exhausted", blocked=True)
    if reserve_role is not None:
        if not state.get("fix_reserve_unlocked", False):
            return reject("fix_reserve_not_unlocked", blocked=True)
        if int(state.get("fix_reserve_runs_used", 0)) >= limits["fix_reserve_runs"]:
            return reject("fix_reserve_exhausted", blocked=True)
    elif int(state.get("base_runs_used", 0)) >= limits["base_agent_runs"]:
        return reject("base_agent_runs_exhausted", blocked=True)
    if attempts > limits["max_retries_per_agent"]:
        return reject("retry_budget_exhausted", blocked=True)
    if int(state.get("fix_cycles_used", 0)) > limits["max_fix_cycles"]:
        return reject("fix_cycle_budget_exhausted", blocked=True)
    if escalated and state.get("escalated_runs", 0) >= limits["max_escalated_runs"]:
        return reject("escalation_budget_exhausted", blocked=True)

    effective = dict(runner)
    effective["adapter"] = dict(runner["adapter"])
    effective["adapter"]["model"] = model
    original_extra = list(effective["adapter"].get("extra_args", []))
    extra: list[Any] = []
    index = 0
    while index < len(original_extra):
        current = str(original_extra[index])
        following = str(original_extra[index + 1]) if index + 1 < len(original_extra) else ""
        if current == "-c" and following.startswith("model_reasoning_effort="):
            index += 2
            continue
        extra.append(original_extra[index])
        index += 1
    effective["adapter"]["extra_args"] = extra + ["-c", f'model_reasoning_effort="{effort}"']
    temporary = RUNTIME / "runners" / f"{args.agent}-{event_id}.yaml"
    temporary.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_text(yaml.safe_dump(effective, sort_keys=False), encoding="utf-8")
    state["runs"] = int(state.get("runs", 0)) + 1
    if reserve_role is not None:
        state["fix_reserve_runs_used"] = int(state.get("fix_reserve_runs_used", 0)) + 1
    else:
        state["base_runs_used"] = int(state.get("base_runs_used", 0)) + 1
    if escalated:
        state["escalated_runs"] = int(state.get("escalated_runs", 0)) + 1
    state["attempts"][args.agent][retry_key] = attempts + 1
    write_json(state_path, state)
    result = subprocess.run([
        str(BUS), "run", "--workspace", str(ROOT), "--config", str(temporary), "--once"
    ], check=False, capture_output=True, text=True)
    result_path = ROOT / ".agentbus" / "runs" / str(event_id) / "result.json"
    record = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "event_id": event_id, "initiative": payload["initiative"], "agent": args.agent,
        "runner_id": runner["runner_id"], "model": model, "reasoning_effort": effort,
        "escalated": escalated, "exit_code": result.returncode,
        "token_usage": token_usage(result_path),
    }
    telemetry = RUNTIME / "usage.jsonl"
    telemetry.parent.mkdir(parents=True, exist_ok=True)
    with telemetry.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    cursor["last_examined_event_id"] = event_id
    write_json(cursor_path, cursor)
    result_text = result.stdout + result.stderr
    if result_path.exists():
        result_text += result_path.read_text(encoding="utf-8")
    lowered = result_text.lower()
    if "usage limit" in lowered or "quota" in lowered or "rate limit" in lowered or "account limit" in lowered:
        publish_blocked(args.agent, event, "quota_exhausted")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
