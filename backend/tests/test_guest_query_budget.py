"""Cost-boundary tests for anonymous demo queries."""

from unittest.mock import Mock

import pytest

from app.services.guest_query_budget_service import (
    GuestBudgetExceededError,
    GuestQueryBudgetService,
)


def test_guest_budget_reserves_uid_ip_and_global_atomically() -> None:
    tracker = Mock()
    tracker.reserve.return_value = (True, 2, None)
    service = GuestQueryBudgetService(
        tracker=tracker,
        uid_daily_limit=8,
        ip_daily_limit=20,
        global_daily_limit=100,
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


@pytest.mark.parametrize("scope", ["uid", "ip", "global"])
def test_guest_budget_fails_closed_for_every_limit(scope: str) -> None:
    tracker = Mock()
    tracker.reserve.return_value = (False, 8, scope)
    service = GuestQueryBudgetService(tracker, 8, 20, 100)

    with pytest.raises(GuestBudgetExceededError, match=scope):
        service.reserve("guest-a", "203.0.113.8")
