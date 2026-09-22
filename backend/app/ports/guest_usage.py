"""Application-facing contract for atomic guest demo usage."""

from typing import Protocol


class GuestUsagePort(Protocol):
    """Reserve UID, IP, and deployment-wide daily capacity together."""

    def reserve(
        self,
        *,
        uid: str,
        ip_address: str,
        uid_limit: int,
        ip_limit: int,
        global_limit: int,
    ) -> tuple[bool, int, str | None]:
        """Return whether capacity was reserved, UID count, and limiting scope."""

    def get_usage(self, *, uid: str, ip_address: str) -> tuple[int, int, int]:
        """Return today's UID, IP, and global reserved counts."""
