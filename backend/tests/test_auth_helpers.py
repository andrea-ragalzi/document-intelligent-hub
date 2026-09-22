"""
Comprehensive Tests for Auth Router Helper Functions

Tests cover:
- load_app_config function
- Error handling
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from app.routers.auth_router import (
    clear_cache,
    load_app_config,
)


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
            assert result["limits"]["UNLIMITED"]["max_queries_per_day"] == 500

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
            assert result["limits"]["UNLIMITED"]["max_queries_per_day"] == 500

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
            assert result["limits"]["UNLIMITED"]["max_queries_per_day"] == 500

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
            assert result["limits"]["UNLIMITED"]["max_queries_per_day"] == 500
