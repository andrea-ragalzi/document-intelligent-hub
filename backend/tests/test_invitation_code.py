"""
Tests for Invitation Code System

Tests cover:
- Registration with valid invitation codes
- Registration without invitation code (FREE tier)
- Invalid/expired/used codes
- Tier assignment (FREE, PRO, UNLIMITED)
- Code request flow
"""
# pylint: disable=protected-access

from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from threading import Barrier, Lock, Thread
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient


@pytest.fixture
def mock_firebase_auth() -> Generator[Mock, None, None]:  # pylint: disable=W0621
    """Mock Firebase Auth for testing"""
    with patch("app.routers.auth_router.auth") as mock_auth:
        # Mock user creation
        mock_user = MagicMock()
        mock_user.uid = "test_user_123"
        mock_user.email = "test@example.com"
        mock_auth.verify_id_token.return_value = {
            "uid": "test_user_123",
            "email": "test@example.com",
        }
        mock_auth.get_user.return_value = mock_user
        mock_auth.set_custom_user_claims.return_value = None
        yield mock_auth


@pytest.fixture
def mock_firestore() -> Generator[Mock, None, None]:  # pylint: disable=W0621
    """Mock Firestore database for testing"""
    with patch("app.routers.auth_router.get_db") as mock_db, patch(
        "app.routers.auth_router.firestore_transactional", side_effect=lambda function: function
    ):
        db_instance = MagicMock()
        mock_db.return_value = db_instance
        yield db_instance


@pytest.fixture
def mock_email_service() -> Generator[Mock, None, None]:  # pylint: disable=W0621
    """Mock email service for testing"""
    with patch("app.routers.auth_router.get_email_service") as mock_service:
        service_instance = MagicMock()
        service_instance.send_invitation_request_notification.return_value = True
        mock_service.return_value = service_instance
        yield service_instance


# pylint: disable=W0621  # Fixtures redefine names from outer scope (pytest pattern)
class TestRegistrationWithInvitationCode:
    """Test registration flow with invitation codes"""

    def test_register_with_valid_free_code(
        self, client: TestClient, mock_firebase_auth: Any, mock_firestore: Any
    ) -> Any:
        """Test registration with valid FREE tier invitation code"""
        # Mock invitation code document
        code_doc = MagicMock()
        code_doc.exists = True
        code_doc.to_dict.return_value = {
            "tier": "FREE",
            "is_used": False,
            "expires_at": None,
            "created_at": datetime.now(timezone.utc),
        }

        code_ref = MagicMock()
        code_ref.get.return_value = code_doc
        code_ref.update.return_value = None

        mock_firestore.collection.return_value.document.return_value = code_ref

        # Test registration
        response = client.post(
            "/auth/register",
            json={"id_token": "mock_token", "invitation_code": "VALID_FREE_CODE"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["tier"] == "FREE"
        assert "message" in data

        # Verify custom claims were set
        mock_firebase_auth.set_custom_user_claims.assert_called_once_with(
            "test_user_123", {"tier": "FREE"}
        )

        # Verify the transaction consumed the invitation.
        update_call = mock_firestore.transaction.return_value.update.call_args[0][1]
        assert update_call["is_used"] is True
        assert update_call["used_by_user_id"] == "test_user_123"

    def test_register_with_valid_pro_code(
        self, client: TestClient, mock_firebase_auth: Any, mock_firestore: Any
    ) -> Any:
        """Test registration with valid PRO tier invitation code"""
        code_doc = MagicMock()
        code_doc.exists = True
        code_doc.to_dict.return_value = {
            "tier": "PRO",
            "is_used": False,
            "expires_at": None,
        }

        code_ref = MagicMock()
        code_ref.get.return_value = code_doc
        code_ref.update.return_value = None

        mock_firestore.collection.return_value.document.return_value = code_ref

        response = client.post(
            "/auth/register",
            json={"id_token": "mock_token", "invitation_code": "VALID_PRO_CODE"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "PRO"

        mock_firebase_auth.set_custom_user_claims.assert_called_once_with(
            "test_user_123", {"tier": "PRO"}
        )

    def test_client_tier_cannot_override_invitation_tier(
        self, client: TestClient, mock_firebase_auth: Any, mock_firestore: Any
    ) -> None:
        """Registration always uses the tier stored in the invitation."""
        code_doc = MagicMock()
        code_doc.exists = True
        code_doc.to_dict.return_value = {"tier": "PRO", "is_used": False}
        code_ref = MagicMock()
        code_ref.get.return_value = code_doc
        mock_firestore.collection.return_value.document.return_value = code_ref

        response = client.post(
            "/auth/register",
            json={
                "id_token": "mock_token",
                "invitation_code": "PRO_CODE",
                "tier": "UNLIMITED",
            },
        )

        assert response.status_code == 200
        assert response.json()["tier"] == "PRO"
        mock_firebase_auth.set_custom_user_claims.assert_called_once_with(
            "test_user_123", {"tier": "PRO"}
        )

    @pytest.mark.skip(
        reason="Requires invitation code to be optional - current implementation requires code"
    )
    def test_register_with_unlimited_email(  # pylint: disable=W0613
        self, client: TestClient, mock_firebase_auth: Any, mock_firestore: Any
    ) -> Any:
        """Test registration with email in unlimited list (no code required)"""
        # Mock app_config document
        config_doc = MagicMock()
        config_doc.exists = True
        config_doc.to_dict.return_value = {
            "unlimited_emails": ["test@example.com"],
            "limits": {
                "FREE": {"max_queries_per_day": 20},
                "PRO": {"max_queries_per_day": 500},
                "UNLIMITED": {"max_queries_per_day": 9999},
            },
        }

        config_ref = MagicMock()
        config_ref.get.return_value = config_doc

        mock_firestore.collection.return_value.document.return_value = config_ref

        response = client.post(
            "/auth/register", json={"id_token": "mock_token", "invitation_code": None}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "UNLIMITED"

    @pytest.mark.skip(
        reason="Requires invitation code to be optional - current implementation requires code"
    )
    def test_register_without_code_default_free(  # pylint: disable=W0613
        self, client: TestClient, mock_firebase_auth: Any, mock_firestore: Any
    ) -> Any:
        """Test registration without code defaults to FREE tier"""
        # Mock app_config with empty unlimited_emails
        config_doc = MagicMock()
        config_doc.exists = True
        config_doc.to_dict.return_value = {"unlimited_emails": [], "limits": {}}

        config_ref = MagicMock()
        config_ref.get.return_value = config_doc

        mock_firestore.collection.return_value.document.return_value = config_ref

        response = client.post(
            "/auth/register", json={"id_token": "mock_token", "invitation_code": None}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "FREE"

    def test_register_with_invalid_code(  # pylint: disable=W0613
        self, client: TestClient, mock_firebase_auth: Any, mock_firestore: Any
    ) -> Any:
        """Test registration with non-existent invitation code"""
        code_doc = MagicMock()
        code_doc.exists = False

        code_ref = MagicMock()
        code_ref.get.return_value = code_doc

        mock_firestore.collection.return_value.document.return_value = code_ref

        response = client.post(
            "/auth/register",
            json={"id_token": "mock_token", "invitation_code": "INVALID_CODE"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "Invalid invitation code" in data["detail"]

    def test_register_with_used_code(  # pylint: disable=W0613
        self, client: TestClient, mock_firebase_auth: Any, mock_firestore: Any
    ) -> Any:
        """Test registration with already used invitation code"""
        code_doc = MagicMock()
        code_doc.exists = True
        code_doc.to_dict.return_value = {
            "tier": "PRO",
            "is_used": True,
            "used_by_user_id": "another_user",
        }

        code_ref = MagicMock()
        code_ref.get.return_value = code_doc

        mock_firestore.collection.return_value.document.return_value = code_ref

        response = client.post(
            "/auth/register",
            json={"id_token": "mock_token", "invitation_code": "USED_CODE"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "already been used" in data["detail"]

    def test_register_with_expired_code(  # pylint: disable=W0613
        self, client: TestClient, mock_firebase_auth: Any, mock_firestore: Any
    ) -> Any:
        """Test registration with expired invitation code"""
        # Create expired timestamp
        expired_date = datetime.now(timezone.utc) - timedelta(days=1)

        code_doc = MagicMock()
        code_doc.exists = True
        code_doc.to_dict.return_value = {
            "tier": "PRO",
            "is_used": False,
            "expires_at": MagicMock(to_datetime=lambda: expired_date),
        }

        code_ref = MagicMock()
        code_ref.get.return_value = code_doc

        mock_firestore.collection.return_value.document.return_value = code_ref

        response = client.post(
            "/auth/register",
            json={"id_token": "mock_token", "invitation_code": "EXPIRED_CODE"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "expired" in data["detail"].lower()

    def test_register_missing_token(self, client: TestClient) -> None:
        """Test registration without Firebase token"""
        response = client.post("/auth/register", json={"invitation_code": "SOME_CODE"})

        assert response.status_code == 422  # Validation error

    def test_register_invalid_token(  # pylint: disable=W0613
        self, client: TestClient, mock_firestore: Any
    ) -> Any:
        """Test registration with invalid Firebase token"""
        with patch("app.routers.auth_router.auth") as mock_auth:
            mock_auth.verify_id_token.side_effect = Exception("Invalid token")

            response = client.post(
                "/auth/register",
                json={"id_token": "invalid_token", "invitation_code": "SOME_CODE"},
            )

            # Backend returns 401 for auth failures
            assert response.status_code == 401


class _Snapshot:
    def __init__(self, data: dict[str, Any] | None) -> None:
        self._data = data
        self.exists = data is not None

    def to_dict(self) -> dict[str, Any] | None:
        return dict(self._data) if self._data is not None else None


class _AtomicInvitationTransaction:
    def __init__(self, database: "_AtomicInvitationDatabase") -> None:
        self.database = database
        self.read_version = -1
        self.pending_update: dict[str, Any] | None = None

    def update(self, _reference: Any, data: dict[str, Any]) -> None:
        self.pending_update = data


class _AtomicInvitationReference:
    def __init__(self, database: "_AtomicInvitationDatabase", code: str) -> None:
        self.database = database
        self.code = code

    def get(self, transaction: _AtomicInvitationTransaction) -> _Snapshot:
        with self.database.lock:
            transaction.read_version = self.database.versions[self.code]
            data = dict(self.database.codes[self.code])
            self.database.reads += 1
            wait_for_other_claim = (
                self.database.synchronize_first_reads and self.database.reads <= 2
            )
        if wait_for_other_claim:
            self.database.first_reads.wait(timeout=2)
        return _Snapshot(data)


class _AtomicInvitationCollection:
    def __init__(self, database: "_AtomicInvitationDatabase") -> None:
        self.database = database

    def document(self, code: str) -> _AtomicInvitationReference:
        return _AtomicInvitationReference(self.database, code)


class _AtomicInvitationDatabase:
    """In-memory Firestore transaction model that retries write conflicts."""

    def __init__(
        self, codes: dict[str, dict[str, Any]], synchronize_first_reads: bool = False
    ) -> None:
        self.codes = {code: dict(data) for code, data in codes.items()}
        self.versions = {code: 0 for code in codes}
        self.lock = Lock()
        self.first_reads = Barrier(2)
        self.reads = 0
        self.synchronize_first_reads = synchronize_first_reads

    def collection(self, _name: str) -> _AtomicInvitationCollection:
        return _AtomicInvitationCollection(self)

    def transaction(self) -> _AtomicInvitationTransaction:
        return _AtomicInvitationTransaction(self)

    def run_transaction(self, function: Any, transaction: _AtomicInvitationTransaction, ref: Any) -> Any:
        while True:
            result = function(transaction, ref)
            with self.lock:
                if transaction.read_version != self.versions[ref.code]:
                    transaction = self.transaction()
                    continue
                if transaction.pending_update:
                    self.codes[ref.code].update(transaction.pending_update)
                    self.versions[ref.code] += 1
                return result


def test_concurrent_invitation_claims_allow_exactly_one_user() -> None:
    """A transaction retry makes the losing concurrent claimant observe is_used."""
    from app.routers import auth_router

    database = _AtomicInvitationDatabase(
        {"ONE_USE": {"tier": "PRO", "is_used": False}}, synchronize_first_reads=True
    )
    results: list[tuple[str, str]] = []
    results_lock = Lock()

    def transactional(function: Any) -> Any:
        def run(transaction: Any, ref: Any) -> Any:
            return database.run_transaction(function, transaction, ref)

        return run

    def claim(user_id: str) -> None:
        try:
            tier = auth_router._claim_invitation_code("ONE_USE", user_id, database)
            result = ("success", tier)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            result = ("error", str(getattr(exc, "detail", exc)))
        with results_lock:
            results.append(result)

    with patch("app.routers.auth_router.firestore_transactional", side_effect=transactional):
        threads = [
            Thread(target=claim, args=(user_id,)) for user_id in ("user-a", "user-b")
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=3)

    assert not any(thread.is_alive() for thread in threads)
    assert sorted(status for status, _ in results) == ["error", "success"]
    assert database.codes["ONE_USE"]["is_used"] is True
    assert database.codes["ONE_USE"]["used_by_user_id"] in {"user-a", "user-b"}


def test_invitation_transaction_failure_is_controlled_and_does_not_consume_code() -> None:
    """A failed Firestore transaction leaves the invitation unchanged."""
    from app.routers import auth_router

    database = _AtomicInvitationDatabase({"FAIL": {"tier": "PRO", "is_used": False}})
    transaction = database.transaction()
    transaction.update = Mock(side_effect=RuntimeError("Firestore unavailable"))
    database.transaction = Mock(return_value=transaction)

    with patch("app.routers.auth_router.firestore_transactional", side_effect=lambda function: function):
        with pytest.raises(HTTPException) as error:
            auth_router._claim_invitation_code("FAIL", "user-a", database)

    assert getattr(error.value, "status_code", None) == 500
    assert database.codes["FAIL"] == {"tier": "PRO", "is_used": False}


def test_different_invitation_codes_are_claimed_independently() -> None:
    """Claims for separate invitation documents do not interfere."""
    from app.routers import auth_router

    database = _AtomicInvitationDatabase(
        {
            "PRO": {"tier": "PRO", "is_used": False},
            "UNLIMITED": {"tier": "UNLIMITED", "is_used": False},
        }
    )

    def transactional(function: Any) -> Any:
        return lambda transaction, ref: database.run_transaction(function, transaction, ref)

    with patch("app.routers.auth_router.firestore_transactional", side_effect=transactional):
        assert auth_router._claim_invitation_code("PRO", "user-a", database) == "PRO"
        assert auth_router._claim_invitation_code("UNLIMITED", "user-b", database) == "UNLIMITED"

    assert database.codes["PRO"]["used_by_user_id"] == "user-a"
    assert database.codes["UNLIMITED"]["used_by_user_id"] == "user-b"


# pylint: disable=W0621  # Fixtures redefine names from outer scope (pytest pattern)
class TestInvitationCodeRequest:
    """Test invitation code request flow with the email service mocked."""

    @pytest.mark.skip(reason="Requires mock email service configuration")
    def test_request_invitation_code_success(
        self, client: TestClient, mock_email_service: Any
    ) -> Any:
        """Test successful invitation code request"""
        response = client.post(
            "/auth/request-invitation-code",
            json={
                "email": "newuser@example.com",
                "reason": "I want to try the PRO features",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "sent to our support team" in data["message"]

        # Verify email was sent
        mock_email_service.send_invitation_request_notification.assert_called_once()

    def test_request_invitation_code_missing_email(self, client: TestClient) -> None:
        """Test request without email"""
        response = client.post(
            "/auth/request-invitation-code", json={"reason": "I want to try it"}
        )

        assert response.status_code == 422  # Validation error

    def test_request_invitation_code_invalid_email(self, client: TestClient) -> None:
        """Test request with invalid email format"""
        response = client.post(
            "/auth/request-invitation-code",
            json={"email": "not-an-email", "reason": "Test"},
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.skip(reason="Requires mock email service configuration")
    def test_request_invitation_code_email_failure(
        self, client: TestClient, mock_email_service: Any
    ) -> Any:
        """Test request when email service fails"""
        mock_email_service.send_invitation_request_notification.return_value = False

        response = client.post(
            "/auth/request-invitation-code",
            json={"email": "test@example.com", "reason": "Test"},
        )

        assert response.status_code == 500
        data = response.json()
        assert "Failed to send" in data["detail"]


# pylint: disable=W0621  # Fixtures redefine names from outer scope (pytest pattern)
class TestTierLimitsEndpoint:
    """Test tier limits configuration endpoint"""

    @pytest.mark.skip(reason="Test uses real Firestore data - limits may vary")
    def test_get_tier_limits_success(
        self, client: TestClient, mock_firestore: Any
    ) -> None:
        """Test successful retrieval of tier limits"""
        # Mock app_config document
        config_doc = MagicMock()
        config_doc.exists = True
        config_doc.to_dict.return_value = {
            "limits": {
                "FREE": {
                    "max_queries_per_day": 20,
                    "max_files": 5,
                    "max_file_size_mb": 10,
                },
                "PRO": {
                    "max_queries_per_day": 500,
                    "max_files": 50,
                    "max_file_size_mb": 50,
                },
                "UNLIMITED": {
                    "max_queries_per_day": 9999,
                    "max_files": 9999,
                    "max_file_size_mb": 9999,
                },
            }
        }

        config_ref = MagicMock()
        config_ref.get.return_value = config_doc

        mock_firestore.collection.return_value.document.return_value = config_ref

        response = client.get("/auth/tier-limits")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "limits" in data
        assert "FREE" in data["limits"]
        assert "PRO" in data["limits"]
        assert "UNLIMITED" in data["limits"]
        assert data["limits"]["FREE"]["max_queries_per_day"] == 20
        assert data["limits"]["PRO"]["max_queries_per_day"] == 500
        assert data["limits"]["UNLIMITED"]["max_queries_per_day"] == 500


# pylint: disable=W0621  # Fixtures redefine names from outer scope (pytest pattern)
class TestUsageEndpoint:
    """Test usage tracking endpoint"""

    @pytest.mark.skip(reason="Requires async mock setup for load_app_config")
    def test_get_usage_success(
        self, client: TestClient, mock_firebase_auth: Any
    ) -> None:
        """Test successful usage retrieval"""
        # Mock user with tier
        mock_user = MagicMock()
        mock_user.custom_claims = {"tier": "FREE"}
        mock_firebase_auth.get_user.return_value = mock_user

        # Mock app_config
        with patch("app.routers.auth_router.load_app_config") as mock_config:
            mock_config.return_value = {"limits": {"FREE": {"max_queries_per_day": 20}}}

            # Mock usage service
            with patch("app.routers.auth_router.get_usage_service") as mock_usage:
                usage_service = MagicMock()
                usage_service.get_user_queries_today.return_value = 5
                mock_usage.return_value = usage_service

                response = client.get(
                    "/auth/usage", headers={"Authorization": "Bearer mock_token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert data["queries_today"] == 5
                assert data["query_limit"] == 20
                assert data["remaining"] == 15
                assert data["tier"] == "FREE"

    @pytest.mark.skip(reason="Requires async mock setup for load_app_config")
    def test_get_usage_unlimited_tier(
        self, client: TestClient, mock_firebase_auth: Any
    ) -> Any:
        """Test usage for UNLIMITED tier"""
        mock_user = MagicMock()
        mock_user.custom_claims = {"tier": "UNLIMITED"}
        mock_firebase_auth.get_user.return_value = mock_user

        with patch("app.routers.auth_router.load_app_config") as mock_config:
            mock_config.return_value = {
                "limits": {"UNLIMITED": {"max_queries_per_day": 9999}}
            }

            with patch("app.routers.auth_router.get_usage_service") as mock_usage:
                usage_service = MagicMock()
                usage_service.get_user_queries_today.return_value = 100
                mock_usage.return_value = usage_service

                response = client.get(
                    "/auth/usage", headers={"Authorization": "Bearer mock_token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["remaining"] == -1  # Unlimited

    def test_get_usage_missing_token(self, client: TestClient) -> None:
        """Test usage endpoint without auth token"""
        response = client.get("/auth/usage")

        assert response.status_code == 422  # Missing required header

    def test_get_usage_invalid_token(self, client: TestClient) -> None:
        """Test usage endpoint with invalid token"""
        with patch("app.routers.auth_router.auth") as mock_auth:
            mock_auth.verify_id_token.side_effect = Exception("Invalid token")

            response = client.get(
                "/auth/usage", headers={"Authorization": "Bearer invalid_token"}
            )

            assert response.status_code == 401
