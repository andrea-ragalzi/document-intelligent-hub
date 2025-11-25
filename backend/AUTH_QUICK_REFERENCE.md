# Authentication System - Quick Reference

## 🚀 Quick Start

### 1. Install Dependencies (Already Done)

```bash
cd backend
poetry add firebase-admin
```

### 2. Configure Firebase Credentials

**Option A - Environment Variable (Recommended):**
```bash
export FIREBASE_CREDENTIALS='{"type":"service_account","project_id":"...",...}'
```

**Option B - File Path:**
```bash
export FIREBASE_SERVICE_ACCOUNT_PATH="/path/to/firebase-service-account.json"
```

**Option C - Default Location:**
```bash
cp firebase-service-account.json backend/app/config/
```

### 3. Create Test Data

```bash
cd backend
poetry run python examples/test_registration_setup.py
```

### 4. Start Backend

```bash
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Look for: `✅ Firebase Admin SDK initialized`

## 📡 API Endpoints

### Register User

```bash
POST /auth/register
Content-Type: application/json

{
  "id_token": "string",              # Firebase ID token (required)
  "invitation_code": "string | null"  # Code or null for unlimited emails
}
```

**Response (200):**
```json
{
  "status": "success",
  "tier": "PRO",
  "message": "Registration successful. Tier assigned: PRO"
}
```

**Errors:**
- `401`: Invalid Firebase token
- `400`: Invalid/expired/used invitation code
- `400`: No code provided and email not in unlimited list
- `500`: Server error

### Check User Tier

```bash
POST /auth/refresh-claims
Content-Type: application/json

{
  "id_token": "string"  # Firebase ID token
}
```

**Response (200):**
```json
{
  "tier": "PRO",
  "custom_claims": {
    "tier": "PRO"
  }
}
```

## 🎫 Tier Assignment Logic

```
1. Verify Firebase ID token → Extract user_id and email
2. Check unlimited_emails list
   └─ If found → Assign UNLIMITED tier (skip code)
3. If not in unlimited list → Validate invitation_code
   ├─ Check exists
   ├─ Check not used (is_used: false)
   └─ Check not expired (expires_at > now)
4. Extract tier from code
5. Set Firebase Custom Claim: {tier: "PRO"}
6. Mark code as used
7. Return success response
```

## 🔐 Firestore Schema

### Collection: `invitation_codes`

Document ID = code string (e.g., "PRO2024")

```javascript
{
  tier: "FREE" | "PRO" | "UNLIMITED",
  is_used: boolean,
  expires_at: Timestamp,
  created_at: Timestamp,
  // After use:
  used_by_user_id: string,
  used_at: Timestamp
}
```

### Document: `app_config/settings`

```javascript
{
  unlimited_emails: string[],
  updated_at: Timestamp
}
```

## 🧪 Test Codes (After Setup Script)

| Code | Tier | Expiry | Status |
|------|------|--------|--------|
| `FREE2024` | FREE | 30 days | Valid |
| `PRO2024` | PRO | 90 days | Valid |
| `UNLIMITED2024` | UNLIMITED | 365 days | Valid |
| `EXPIRED2023` | PRO | Yesterday | **Expired** |

## 💻 Frontend Integration

### 1. Get Firebase ID Token

```typescript
import { getAuth } from 'firebase/auth';

const auth = getAuth();
const user = auth.currentUser;
const idToken = await user?.getIdToken();
```

### 2. Call Registration Endpoint

```typescript
const response = await fetch('http://localhost:8000/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    id_token: idToken,
    invitation_code: invitationCode || null
  })
});

const data = await response.json();
console.log('Assigned tier:', data.tier);
```

### 3. Force Token Refresh

```typescript
// After successful registration, refresh token to get new custom claims
await user?.getIdToken(true);

// Verify custom claims
const idTokenResult = await user?.getIdTokenResult();
console.log('Custom claims:', idTokenResult?.claims);
// { tier: "PRO", ... }
```

### 4. Use Tier for Feature Gating

```typescript
const tier = idTokenResult?.claims?.tier as 'FREE' | 'PRO' | 'UNLIMITED';

// Example: Limit features based on tier
const canUploadMultiple = tier !== 'FREE';
const maxDocuments = tier === 'FREE' ? 5 : tier === 'PRO' ? 50 : Infinity;
```

## 📝 Testing with cURL

### Register with Unlimited Email

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "YOUR_TOKEN_HERE",
    "invitation_code": null
  }'
```

### Register with Invitation Code

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "YOUR_TOKEN_HERE",
    "invitation_code": "PRO2024"
  }'
```

### Check Current Tier

```bash
curl -X POST http://localhost:8000/auth/refresh-claims \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "YOUR_TOKEN_HERE"
  }'
```

## 🐛 Troubleshooting

### "Firebase credentials not found"

```bash
# Check environment variables
echo $FIREBASE_CREDENTIALS
echo $FIREBASE_SERVICE_ACCOUNT_PATH

# Or place file in default location
cp firebase-service-account.json backend/app/config/
```

### "Invitation code not found"

```bash
# Run test data setup
cd backend
poetry run python examples/test_registration_setup.py
```

### "Permission denied" on Firestore

- Go to Firebase Console → IAM & Admin
- Ensure service account has **Firebase Admin** role

### Backend Logs Show Warning

```
⚠️ Firebase Admin SDK not initialized
```

**Solution:** Configure credentials (see "Configure Firebase Credentials" above)

## 📚 Full Documentation

- **Setup Guide**: `backend/FIREBASE_SETUP.md` (detailed setup instructions)
- **API Reference**: `backend/AUTHENTICATION_API.md` (complete API docs)
- **Test Script**: `backend/examples/test_registration_setup.py` (create test data)

## 🔒 Security Notes

- ✅ Never commit service account JSON to git
- ✅ Use environment variables in production
- ✅ Set expiration dates on invitation codes
- ✅ Monitor Firebase usage for suspicious activity
- ✅ Rotate credentials periodically
