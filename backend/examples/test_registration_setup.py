"""
Test script for authentication and registration endpoints.

This script demonstrates how to:
1. Create invitation codes in Firestore
2. Configure unlimited emails list
3. Test the registration endpoint
"""

from datetime import datetime, timedelta
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore import SERVER_TIMESTAMP

# Initialize Firebase Admin SDK
service_account_path = (
    Path(__file__).parent.parent / "app" / "config" / "firebase-service-account.json"
)

# Check if Firebase is initialized using public API
try:
    firebase_admin.get_app()
    print("✅ Firebase already initialized")
except ValueError:
    cred = credentials.Certificate(str(service_account_path))
    firebase_admin.initialize_app(cred)
    print(f"✅ Firebase initialized with: {service_account_path}")

# Initialize Firestore client
db = firestore.client()


def setup_test_data():
    """
    Create test data in Firestore for registration testing.

    Creates:
    - Sample invitation codes with different tiers
    - Unlimited emails configuration
    """
    print("🔧 Setting up test data...")

    # 1. Create invitation codes
    codes_to_create = [
        {
            "code": "FREE2024",
            "tier": "FREE",
            "is_used": False,
            "expires_at": datetime.now() + timedelta(days=30),
            "created_at": SERVER_TIMESTAMP,
        },
        {
            "code": "PRO2024",
            "tier": "PRO",
            "is_used": False,
            "expires_at": datetime.now() + timedelta(days=90),
            "created_at": SERVER_TIMESTAMP,
        },
        {
            "code": "UNLIMITED2024",
            "tier": "UNLIMITED",
            "is_used": False,
            "expires_at": datetime.now() + timedelta(days=365),
            "created_at": SERVER_TIMESTAMP,
        },
        {
            "code": "EXPIRED2023",
            "tier": "PRO",
            "is_used": False,
            "expires_at": datetime.now() - timedelta(days=1),  # Expired yesterday
            "created_at": SERVER_TIMESTAMP,
        },
    ]

    for code_data in codes_to_create:
        code_ref = db.collection("invitation_codes").document(code_data["code"])
        code_ref.set(code_data)
        print(f"✅ Created invitation code: {code_data['code']} ({code_data['tier']})")

    # 2. Configure unlimited emails list
    unlimited_emails = [
        "andrea.ragalzi.social@gmail.com",  # Social account - unlimited access
        "andrea.ragalzi.code@gmail.com",  # Dev account - unlimited access
    ]

    settings_ref = db.collection("app_config").document("settings")
    settings_ref.set(
        {"unlimited_emails": unlimited_emails, "updated_at": SERVER_TIMESTAMP}
    )
    print(f"✅ Configured {len(unlimited_emails)} unlimited emails")

    print("\n🎉 Test data setup complete!")
    print("\n📋 Test Scenarios:")
    print("1. Register with email in unlimited list -> UNLIMITED tier (no code needed)")
    print("2. Register with FREE2024 code -> FREE tier")
    print("3. Register with PRO2024 code -> PRO tier")
    print("4. Register with UNLIMITED2024 code -> UNLIMITED tier")
    print("5. Register with EXPIRED2023 code -> Should fail (expired)")
    print("6. Register without code and not in unlimited list -> Should fail")


def test_registration_flow():
    """
    Example of how to call the registration endpoint.

    Note: This is a demonstration. In practice, you would:
    1. Get id_token from Firebase Auth on frontend
    2. Send POST request to /auth/register with token and optional code
    """
    print("\n🧪 Example API Usage:")
    print("\n1. For unlimited email users:")
    print(
        """
    POST /auth/register
    {
        "id_token": "<firebase_id_token>",
        "invitation_code": null
    }
    """
    )

    print("\n2. For users with invitation code:")
    print(
        """
    POST /auth/register
    {
        "id_token": "<firebase_id_token>",
        "invitation_code": "PRO2024"
    }
    """
    )

    print("\n3. Check current tier:")
    print(
        """
    POST /auth/refresh-claims
    {
        "id_token": "<firebase_id_token>"
    }
    """
    )


if __name__ == "__main__":
    print("=" * 60)
    print("Authentication & Registration Test Setup")
    print("=" * 60)

    # Run setup
    # asyncio.run(setup_test_data())

    # Show usage examples
    # asyncio.run(test_registration_flow())

    print("\n" + "=" * 60)
    print("✅ Setup complete! You can now test the endpoints.")
    print("=" * 60)
