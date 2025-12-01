"""
Firebase Admin SDK Initialization

Initializes Firebase Admin SDK with service account credentials.
Must be called once at application startup.
"""

import os
from pathlib import Path

import firebase_admin
from app.core.logging import logger
from firebase_admin import credentials


def initialize_firebase():
    """
    Initialize Firebase Admin SDK.

    Looks for Firebase credentials in order:
    1. FIREBASE_CREDENTIALS environment variable (JSON string)
    2. FIREBASE_SERVICE_ACCOUNT_PATH environment variable (file path)
    3. Default service account file in config/ directory

    Returns:
        firebase_admin.App: Initialized Firebase app

    Raises:
        ValueError: If no valid credentials found
    """
    # Check if already initialized
    try:
        app = firebase_admin.get_app()
        logger.info("✅ Firebase Admin SDK already initialized")
        return app
    except ValueError:
        # App not initialized yet, continue with initialization
        pass

    logger.info("🔧 Initializing Firebase Admin SDK...")

    # Try environment variable with JSON credentials
    firebase_creds_json = os.getenv("FIREBASE_CREDENTIALS")
    if firebase_creds_json:
        try:
            import json  # pylint: disable=import-outside-toplevel
            cred_dict = json.loads(firebase_creds_json)
            cred = credentials.Certificate(cred_dict)
            app = firebase_admin.initialize_app(cred)
            logger.info("✅ Firebase initialized from FIREBASE_CREDENTIALS env var")
            return app
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"❌ Failed to parse FIREBASE_CREDENTIALS: {e}")

    # Try service account file path from environment
    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    if service_account_path and os.path.exists(service_account_path):
        try:
            cred = credentials.Certificate(service_account_path)
            app = firebase_admin.initialize_app(cred)
            logger.info(f"✅ Firebase initialized from file: {service_account_path}")
            return app
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"❌ Failed to load credentials from {service_account_path}: {e}")

    # Try default service account file location
    default_path = Path(__file__).parent.parent / "config" / "firebase-service-account.json"
    if default_path.exists():
        try:
            cred = credentials.Certificate(str(default_path))
            app = firebase_admin.initialize_app(cred)
            logger.info(f"✅ Firebase initialized from default path: {default_path}")
            return app
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"❌ Failed to load credentials from {default_path}: {e}")

    # No valid credentials found
    error_msg = (
        "Firebase credentials not found. Please set one of:\n"
        "1. FIREBASE_CREDENTIALS environment variable (JSON string)\n"
        "2. FIREBASE_SERVICE_ACCOUNT_PATH environment variable (file path)\n"
        "3. Place firebase-service-account.json in backend/app/config/"
    )
    logger.error(f"❌ {error_msg}")
    raise ValueError(error_msg)


# Initialize on module import (if credentials available)
# This allows optional Firebase features - app will start without it
try:
    initialize_firebase()
except ValueError as e:
    logger.warning(f"⚠️ Firebase not initialized: {e}")
    logger.warning("⚠️ Authentication endpoints will not work without Firebase credentials")
