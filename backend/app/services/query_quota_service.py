"""Application rules for resolving and reserving query quota."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from app.config.security_constants import UNLIMITED_TIER_MAX_QUERIES
from app.core.logging import logger
from app.ports.usage_tracking import UsageTrackingPort


@dataclass(frozen=True)
class QueryQuotaReservation:
    """Successful query quota reservation details."""

    tier: str
    max_queries: int
    reserved_count: int


class QueryLimitExceededError(Exception):
    """Raised when no daily query slot can be reserved."""

    def __init__(self, reserved_count: int, max_queries: int) -> None:
        super().__init__(
            f"Daily query limit exceeded ({reserved_count}/{max_queries}). "
            "Please upgrade your plan or try again tomorrow."
        )
        self.reserved_count = reserved_count
        self.max_queries = max_queries


class QueryQuotaService:
    """Resolve tier limits and reserve quota before paid query work begins."""

    def __init__(
        self,
        tier_provider: Callable[[str], str],
        limits_provider: Callable[[], Mapping[str, Any]],
        usage_tracker: UsageTrackingPort,
    ) -> None:
        self._tier_provider = tier_provider
        self._limits_provider = limits_provider
        self._usage_tracker = usage_tracker

    def reserve(self, user_id: str) -> QueryQuotaReservation:
        """Resolve the user's limit and atomically reserve one query slot."""
        tier = self._tier_provider(user_id)
        logger.info(f"🎫 User ID: {user_id}")
        logger.info(f"🎫 User tier: {tier}")

        if tier == "UNLIMITED":
            max_queries = UNLIMITED_TIER_MAX_QUERIES
        else:
            limits = self._limits_provider()["limits"]
            tier_limits = limits.get(tier, limits["FREE"])
            max_queries = int(tier_limits["max_queries_per_day"])

        can_query, reserved_count = self._usage_tracker.reserve_query_slot(
            user_id, max_queries
        )
        logger.info(
            f"📊 Usage reservation result: reserved={can_query}, "
            f"queries_used={reserved_count}, max_queries={max_queries}"
        )
        if not can_query:
            logger.warning(
                f"⛔ Query limit exceeded for user {user_id} ({tier}): "
                f"{reserved_count}/{max_queries}"
            )
            raise QueryLimitExceededError(reserved_count, max_queries)

        return QueryQuotaReservation(tier, max_queries, reserved_count)
