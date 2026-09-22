"""Anonymous demo budget rules applied before paid RAG work."""

from app.ports.guest_usage import GuestUsagePort
from app.services.query_quota_service import QueryQuotaReservation


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
    ) -> None:
        self._tracker = tracker
        self._uid_daily_limit = uid_daily_limit
        self._ip_daily_limit = ip_daily_limit
        self._global_daily_limit = global_daily_limit

    def reserve(self, uid: str, ip_address: str) -> QueryQuotaReservation:
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
