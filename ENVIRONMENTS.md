# Environment Separation

Document Intelligent Hub uses two environments only. There is no online staging
environment.

## Local / DEV

```text
Frontend  http://localhost:3000
Backend   http://127.0.0.1:8000
API base  http://127.0.0.1:8000/rag
Firebase  dedicated DEV project
Chroma    backend/chroma_db_dev on the local filesystem
OpenAI    dedicated DEV key/project when available
```

Create ignored local configuration from the tracked templates:

```bash
cp frontend/.env.example frontend/.env.local
cp backend/.env.example backend/.env.local
```

The Firebase Admin key for local development must be saved as:

```text
backend/app/config/firebase-service-account.dev.json
```

For the optional local Compose path, supply the frontend DEV values explicitly:

```bash
docker compose --env-file frontend/.env.local up --build
```

The application deliberately does not use the old generic service-account
filename as its local default. If the DEV credential is missing, authenticated
local endpoints remain unavailable instead of silently using PROD.

## Production

```text
Frontend  Vercel production domain
Backend   Railway production service
API base  Railway HTTPS domain with /rag
Firebase  existing PROD project
Chroma    /data/chroma_db on the Railway volume
OpenAI    server-side Railway secret
```

Vercel owns the production `NEXT_PUBLIC_*` values. Railway owns backend secrets,
prompt values, `CHROMA_DB_PATH=/data/chroma_db`, and `HF_HOME=/data/huggingface`.
Production values must not be copied into local environment files or Git.

Google web authentication uses Firebase's popup flow on both desktop and mobile.
This is the supported option for the current Vercel deployment, which does not
serve Firebase redirect helpers from same-origin `/__/auth/*` routes. Keep both
`localhost` in the DEV project's authorized domains and the Vercel application
domain in the PROD project's authorized domains.

## Firebase DEV setup

1. Create a separate Firebase project and add a Web app.
2. Enable Email/Password authentication. Enable Google as well to reproduce all
   login buttons, and keep `localhost` in Authentication authorized domains.
3. Create the `(default)` Firestore database in Native mode.
4. Deploy the tracked owner-only conversation rules:

   ```bash
   npx firebase-tools deploy --only firestore:rules --project <DEV_PROJECT_ID>
   ```

5. Create `app_config/settings` with `unlimited_emails` as an empty array and the
   explicit constrained limits: FREE 20 queries/day, 5 files, 10 MB/file; PRO
   500 queries/day, 50 files, 50 MB/file; UNLIMITED 9999 values.
6. Registration does not depend on an `invitation_codes` collection. Do not create invitation-code documents for ordinary registration testing.
   A code document uses `tier`, `is_used`, and optional `expires_at` fields.
7. Create a DEV service-account key and store it only at the ignored local path
   above. Fill `frontend/.env.local` using the DEV Web app config.

### Firebase-hosted verification email

The client sends Firebase's standard verification email with an action-code URL
back to `/verify-email`. In Firebase Console, repeat these settings for DEV and
PROD: Authentication → Templates → Email address verification, set the sender
display name and template text to `Document Intelligent Hub`, and use a
professional subject such as `Verify your Document Intelligent Hub email`.
Authentication → Settings → Authorized domains must include each deployed app
host (and `localhost` for DEV), or Firebase will reject the continue URL.

Firebase Console owns the sender identity, project branding, subject, body,
reply-to address, and template localization. The repository owns the action-code
return URL and verification lifecycle; it does not add a custom email provider.

`conversations` is created by the browser, while `user_usage` is created by the
backend on the first query. Tier claims are assigned by Firebase Admin during
registration; a new registration receives FREE by default.

## Branch and deployment flow

```text
feature/* -> develop -> local testing with DEV -> main -> production
```

`develop` is never an online environment. Vercel and Railway production should
ultimately deploy from `main`; preview/staging infrastructure is outside this
model.

The older ignored `backend/chroma_db` directory is legacy local data. Preserve
it if it exists, but do not use it for DEV; new local runs use
`backend/chroma_db_dev`.
