"""Compatibility imports for the Firestore usage adapter."""

from app.infrastructure.firestore_usage_tracker import (
    FirestoreUsageTracker,
    get_usage_service,
)

UsageTrackingService = FirestoreUsageTracker

__all__ = ["UsageTrackingService", "get_usage_service"]
