"""
Integration Tests for Auth Endpoints

Tests complete endpoint flows with FastAPI TestClient.
Covers registration, tier limits, and usage tracking.
"""

from unittest.mock import MagicMock, Mock, patch

from fastapi.testclient import TestClient

from app.routers.auth_router import clear_cache
from app.core.config import settings
from main import app

client = TestClient(app)


class TestRegistrationEndpoint:
    """Integration tests for POST /auth/register endpoint"""

    def test_production_allows_new_registration(self) -> None:
        """A verified Firebase user can register."""
        with (
            patch.object(settings, "ENVIRONMENT", "production"),
            patch("app.routers.auth_router.auth") as mock_auth,
            patch("app.routers.auth_router.get_db") as mock_get_db,
            patch("app.routers.auth_router.load_app_config") as mock_config,
        ):
            mock_auth.verify_id_token.return_value = {
                "uid": "new_registration_user",
                "email": "new@example.com",
                "email_verified": True,
            }
            firebase_user = MagicMock()
            firebase_user.custom_claims = {}
            mock_auth.get_user.return_value = firebase_user

            response = client.post("/auth/register", json={"id_token": "valid_token"})

            assert response.status_code == 200
            assert response.json()["tier"] == "FREE"
            mock_auth.set_custom_user_claims.assert_called_once_with(
                "new_registration_user", {"tier": "FREE"}
            )
            mock_get_db.assert_not_called()
            mock_config.assert_called_once()

    def test_signup_verification_then_first_provisioning_requires_no_invitation_code(
        self,
    ) -> None:
        """A verified first-login token receives FREE access with only an ID token."""
        with (
            patch(
                "app.routers.auth_router.load_app_config",
                return_value={"unlimited_emails": []},
            ),
            patch("app.routers.auth_router.auth") as mock_auth,
        ):
            mock_auth.verify_id_token.return_value = {
                "uid": "verified_first_login_user",
                "email": "verified@example.com",
                "email_verified": True,
            }
            firebase_user = MagicMock()
            firebase_user.custom_claims = {}
            mock_auth.get_user.return_value = firebase_user

            response = client.post(
                "/auth/register", json={"id_token": "verified-first-login-token"}
            )

            assert response.status_code == 200
            assert response.json()["tier"] == "FREE"
            mock_auth.set_custom_user_claims.assert_called_once_with(
                "verified_first_login_user", {"tier": "FREE"}
            )

    def test_unverified_email_cannot_complete_first_provisioning(self) -> None:
        """Firebase must reject registration until the email-verification link is used."""
        with patch("app.routers.auth_router.auth") as mock_auth:
            mock_auth.verify_id_token.return_value = {
                "uid": "unverified_first_login_user",
                "email": "unverified@example.com",
                "email_verified": False,
            }

            response = client.post(
                "/auth/register", json={"id_token": "unverified-token"}
            )

            assert response.status_code == 403
            assert (
                response.json()["detail"]
                == "Please verify your email address before registering."
            )
            mock_auth.get_user.assert_not_called()
            mock_auth.set_custom_user_claims.assert_not_called()

    def test_production_preserves_existing_user_tier(self) -> None:
        """Repeat registration does not disrupt an already provisioned account."""
        with (
            patch.object(settings, "ENVIRONMENT", "production"),
            patch("app.routers.auth_router.auth") as mock_auth,
        ):
            mock_auth.verify_id_token.return_value = {
                "uid": "existing_user",
                "email": "existing@example.com",
                "email_verified": True,
            }
            firebase_user = MagicMock()
            firebase_user.custom_claims = {"tier": "FREE"}
            mock_auth.get_user.return_value = firebase_user

            response = client.post(
                "/auth/register",
                json={"id_token": "valid_token"},
            )

            assert response.status_code == 200
            assert response.json()["tier"] == "FREE"
            mock_auth.set_custom_user_claims.assert_not_called()

    def test_new_user_registers_as_free(self) -> None:
        """A verified Firebase user with no claim receives the FREE tier."""
        with (
            patch(
                "app.routers.auth_router.load_app_config",
                return_value={"unlimited_emails": [], "limits": {}},
            ),
            patch("app.routers.auth_router.auth") as mock_auth,
        ):
            mock_auth.verify_id_token.return_value = {
                "uid": "new_public_user",
                "email": "new@example.com",
                "email_verified": True,
            }
            firebase_user = MagicMock()
            firebase_user.custom_claims = {}
            mock_auth.get_user.return_value = firebase_user

            response = client.post(
                "/auth/register",
                json={"id_token": "valid_token"},
            )

            assert response.status_code == 200
            assert response.json()["tier"] == "FREE"
            mock_auth.set_custom_user_claims.assert_called_once_with(
                "new_public_user", {"tier": "FREE"}
            )

    def test_tier_assignment_preserves_existing_admin_claim(self) -> None:
        """A registration tier assignment must never remove administrator access."""
        with (
            patch(
                "app.routers.auth_router.load_app_config",
                return_value={"unlimited_emails": [], "limits": {}},
            ),
            patch("app.routers.auth_router.auth") as mock_auth,
        ):
            mock_auth.verify_id_token.return_value = {
                "uid": "admin_user",
                "email": "admin@example.com",
                "email_verified": True,
            }
            firebase_user = MagicMock()
            firebase_user.custom_claims = {"admin": True}
            mock_auth.get_user.return_value = firebase_user

            response = client.post(
                "/auth/register",
                json={"id_token": "valid_token"},
            )

            assert response.status_code == 200
            mock_auth.set_custom_user_claims.assert_called_once_with(
                "admin_user", {"admin": True, "tier": "FREE"}
            )

    def test_client_cannot_self_assign_elevated_tier(self) -> None:
        """An extra client-supplied tier field cannot bypass server assignment."""
        with (
            patch(
                "app.routers.auth_router.load_app_config",
                return_value={"unlimited_emails": [], "limits": {}},
            ),
            patch("app.routers.auth_router.auth") as mock_auth,
        ):
            mock_auth.verify_id_token.return_value = {
                "uid": "forgery_attempt_user",
                "email": "forgery@example.com",
                "email_verified": True,
            }
            firebase_user = MagicMock()
            firebase_user.custom_claims = {}
            mock_auth.get_user.return_value = firebase_user

            response = client.post(
                "/auth/register",
                json={
                    "id_token": "valid_token",
                    "tier": "UNLIMITED",
                },
            )

            assert response.status_code == 200
            assert response.json()["tier"] == "FREE"
            mock_auth.set_custom_user_claims.assert_called_once_with(
                "forgery_attempt_user", {"tier": "FREE"}
            )

    def test_repeat_registration_preserves_existing_elevated_tier(self) -> None:
        """Calling registration without a code must not downgrade existing users."""
        with (
            patch(
                "app.routers.auth_router.load_app_config",
                return_value={"unlimited_emails": [], "limits": {}},
            ),
            patch("app.routers.auth_router.auth") as mock_auth,
        ):
            mock_auth.verify_id_token.return_value = {
                "uid": "existing_pro_user",
                "email": "pro@example.com",
                "email_verified": True,
            }
            firebase_user = MagicMock()
            firebase_user.custom_claims = {"tier": "PRO"}
            mock_auth.get_user.return_value = firebase_user

            response = client.post(
                "/auth/register",
                json={"id_token": "valid_token"},
            )

            assert response.status_code == 200
            assert response.json()["tier"] == "PRO"
            mock_auth.set_custom_user_claims.assert_not_called()

    def test_repeat_free_registration_preserves_the_existing_free_tier(self) -> None:
        """A retry never creates another Firebase user or rewrites the FREE claim."""
        with (
            patch(
                "app.routers.auth_router.load_app_config",
                return_value={"unlimited_emails": [], "limits": {}},
            ),
            patch("app.routers.auth_router.auth") as mock_auth,
        ):
            mock_auth.verify_id_token.return_value = {
                "uid": "repeat_free_user",
                "email": "repeat@example.com",
                "email_verified": True,
            }
            firebase_user = MagicMock()
            firebase_user.custom_claims = {}
            mock_auth.get_user.return_value = firebase_user

            def record_claims(_user_id: str, claims: dict[str, str]) -> None:
                firebase_user.custom_claims = claims

            mock_auth.set_custom_user_claims.side_effect = record_claims

            first_response = client.post(
                "/auth/register",
                json={"id_token": "valid_token"},
            )
            repeat_response = client.post(
                "/auth/register",
                json={"id_token": "valid_token"},
            )

            assert first_response.status_code == 200
            assert repeat_response.status_code == 200
            assert first_response.json()["tier"] == "FREE"
            assert repeat_response.json()["tier"] == "FREE"
            mock_auth.set_custom_user_claims.assert_called_once_with(
                "repeat_free_user", {"tier": "FREE"}
            )

    def test_register_without_token(self) -> None:
        """Test registration without authorization token"""
        response = client.post(
            "/auth/register",
            json={"email": "test@example.com"},
        )

        assert response.status_code == 422  # FastAPI validation error

    def test_register_with_invalid_token(self) -> None:
        """Test registration with invalid authorization token"""
        with patch("app.routers.auth_router.auth") as mock_auth:
            mock_auth.verify_id_token.side_effect = Exception("Invalid token")

            response = client.post(
                "/auth/register",
                json={"id_token": "invalid_token"},
            )

            assert response.status_code == 401
            assert "Invalid or expired ID token" in response.json()["detail"]


class TestTierLimitsEndpoint:
    """Integration tests for GET /auth/tier-limits endpoint"""

    def test_get_tier_limits_success(self) -> None:
        """Test successful tier limits retrieval"""
        with patch("app.routers.auth_router.get_db") as mock_get_db:
            db_instance = MagicMock()

            # Mock app_config
            config_doc = MagicMock()
            config_doc.exists = True
            config_doc.to_dict.return_value = {
                "unlimited_emails": [],
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
                },
            }
            config_ref = MagicMock()
            config_ref.get.return_value = config_doc

            # Mock collection and document methods
            mock_coll = MagicMock()
            mock_coll.document.return_value = config_ref
            db_instance.collection.return_value = mock_coll
            mock_get_db.return_value = db_instance

            # Clear cache
            clear_cache()

            response = client.get("/auth/tier-limits")

            assert response.status_code == 200
            data = response.json()
            assert "limits" in data
            assert "FREE" in data["limits"]
            assert "PRO" in data["limits"]
            assert "UNLIMITED" in data["limits"]  # Always injected
            assert data["limits"]["FREE"]["max_queries_per_day"] == 20
            assert data["limits"]["UNLIMITED"]["max_queries_per_day"] == 500

    def test_get_tier_limits_with_defaults(self) -> None:
        """Test tier limits retrieval when config doesn't exist"""
        with patch("app.routers.auth_router.get_db") as mock_get_db:
            db_instance = MagicMock()

            # Mock config doesn't exist
            config_doc = MagicMock()
            config_doc.exists = False
            config_ref = MagicMock()
            config_ref.get.return_value = config_doc

            # Mock collection and document methods
            mock_coll = MagicMock()
            mock_coll.document.return_value = config_ref
            db_instance.collection.return_value = mock_coll
            mock_get_db.return_value = db_instance

            # Clear cache
            clear_cache()

            response = client.get("/auth/tier-limits")

            assert response.status_code == 200
            data = response.json()
            assert "limits" in data
            assert "FREE" in data["limits"]
            assert "PRO" in data["limits"]
            assert "UNLIMITED" in data["limits"]
            # Should return defaults
            assert data["limits"]["FREE"]["max_queries_per_day"] == 20
            assert data["limits"]["PRO"]["max_queries_per_day"] == 500


class TestUsageEndpoint:
    """Integration tests for GET /auth/usage endpoint"""

    def test_get_usage_success(self) -> None:
        """Test successful usage retrieval"""
        with (
            patch("app.routers.auth_router.auth") as mock_auth,
            patch("app.routers.auth_router.get_usage_service") as mock_get_service,
        ):
            # Mock Firebase Auth
            mock_auth.verify_id_token.return_value = {"uid": "test_user_123"}

            # Mock auth.get_user() to return user with custom claims
            mock_user = MagicMock()
            mock_user.custom_claims = {"tier": "FREE"}
            mock_auth.get_user.return_value = mock_user

            # Mock usage service
            mock_service = MagicMock()
            mock_service.get_user_queries_today = Mock(return_value=15)
            mock_get_service.return_value = mock_service

            # Mock get_db for app_config
            with patch("app.routers.auth_router.get_db") as mock_get_db:
                db_instance = MagicMock()

                # Mock user document with tier
                user_doc = MagicMock()
                user_doc.exists = True
                user_doc.to_dict.return_value = {"tier": "FREE"}
                user_ref = MagicMock()
                user_ref.get.return_value = user_doc

                # Mock app_config
                config_doc = MagicMock()
                config_doc.exists = True
                config_doc.to_dict.return_value = {
                    "unlimited_emails": [],
                    "limits": {"FREE": {"max_queries_per_day": 20}},
                }
                config_ref = MagicMock()
                config_ref.get.return_value = config_doc

                def mock_document(doc_id: str) -> MagicMock:
                    if doc_id == "test_user_123":
                        return user_ref
                    if doc_id == "settings":
                        return config_ref
                    return MagicMock()

                def mock_collection(
                    _collection_name: str,
                ) -> MagicMock:  # pylint: disable=unused-argument
                    mock_coll = MagicMock()
                    mock_coll.document = mock_document
                    return mock_coll

                db_instance.collection = mock_collection
                mock_get_db.return_value = db_instance

                # Clear cache
                clear_cache()

                response = client.get(
                    "/auth/usage", headers={"Authorization": "Bearer valid_token"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["queries_today"] == 15
            assert data["query_limit"] == 20
            assert data["remaining"] == 5
            assert data["tier"] == "FREE"

    def test_get_usage_without_token(self) -> None:
        """Test usage endpoint without authorization token"""
        response = client.get("/auth/usage")

        assert response.status_code == 401

    def test_get_usage_with_invalid_token(self) -> None:
        """Test usage endpoint with invalid token"""
        with patch(
            "app.core.auth.auth.verify_id_token", side_effect=Exception("Invalid token")
        ):
            response = client.get(
                "/auth/usage", headers={"Authorization": "Bearer invalid_token"}
            )

            assert response.status_code == 401
            assert "Authentication failed" in response.json()["detail"]

    def test_get_usage_unlimited_tier(self) -> None:
        """Test usage for UNLIMITED tier user"""
        with (
            patch("app.routers.auth_router.auth") as mock_auth,
            patch("app.routers.auth_router.get_usage_service") as mock_get_service,
        ):
            mock_auth.verify_id_token.return_value = {"uid": "unlimited_user"}

            # Mock auth.get_user() to return user with UNLIMITED tier
            mock_user = MagicMock()
            mock_user.custom_claims = {"tier": "UNLIMITED"}
            mock_auth.get_user.return_value = mock_user

            mock_service = MagicMock()
            mock_service.get_user_queries_today = Mock(return_value=1000)
            mock_get_service.return_value = mock_service

            with patch("app.routers.auth_router.get_db") as mock_get_db:
                db_instance = MagicMock()

                # Mock user with UNLIMITED tier
                user_doc = MagicMock()
                user_doc.exists = True
                user_doc.to_dict.return_value = {"tier": "UNLIMITED"}
                user_ref = MagicMock()
                user_ref.get.return_value = user_doc

                # Mock app_config
                config_doc = MagicMock()
                config_doc.exists = True
                config_doc.to_dict.return_value = {
                    "unlimited_emails": [],
                    "limits": {
                        "FREE": {"daily_limit": 20, "requests_per_hour": 10},
                        "UNLIMITED": {"daily_limit": 9999, "requests_per_hour": 9999},
                    },
                }
                config_ref = MagicMock()
                config_ref.get.return_value = config_doc

                def mock_document(doc_id: str) -> MagicMock:
                    if doc_id == "unlimited_user":
                        return user_ref
                    if doc_id == "settings":
                        return config_ref
                    return MagicMock()

                def mock_collection(
                    _collection_name: str,
                ) -> MagicMock:  # pylint: disable=unused-argument
                    mock_coll = MagicMock()
                    mock_coll.document = mock_document
                    return mock_coll

                db_instance.collection = mock_collection
                mock_get_db.return_value = db_instance

                # Clear cache
                clear_cache()

                response = client.get(
                    "/auth/usage", headers={"Authorization": "Bearer valid_token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["queries_today"] == 1000
                assert data["query_limit"] == 500
                assert data["remaining"] == 0
                assert data["tier"] == "UNLIMITED"

    def test_get_usage_unlimited_tier_high_usage(self) -> None:
        """Test usage for UNLIMITED tier user with usage exceeding normal limits"""
        with (
            patch("app.routers.auth_router.auth") as mock_auth,
            patch("app.routers.auth_router.get_usage_service") as mock_get_service,
        ):
            mock_auth.verify_id_token.return_value = {"uid": "unlimited_user"}

            # Mock auth.get_user() to return user with UNLIMITED tier
            mock_user = MagicMock()
            mock_user.custom_claims = {"tier": "UNLIMITED"}
            mock_auth.get_user.return_value = mock_user

            mock_service = MagicMock()
            # 5000 queries - exceeds FREE (20) and PRO (200) limits
            mock_service.get_user_queries_today = Mock(return_value=5000)
            mock_get_service.return_value = mock_service

            with patch("app.routers.auth_router.get_db") as mock_get_db:
                db_instance = MagicMock()

                # Mock user with UNLIMITED tier
                user_doc = MagicMock()
                user_doc.exists = True
                user_doc.to_dict.return_value = {"tier": "UNLIMITED"}
                user_ref = MagicMock()
                user_ref.get.return_value = user_doc

                # Mock app_config
                config_doc = MagicMock()
                config_doc.exists = True
                config_doc.to_dict.return_value = {
                    "unlimited_emails": [],
                    "limits": {
                        "FREE": {"daily_limit": 20, "requests_per_hour": 10},
                        "UNLIMITED": {"daily_limit": 9999, "requests_per_hour": 9999},
                    },
                }
                config_ref = MagicMock()
                config_ref.get.return_value = config_doc

                def mock_document(doc_id: str) -> MagicMock:
                    if doc_id == "unlimited_user":
                        return user_ref
                    if doc_id == "settings":
                        return config_ref
                    return MagicMock()

                def mock_collection(
                    _collection_name: str,
                ) -> MagicMock:  # pylint: disable=unused-argument
                    mock_coll = MagicMock()
                    mock_coll.document = mock_document
                    return mock_coll

                db_instance.collection = mock_collection
                mock_get_db.return_value = db_instance

                # Clear cache
                clear_cache()

                response = client.get(
                    "/auth/usage", headers={"Authorization": "Bearer valid_token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["queries_today"] == 5000
                assert data["query_limit"] == 500
                assert data["remaining"] == 0
                assert data["tier"] == "UNLIMITED"
