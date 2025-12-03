"""
Comprehensive Tests for Auth Router Helper Functions

Tests cover:
- load_app_config function
- get_current_user_id dependency
- Token validation
- Error handling
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from app.routers.auth_router import (
    clear_cache,
    get_current_user_id,
    load_app_config,
)
from fastapi import HTTPException


class TestLoadAppConfig:
    """Test load_app_config helper function"""

    @pytest.mark.asyncio
    async def test_load_app_config_success(self) -> Any:
        """Test successful loading of app config"""
        # Clear cache before test
        clear_cache()

        with patch("app.routers.auth_router.get_db") as mock_get_db:
            # Mock Firestore
            config_doc = MagicMock()
            config_doc.exists = True
            config_doc.to_dict.return_value = {
                "unlimited_emails": ["admin@example.com"],
                "limits": {
                    "FREE": {"max_queries_per_day": 20},
                    "PRO": {"max_queries_per_day": 500},
                },
            }

            doc_ref = MagicMock()
            doc_ref.get.return_value = config_doc

            db_instance = MagicMock()
            db_instance.collection.return_value.document.return_value = doc_ref
            mock_get_db.return_value = db_instance

            result = load_app_config()

            assert "unlimited_emails" in result
            assert "limits" in result
            assert result["unlimited_emails"] == ["admin@example.com"]
            assert result["limits"]["FREE"]["max_queries_per_day"] == 20
            # UNLIMITED tier is always injected
            assert result["limits"]["UNLIMITED"]["max_queries_per_day"] == 9999

    @pytest.mark.asyncio
    async def test_load_app_config_caching(self) -> Any:
        """Test that app config is cached after first load"""
        # Clear cache
        clear_cache()

        with patch("app.routers.auth_router.get_db") as mock_get_db:
            config_doc = MagicMock()
            config_doc.exists = True
            config_doc.to_dict.return_value = {"unlimited_emails": [], "limits": {}}

            doc_ref = MagicMock()
            doc_ref.get.return_value = config_doc

            db_instance = MagicMock()
            db_instance.collection.return_value.document.return_value = doc_ref
            mock_get_db.return_value = db_instance

            # First call
            result1 = load_app_config()

            # Second call
            result2 = load_app_config()

            # Should be same values (cached)
            assert result1["unlimited_emails"] == result2["unlimited_emails"]

            # Firestore should only be called once
            assert doc_ref.get.call_count == 1

    @pytest.mark.asyncio
    async def test_load_app_config_document_not_exists(self) -> Any:
        """Test when config document doesn't exist"""
        # Clear cache
        clear_cache()

        with patch("app.routers.auth_router.get_db") as mock_get_db:
            config_doc = MagicMock()
            config_doc.exists = False

            doc_ref = MagicMock()
            doc_ref.get.return_value = config_doc

            db_instance = MagicMock()
            db_instance.collection.return_value.document.return_value = doc_ref
            mock_get_db.return_value = db_instance

            result = load_app_config()

            # Should return defaults
            assert result["unlimited_emails"] == []
            assert "FREE" in result["limits"]
            assert result["limits"]["UNLIMITED"]["max_queries_per_day"] == 9999

    @pytest.mark.asyncio
    async def test_load_app_config_firestore_error(self) -> Any:
        """Test error handling when Firestore fails"""
        # Clear cache
        clear_cache()

        with patch("app.routers.auth_router.get_db") as mock_get_db:
            doc_ref = MagicMock()
            doc_ref.get.side_effect = Exception("Firestore error")

            db_instance = MagicMock()
            db_instance.collection.return_value.document.return_value = doc_ref
            mock_get_db.return_value = db_instance

            result = load_app_config()

            # Should return defaults on error
            assert result["unlimited_emails"] == []
            assert "FREE" in result["limits"]
            assert result["limits"]["UNLIMITED"]["max_queries_per_day"] == 9999

    @pytest.mark.asyncio
    async def test_load_app_config_missing_fields(self) -> Any:
        """Test handling when config document has missing fields"""
        # Clear cache
        clear_cache()

        with patch("app.routers.auth_router.get_db") as mock_get_db:
            config_doc = MagicMock()
            config_doc.exists = True
            config_doc.to_dict.return_value = {
                # Missing unlimited_emails and limits
            }

            doc_ref = MagicMock()
            doc_ref.get.return_value = config_doc

            db_instance = MagicMock()
            db_instance.collection.return_value.document.return_value = doc_ref
            mock_get_db.return_value = db_instance

            result = load_app_config()

            # Should have defaults for missing fields
            assert "unlimited_emails" in result
            assert "limits" in result
            assert result["unlimited_emails"] == []
            assert result["limits"]["UNLIMITED"]["max_queries_per_day"] == 9999


class TestGetCurrentUserId:
    """Test get_current_user_id dependency"""

    @pytest.mark.asyncio
    async def test_get_current_user_id_success(self) -> Any:
        """Test successful user ID extraction from valid token"""
        with patch("app.routers.auth_router.auth") as mock_auth:
            mock_auth.verify_id_token.return_value = {
                "uid": "user123",
                "email": "test@example.com",
            }

            user_id = get_current_user_id("Bearer valid_token")

            assert user_id == "user123"
            mock_auth.verify_id_token.assert_called_once_with("valid_token")

    @pytest.mark.asyncio
    async def test_get_current_user_id_missing_header(self) -> Any:
        """Test with missing authorization header"""
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_id("")  # Empty string instead of None

        assert exc_info.value.status_code == 401
        assert "Missing or invalid" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_id_invalid_format(self) -> Any:
        """Test with invalid authorization header format (no Bearer)"""
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_id("InvalidToken")

        assert exc_info.value.status_code == 401
        assert "Missing or invalid" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_id_empty_bearer(self) -> Any:
        """Test with empty Bearer token"""
        with patch("app.routers.auth_router.auth") as mock_auth:
            # Mock the call to verify_id_token to raise an exception for an empty string
            def verify_token_side_effect(t: str) -> dict[str, str]:
                if t:
                    return {"uid": "user123"}
                raise ValueError("Empty token")

            mock_auth.verify_id_token.side_effect = verify_token_side_effect

            with pytest.raises(HTTPException) as exc_info:
                get_current_user_id("Bearer ")

            assert exc_info.value.status_code == 401
            assert "Invalid or expired token" in exc_info.value.detail
            # Ensure it was called with an empty string
            mock_auth.verify_id_token.assert_called_once_with("")

    @pytest.mark.asyncio
    async def test_get_current_user_id_invalid_token(self) -> Any:
        """Test with invalid token that fails verification"""
        with patch("app.routers.auth_router.auth") as mock_auth:
            mock_auth.verify_id_token.side_effect = Exception("Invalid token")

            with pytest.raises(HTTPException) as exc_info:
                get_current_user_id("Bearer invalid_token")

            assert exc_info.value.status_code == 401
            assert "Invalid or expired token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_id_expired_token(self) -> Any:
        """Test with expired token"""
        with patch("app.routers.auth_router.auth") as mock_auth:
            mock_auth.verify_id_token.side_effect = Exception("Token expired")

            with pytest.raises(HTTPException) as exc_info:
                get_current_user_id("Bearer expired_token")

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_id_malformed_token(self) -> Any:
        """Test with malformed token"""
        with patch("app.routers.auth_router.auth") as mock_auth:
            mock_auth.verify_id_token.side_effect = Exception("Malformed token")

            with pytest.raises(HTTPException) as exc_info:
                get_current_user_id("Bearer malformed")

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_id_bearer_case_sensitive(self) -> Any:
        """Test that Bearer prefix is case-sensitive"""
        # Should only accept "Bearer" not "bearer" or "BEARER"
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_id("bearer token")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_id_multiple_spaces(self) -> Any:
        """Test token with multiple spaces after Bearer"""
        with patch("app.routers.auth_router.auth") as mock_auth:
            mock_auth.verify_id_token.return_value = {"uid": "user123"}

            # Should handle multiple spaces
            user_id = get_current_user_id("Bearer  token_with_spaces")

            # Should extract "token_with_spaces" after removing "Bearer "
            assert user_id == "user123"

    @pytest.mark.asyncio
    async def test_get_current_user_id_token_without_uid(self) -> Any:
        """Test valid token but missing uid field"""
        with patch("app.routers.auth_router.auth") as mock_auth:
            mock_auth.verify_id_token.return_value = {
                "email": "test@example.com"
                # Missing uid
            }

            with pytest.raises(HTTPException) as exc_info:
                get_current_user_id("Bearer valid_token")

            # Should catch KeyError and raise HTTPException
            assert exc_info.value.status_code == 401
            assert "Invalid or expired token" in exc_info.value.detail
