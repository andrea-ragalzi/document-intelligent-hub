"""
Debug script to check and fix user tier.

Usage:
    poetry run python debug_user_tier.py <user_email>
"""

import os
import sys
from pathlib import Path

# Add app directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.core.firebase import initialize_firebase
from firebase_admin import auth

# Initialize Firebase Admin using app's initialization logic
initialize_firebase()

def check_and_fix_user_tier(email: str):
    """Check user's tier and fix if needed."""
    try:
        # Get user by email
        user = auth.get_user_by_email(email)
        
        print(f"\n{'='*60}")
        print(f"User: {user.email}")
        print(f"UID: {user.uid}")
        print(f"{'='*60}\n")
        
        # Check custom claims
        custom_claims = user.custom_claims or {}
        current_tier = custom_claims.get("tier", "NOT_SET")
        
        print(f"Current tier: {current_tier}")
        print(f"All custom claims: {custom_claims}")
        
        if current_tier != "UNLIMITED":
            print(f"\n⚠️  Tier is not UNLIMITED!")
            response = input(f"Set tier to UNLIMITED for {email}? (y/n): ")
            
            if response.lower() == 'y':
                # Set tier to UNLIMITED
                auth.set_custom_user_claims(user.uid, {"tier": "UNLIMITED"})
                print(f"✅ Tier set to UNLIMITED for {email}")
                print(f"User must log out and log back in for changes to take effect!")
                
                # Verify
                user = auth.get_user(user.uid)
                new_tier = user.custom_claims.get("tier")
                print(f"✅ Verified: New tier = {new_tier}")
            else:
                print("❌ Cancelled")
        else:
            print(f"✅ Tier is already UNLIMITED")
            
    except auth.UserNotFoundError:
        print(f"❌ User not found: {email}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: poetry run python debug_user_tier.py <user_email>")
        sys.exit(1)
    
    email = sys.argv[1]
    check_and_fix_user_tier(email)
