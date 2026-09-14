"""Small in-process concurrency guard for expensive RAG requests."""

import asyncio
import os


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
    """Non-queuing process-wide admission guard for paid/CPU-heavy operations."""

    def __init__(self, maximum: int | None = None) -> None:
        self.maximum = maximum if maximum is not None else int(os.getenv("MAX_GLOBAL_EXPENSIVE_OPERATIONS", "2"))
        self.active = 0
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        async with self._lock:
            if self.active >= self.maximum:
                return False
            self.active += 1
            return True

    async def release(self) -> None:
        async with self._lock:
            self.active = max(0, self.active - 1)


global_expensive_operation_limiter = GlobalExpensiveOperationLimiter()
