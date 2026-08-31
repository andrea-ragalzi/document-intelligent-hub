"""Security coverage for the administrator-only tier assignment endpoint."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def admin_client() -> TestClient:
    """Use the real route dependency so custom-claim authorization is exercised."""
    with TestClient(app) as test_client:
        yield test_client


def _request(
    client: TestClient,
    tier: str,
    token: str = "signed-token",
    email: str = "target@example.com",
):
    return client.post(
        "/auth/admin/set-tier",
        params={"email": email, "tier": tier},
        headers={"Authorization": f"Bearer {token}"},
    )


def test_set_tier_rejects_unauthenticated_requests(admin_client: TestClient) -> None:
    """A missing Firebase bearer token cannot reach the administrator action."""
    response = admin_client.post(
        "/auth/admin/set-tier",
        params={"email": "target@example.com", "tier": "PRO"},
    )

    assert response.status_code == 401


@pytest.mark.parametrize("tier", ["PRO", "UNLIMITED"])
def test_normal_user_cannot_promote_themselves(
    admin_client: TestClient, tier: str
) -> None:
    """A signed but non-admin Firebase token cannot assign elevated tiers."""
    with patch("app.routers.auth_router.auth.verify_id_token") as verify_token, patch(
        "app.routers.auth_router.auth.get_user_by_email"
    ) as get_user_by_email, patch(
        "app.routers.auth_router.auth.set_custom_user_claims"
    ) as set_claims:
        verify_token.return_value = {"uid": "normal-user", "admin": False}

        response = _request(admin_client, tier, email="normal@example.com")

    assert response.status_code == 403
    get_user_by_email.assert_not_called()
    set_claims.assert_not_called()


@pytest.mark.parametrize("tier", ["FREE", "PRO", "UNLIMITED"])
def test_explicitly_trusted_admin_can_assign_supported_tier(
    admin_client: TestClient, tier: str
) -> None:
    """Only Firebase tokens with the signed ``admin: true`` claim may assign tiers."""
    target_user = SimpleNamespace(uid="target-user")
    with patch("app.routers.auth_router.auth.verify_id_token") as verify_token, patch(
        "app.routers.auth_router.auth.get_user_by_email", return_value=target_user
    ) as get_user_by_email, patch(
        "app.routers.auth_router.auth.set_custom_user_claims"
    ) as set_claims:
        verify_token.return_value = {"uid": "trusted-admin", "admin": True}

        response = _request(admin_client, tier)

    assert response.status_code == 200
    get_user_by_email.assert_called_once_with("target@example.com")
    set_claims.assert_called_once_with("target-user", {"tier": tier})
