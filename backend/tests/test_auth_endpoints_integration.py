"""
Integration Tests for Auth Endpoints

Tests complete endpoint flows with FastAPI TestClient.
Covers registration, invitation requests, tier limits, and usage tracking.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestRegistrationEndpoint:
    """Integration tests for POST /auth/register endpoint"""

    def test_register_with_valid_free_code_full_flow(self):
        """Test complete registration flow with valid FREE invitation code"""
        with patch("app.routers.auth_router.get_db") as mock_get_db, \
             patch("app.routers.auth_router.auth") as mock_auth:
            
            # Mock Firebase Auth
            mock_auth.verify_id_token.return_value = {"uid": "test_user_123"}
            mock_auth.set_custom_user_claims = MagicMock()
            
            # Mock Firestore
            db_instance = MagicMock()
            
            # Mock invitation code document (valid FREE code)
            code_doc = MagicMock()
            code_doc.exists = True
            code_doc.to_dict.return_value = {
                "tier": "FREE",
                "used": False,
                "expires_at": datetime.now(timezone.utc) + timedelta(days=7)
            }
            code_ref = MagicMock()
            code_ref.get.return_value = code_doc
            
            # Mock app_config document
            config_doc = MagicMock()
            config_doc.exists = True
            config_doc.to_dict.return_value = {
                "unlimited_emails": [],
                "limits": {
                    "FREE": {"max_queries_per_day": 20},
                    "PRO": {"max_queries_per_day": 500}
                }
            }
            config_ref = MagicMock()
            config_ref.get.return_value = config_doc
            
            def mock_document(doc_id):
                if doc_id == "TESTCODE123":
                    return code_ref
                elif doc_id == "settings":
                    return config_ref
                return MagicMock()
            
            def mock_collection(collection_name):
                mock_coll = MagicMock()
                mock_coll.document = mock_document
                return mock_coll
            
            db_instance.collection = mock_collection
            mock_get_db.return_value = db_instance
            
            # Clear cache
            import app.routers.auth_router as auth_router_module
            auth_router_module._unlimited_emails_cache = None
            auth_router_module._tier_limits_cache = None
            
            # Make request
            response = client.post(
                "/auth/register",
                json={
                    "invitation_code": "TESTCODE123",
                    "email": "test@example.com"
                },
                headers={"Authorization": "Bearer valid_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Registration successful"
            assert data["tier"] == "FREE"
            assert data["user_id"] == "test_user_123"
            
            # Verify Firebase set_custom_user_claims was called
            mock_auth.set_custom_user_claims.assert_called_once_with(
                "test_user_123",
                {"tier": "FREE"}
            )
            
            # Verify code was marked as used
            code_ref.update.assert_called_once()

    def test_register_with_invalid_code(self):
        """Test registration with invalid invitation code"""
        with patch("app.routers.auth_router.get_db") as mock_get_db, \
             patch("app.routers.auth_router.auth") as mock_auth:
            
            mock_auth.verify_id_token.return_value = {"uid": "test_user_123"}
            
            db_instance = MagicMock()
            
            # Mock code document doesn't exist
            code_doc = MagicMock()
            code_doc.exists = False
            code_ref = MagicMock()
            code_ref.get.return_value = code_doc
            
            # Mock app_config
            config_doc = MagicMock()
            config_doc.exists = True
            config_doc.to_dict.return_value = {
                "unlimited_emails": [],
                "limits": {}
            }
            config_ref = MagicMock()
            config_ref.get.return_value = config_doc
            
            def mock_document(doc_id):
                if doc_id == "INVALID123":
                    return code_ref
                elif doc_id == "settings":
                    return config_ref
                return MagicMock()
            
            def mock_collection(collection_name):
                mock_coll = MagicMock()
                mock_coll.document = mock_document
                return mock_coll
            
            db_instance.collection = mock_collection
            mock_get_db.return_value = db_instance
            
            # Clear cache
            import app.routers.auth_router as auth_router_module
            auth_router_module._unlimited_emails_cache = None
            auth_router_module._tier_limits_cache = None
            
            response = client.post(
                "/auth/register",
                json={
                    "invitation_code": "INVALID123",
                    "email": "test@example.com"
                },
                headers={"Authorization": "Bearer valid_token"}
            )
            
            assert response.status_code == 400
            assert "Invalid invitation code" in response.json()["detail"]

    def test_register_with_expired_code(self):
        """Test registration with expired invitation code"""
        with patch("app.routers.auth_router.get_db") as mock_get_db, \
             patch("app.routers.auth_router.auth") as mock_auth:
            
            mock_auth.verify_id_token.return_value = {"uid": "test_user_123"}
            
            db_instance = MagicMock()
            
            # Mock expired code
            code_doc = MagicMock()
            code_doc.exists = True
            code_doc.to_dict.return_value = {
                "tier": "FREE",
                "used": False,
                "expires_at": datetime.now(timezone.utc) - timedelta(days=1)  # Expired
            }
            code_ref = MagicMock()
            code_ref.get.return_value = code_doc
            
            # Mock app_config
            config_doc = MagicMock()
            config_doc.exists = True
            config_doc.to_dict.return_value = {
                "unlimited_emails": [],
                "limits": {}
            }
            config_ref = MagicMock()
            config_ref.get.return_value = config_doc
            
            def mock_document(doc_id):
                if doc_id == "EXPIRED123":
                    return code_ref
                elif doc_id == "settings":
                    return config_ref
                return MagicMock()
            
            def mock_collection(collection_name):
                mock_coll = MagicMock()
                mock_coll.document = mock_document
                return mock_coll
            
            db_instance.collection = mock_collection
            mock_get_db.return_value = db_instance
            
            # Clear cache
            import app.routers.auth_router as auth_router_module
            auth_router_module._unlimited_emails_cache = None
            auth_router_module._tier_limits_cache = None
            
            response = client.post(
                "/auth/register",
                json={
                    "invitation_code": "EXPIRED123",
                    "email": "test@example.com"
                },
                headers={"Authorization": "Bearer valid_token"}
            )
            
            assert response.status_code == 400
            assert "expired" in response.json()["detail"].lower()

    def test_register_with_used_code(self):
        """Test registration with already used invitation code"""
        with patch("app.routers.auth_router.get_db") as mock_get_db, \
             patch("app.routers.auth_router.auth") as mock_auth:
            
            mock_auth.verify_id_token.return_value = {"uid": "test_user_123"}
            
            db_instance = MagicMock()
            
            # Mock used code
            code_doc = MagicMock()
            code_doc.exists = True
            code_doc.to_dict.return_value = {
                "tier": "FREE",
                "used": True,  # Already used
                "expires_at": datetime.now(timezone.utc) + timedelta(days=7)
            }
            code_ref = MagicMock()
            code_ref.get.return_value = code_doc
            
            # Mock app_config
            config_doc = MagicMock()
            config_doc.exists = True
            config_doc.to_dict.return_value = {
                "unlimited_emails": [],
                "limits": {}
            }
            config_ref = MagicMock()
            config_ref.get.return_value = config_doc
            
            def mock_document(doc_id):
                if doc_id == "USED123":
                    return code_ref
                elif doc_id == "settings":
                    return config_ref
                return MagicMock()
            
            def mock_collection(collection_name):
                mock_coll = MagicMock()
                mock_coll.document = mock_document
                return mock_coll
            
            db_instance.collection = mock_collection
            mock_get_db.return_value = db_instance
            
            # Clear cache
            import app.routers.auth_router as auth_router_module
            auth_router_module._unlimited_emails_cache = None
            auth_router_module._tier_limits_cache = None
            
            response = client.post(
                "/auth/register",
                json={
                    "invitation_code": "USED123",
                    "email": "test@example.com"
                },
                headers={"Authorization": "Bearer valid_token"}
            )
            
            assert response.status_code == 400
            assert "already been used" in response.json()["detail"]

    def test_register_without_token(self):
        """Test registration without authorization token"""
        response = client.post(
            "/auth/register",
            json={
                "invitation_code": "TESTCODE123",
                "email": "test@example.com"
            }
        )
        
        assert response.status_code == 422  # FastAPI validation error

    def test_register_with_invalid_token(self):
        """Test registration with invalid authorization token"""
        with patch("app.routers.auth_router.auth") as mock_auth:
            mock_auth.verify_id_token.side_effect = Exception("Invalid token")
            
            response = client.post(
                "/auth/register",
                json={
                    "invitation_code": "TESTCODE123",
                    "email": "test@example.com"
                },
                headers={"Authorization": "Bearer invalid_token"}
            )
            
            assert response.status_code == 401
            assert "Invalid or expired token" in response.json()["detail"]


class TestInvitationRequestEndpoint:
    """Integration tests for POST /auth/request-invitation endpoint"""

    @patch("app.routers.auth_router.get_email_service")
    def test_request_invitation_success(self, mock_get_email_service):
        """Test successful invitation code request"""
        # Mock email service
        mock_email_service = MagicMock()
        mock_email_service.send_invitation_request = AsyncMock(return_value=True)
        mock_get_email_service.return_value = mock_email_service
        
        response = client.post(
            "/auth/request-invitation",
            json={"email": "test@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Invitation request submitted successfully"
        assert data["email"] == "test@example.com"

    def test_request_invitation_invalid_email(self):
        """Test invitation request with invalid email format"""
        response = client.post(
            "/auth/request-invitation",
            json={"email": "invalid-email"}
        )
        
        assert response.status_code == 422  # Pydantic validation error

    def test_request_invitation_missing_email(self):
        """Test invitation request without email"""
        response = client.post(
            "/auth/request-invitation",
            json={}
        )
        
        assert response.status_code == 422  # Pydantic validation error

    @patch("app.routers.auth_router.get_email_service")
    def test_request_invitation_email_failure(self, mock_get_email_service):
        """Test invitation request when email service fails"""
        # Mock email service failure
        mock_email_service = MagicMock()
        mock_email_service.send_invitation_request = AsyncMock(
            side_effect=Exception("Email service error")
        )
        mock_get_email_service.return_value = mock_email_service
        
        response = client.post(
            "/auth/request-invitation",
            json={"email": "test@example.com"}
        )
        
        assert response.status_code == 500
        assert "Failed to send invitation request" in response.json()["detail"]


class TestTierLimitsEndpoint:
    """Integration tests for GET /auth/tier-limits endpoint"""

    def test_get_tier_limits_success(self):
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
                        "max_file_size_mb": 10
                    },
                    "PRO": {
                        "max_queries_per_day": 500,
                        "max_files": 50,
                        "max_file_size_mb": 50
                    }
                }
            }
            config_ref = MagicMock()
            config_ref.get.return_value = config_doc
            
            db_instance.collection.return_value.document.return_value = config_ref
            mock_get_db.return_value = db_instance
            
            # Clear cache
            import app.routers.auth_router as auth_router_module
            auth_router_module._unlimited_emails_cache = None
            auth_router_module._tier_limits_cache = None
            
            response = client.get("/auth/tier-limits")
            
            assert response.status_code == 200
            data = response.json()
            assert "FREE" in data
            assert "PRO" in data
            assert "UNLIMITED" in data  # Always injected
            assert data["FREE"]["max_queries_per_day"] == 20
            assert data["UNLIMITED"]["max_queries_per_day"] == 9999

    def test_get_tier_limits_with_defaults(self):
        """Test tier limits retrieval when config doesn't exist"""
        with patch("app.routers.auth_router.get_db") as mock_get_db:
            db_instance = MagicMock()
            
            # Mock config doesn't exist
            config_doc = MagicMock()
            config_doc.exists = False
            config_ref = MagicMock()
            config_ref.get.return_value = config_doc
            
            db_instance.collection.return_value.document.return_value = config_ref
            mock_get_db.return_value = db_instance
            
            # Clear cache
            import app.routers.auth_router as auth_router_module
            auth_router_module._unlimited_emails_cache = None
            auth_router_module._tier_limits_cache = None
            
            response = client.get("/auth/tier-limits")
            
            assert response.status_code == 200
            data = response.json()
            assert "FREE" in data
            assert "PRO" in data
            assert "UNLIMITED" in data
            # Should return defaults
            assert data["FREE"]["max_queries_per_day"] == 20
            assert data["PRO"]["max_queries_per_day"] == 500


class TestUsageEndpoint:
    """Integration tests for GET /auth/usage endpoint"""

    def test_get_usage_success(self):
        """Test successful usage retrieval"""
        with patch("app.routers.auth_router.auth") as mock_auth, \
             patch("app.routers.auth_router.get_usage_service") as mock_get_service:
            
            # Mock Firebase Auth
            mock_auth.verify_id_token.return_value = {"uid": "test_user_123"}
            
            # Mock auth.get_user() to return user with custom claims
            mock_user = MagicMock()
            mock_user.custom_claims = {"tier": "FREE"}
            mock_auth.get_user.return_value = mock_user
            
            # Mock usage service
            mock_service = MagicMock()
            mock_service.get_user_queries_today = AsyncMock(return_value=15)
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
                    "limits": {
                        "FREE": {"max_queries_per_day": 20}
                    }
                }
                config_ref = MagicMock()
                config_ref.get.return_value = config_doc
                
                def mock_document(doc_id):
                    if doc_id == "test_user_123":
                        return user_ref
                    elif doc_id == "settings":
                        return config_ref
                    return MagicMock()
                
                def mock_collection(collection_name):
                    mock_coll = MagicMock()
                    mock_coll.document = mock_document
                    return mock_coll
                
                db_instance.collection = mock_collection
                mock_get_db.return_value = db_instance
                
                # Clear cache
                import app.routers.auth_router as auth_router_module
                auth_router_module._unlimited_emails_cache = None
                auth_router_module._tier_limits_cache = None
                
                response = client.get(
                    "/auth/usage",
                    headers={"Authorization": "Bearer valid_token"}
                )
                
            assert response.status_code == 200
            data = response.json()
            assert data["queries_today"] == 15
            assert data["query_limit"] == 20
            assert data["remaining"] == 5
            assert data["tier"] == "FREE"

    def test_get_usage_without_token(self):
        """Test usage endpoint without authorization token"""
        response = client.get("/auth/usage")
        
        assert response.status_code == 422  # FastAPI validation error

    def test_get_usage_with_invalid_token(self):
        """Test usage endpoint with invalid token"""
        with patch("app.routers.auth_router.auth") as mock_auth:
            mock_auth.verify_id_token.side_effect = Exception("Invalid token")
            
            response = client.get(
                "/auth/usage",
                headers={"Authorization": "Bearer invalid_token"}
            )
            
            assert response.status_code == 401
            assert "Invalid or expired token" in response.json()["detail"]

    def test_get_usage_unlimited_tier(self):
        """Test usage for UNLIMITED tier user"""
        with patch("app.routers.auth_router.auth") as mock_auth, \
             patch("app.routers.auth_router.get_usage_service") as mock_get_service:
            
            mock_auth.verify_id_token.return_value = {"uid": "unlimited_user"}
            
            # Mock auth.get_user() to return user with UNLIMITED tier
            mock_user = MagicMock()
            mock_user.custom_claims = {"tier": "UNLIMITED"}
            mock_auth.get_user.return_value = mock_user
            
            mock_service = MagicMock()
            mock_service.get_user_queries_today = AsyncMock(return_value=1000)
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
                        "UNLIMITED": {"daily_limit": 9999, "requests_per_hour": 9999}
                    }
                }
                config_ref = MagicMock()
                config_ref.get.return_value = config_doc
                
                def mock_document(doc_id):
                    if doc_id == "unlimited_user":
                        return user_ref
                    elif doc_id == "settings":
                        return config_ref
                    return MagicMock()
                
                def mock_collection(collection_name):
                    mock_coll = MagicMock()
                    mock_coll.document = mock_document
                    return mock_coll
                
                db_instance.collection = mock_collection
                mock_get_db.return_value = db_instance
                
                # Clear cache
                import app.routers.auth_router as auth_router_module
                auth_router_module._unlimited_emails_cache = None
                auth_router_module._tier_limits_cache = None
                
                response = client.get(
                    "/auth/usage",
                    headers={"Authorization": "Bearer valid_token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["queries_today"] == 1000
                assert data["query_limit"] == 9999
                assert data["remaining"] == -1  # UNLIMITED tier returns -1 for remaining
                assert data["tier"] == "UNLIMITED"

    def test_get_usage_unlimited_tier_high_usage(self):
        """Test usage for UNLIMITED tier user with usage exceeding normal limits"""
        with patch("app.routers.auth_router.auth") as mock_auth, \
             patch("app.routers.auth_router.get_usage_service") as mock_get_service:
            
            mock_auth.verify_id_token.return_value = {"uid": "unlimited_user"}
            
            # Mock auth.get_user() to return user with UNLIMITED tier
            mock_user = MagicMock()
            mock_user.custom_claims = {"tier": "UNLIMITED"}
            mock_auth.get_user.return_value = mock_user
            
            mock_service = MagicMock()
            # 5000 queries - exceeds FREE (20) and PRO (200) limits
            mock_service.get_user_queries_today = AsyncMock(return_value=5000)
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
                        "UNLIMITED": {"daily_limit": 9999, "requests_per_hour": 9999}
                    }
                }
                config_ref = MagicMock()
                config_ref.get.return_value = config_doc
                
                def mock_document(doc_id):
                    if doc_id == "unlimited_user":
                        return user_ref
                    elif doc_id == "settings":
                        return config_ref
                    return MagicMock()
                
                def mock_collection(collection_name):
                    mock_coll = MagicMock()
                    mock_coll.document = mock_document
                    return mock_coll
                
                db_instance.collection = mock_collection
                mock_get_db.return_value = db_instance
                
                # Clear cache
                import app.routers.auth_router as auth_router_module
                auth_router_module._unlimited_emails_cache = None
                auth_router_module._tier_limits_cache = None
                
                response = client.get(
                    "/auth/usage",
                    headers={"Authorization": "Bearer valid_token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["queries_today"] == 5000
                assert data["query_limit"] == 9999
                assert data["remaining"] == -1  # UNLIMITED always returns -1
                assert data["tier"] == "UNLIMITED"

