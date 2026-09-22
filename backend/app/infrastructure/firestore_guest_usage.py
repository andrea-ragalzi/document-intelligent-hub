"""Atomic Firestore adapter for anonymous demo budgets."""

import hashlib
from datetime import UTC, datetime
from typing import Any, cast

from firebase_admin import firestore
from google.cloud.firestore import transactional as firestore_transactional
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

from app.core.logging import logger


class FirestoreGuestUsageTracker:
    """Atomically reserve UID, hashed-IP, and global daily counters."""

    def __init__(self) -> None:
        self.db = firestore.client()

    @staticmethod
    def _today() -> str:
        return datetime.now(UTC).strftime("%Y-%m-%d")

    @staticmethod
    def _ip_key(ip_address: str) -> str:
        return hashlib.sha256(ip_address.encode("utf-8")).hexdigest()

    def reserve(
        self,
        *,
        uid: str,
        ip_address: str,
        uid_limit: int,
        ip_limit: int,
        global_limit: int,
    ) -> tuple[bool, int, str | None]:
        """Check and increment every limit in one retryable transaction."""
        try:
            day = self._today()
            usage_ref = self.db.collection("guest_demo_usage").document("current")
            transaction = self.db.transaction()

            @firestore_transactional  # type: ignore[untyped-decorator]
            def reserve_all(transaction: Any) -> tuple[bool, int, str | None]:
                snapshot = usage_ref.get(transaction=transaction)
                data = snapshot.to_dict() if snapshot.exists else {}
                if (data or {}).get("day") != day:
                    data = {}

                uid_counts = dict((data or {}).get("uid_counts", {}))
                ip_counts = dict((data or {}).get("ip_counts", {}))
                global_count = int((data or {}).get("global_count", 0) or 0)
                uid_count = int(uid_counts.get(uid, 0) or 0)
                ip_key = self._ip_key(ip_address)
                ip_count = int(ip_counts.get(ip_key, 0) or 0)

                if uid_count >= uid_limit:
                    return False, uid_count, "uid"
                if ip_count >= ip_limit:
                    return False, uid_count, "ip"
                if global_count >= global_limit:
                    return False, uid_count, "global"

                uid_counts[uid] = uid_count + 1
                ip_counts[ip_key] = ip_count + 1
                transaction.set(
                    usage_ref,
                    {
                        "day": day,
                        "uid_counts": uid_counts,
                        "ip_counts": ip_counts,
                        "global_count": global_count + 1,
                        "updated_at": SERVER_TIMESTAMP,
                    },
                )
                return True, uid_count + 1, None

            return cast(tuple[bool, int, str | None], reserve_all(transaction))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error(
                "Guest demo budget reservation failed | Type: {}", type(exc).__name__
            )
            return False, uid_limit, "global"


def get_guest_usage_tracker() -> FirestoreGuestUsageTracker:
    """Return one process-local adapter around the shared Firestore state."""
    if not hasattr(get_guest_usage_tracker, "instance"):
        get_guest_usage_tracker.instance = FirestoreGuestUsageTracker()  # type: ignore[attr-defined]
    return get_guest_usage_tracker.instance  # type: ignore[attr-defined,no-any-return]
