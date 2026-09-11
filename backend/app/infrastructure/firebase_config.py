"""Firestore-backed application configuration."""

from collections.abc import Callable
from typing import Any

from app.config.security_constants import UNLIMITED_TIER_MAX_QUERIES
from app.core.logging import logger
from firebase_admin import firestore


def get_db() -> Any:
    """Get or initialize the Firestore client."""
    if not hasattr(get_db, "client"):
        get_db.client = firestore.client()  # type: ignore[attr-defined]
    return get_db.client  # type: ignore[attr-defined]


def clear_cache() -> None:
    """Clear the cached application configuration."""
    for name in ("unlimited_emails_cache", "tier_limits_cache"):
        if hasattr(load_app_config, name):
            delattr(load_app_config, name)


def load_app_config(db_provider: Callable[[], Any] | None = None) -> dict[str, Any]:
    """Load and cache tier configuration from Firestore, with safe defaults."""
    if hasattr(load_app_config, "unlimited_emails_cache") and hasattr(
        load_app_config, "tier_limits_cache"
    ):
        return {
            "unlimited_emails": load_app_config.unlimited_emails_cache,
            "limits": load_app_config.tier_limits_cache,
        }

    try:
        db = (db_provider or get_db)()
        settings_doc = db.collection("app_config").document("settings").get()
        if settings_doc.exists:
            data = settings_doc.to_dict()
            if data:
                unlimited_emails = data.get("unlimited_emails", [])
                tier_limits = data.get("limits", {})
                tier_limits["UNLIMITED"] = {
                    "max_queries_per_day": UNLIMITED_TIER_MAX_QUERIES,
                    "max_files": 9999,
                    "max_file_size_mb": 9999,
                }
                load_app_config.unlimited_emails_cache = unlimited_emails  # type: ignore[attr-defined]
                load_app_config.tier_limits_cache = tier_limits  # type: ignore[attr-defined]
                logger.info(
                    "✅ Loaded app config: %s unlimited emails, %s tier limits",
                    len(unlimited_emails),
                    len(tier_limits),
                )
                return {"unlimited_emails": unlimited_emails, "limits": tier_limits}

        logger.warning("⚠️ app_config/settings not found, using defaults")
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error("❌ Error loading app config: %s", exc)

    return {
        "unlimited_emails": [],
        "limits": {
            "FREE": {"max_queries_per_day": 20, "max_files": 5, "max_file_size_mb": 10},
            "PRO": {"max_queries_per_day": 500, "max_files": 50, "max_file_size_mb": 50},
            "UNLIMITED": {
                "max_queries_per_day": UNLIMITED_TIER_MAX_QUERIES,
                "max_files": 9999,
                "max_file_size_mb": 9999,
            },
        },
    }
