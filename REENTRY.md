# REENTRY.md — Document Intelligent Hub

Recovery and re-entry runbook. Written after the April 2026 recovery from a 5-month pause + machine migration (Pop!_OS 22 → 24).

---

## Stack at a glance

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, TypeScript, Tailwind CSS, Firebase Auth |
| Backend | Python 3.12, FastAPI, Poetry |
| Vector store | ChromaDB (persistent Docker volume) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local, CPU) |
| LLM | OpenAI `gpt-3.5-turbo` via LangChain 1.x |
| Reranking | Local keyword scorer (no external API needed) |
| Auth | Firebase Admin SDK (backend) + Firebase JS SDK (frontend) |
| Conversations | Firestore |
| Email | SendGrid |
| Orchestration | Docker Compose + Makefile |
| Package managers | Poetry (backend), npm (frontend) |

---

## Repository layout

```
document-intelligent-hub/
├── docker-compose.yml          ← orchestration entrypoint
├── Makefile                    ← task runner (use this, not docker compose directly)
├── backend/
│   ├── main.py                 ← FastAPI entrypoint (uvicorn)
│   ├── pyproject.toml          ← Poetry deps
│   ├── .env                    ← secrets (gitignored) — must exist
│   ├── app/
│   │   ├── core/               ← config, logging, auth, firebase, security
│   │   ├── db/                 ← ChromaDB client + HuggingFace embeddings
│   │   ├── repositories/       ← vector store repository + DI
│   │   ├── routers/            ← documents, query, auth, support
│   │   ├── schemas/            ← Pydantic models
│   │   └── services/           ← 15 services forming the RAG pipeline
│   ├── config/
│   │   ├── rag_system_prompt.txt          ← gitignored, must exist
│   │   ├── classification_prompt.txt      ← gitignored, must exist
│   │   └── query_reformulation_prompt.txt ← gitignored, must exist
│   └── app/config/
│       └── firebase-service-account.json  ← gitignored, must exist
└── frontend/
    ├── .env.local              ← secrets (gitignored) — must exist
    ├── app/                    ← Next.js App Router
    ├── contexts/AuthContext.tsx
    └── lib/firebase.ts         ← lazy Firebase init (never throws at build time)
```

---

## Critical local files (gitignored — must be present before building)

| File | Purpose | Where to get it |
|---|---|---|
| `backend/.env` | OpenAI key, SendGrid, app config | Backup or recreate from `backend/.env.example` |
| `frontend/.env.local` | Firebase public config, API URL | Backup or Firebase Console → Project Settings → Your apps |
| `backend/app/config/firebase-service-account.json` | Firebase Admin auth | Firebase Console → Project Settings → Service Accounts → Generate key |
| `backend/config/rag_system_prompt.txt` | RAG behavior prompt | Backup or recreate from `backend/config/rag_system_prompt.txt.example` |
| `backend/config/classification_prompt.txt` | Query classification prompt | Backup or `.example` |
| `backend/config/query_reformulation_prompt.txt` | Query expansion prompt | Backup or `.example` |

---

## Environment variable map

### `backend/.env`

```
OPENAI_API_KEY=sk-...
APP_NAME=Document Intelligent Hub
LLM_MODEL=gpt-3.5-turbo
SENDGRID_API_KEY=SG....
SENDGRID_FROM_EMAIL=you@domain.com
SUPPORT_EMAIL=support@domain.com
```

### `frontend/.env.local`

```
NEXT_PUBLIC_FIREBASE_API_KEY=...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=...
NEXT_PUBLIC_FIREBASE_APP_ID=...
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/rag
```

---

## How env vars reach the containers

| Var | How it gets in |
|---|---|
| `OPENAI_API_KEY` and other backend secrets | `env_file: ./backend/.env` in docker-compose — loaded at runtime |
| `FIREBASE_SERVICE_ACCOUNT_PATH` | Set in docker-compose `environment:`, file mounted as read-only volume |
| `NEXT_PUBLIC_FIREBASE_*` | Passed as Docker build args via `docker compose --env-file frontend/.env.local build` — **baked into the JS bundle at build time** |
| `NEXT_PUBLIC_API_BASE_URL` | Value from `frontend/.env.local` at build time — runtime override in compose has no effect |

> ⚠️ `NEXT_PUBLIC_*` vars are compiled into the JS bundle. Changing them requires a frontend rebuild, not just a container restart.

---

## Standard commands

Always use `make`, not bare `docker compose`, for builds — the Makefile handles the Firebase build args.

```bash
# First-time or full rebuild
make build        # builds backend then frontend (sources frontend/.env.local for Firebase args)
make up           # starts all containers

# Day-to-day
make up           # start
make down         # stop
make restart      # restart without rebuilding
make logs         # follow all logs
make logs-backend
make logs-frontend

# Targeted rebuilds
make build-backend    # rebuild backend only
make build-frontend   # rebuild frontend only (re-bakes Firebase config)

# Dev mode (hot reload, no Docker)
make dev-backend      # uvicorn with --reload
make dev-frontend     # next dev

# Tests
make test-backend
make test-coverage

# Maintenance
make clean        # remove containers, keep volumes (ChromaDB data preserved)
make prune        # ⚠️ removes containers AND volumes (deletes ChromaDB index)
```

---

## Service URLs

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |

---

## ChromaDB / Vector index

- Stored in a named Docker volume: `document-intelligent-hub_chroma_data`
- Mounted at `/app/chroma_db` inside the backend container
- **Not backed up in git or backup archives** — must be regenerated by re-ingesting documents
- `make clean` preserves it. `make prune` deletes it permanently.
- If lost: upload documents via the dashboard and re-ingest — the pipeline recreates the index automatically

---

## Embedding model

- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Downloaded from HuggingFace on first backend startup
- Cached inside the Docker image layer after first build
- No API key required — runs on CPU locally
- First startup after a clean build takes ~30s while the model loads

---

## Recovery checklist (for next reentry)

Run through this in order. Do not skip to builds.

- [ ] Clone repo (treat as source of truth)
- [ ] Verify `backend/.env` exists and has all required keys
- [ ] Verify `frontend/.env.local` exists and has all `NEXT_PUBLIC_FIREBASE_*` keys
- [ ] Verify `backend/app/config/firebase-service-account.json` exists
- [ ] Verify `backend/config/*.txt` prompt files exist (not just `.example` files)
- [ ] Decide on ChromaDB: restore from backup or plan re-ingest
- [ ] Run `make build` (not `docker compose build` directly)
- [ ] Run `make up`
- [ ] Run `docker compose logs backend --tail 40` — check for startup errors
- [ ] Open http://localhost:3000 — check browser console for Firebase errors
- [ ] Upload a test document and run a query to verify RAG pipeline

---

## Known issues resolved during April 2026 recovery

| Issue | Fix |
|---|---|
| `README.md` missing in `backend/` — Docker build failed | Created `backend/README.md` (required by `pyproject.toml` `readme` field) |
| Firebase threw at Next.js build time (static pre-rendering crash) | Refactored `firebase.ts` to lazy initialization — `getFirebaseAuth()` / `getFirebaseDb()` getters |
| `loguru` missing from `pyproject.toml` | Added `loguru = "^0.7.0"` |
| `langchain-huggingface` incompatible with LangChain 1.x | Removed it; import `HuggingFaceEmbeddings` from `langchain_community.embeddings` instead; added `sentence-transformers = "^3.0.0"` |
| `OPENAI_API_KEY` silently blank in container | Added `env_file: ./backend/.env` to backend service in docker-compose; removed `${OPENAI_API_KEY}` override that was winning with a blank value |
| `NEXT_PUBLIC_FIREBASE_*` not baked into frontend bundle | Use `docker compose --env-file frontend/.env.local build frontend`; Makefile `build` and `build-frontend` targets handle this automatically |
| Firebase service account not found in container | Mounted via volume: `./backend/app/config/firebase-service-account.json:/run/secrets/firebase-service-account.json:ro` |
| Makefile `$(shell)` trick for env sourcing didn't propagate to Docker | Replaced with `docker compose --env-file frontend/.env.local build` |

---

## Architecture note: RAG pipeline

```
Upload PDF
    └─→ DocumentIndexingService
            └─→ UnstructuredPDFLoader (langchain_community)
            └─→ RecursiveCharacterTextSplitter
            └─→ HuggingFaceEmbeddings (all-MiniLM-L6-v2)
            └─→ ChromaDB (persistent volume)

Query
    └─→ QueryParserService       (file filtering)
    └─→ QueryProcessingService   (classification)
    └─→ QueryExpansionService    (multi-query generation via OpenAI)
    └─→ VectorStoreRepository    (ChromaDB retrieval)
    └─→ RerankingService         (local keyword scorer)
    └─→ AnswerGenerationService  (OpenAI gpt-3.5-turbo)
    └─→ TranslationService       (if language mismatch detected)
```

---

---

## First login after recovery

The app uses Firebase Auth + a tier system. There is no default admin user — users live in Firebase Auth and are assigned tiers via Firestore.

### To get in after a fresh recovery

**Option A — Unlimited email list (recommended for owner)**

1. Go to [console.firebase.google.com](https://console.firebase.google.com)
2. Make sure you are logged in with the **correct Google account** (the one that created the project — `intelligent-document-hub-a16c1`). If you see "This project does not exist", switch accounts.
3. Navigate to **Firestore Database** → collection `app_config` → document `settings`
4. Add your email to the `unlimited_emails` array field
5. Sign in via Google (or email) on the frontend — tier `UNLIMITED` is assigned automatically, no invitation code needed

**Option B — Invitation code**

Create a document in Firestore collection `invitation_codes`:
```
Document ID: your-chosen-code
Fields:
  tier:     "UNLIMITED"   (string)
  used:     false          (boolean)
```
Then use that code in the signup form.

### ⚠️ Firebase account gotcha

The Firebase project `intelligent-document-hub-a16c1` belongs to a specific Google account. If the console shows *"This project does not exist"*, you are logged into the wrong Google account in the browser. Switch accounts or use an incognito window.

### What success looks like

- Dashboard loads at `http://localhost:3000/dashboard`
- Top bar shows **🏆 Unlimited**
- Backend logs show: `📊 Usage retrieved for user ...: 0/9999 (UNLIMITED)`

---

*Last updated: April 2026 — after machine migration and 5-month reentry.*