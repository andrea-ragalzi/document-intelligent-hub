"""Cost-boundary tests for anonymous demo queries."""

from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from unittest.mock import Mock

import pytest

from app.services.guest_query_budget_service import (
    GuestBudgetStatus,
    GuestBudgetExceededError,
    GuestQueryBudgetService,
)
from app.infrastructure.firestore_guest_usage import FirestoreGuestUsageTracker
from app.core.config import Settings


class _Snapshot:
    def __init__(self, data: dict[str, object] | None) -> None:
        self._data = data
        self.exists = data is not None

    def to_dict(self) -> dict[str, object] | None:
        return self._data


class _DocumentReference:
    def __init__(self, database: "_AtomicDatabase") -> None:
        self.database = database

    def get(self, transaction: object | None = None) -> _Snapshot:
        del transaction
        data = None if self.database.data is None else dict(self.database.data)
        return _Snapshot(data)


class _Transaction:
    def __init__(self, database: "_AtomicDatabase") -> None:
        self.database = database

    def set(self, reference: _DocumentReference, data: dict[str, object]) -> None:
        del reference
        self.database.data = dict(data)


class _Collection:
    def __init__(self, database: "_AtomicDatabase") -> None:
        self.database = database

    def document(self, name: str) -> _DocumentReference:
        assert name == "current"
        return _DocumentReference(self.database)


class _AtomicDatabase:
    def __init__(self) -> None:
        self.data: dict[str, object] | None = None
        self.lock = Lock()

    def collection(self, name: str) -> _Collection:
        assert name == "guest_demo_usage"
        return _Collection(self)

    def transaction(self) -> _Transaction:
        return _Transaction(self)


def _atomic_transactional(function):  # type: ignore[no-untyped-def]
    def run(transaction, *args, **kwargs):  # type: ignore[no-untyped-def]
        with transaction.database.lock:
            return function(transaction, *args, **kwargs)

    return run


def _firestore_tracker(monkeypatch: pytest.MonkeyPatch) -> FirestoreGuestUsageTracker:
    monkeypatch.setattr(
        "app.infrastructure.firestore_guest_usage.firestore_transactional",
        _atomic_transactional,
    )
    tracker = FirestoreGuestUsageTracker.__new__(FirestoreGuestUsageTracker)
    tracker.db = _AtomicDatabase()
    return tracker


def test_guest_budget_reserves_uid_ip_and_global_atomically() -> None:
    tracker = Mock()
    tracker.reserve.return_value = (True, 2, None)
    service = GuestQueryBudgetService(
        tracker=tracker,
        uid_daily_limit=8,
        ip_daily_limit=20,
        global_daily_limit=100,
        daily_quotas_enabled=True,
    )

    reservation = service.reserve("guest-a", "203.0.113.8")

    assert reservation.tier == "GUEST"
    assert reservation.max_queries == 8
    tracker.reserve.assert_called_once_with(
        uid="guest-a",
        ip_address="203.0.113.8",
        uid_limit=8,
        ip_limit=20,
        global_limit=100,
    )


def test_guest_budget_reports_effective_authoritative_remaining() -> None:
    tracker = Mock()
    tracker.get_usage.return_value = (3, 19, 40)
    service = GuestQueryBudgetService(tracker, 8, 20, 100, daily_quotas_enabled=True)

    status = service.get_status("guest-a", "203.0.113.8")

    assert status == GuestBudgetStatus(
        queries_today=3, query_limit=8, remaining=1, limited=True
    )
    tracker.get_usage.assert_called_once_with(uid="guest-a", ip_address="203.0.113.8")


def test_development_guest_budget_is_unlimited_without_reservations() -> None:
    tracker = Mock()
    service = GuestQueryBudgetService(
        tracker, 1, 1, 1, daily_quotas_enabled=False
    )

    for _ in range(10):
        reservation = service.reserve("guest-a", "203.0.113.8")
        assert reservation.tier == "GUEST"

    assert service.get_status("guest-a", "203.0.113.8") == GuestBudgetStatus(
        queries_today=0, query_limit=None, remaining=None, limited=False
    )
    tracker.reserve.assert_not_called()
    tracker.get_usage.assert_not_called()


@pytest.mark.parametrize(
    ("environment", "configured", "expected"),
    [
        ("development", None, False),
        ("development", True, True),
        ("development", False, False),
        ("production", None, True),
        ("production", False, True),
        ("staging", None, True),
    ],
)
def test_guest_quota_configuration_is_disabled_only_for_explicit_development(
    environment: str, configured: bool | None, expected: bool
) -> None:
    settings = Settings(
        ENVIRONMENT=environment, GUEST_DAILY_QUOTAS_ENABLED=configured
    )

    assert settings.guest_daily_quotas_enabled is expected


@pytest.mark.parametrize("scope", ["uid", "ip", "global"])
def test_guest_budget_fails_closed_for_every_limit(scope: str) -> None:
    tracker = Mock()
    tracker.reserve.return_value = (False, 8, scope)
    service = GuestQueryBudgetService(tracker, 8, 20, 100, daily_quotas_enabled=True)

    with pytest.raises(GuestBudgetExceededError, match=scope):
        service.reserve("guest-a", "203.0.113.8")


def test_atomic_tracker_enforces_uid_ip_and_global_limits_across_identities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tracker = _firestore_tracker(monkeypatch)
    monkeypatch.setattr(tracker, "_today", lambda: "2026-09-22")
    service = GuestQueryBudgetService(tracker, 2, 3, 5, daily_quotas_enabled=True)

    assert service.reserve("guest-a", "198.51.100.1").reserved_count == 1
    assert service.reserve("guest-a", "198.51.100.1").reserved_count == 2
    with pytest.raises(GuestBudgetExceededError, match="uid"):
        service.reserve("guest-a", "198.51.100.1")

    assert service.reserve("guest-b", "198.51.100.1").reserved_count == 1
    with pytest.raises(GuestBudgetExceededError, match="ip"):
        service.reserve("guest-b", "198.51.100.1")

    assert service.reserve("guest-c", "198.51.100.2").reserved_count == 1
    assert service.reserve("guest-d", "198.51.100.3").reserved_count == 1
    with pytest.raises(GuestBudgetExceededError, match="global"):
        service.reserve("guest-e", "198.51.100.4")


def test_atomic_tracker_prevents_concurrent_quota_overrun(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tracker = _firestore_tracker(monkeypatch)
    monkeypatch.setattr(tracker, "_today", lambda: "2026-09-22")

    def reserve_once(index: int) -> bool:
        return tracker.reserve(
            uid=f"guest-{index}",
            ip_address=f"198.51.100.{index}",
            uid_limit=10,
            ip_limit=10,
            global_limit=5,
        )[0]

    with ThreadPoolExecutor(max_workers=12) as executor:
        results = list(executor.map(reserve_once, range(20)))

    assert results.count(True) == 5
    assert results.count(False) == 15


def test_guest_quota_resets_at_utc_day_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tracker = _firestore_tracker(monkeypatch)
    current_day = "2026-09-22"
    monkeypatch.setattr(tracker, "_today", lambda: current_day)

    assert tracker.reserve(
        uid="guest-a",
        ip_address="198.51.100.1",
        uid_limit=1,
        ip_limit=1,
        global_limit=1,
    )[0]
    assert not tracker.reserve(
        uid="guest-a",
        ip_address="198.51.100.1",
        uid_limit=1,
        ip_limit=1,
        global_limit=1,
    )[0]

    current_day = "2026-09-23"

    assert tracker.get_usage(uid="guest-a", ip_address="198.51.100.1") == (0, 0, 0)
    assert tracker.reserve(
        uid="guest-a",
        ip_address="198.51.100.1",
        uid_limit=1,
        ip_limit=1,
        global_limit=1,
    )[0]
