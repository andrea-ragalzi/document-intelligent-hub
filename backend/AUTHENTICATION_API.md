# Authentication & Registration API

## Overview

The authentication system handles user registration and tier assignment using Firebase Custom Claims. Users are assigned one of three tiers: **FREE**, **PRO**, or **UNLIMITED**.

## Tier Assignment Logic

### Priority Order

1. **Unlimited Email List** (Highest Priority)
   - If user's email is in the `app_config/settings.unlimited_emails` array
   - Automatically assigned **UNLIMITED** tier
   - No invitation code required

2. **Invitation Code**
   - If user is NOT in unlimited list, invitation code is **required**
   - Code determines tier (FREE, PRO, or UNLIMITED)
   - Code must be valid, unused, and not expired

## Firestore Schema

### Collection: `invitation_codes`

```typescript
{
  // Document ID is the invitation code itself (e.g., "PRO2024")
  tier: "FREE" | "PRO" | "UNLIMITED",
  is_used: boolean,
  expires_at: Timestamp,
  created_at: Timestamp,
  used_by_user_id?: string,  // Set when code is used
  used_at?: Timestamp         // Set when code is used
}
```

### Collection: `app_config` → Document: `settings`

```typescript
{
  unlimited_emails: string[],  // Array of email addresses
  updated_at: Timestamp
}
```

## API Endpoints

### POST `/auth/register`

Register a user and assign tier based on email or invitation code.

**Request Body:**
```json
{
  "id_token": "firebase_id_token_string",
  "invitation_code": "PRO2024"  // Optional - required if not in unlimited list
}
```

**Response (Success):**
```json
{
  "status": "success",
  "tier": "PRO",
  "message": "Access to plan assigned successfully. You may need to refresh your token."
}
```

**Response (Error - 400):**
```json
{
  "detail": "Invitation code is required for registration"
}
```

**Response (Error - 401):**
```json
{
  "detail": "Invalid or expired ID token"
}
```

### POST `/auth/refresh-claims`

Retrieve current user tier from Firebase Custom Claims.

**Request Body:**
```json
{
  "id_token": "firebase_id_token_string"
}
```

**Response:**
```json
{
  "status": "success",
  "tier": "PRO",
  "claims": {
    "tier": "PRO"
  }
}
```

## Usage Flow

### Frontend Integration

```typescript
// 1. User signs in with Firebase
const userCredential = await signInWithEmailAndPassword(auth, email, password);
const idToken = await userCredential.user.getIdToken();

// 2. Register user with backend
const response = await fetch('/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    id_token: idToken,
    invitation_code: userEnteredCode || null
  })
});

const result = await response.json();
console.log('Assigned tier:', result.tier);

// 3. Force token refresh to get new claims
await userCredential.user.getIdToken(true);

// 4. Verify new claims
const newToken = await userCredential.user.getIdToken();
const claimsResponse = await fetch('/auth/refresh-claims', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ id_token: newToken })
});

const claims = await claimsResponse.json();
console.log('Current tier:', claims.tier);
```

## Test Scenarios

### 1. Unlimited Email User (No Code Needed)
```bash
POST /auth/register
{
  "id_token": "<token_for_admin@example.com>",
  "invitation_code": null
}

Expected: tier = "UNLIMITED"
```

### 2. User with FREE Code
```bash
POST /auth/register
{
  "id_token": "<token>",
  "invitation_code": "FREE2024"
}

Expected: tier = "FREE", code marked as used
```

### 3. User with PRO Code
```bash
POST /auth/register
{
  "id_token": "<token>",
  "invitation_code": "PRO2024"
}

Expected: tier = "PRO", code marked as used
```

### 4. User with Expired Code
```bash
POST /auth/register
{
  "id_token": "<token>",
  "invitation_code": "EXPIRED2023"
}

Expected: 400 error - "Invitation code has expired"
```

### 5. User without Code (Not in Unlimited List)
```bash
POST /auth/register
{
  "id_token": "<token>",
  "invitation_code": null
}

Expected: 400 error - "Invitation code is required for registration"
```

### 6. Already Used Code
```bash
# First use - succeeds
POST /auth/register
{
  "id_token": "<token1>",
  "invitation_code": "PRO2024"
}

# Second use - fails
POST /auth/register
{
  "id_token": "<token2>",
  "invitation_code": "PRO2024"
}

Expected: 400 error - "Invitation code has already been used"
```

## Setup Instructions

### 1. Create Test Data
```bash
cd backend
poetry run python examples/test_registration_setup.py
```

This creates:
- Sample invitation codes (FREE2024, PRO2024, UNLIMITED2024, EXPIRED2023)
- Unlimited emails configuration

### 2. Test with cURL
```bash
# Get Firebase ID token first (via Firebase Auth)
ID_TOKEN="<your_firebase_id_token>"

# Register with invitation code
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"id_token\": \"$ID_TOKEN\", \"invitation_code\": \"PRO2024\"}"

# Check current claims
curl -X POST http://localhost:8000/auth/refresh-claims \
  -H "Content-Type: application/json" \
  -d "{\"id_token\": \"$ID_TOKEN\"}"
```

## Security Considerations

1. **Firebase Token Verification**: All requests verify Firebase ID tokens server-side
2. **One-Time Use Codes**: Invitation codes can only be used once
3. **Expiration Dates**: Codes have expiration dates to limit validity
4. **Custom Claims**: Tier stored in Firebase Custom Claims (verified by Firebase)
5. **Cache Strategy**: Unlimited emails list is cached in memory to reduce Firestore reads

## Error Handling

All errors return proper HTTP status codes:
- `400`: Invalid/expired/used invitation code, missing required code
- `401`: Invalid or expired Firebase ID token
- `500`: Server error (Firestore failure, claims assignment failure)

## Notes

- After registration, users should refresh their Firebase ID token to get new custom claims
- The frontend can check `user.getIdTokenResult().claims.tier` to access the tier
- Unlimited emails are cached in memory - restart backend to clear cache if list changes
