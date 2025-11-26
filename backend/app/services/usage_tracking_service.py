"""
Usage Tracking Service

Tracks user queries per day in Firestore and enforces tier limits.
"""

from datetime import datetime, timezone

from app.core.logging import logger
from firebase_admin import firestore
from google.cloud.firestore import transactional as firestore_transactional
from google.cloud.firestore_v1 import SERVER_TIMESTAMP


class UsageTrackingService:
    """Service for tracking user query usage and enforcing limits."""
    
    def __init__(self):
        self.db = firestore.client()
    
    def _get_today_key(self) -> str:
        """Get today's date key in YYYY-MM-DD format (UTC)."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    async def get_user_queries_today(self, user_id: str) -> int:
        """
        Get the number of queries the user has made today.
        
        Args:
            user_id: Firebase user ID
            
        Returns:
            Number of queries made today
        """
        try:
            today = self._get_today_key()
            usage_ref = self.db.collection("user_usage").document(user_id)
            usage_doc = usage_ref.get()
            
            if not usage_doc.exists:
                return 0
            
            data = usage_doc.to_dict()
            if not data:
                return 0
            
            # Get today's query count
            queries_today = data.get("queries", {}).get(today, 0)
            return queries_today
            
        except Exception as e:
            logger.error(f"❌ Error getting user queries: {e}")
            return 0
    
    async def increment_user_queries(self, user_id: str) -> int:
        """
        Increment the user's query count for today.
        
        Args:
            user_id: Firebase user ID
            
        Returns:
            New total queries for today
        """
        try:
            today = self._get_today_key()
            usage_ref = self.db.collection("user_usage").document(user_id)
            
            # Use transaction to ensure atomic increment
            transaction = self.db.transaction()
            @firestore_transactional
            def update_in_transaction(transaction, ref):
                snapshot = ref.get(transaction=transaction)
                
                if snapshot.exists:
                    data = snapshot.to_dict() or {}
                    queries = data.get("queries", {})
                    current_count = queries.get(today, 0)
                    new_count = current_count + 1
                    queries[today] = new_count
                    transaction.update(ref, {
                        "queries": queries,
                        "last_query_at": SERVER_TIMESTAMP,
                        "updated_at": SERVER_TIMESTAMP
                    })
                    return new_count
                else:
                    new_data = {
                        "queries": {today: 1},
                        "last_query_at": SERVER_TIMESTAMP,
                        "created_at": SERVER_TIMESTAMP,
                        "updated_at": SERVER_TIMESTAMP
                    }
                    transaction.set(ref, new_data)
                    return 1
            
            new_count = update_in_transaction(transaction, usage_ref)
            logger.info(f"📊 User {user_id} queries today: {new_count}")
            return new_count
            
        except Exception as e:
            logger.error(f"❌ Error incrementing user queries: {e}")
            raise
    
    async def check_query_limit(self, user_id: str, max_queries: int) -> tuple[bool, int]:
        """
        Check if user has exceeded their daily query limit.
        
        Args:
            user_id: Firebase user ID
            max_queries: Maximum queries allowed per day (9999 = unlimited)
            
        Returns:
            Tuple of (can_query: bool, queries_used: int)
        """
        try:
            # Unlimited users (9999) always pass
            if max_queries >= 9999:
                queries_used = await self.get_user_queries_today(user_id)
                return True, queries_used
            
            queries_used = await self.get_user_queries_today(user_id)
            can_query = queries_used < max_queries
            
            if not can_query:
                logger.warning(f"⚠️ User {user_id} has exceeded daily query limit ({queries_used}/{max_queries})")
            
            return can_query, queries_used
            
        except Exception as e:
            logger.error(f"❌ Error checking query limit: {e}")
            # On error, allow the query but log it
            return True, 0
    
    async def cleanup_old_usage(self, days_to_keep: int = 30):
        """
        Clean up old usage data (keep last N days).
        
        This should be run periodically (e.g., daily cron job).
        
        Args:
            days_to_keep: Number of days to keep data for
        """
        try:
            cutoff_date = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            
            # Get all user usage documents
            usage_docs = self.db.collection("user_usage").stream()
            
            for doc in usage_docs:
                data = doc.to_dict()
                if not data:
                    continue
                
                queries = data.get("queries", {})
                if not queries:
                    continue
                
                # Remove old date keys
                updated_queries = {}
                for date_key, count in queries.items():
                    try:
                        date_obj = datetime.strptime(date_key, "%Y-%m-%d")
                        days_old = (cutoff_date - date_obj).days
                        
                        if days_old <= days_to_keep:
                            updated_queries[date_key] = count
                    except Exception:
                        # Invalid date format, skip
                        continue
                
                # Update document if changed
                if len(updated_queries) < len(queries):
                    doc.reference.update({"queries": updated_queries})
                    logger.info(f"🧹 Cleaned up usage for user {doc.id}")
            
            logger.info("✅ Usage cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up usage: {e}")


# Singleton instance
_usage_service = None

def get_usage_service() -> UsageTrackingService:
    """Get or create usage tracking service instance."""
    global _usage_service
    if _usage_service is None:
        _usage_service = UsageTrackingService()
    return _usage_service
