"""Application-facing contract for query usage persistence."""

from typing import Protocol


class UsageTrackingPort(Protocol):
    """Operations required to reserve daily query capacity."""

    def reserve_query_slot(self, user_id: str, max_queries: int) -> tuple[bool, int]:
        """Atomically reserve a query slot and return its resulting count."""
