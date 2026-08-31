"""Small in-process rate limiter for authenticated support submissions."""

import asyncio
import time
from collections import defaultdict, deque

from app.config.security_constants import BUG_REPORT_RATE_LIMIT, FEEDBACK_RATE_LIMIT


class SupportRateLimiter:
    """Limit bug reports and feedback per authenticated UID in a rolling hour."""

    def __init__(self) -> None:
        self._events: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()
        self._limits = {
            "bug_report": self._limit_from_setting(BUG_REPORT_RATE_LIMIT),
            "feedback": self._limit_from_setting(FEEDBACK_RATE_LIMIT),
        }

    @staticmethod
    def _limit_from_setting(setting: str) -> int:
        return int(setting.split("/", maxsplit=1)[0])

    async def allow(self, event_type: str, user_id: str) -> bool:
        """Reserve a submission slot, returning False once its hourly limit is full."""
        now = time.monotonic()
        key = (event_type, user_id)
        async with self._lock:
            events = self._events[key]
            while events and now - events[0] >= 3600:
                events.popleft()
            if len(events) >= self._limits[event_type]:
                return False
            events.append(now)
            return True

    def clear(self) -> None:
        """Clear process-local state; used by focused tests."""
        self._events.clear()


support_rate_limiter = SupportRateLimiter()
