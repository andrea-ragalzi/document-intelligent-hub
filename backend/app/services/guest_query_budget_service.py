"""Anonymous demo budget rules applied before paid RAG work."""

from dataclasses import dataclass

from app.ports.guest_usage import GuestUsagePort
from app.services.query_quota_service import QueryQuotaReservation


@dataclass(frozen=True)
class GuestBudgetStatus:
    """Authoritative effective allowance for one anonymous request identity."""

    queries_today: int
    query_limit: int | None
    remaining: int | None
    limited: bool


class GuestBudgetExceededError(Exception):
    """Raised when an anonymous demo budget has been exhausted."""

    def __init__(self, scope: str) -> None:
        super().__init__(
            f"Guest demo {scope} daily limit reached. Please try again tomorrow."
        )
        self.scope = scope


class GuestQueryBudgetService:
    """Reserve all anonymous cost limits in one storage transaction."""

    def __init__(
        self,
        tracker: GuestUsagePort,
        uid_daily_limit: int,
        ip_daily_limit: int,
        global_daily_limit: int,
        daily_quotas_enabled: bool = True,
    ) -> None:
        self._tracker = tracker
        self._uid_daily_limit = uid_daily_limit
        self._ip_daily_limit = ip_daily_limit
        self._global_daily_limit = global_daily_limit
        self._daily_quotas_enabled = daily_quotas_enabled

    def reserve(self, uid: str, ip_address: str) -> QueryQuotaReservation:
        if not self._daily_quotas_enabled:
            return QueryQuotaReservation("GUEST", 0, 0)
        reserved, count, scope = self._tracker.reserve(
            uid=uid,
            ip_address=ip_address,
            uid_limit=self._uid_daily_limit,
            ip_limit=self._ip_daily_limit,
            global_limit=self._global_daily_limit,
        )
        if not reserved:
            raise GuestBudgetExceededError(scope or "global")
        return QueryQuotaReservation("GUEST", self._uid_daily_limit, count)

    def get_status(self, uid: str, ip_address: str) -> GuestBudgetStatus:
        """Read effective remaining capacity without reserving a query."""
        if not self._daily_quotas_enabled:
            return GuestBudgetStatus(
                queries_today=0,
                query_limit=None,
                remaining=None,
                limited=False,
            )
        uid_count, ip_count, global_count = self._tracker.get_usage(
            uid=uid, ip_address=ip_address
        )
        remaining = max(
            0,
            min(
                self._uid_daily_limit - uid_count,
                self._ip_daily_limit - ip_count,
                self._global_daily_limit - global_count,
            ),
        )
        return GuestBudgetStatus(
            queries_today=uid_count,
            query_limit=self._uid_daily_limit,
            remaining=remaining,
            limited=True,
        )
