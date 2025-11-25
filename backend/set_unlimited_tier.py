"""
Simple script to set tier to UNLIMITED for a user.
Usage: poetry run python set_unlimited_tier.py <email>
"""

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.firebase import initialize_firebase
from firebase_admin import auth


def set_unlimited_tier(email: str):
    """Set tier to UNLIMITED for the given email."""
    try:
        # Initialize Firebase
        print("🔧 Initializing Firebase...")
        initialize_firebase()
        print("✅ Firebase initialized\n")
        
        # Get user
        print(f"🔍 Looking for user: {email}")
        user = auth.get_user_by_email(email)
        print(f"✅ Found user: {user.uid}\n")
        
        # Check current tier
        current_claims = user.custom_claims or {}
        current_tier = current_claims.get("tier", "NOT_SET")
        print(f"Current tier: {current_tier}")
        
        if current_tier == "UNLIMITED":
            print("✅ User already has UNLIMITED tier!")
            return
        
        # Set tier to UNLIMITED
        print(f"\n🔧 Setting tier to UNLIMITED for {email}...")
        auth.set_custom_user_claims(user.uid, {"tier": "UNLIMITED"})
        print("✅ Tier set successfully!\n")
        
        # Verify
        user_updated = auth.get_user(user.uid)
        new_tier = user_updated.custom_claims.get("tier")
        print(f"✅ Verified: New tier = {new_tier}\n")
        
        print("=" * 60)
        print("⚠️  IMPORTANT: User must log out and log back in")
        print("   for changes to take effect!")
        print("=" * 60)
        
    except auth.UserNotFoundError:
        print(f"❌ User not found: {email}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: poetry run python set_unlimited_tier.py <email>")
        sys.exit(1)
    
    email = sys.argv[1]
    set_unlimited_tier(email)
