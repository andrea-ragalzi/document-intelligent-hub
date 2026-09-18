#!/usr/bin/env python3
"""Deterministic gate for isolated AgentBus capability runners."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
POLICY_PATH = ROOT / ".agentbus" / "team-policy.yaml"
RUNTIME = ROOT / ".agentbus" / "team-runtime"
BUS = ROOT / ".agentbus-venv" / "bin" / "agentbus"


def read_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError(f"expected mapping: {path}")
    return value


def read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else default


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def event_from_store(event_id: int) -> dict[str, Any] | None:
    db = ROOT / ".agentbus" / "events.db"
    if not db.exists():
        return None
    with sqlite3.connect(db) as con:
        row = con.execute("SELECT event_id, topic, producer_id, payload, causation_id, status FROM events WHERE event_id = ?", (event_id,)).fetchone()
    if row is None:
        return None
    return {"event_id": row[0], "topic": row[1], "producer_id": row[2], "payload": json.loads(row[3]), "causation_id": row[4], "status": row[5]}


def handoffs(initiative: str) -> int:
    db = ROOT / ".agentbus" / "events.db"
    if not db.exists():
        return 0
    with sqlite3.connect(db) as con:
        rows = con.execute("SELECT payload FROM events WHERE topic='okf/handoff' AND status='PUBLISHED'").fetchall()
    return sum(1 for (raw,) in rows if (payload := json.loads(raw)).get("initiative") == initiative and payload.get("action", {}).get("type") != "runner_ack")


def publish_blocked(agent: str, event: dict[str, Any], reason: str) -> None:
    payload = event["payload"]
    body = {"from": agent, "to": payload.get("from", "mateo"), "initiative": payload.get("initiative"), "summary": f"BLOCKED: {reason}; event {event['event_id']} preserved.", "reason": reason, "action": {"type": "message", "kind": "blocked"}}
    subprocess.run([str(BUS), "publish", "--workspace", str(ROOT), "--topic", f"okf/status/{payload.get('initiative', 'unknown')}", "--producer-id", agent, "--causation-id", str(event["event_id"]), "--idempotency-key", f"blocked:{agent}:{event['event_id']}:{reason}", "--payload", json.dumps(body)], check=False, capture_output=True)


def model_for(execution: dict[str, Any], policy: dict[str, Any]) -> tuple[str, str, bool]:
    override = execution.get("model_override")
    default = policy["default_runner"]
    if override is None:
        return str(default["model"]), str(default["reasoning_effort"]), False
    escalation = policy["escalation"]
    if override.get("requested_by") != escalation["requested_by"] or override.get("scope") != escalation["scope"] or override.get("reason") not in escalation["reasons"]:
        raise ValueError("invalid_model_override")
    pair = {"model": override.get("model"), "reasoning_effort": override.get("reasoning_effort")}
    if pair not in escalation["allowed"]:
        raise ValueError("invalid_model_override_target")
    return str(pair["model"]), str(pair["reasoning_effort"]), True


def limits_for(execution: dict[str, Any], state: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    requested = execution.get("budget_profile")
    current = state.get("budget_profile")
    if current is not None and requested != current:
        raise ValueError("budget_profile_change_requires_manual_approval")
    if requested not in policy["budget_profiles"]:
        raise ValueError("budget_profile_missing_or_invalid")
    state["budget_profile"] = requested
    return policy["budget_profiles"][requested]


def workspace_preflight(execution: dict[str, Any]) -> Path:
    raw = execution.get("workspace_path")
    if not isinstance(raw, str) or not raw:
        raise ValueError("workspace_path_required")
    workspace = Path(raw).expanduser().resolve()
    if not workspace.is_dir() or not (workspace / "backend" / "pyproject.toml").exists():
        raise ValueError("invalid_worktree")
    poetry = os.environ.get("POETRY", "poetry")
    env_path = subprocess.run([poetry, "env", "info", "--path", "--directory", str(workspace / "backend")], capture_output=True, text=True, check=False).stdout.strip()
    if not env_path or not (Path(env_path) / "bin" / "python").exists():
        raise ValueError("project_environment_missing")
    branch = execution.get("branch")
    if branch:
        actual = subprocess.run(["git", "-C", str(workspace), "branch", "--show-current"], capture_output=True, text=True, check=False).stdout.strip()
        if actual != branch:
            raise ValueError("branch_mismatch")
    base = execution.get("base_sha")
    if base and subprocess.run(["git", "-C", str(workspace), "cat-file", "-e", f"{base}^{{commit}}"], capture_output=True, check=False).returncode:
        raise ValueError("base_sha_missing")
    if subprocess.run([poetry, "check", "--directory", str(workspace / "backend")], capture_output=True, check=False).returncode:
        raise ValueError("project_environment_invalid")
    return workspace


def preflight_report(execution: dict[str, Any], runner: dict[str, Any]) -> dict[str, Any]:
    """Run the production preflight and expose its evidence without dispatch."""
    workspace = workspace_preflight(execution)
    git_root = subprocess.run(["git", "-C", str(workspace), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip()
    head = subprocess.run(["git", "-C", str(workspace), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    branch = subprocess.run(["git", "-C", str(workspace), "branch", "--show-current"], capture_output=True, text=True, check=True).stdout.strip()
    cwd = subprocess.run(["pwd"], cwd=workspace, capture_output=True, text=True, check=True).stdout.strip()
    poetry = os.environ.get("POETRY", "poetry")
    env_path = Path(subprocess.run([poetry, "env", "info", "--path", "--directory", str(workspace / "backend")], capture_output=True, text=True, check=True).stdout.strip())
    python = env_path / "bin" / "python"
    tools: dict[str, Any] = {"python": str(python)}
    for tool in ("pytest", "ruff", "mypy"):
        executable = env_path / "bin" / tool
        check = subprocess.run([str(executable), "--version"], cwd=workspace / "backend", capture_output=True, text=True, check=False)
        tools[tool] = {"available": check.returncode == 0, "version": (check.stdout or check.stderr).strip()}
    return {"workspace_path": str(workspace), "cwd": cwd, "git_root": git_root,
            "expected_branch": execution.get("branch"), "actual_branch": branch,
            "expected_base_sha": execution.get("base_sha"), "actual_head": head,
            "clean": not bool(subprocess.run(["git", "-C", str(workspace), "status", "--porcelain"], capture_output=True, text=True, check=True).stdout.strip()),
            "python": str(python), "tools": tools, "codex_command": codex_command(runner, workspace)}


def validate_route(capability: str, event: dict[str, Any], execution: dict[str, Any], state: dict[str, Any], limits: dict[str, Any]) -> bool:
    source = event["payload"].get("from")
    if capability == "implementer":
        if source == "verifier":
            if execution.get("verification_failure") is not True or not str(execution.get("failure_summary", "")).strip():
                raise ValueError("invalid_verification_failure")
            if state.get("fix_cycles_used", 0) >= limits["max_fix_cycles"] or state.get("fix_reserve_unlocked"):
                raise ValueError("fix_cycle_budget_exhausted")
            state["fix_cycles_used"] = int(state.get("fix_cycles_used", 0)) + 1
            state["fix_reserve_unlocked"] = True
            return True
        if source not in {"router", "mateo", "analysis"}:
            raise ValueError("implementer_source_not_allowed")
    elif capability == "verifier" and source not in {"implementer", "router", "mateo"}:
        raise ValueError("verifier_source_not_allowed")
    return False


def codex_command(runner: dict[str, Any], workspace: Path) -> list[str]:
    adapter = runner["adapter"]
    return [str(adapter["command"]), "exec", "-C", str(workspace), "--ephemeral", "--json", "-m", str(adapter["model"]), *map(str, adapter.get("extra_args", [])), "-"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", required=True)
    parser.add_argument("--runner", required=True)
    parser.add_argument("--print-command", action="store_true")
    parser.add_argument("--workspace")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--initiative")
    parser.add_argument("--branch")
    parser.add_argument("--base-sha")
    args = parser.parse_args()
    policy = read_yaml(POLICY_PATH)
    runner = read_yaml((ROOT / args.runner).resolve())
    if args.print_command:
        workspace = Path(args.workspace).expanduser().resolve() if args.workspace else Path("<initiative-workspace>")
        print(" ".join(codex_command(runner, workspace)))
        return 0
    if args.preflight_only:
        if not args.workspace or not args.initiative:
            parser.error("--preflight-only requires --workspace and --initiative")
        execution = {"workspace_path": args.workspace, "expected_initiative": args.initiative,
                     "branch": args.branch, "base_sha": args.base_sha}
        try:
            print(json.dumps(preflight_report(execution, runner), indent=2))
        except (OSError, subprocess.CalledProcessError, ValueError) as exc:
            print(json.dumps({"status": "INFRASTRUCTURE_FAILURE", "reason": str(exc)}))
            return 2
        return 0
    wake = read_json(ROOT / ".agentbus" / f"WAKE.{args.agent}.json", {})
    event_id = wake.get("event_id")
    if not isinstance(event_id, int):
        return 0
    event = event_from_store(event_id)
    if event is None:
        return 0
    payload, execution = event["payload"], event["payload"].get("execution")
    cursor_path = RUNTIME / "cursors" / f"{args.agent}.json"
    cursor = read_json(cursor_path, {"last_examined_event_id": 0})
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
        return reject("active_initiative_mismatch", True)
    if payload["initiative"].startswith("smoke/") and execution.get("smoke_test") is not True:
        return reject("smoke_not_explicit", True)
    try:
        workspace = workspace_preflight(execution)
        model, effort, escalated = model_for(execution, policy)
        state_path = RUNTIME / "state" / f"{payload['initiative']}.json"
        state = read_json(state_path, {"runs": 0, "base_runs_used": 0, "fix_reserve_runs_used": 0, "fix_reserve_unlocked": False, "escalated_runs": 0, "fix_cycles_used": 0})
        limits = limits_for(execution, state, policy)
        if state["runs"] >= limits["max_agent_runs"] or handoffs(payload["initiative"]) >= limits["max_handoffs"]:
            raise ValueError("budget_exhausted")
        reserve = validate_route(str(runner.get("capability", "implementer")), event, execution, state, limits)
        if reserve and state["fix_reserve_runs_used"] >= limits["fix_reserve_runs"]:
            raise ValueError("fix_reserve_exhausted")
        if not reserve and state["base_runs_used"] >= limits["base_agent_runs"]:
            raise ValueError("base_agent_runs_exhausted")
        if escalated and state["escalated_runs"] >= limits["max_escalated_runs"]:
            raise ValueError("escalation_budget_exhausted")
        write_json(state_path, state)
    except ValueError as exc:
        reason = str(exc)
        if reason in {"workspace_path_required", "invalid_worktree", "project_environment_missing", "branch_mismatch", "base_sha_missing", "project_environment_invalid"}:
            reason = f"INFRASTRUCTURE_FAILURE:{reason}"
        return reject(reason, True)
    effective = dict(runner)
    effective["adapter"] = dict(runner["adapter"])
    effective["adapter"]["model"] = model
    extra = list(effective["adapter"].get("extra_args", []))
    effective["adapter"]["extra_args"] = [item for item in extra if not str(item).startswith("model_reasoning_effort=")]
    effective["adapter"]["extra_args"] += ["-c", f'model_reasoning_effort="{effort}"']
    temporary = RUNTIME / "runners" / f"{args.agent}-{event_id}.yaml"
    temporary.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_text(yaml.safe_dump(effective, sort_keys=False), encoding="utf-8")
    state["runs"] += 1
    state["fix_reserve_runs_used"] += int(reserve)
    state["base_runs_used"] += int(not reserve)
    state["escalated_runs"] += int(escalated)
    write_json(state_path, state)
    result = subprocess.run([str(BUS), "run", "--workspace", str(workspace), "--config", str(temporary), "--once"], capture_output=True, text=True, check=False)
    cursor["last_examined_event_id"] = event_id
    write_json(cursor_path, cursor)
    telemetry = RUNTIME / "usage.jsonl"
    telemetry.parent.mkdir(parents=True, exist_ok=True)
    with telemetry.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"timestamp": dt.datetime.now(dt.timezone.utc).isoformat(), "event_id": event_id, "initiative": payload["initiative"], "capability": runner.get("capability"), "model": model, "reasoning_effort": effort, "exit_code": result.returncode}, sort_keys=True) + "\n")
    output = (result.stdout + result.stderr).lower()
    if any(marker in output for marker in ("usage limit", "quota", "rate limit", "account limit")):
        publish_blocked(args.agent, event, "quota_exhausted")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
