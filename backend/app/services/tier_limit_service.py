"""
Tier Limit Service - Dynamic Limit Management Based on User Tier

Provides functions to retrieve tier-based limits from Firestore configuration.
Integrates with Firebase Auth custom claims to determine user tier.
"""

from typing import Any, Dict, Tuple

from app.core.logging import logger
from firebase_admin import auth


async def get_user_tier_limits(user_id: str) -> Tuple[str, Dict[str, int]]:
    """
    Get user's tier and associated limits from Firebase config.
    
    Args:
        user_id: Firebase Auth user ID
        
    Returns:
        Tuple of (tier_name, limits_dict)
        
        limits_dict contains:
        - max_queries_per_day: int
        - max_files: int
        - max_file_size_mb: int
        
    Examples:
        >>> tier, limits = await get_user_tier_limits("user123")
        >>> print(f"Tier: {tier}, Max file size: {limits['max_file_size_mb']}MB")
        Tier: PRO, Max file size: 50MB
    """
    try:
        # Get user's custom claims
        user = auth.get_user(user_id)
        custom_claims = user.custom_claims or {}
        tier = custom_claims.get("tier", "FREE")
        
        # Import here to avoid circular dependency
        from app.routers.auth_router import load_app_config
        
        # Load limits from Firestore
        app_config = await load_app_config()
        tier_limits = app_config["limits"]
        
        # Get limits for user's tier (fallback to FREE if tier not found)
        limits = tier_limits.get(tier, tier_limits.get("FREE", {
            "max_queries_per_day": 20,
            "max_files": 5,
            "max_file_size_mb": 10
        }))
        
        logger.debug(f"📊 User {user_id} | Tier: {tier} | Limits: {limits}")
        
        return tier, limits
        
    except Exception as e:
        logger.error(f"❌ Error getting tier limits for user {user_id}: {e}")
        # Return FREE tier defaults on error
        return "FREE", {
            "max_queries_per_day": 20,
            "max_files": 5,
            "max_file_size_mb": 10
        }


async def get_max_upload_size_bytes(user_id: str) -> int:
    """
    Get maximum upload size in bytes for user based on their tier.
    
    Args:
        user_id: Firebase Auth user ID
        
    Returns:
        int: Maximum file size in bytes
        
    Examples:
        >>> max_size = await get_max_upload_size_bytes("user123")
        >>> print(f"Max upload: {max_size / 1024 / 1024}MB")
        Max upload: 50.0MB
    """
    _, limits = await get_user_tier_limits(user_id)
    max_mb = limits.get("max_file_size_mb", 10)
    return max_mb * 1024 * 1024  # Convert MB to bytes


async def check_file_count_limit(user_id: str, current_count: int) -> Tuple[bool, int]:
    """
    Check if user has reached their maximum file upload limit.
    
    Args:
        user_id: Firebase Auth user ID
        current_count: Current number of uploaded files
        
    Returns:
        Tuple of (can_upload, max_files)
        
    Examples:
        >>> can_upload, max_files = await check_file_count_limit("user123", 4)
        >>> if not can_upload:
        >>>     print(f"Limit reached! Max: {max_files}")
    """
    _, limits = await get_user_tier_limits(user_id)
    max_files = limits.get("max_files", 5)
    
    can_upload = current_count < max_files
    
    return can_upload, max_files


async def get_tier_info_for_display(user_id: str) -> Dict[str, Any]:
    """
    Get formatted tier information for display in UI.
    
    Args:
        user_id: Firebase Auth user ID
        
    Returns:
        Dictionary with tier name and all limits
        
    Example:
        >>> info = await get_tier_info_for_display("user123")
        >>> print(info)
        {
            "tier": "PRO",
            "max_queries_per_day": 500,
            "max_files": 50,
            "max_file_size_mb": 50
        }
    """
    tier, limits = await get_user_tier_limits(user_id)
    
    return {
        "tier": tier,
        **limits
    }
