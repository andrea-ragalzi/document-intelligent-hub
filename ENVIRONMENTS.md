# Environment Separation

Document Intelligent Hub uses two environments only. There is no online staging
environment.

## Local / DEV

```text
Frontend  http://localhost:3000
Backend   http://127.0.0.1:8000
API base  http://127.0.0.1:8000/rag
Firebase  dedicated DEV project
Chroma    backend/chroma_db on the local filesystem
OpenAI    dedicated DEV key/project when available
```

Create ignored local configuration from the tracked templates:

```bash
cp frontend/.env.example frontend/.env.development.local
cp backend/.env.example backend/.env.development.local
```

The Firebase Admin key for local development must be saved as:

```text
backend/app/config/firebase-service-account.dev.json
```

For the optional local Compose path, supply the frontend DEV values explicitly:

```bash
docker compose --env-file frontend/.env.development.local up --build
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

## Firebase DEV setup

1. Create a separate Firebase project and add a Web app.
2. Enable Email/Password authentication. Enable Google as well to reproduce all
   login buttons, and keep `localhost` in Authentication authorized domains.
3. Create the `(default)` Firestore database in Native mode.
4. Deploy the tracked owner-only conversation rules:

   ```bash
   npx firebase-tools deploy --only firestore:rules --project <DEV_PROJECT_ID>
   ```

5. Create `app_config/settings` with `unlimited_emails` as an empty array and a
   `limits` map when explicit configuration is desired. If absent, the backend
   uses its constrained defaults: FREE 20 queries/day, 5 files, 10 MB/file;
   PRO 500 queries/day, 50 files, 50 MB/file; UNLIMITED 9999 values.
6. Do not create `invitation_codes` unless elevated-tier testing is required.
   A code document uses `tier`, `is_used`, and optional `expires_at` fields.
7. Create a DEV service-account key and store it only at the ignored local path
   above. Fill `frontend/.env.development.local` using the DEV Web app config.

`conversations` is created by the browser, while `user_usage` is created by the
backend on the first query. Tier claims are assigned by Firebase Admin during
registration; a registration without an invitation receives FREE.

## Branch and deployment flow

```text
feature/* -> develop -> local testing with DEV -> main -> production
```

`develop` is never an online environment. Vercel and Railway production should
ultimately deploy from `main`; preview/staging infrastructure is outside this
model.
