#!/usr/bin/env bash
set -euo pipefail

# Run once per isolated worktree, outside AgentBus/model execution.
worktree="${1:?usage: bootstrap-worktree.sh <worktree> }"
worktree="$(cd "$worktree" && pwd -P)"
cd "$worktree/backend"
poetry config virtualenvs.in-project false --local
poetry config virtualenvs.path "$worktree/.poetry-venvs" --local
poetry env remove --all >/dev/null 2>&1 || true
poetry install --no-root
