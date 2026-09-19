"""Optional read-only observability contract for evaluator runs.

The application never enables this observer for normal requests.  Keeping the
contract in a small port module avoids importing evaluator code into the RAG
services and makes tracing side-effect free when disabled.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol


class EvaluationTraceObserver(Protocol):
    """Receive immutable, metadata-only pipeline observations."""

    def record(self, stage: str, payload: Mapping[str, Any]) -> None:
        """Record one stage snapshot without changing pipeline state."""
