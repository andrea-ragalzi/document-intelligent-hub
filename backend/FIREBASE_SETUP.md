# Firebase Setup Guide

## Overview

The Document Intelligent Hub uses Firebase Authentication with Custom Claims to implement a tier-based access control system. This guide explains how to set up Firebase credentials for the backend.

## Tier System

- **FREE**: Basic access with rate limits
- **PRO**: Enhanced features and higher limits
- **UNLIMITED**: Full access without restrictions

## Prerequisites

1. **Firebase Project**: You need a Firebase project with:
   - Authentication enabled
   - Firestore database created
   - Service account with admin privileges

2. **Service Account Key**: Download a Firebase Admin SDK service account JSON file

## How to Get Firebase Service Account Credentials

### Step 1: Go to Firebase Console

1. Visit [Firebase Console](https://console.firebase.google.com/)
2. Select your project (or create a new one)

### Step 2: Generate Service Account Key

1. Click the **gear icon** (⚙️) next to "Project Overview"
2. Select **"Project settings"**
3. Go to the **"Service accounts"** tab
4. Click **"Generate new private key"**
5. Click **"Generate key"** in the confirmation dialog
6. A JSON file will be downloaded (e.g., `your-project-firebase-adminsdk-xxxxx.json`)

⚠️ **IMPORTANT**: Keep this file secure! It contains sensitive credentials that give admin access to your Firebase project.

### Step 3: Configure Backend

You have **three options** to provide credentials to the backend:

#### Option 1: Environment Variable (Recommended for Production)

Set the entire JSON content as an environment variable:

```bash
# Export the JSON content (Linux/macOS)
export FIREBASE_CREDENTIALS='{"type": "service_account", "project_id": "your-project", ...}'

# Or add to .env file
echo 'FIREBASE_CREDENTIALS='\''{"type": "service_account", "project_id": "your-project", ...}'\''' >> backend/.env
```

#### Option 2: File Path Environment Variable

Set the path to your service account file:

```bash
# Export file path
export FIREBASE_SERVICE_ACCOUNT_PATH="/path/to/firebase-service-account.json"

# Or add to .env file
echo 'FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/firebase-service-account.json' >> backend/.env
```

#### Option 3: Default File Location

Place the service account JSON file in the backend config directory:

```bash
# Copy to default location
cp ~/Downloads/your-project-firebase-adminsdk-xxxxx.json backend/app/config/firebase-service-account.json
```

⚠️ **Security Note**: If using Option 3, add the file to `.gitignore`:

```bash
echo "backend/app/config/firebase-service-account.json" >> .gitignore
```

## Firestore Database Setup

### Required Collections

#### 1. `invitation_codes` Collection

Stores invitation codes for user registration:

```javascript
// Document ID: the code itself (e.g., "PRO2024")
{
  tier: "FREE" | "PRO" | "UNLIMITED",
  is_used: false,
  expires_at: Timestamp,
  created_at: Timestamp,
  // Fields added after code is used:
  used_by_user_id: "firebase_uid",
  used_at: Timestamp
}
```

#### 2. `app_config/settings` Document

Stores configuration for unlimited tier emails:

```javascript
// Document path: app_config/settings
{
  unlimited_emails: [
    "admin@example.com",
    "vip@example.com"
  ],
  updated_at: Timestamp
}
```

### Create Test Data

Run the provided setup script to create sample invitation codes:

```bash
cd backend
poetry run python examples/test_registration_setup.py
```

This creates:
- `FREE2024`: Free tier code (expires in 30 days)
- `PRO2024`: Pro tier code (expires in 90 days)
- `UNLIMITED2024`: Unlimited tier code (expires in 365 days)
- `EXPIRED2023`: Expired code (for testing error handling)
- `app_config/settings` with sample unlimited emails

## Verification

### 1. Start Backend

```bash
cd backend
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Look for this line in the logs:
```
✅ Firebase Admin SDK initialized - Authentication endpoints available
```

If you see:
```
⚠️ Firebase Admin SDK not initialized - Authentication endpoints disabled
```

Then credentials are not configured correctly.

### 2. Check FastAPI Docs

Visit http://localhost:8000/docs

You should see two new endpoints:
- `POST /auth/register` - Register user with tier assignment
- `POST /auth/refresh-claims` - Get current user tier

### 3. Test Registration

#### Get Firebase ID Token

First, authenticate a user in your frontend and get the ID token:

```typescript
// Frontend code
import { getAuth } from 'firebase/auth';

const auth = getAuth();
const user = auth.currentUser;
const idToken = await user?.getIdToken();
console.log('ID Token:', idToken);
```

#### Test with cURL

```bash
# Register with unlimited email (no code needed)
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "YOUR_FIREBASE_ID_TOKEN",
    "invitation_code": null
  }'

# Register with invitation code
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "YOUR_FIREBASE_ID_TOKEN",
    "invitation_code": "PRO2024"
  }'

# Check current tier
curl -X POST http://localhost:8000/auth/refresh-claims \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "YOUR_FIREBASE_ID_TOKEN"
  }'
```

Expected response (success):
```json
{
  "status": "success",
  "tier": "PRO",
  "message": "Registration successful. Tier assigned: PRO"
}
```

### 4. Verify Custom Claims in Firebase

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Navigate to **Authentication** → **Users**
3. Find the registered user
4. You won't see custom claims in the UI, but you can verify in your app:

```typescript
// Frontend verification
const user = auth.currentUser;
const idTokenResult = await user?.getIdTokenResult();
console.log('Custom Claims:', idTokenResult?.claims);
// Should show: { tier: "PRO", ... }
```

## Troubleshooting

### Error: "Firebase credentials not found"

**Solution**: You haven't configured any of the three credential options. Follow "Step 3: Configure Backend" above.

### Error: "Failed to parse FIREBASE_CREDENTIALS"

**Solution**: The JSON in the environment variable is malformed. Make sure:
1. The entire JSON is on one line
2. All quotes are properly escaped
3. No trailing commas or syntax errors

### Error: "Permission denied" when accessing Firestore

**Solution**: The service account doesn't have the correct permissions. In Firebase Console:
1. Go to **IAM & Admin** → **Service Accounts**
2. Find your service account
3. Ensure it has **Firebase Admin** role

### Warning: "Firebase Admin SDK not initialized"

**Solution**: The backend couldn't find credentials. Check:
1. Environment variables are set correctly
2. Service account file path is correct
3. JSON file is valid and readable

### Error: "Invitation code not found" during registration

**Solution**: You haven't created invitation codes in Firestore. Run:
```bash
poetry run python examples/test_registration_setup.py
```

## Security Best Practices

1. **Never commit service account files** to git
2. **Use environment variables** in production (Option 1)
3. **Rotate credentials** periodically
4. **Limit service account permissions** to only what's needed
5. **Monitor Firebase usage** for suspicious activity
6. **Set expiration dates** on invitation codes
7. **Use unlimited_emails list** only for trusted accounts

## Frontend Integration

Once Firebase is configured in the backend, integrate the registration flow in your frontend:

1. **On First Login**: Call `/auth/register` endpoint
2. **Force Token Refresh**: After registration, call `user.getIdToken(true)` to refresh the token with new custom claims
3. **Store Tier**: Save tier in React state/context for UI decisions
4. **Feature Gating**: Use tier to enable/disable features

See `AUTHENTICATION_API.md` for complete frontend integration examples.

## Production Deployment

### Docker

Add Firebase credentials to your docker-compose.yml:

```yaml
backend:
  environment:
    - FIREBASE_CREDENTIALS=${FIREBASE_CREDENTIALS}
```

Then set the environment variable on your host:

```bash
export FIREBASE_CREDENTIALS='{"type": "service_account", ...}'
docker-compose up -d
```

### Cloud Hosting

Most cloud providers support secret management:

- **AWS**: Use AWS Secrets Manager
- **Google Cloud**: Use Secret Manager
- **Azure**: Use Key Vault
- **Heroku**: Use Config Vars

Store the service account JSON as a secret and inject it as `FIREBASE_CREDENTIALS` environment variable.

## Additional Resources

- [Firebase Admin SDK Documentation](https://firebase.google.com/docs/admin/setup)
- [Custom Claims Documentation](https://firebase.google.com/docs/auth/admin/custom-claims)
- [Firestore Security Rules](https://firebase.google.com/docs/firestore/security/get-started)
- API Reference: See `AUTHENTICATION_API.md`
