"""Small in-process concurrency guard for expensive RAG requests."""

import asyncio

from app.core.config import settings


class QueryConcurrencyLimiter:
    """Limit simultaneously active RAG requests for each authenticated UID."""

    def __init__(self, max_concurrent_per_user: int = 1) -> None:
        self.max_concurrent_per_user = max_concurrent_per_user
        self._active_requests: dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def acquire(self, user_id: str) -> bool:
        """Reserve a per-user slot, returning False when already at capacity."""
        async with self._lock:
            active_count = self._active_requests.get(user_id, 0)
            if active_count >= self.max_concurrent_per_user:
                return False
            self._active_requests[user_id] = active_count + 1
            return True

    async def release(self, user_id: str) -> None:
        """Release a slot after either a successful or failed query."""
        async with self._lock:
            active_count = self._active_requests.get(user_id, 0)
            if active_count <= 1:
                self._active_requests.pop(user_id, None)
            else:
                self._active_requests[user_id] = active_count - 1


query_concurrency_limiter = QueryConcurrencyLimiter()


class GlobalExpensiveOperationLimiter:
    """Process-local guard for paid/CPU-heavy operations with bounded waiting.

    It is sufficient for the current single-process public demo. Multiple
    processes or replicas need a shared limiter for deployment-wide bounds.
    """

    def __init__(self, maximum: int | None = None) -> None:
        self.maximum = (
            maximum if maximum is not None else settings.MAX_GLOBAL_EXPENSIVE_OPERATIONS
        )
        self.active = 0
        self._condition = asyncio.Condition()

    async def acquire(self) -> bool:
        async with self._condition:
            if self.active >= self.maximum:
                return False
            self.active += 1
            return True

    async def acquire_with_timeout(self, timeout_seconds: float) -> bool:
        """Wait briefly for a global slot, without allowing an unbounded queue."""

        async def reserve_slot() -> None:
            async with self._condition:
                while self.active >= self.maximum:
                    await self._condition.wait()
                self.active += 1

        try:
            await asyncio.wait_for(reserve_slot(), timeout=timeout_seconds)
            return True
        except TimeoutError:
            return False

    async def release(self) -> None:
        async with self._condition:
            self.active = max(0, self.active - 1)
            self._condition.notify(1)


global_expensive_operation_limiter = GlobalExpensiveOperationLimiter()
