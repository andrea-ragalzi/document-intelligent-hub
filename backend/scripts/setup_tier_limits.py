"""
Setup Tier Limits in Firestore

Creates or updates the app_config/settings document with tier limits
and unlimited emails list.
"""

from app.core.firebase import initialize_firebase
from firebase_admin import firestore
from google.cloud.firestore import SERVER_TIMESTAMP


def setup_tier_limits():
    """Create/update app_config/settings document with tier limits."""

    # Initialize Firebase
    initialize_firebase()

    # Get Firestore client
    db = firestore.client()

    # Define tier limits
    tier_limits = {
        "FREE": {
            "max_queries_per_day": 20,
            "max_files": 5,
            "max_file_size_mb": 10
        },
        "PRO": {
            "max_queries_per_day": 500,
            "max_files": 50,
            "max_file_size_mb": 50
        },
        "UNLIMITED": {
            "max_queries_per_day": 9999,
            "max_files": 9999,
            "max_file_size_mb": 9999
        }
    }

    # Define unlimited emails list
    unlimited_emails = [
        "andrea.ragalzi.social@gmail.com",
        "andrea.ragalzi.code@gmail.com"
    ]

    # Create settings document
    settings_data = {
        "limits": tier_limits,
        "unlimited_emails": unlimited_emails,
        "updated_at": SERVER_TIMESTAMP
    }

    # Update or create the document
    settings_ref = db.collection("app_config").document("settings")
    settings_ref.set(settings_data, merge=True)

    print("✅ Tier limits configured successfully!")
    print("\n📊 Tier Limits:")
    for tier, limits in tier_limits.items():
        print(f"\n  {tier}:")
        for key, value in limits.items():
            print(f"    - {key}: {value}")

    print(f"\n🌟 Unlimited Emails ({len(unlimited_emails)}):")
    for email in unlimited_emails:
        print(f"    - {email}")


if __name__ == "__main__":
    try:
        setup_tier_limits()
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Error setting up tier limits: {e}")
        exit(1)
