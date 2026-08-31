"""Small in-process concurrency guard for expensive RAG requests."""

import asyncio


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
