# Backend

This is the backend for Document Intelligent Hub, a personal, independently built backend-heavy full-stack project. The Python 3.12 FastAPI service owns authenticated PDF ingestion, document management, retrieval-augmented question answering, usage tracking, and support integrations.

## Responsibilities

- Expose REST endpoints for authentication, document lifecycle operations, RAG queries, usage, language discovery, feedback, and bug reports.
- Turn uploaded PDFs into owned, searchable chunks and persist them in ChromaDB.
- Retrieve either a registered user's private context or the shared read-only guest corpus, generate an answer with OpenAI, and return evidence-backed filename/page citations.
- Coordinate Firebase Admin, Firestore, local HuggingFace embeddings, and optional Resend email delivery.

## Architecture

The implementation is organized under `backend/app/`:

- `routers/` contains the HTTP boundary. `documents_router.py`, `query_router.py`, `auth_router.py`, and `support_router.py` declare endpoints, dependencies, request handling, and response mapping.
- `services/` contains application workflows. `rag_orchestrator_service.py` coordinates specialized services for indexing, query processing, answer generation, document management, and conversation summaries.
- `ports/` contains application-owned capability contracts such as `VectorStorePort`, `UsageTrackingPort`, `TranslationPort`, and `FileStoragePort`.
- `repositories/` contains vector-store persistence access. `VectorStoreRepository` is the only repository because vector/document storage is the only current persistence boundary that benefits from repository semantics; services do not require a repository merely because they exist.
- `infrastructure/` contains concrete outbound adapters and providers, including `FirestoreUsageTracker`, `OpenAITranslationAdapter`, `LocalFileStorage`, and `ResendEmailAdapter`. `dependencies.py` is the composition root that wires these implementations into application services and FastAPI dependencies.
- `schemas/` contains Pydantic request and response contracts, including `rag_schema.py`, `auth_schema.py`, and language/translation schemas.
- `db/` contains ChromaDB and embedding setup. `chroma_client.py` creates the persistent client, collection, LangChain vector store, and local embedding singleton.
- `core/` contains cross-cutting configuration, Firebase initialization, bearer-token verification, logging, and constants.
- `config/` contains language/security constants and local prompt files. The active prompt files are ignored; tracked `.example` files show the expected names.

## Request Flow

For a protected document or query request, the path is:

```text
HTTP request
→ main.py router registration
→ router dependency: Firebase token verification + FastAPI/Pydantic validation
→ application service (usually RAGService)
→ application-owned port
→ concrete infrastructure adapter or repository
→ Pydantic response model / JSON response
```

For example, `POST /rag/upload/` is handled by `app/routers/documents_router.py`, resolves an explicit filename conflict action, delegates to `RAGService.index_document()`, and reaches `DocumentIndexingService` and `VectorStoreRepository`. `POST /rag/query/` is handled by `app/routers/query_router.py`, parses file filters, calls `RAGService.answer_query()`, and returns `QueryResponse` from `app/schemas/rag_schema.py`.

## RAG Flow

### Document upload and indexing

```text
Authenticated PDF upload
→ verified registered Firebase identity and workspace validation
→ filename, PDF, size/count, duplicate-action, and resource-limit validation
→ temporary-file handling and bounded PDF parsing
→ document-language detection and document classification
→ structural or fixed-size chunking
→ chunk metadata: verified workspace UID, filename, language, section, and timestamp
→ local HuggingFace embeddings through `db/chroma_client.py`
→ `VectorStoreRepository.add_documents()` indexes the UID-scoped chunks in ChromaDB
→ document becomes available to that workspace's retrieval path
```

Guest identities cannot upload, replace, or delete documents. Registered uploads use the verified Firebase UID selected by the server; client-supplied ownership is never accepted. The original PDF is retained separately for authenticated document access, while its searchable chunks are stored in the shared ChromaDB collection with the UID metadata filter.

### Question and answer

```text
Question
→ verified registered UID workspace or the restricted shared guest workspace
→ quota reservation and accessible document catalog
→ narrow deterministic lookup, extraction, or count route when validated evidence supports it
→ otherwise normal RAG: query parsing and optional owned-file filters
→ optional contextual reformulation for follow-up questions
→ user/file-filtered semantic retrieval plus lexical candidates
→ candidate deduplication, reranking, and final evidence selection
→ grounded answer generation from the selected context
→ trusted chunk filename/page metadata mapped to citations
→ complete `QueryResponse` JSON response
```

The deterministic route is deliberately limited to supported requests with validated evidence. Unsupported, ambiguous, conversational, or failed-validation requests continue through normal RAG. The normal path does not call semantic query classification: `QueryProcessingService` reformulates only when conversation context is needed, then answer generation retrieves and grounds the response. Query expansion and retrieval-language translation may supply additional retrieval candidates, but the final answer language is resolved from the request and bounded history. The API returns complete JSON rather than streaming model tokens.

Filename/page citations are derived from selected backend chunk metadata, rather than model-invented references. Registered retrieval always filters by the verified UID; guests can query only the server-selected shared InGen corpus. The classification service and prompt remain available for isolated use cases and tests, but are outside the normal production RAG path.

`POST /rag/upload/` accepts a PDF multipart field and optional `duplicate_action`: `reject` (default, returns `409` for a colliding owned filename), `replace`, or `rename` (server assigns `name (n).pdf`). Upload and every document mutation require a verified registered user. `POST /rag/query/` accepts `query`, bounded `conversation_history`, and optional `output_language`; it returns `answer`, compatibility `source_documents`, and `citations`, whose items contain `filename` and an optional one-based `page_number`. A verified registered user queries their UID-scoped collection. A Firebase anonymous identity queries the reserved shared InGen demo namespace under the guest budgets described below. Stored originals are available through authenticated `GET /rag/documents/content`; ownership or the guest namespace is selected only from verified token claims.

## Authentication & User Isolation

- `app/core/auth.py::verify_firebase_token` reads the `Authorization: Bearer <token>` header and calls Firebase Admin `auth.verify_id_token()`.
- The verified Firebase token is converted into a `FirebasePrincipal`. Registered users retain their UID-scoped workspace; email/password users need a verified Firebase email before provisioning or protected backend work. Tokens whose signed-in provider is `anonymous` are mapped to the reserved `__shared_ingen_demo_v1__` namespace for list/content/query only. Client-supplied ownership is never used.
- `/auth/register` receives the Firebase ID token, rejects an unverified email before first provisioning, preserves an existing valid tier on repeat registration, assigns `UNLIMITED` to configured allowlisted emails, and assigns `FREE` to other new users. No invitation code is required.
- Guest upload, ingestion, seeding, deletion, account cleanup, support submission, and summarization are rejected by server dependencies. Guest conversations are not written to Firestore.
- `DocumentIndexingService._prepare_chunks_with_metadata()` writes the verified user ID to each chunk's `source` metadata field and stores `original_filename` alongside language and section metadata.
- `VectorStoreRepository` applies `source=<user_id>` when listing, retrieving, and deleting chunks. Optional filename filters are combined with the same ownership condition.

This is application-level isolation inside a shared ChromaDB collection. The guarantee depends on every access path using the verified user ID and repository filters.

Relevant files: `app/core/auth.py`, `app/core/firebase.py`, `app/routers/documents_router.py`, `app/routers/query_router.py`, `app/services/document_indexing_service.py`, and `app/repositories/vector_store_repository.py`.

## External Integrations

| Integration                       | Purpose                                                                    | Main locations                                                                                                                                                                                                |
| --------------------------------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Firebase Admin                    | Verify ID tokens; access Firebase Auth and custom claims                   | `app/core/firebase.py`, `app/core/auth.py`, `app/routers/auth_router.py`                                                                                                                                      |
| Firestore                         | Store application configuration and usage counters                         | `app/infrastructure/firebase_config.py`, `app/infrastructure/firestore_usage_tracker.py`, `app/routers/auth_router.py`                                                                                        |
| ChromaDB                          | Persist embedded chunks and perform metadata-filtered retrieval/deletion   | `app/db/chroma_client.py`, `app/repositories/vector_store_repository.py`                                                                                                                                      |
| HuggingFace Sentence Transformers | Generate local `all-MiniLM-L6-v2` document/query embeddings                | `app/db/chroma_client.py`                                                                                                                                                                                     |
| OpenAI                            | Query parsing, reformulation/expansion, translation, and answer generation | `app/dependencies.py`, `app/infrastructure/openai_translation_adapter.py`, `app/services/query_processing_service.py`, `app/services/query_expansion_service.py`, `app/services/answer_generation_service.py` |
| Resend                            | Send bug-report and feedback emails when configured                        | `app/infrastructure/resend_email_adapter.py`, `app/routers/support_router.py`                                                                                                                                 |

## Configuration

Create the ignored local configuration with `cp backend/.env.example backend/.env.local`. `Settings` loads `backend/.env.local` for every local execution path; existing process variables remain authoritative. Docker Compose passes the same file through `env_file`. Local development expects the dedicated DEV service-account file at `backend/app/config/firebase-service-account.dev.json`. Deployment images exclude local environment files, and Railway supplies the PROD credential through `FIREBASE_CREDENTIALS`; never commit either credential.

| Variable                          | Controls                                                                                                     |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `OPENAI_API_KEY`                  | OpenAI calls used by query processing, expansion, and answer generation                                      |
| `LLM_MODEL`                       | Main OpenAI chat model; known capability limits such as Luna's temperature restriction are applied centrally |
| `CHROMA_DB_PATH`                  | Persistent ChromaDB storage path                                                                             |
| `DOCUMENT_STORAGE_PATH`           | Private original-PDF storage for authenticated preview/download                                              |
| `FIREBASE_CREDENTIALS`            | Firebase service-account JSON supplied as an environment value                                               |
| `FIREBASE_SERVICE_ACCOUNT_PATH`   | Alternate path to a Firebase service-account JSON file                                                       |
| `RAG_SYSTEM_PROMPT_PATH`          | Override path for the RAG system prompt                                                                      |
| `CLASSIFICATION_PROMPT_PATH`      | Override path for the isolated classification prompt; not used by normal production RAG requests             |
| `QUERY_REFORMULATION_PROMPT_PATH` | Override path for the query-reformulation prompt                                                             |
| `ENVIRONMENT`                     | Selects production CORS behavior when set to `production`                                                    |
| `ALLOWED_ORIGINS`                 | Comma-separated production CORS origins                                                                      |
| `TRUSTED_PROXY_IPS`               | Comma-separated trusted reverse-proxy IPs/CIDRs for client-IP headers                                        |
| `RESEND_API_KEY`                  | Enables backend-only Resend email delivery                                                                   |
| `RESEND_FROM_EMAIL`               | Verified Resend sender address                                                                               |
| `REPORT_RECIPIENT_EMAIL`          | Fixed recipient for support notifications                                                                    |
| `ENABLE_SHARED_DEMO_CORPUS`       | Provision the five bundled synthetic InGen PDFs in the stable shared namespace at startup                     |
| `GUEST_DAILY_QUOTAS_ENABLED`      | Enables UID/IP/global anonymous daily quotas; defaults off only for `ENVIRONMENT=development`, fail-closed elsewhere |
| `GUEST_UID_DAILY_QUERY_LIMIT`     | Daily query ceiling for one Firebase anonymous UID                                                            |
| `GUEST_IP_DAILY_QUERY_LIMIT`      | Secondary daily query ceiling for one hashed client IP                                                        |
| `GUEST_GLOBAL_DAILY_QUERY_BUDGET` | Hard daily ceiling across the anonymous demo                                                                  |
| `MAX_CONCURRENT_GUEST_QUERIES`    | In-process concurrent anonymous query ceiling for the current single-process deployment                       |

If prompt files are absent, `app/core/config.py` falls back to built-in prompt text. For local customization, copy the tracked files in `config/*.txt.example` to the corresponding ignored `.txt` filenames.

Uploaded PDF originals are retained separately from ChromaDB data structures so their owner can preview or download them. For Railway, set `DOCUMENT_STORAGE_PATH` to a mounted persistent volume path (for example `/data/uploads`); without a volume, originals disappear on a redeploy while indexed chunks may remain.

## Running Locally

From the backend directory:

```bash
cd backend
poetry install
poetry run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The health endpoint is `http://127.0.0.1:8000/` and FastAPI's interactive documentation is `http://127.0.0.1:8000/docs`. Use `--host 0.0.0.0` when deliberately testing access from another device on the LAN.

## Testing

Pytest is configured in `pytest.ini` with `tests/` as the test path:

```bash
cd backend
poetry run pytest
```

For a coverage report:

```bash
poetry run pytest --cov=app --cov-report=term
```

GitHub Actions validates backend changes with Pylint, MyPy, Lizard, and pytest, alongside the repository's frontend, secret-scanning, Docker, and Firebase integration checks. Firebase, OpenAI, Resend, and local model availability can affect tests in other environments.

## Important Code Paths

| Area                                            | Start here                                                                                          |
| ----------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Application startup and router registration     | `main.py`                                                                                           |
| Authentication and Firebase initialization      | `app/core/auth.py`, `app/core/firebase.py`                                                          |
| Settings and prompt loading                     | `app/core/config.py`, `config/*.txt.example`                                                        |
| HTTP endpoints                                  | `app/routers/`                                                                                      |
| RAG orchestration                               | `app/services/rag_orchestrator_service.py`                                                          |
| PDF parsing, classification, chunking, metadata | `app/services/document_indexing_service.py`, `document_classifier_service.py`                       |
| Query parsing, reformulation, expansion         | `app/services/query_parser_service.py`, `query_processing_service.py`, `query_expansion_service.py` |
| Retrieval, reranking, prompt, sources           | `app/services/answer_generation_service.py`, `reranking_service.py`                                 |
| Document CRUD                                   | `app/services/document_management_service.py`, `app/repositories/vector_store_repository.py`        |
| ChromaDB and embeddings                         | `app/db/chroma_client.py`                                                                           |
| API contracts                                   | `app/schemas/`                                                                                      |
| Tests and fixtures                              | `tests/`                                                                                            |

## Common Development Gotchas

- Run Uvicorn from `backend/`: `.env.local`, the default prompt paths, and the relative `CHROMA_DB_PATH` are resolved from the backend working directory.
- Firebase initialization is attempted at startup. Without valid Firebase credentials the process can start, but protected/authentication routes are unavailable.
- Startup preloads the local HuggingFace embedding model and creates the persistent ChromaDB directory if needed; the first run can be slow and may require model download access.
- Startup also checks the stable shared InGen namespace. It indexes the five bundled, synthetic fan-made enterprise documents only when the namespace is absent or incomplete; anonymous sessions never seed or copy vectors. Enable Anonymous sign-in in the deployed Firebase project before publishing.
- ChromaDB contains the local search index rather than the original PDFs. Deleting `CHROMA_DB_PATH` loses indexed chunks and requires the documents to be uploaded again.
- Development CORS allows all origins. Setting `ENVIRONMENT=production` switches to the comma-separated `ALLOWED_ORIGINS` list.
- Support-submission limits are process-local for the current single-instance demo. Set `TRUSTED_PROXY_IPS` to the real production reverse-proxy address or CIDR so the limiter can use forwarded client IPs safely; never set it to `*`.
- Guest UID, hashed-IP, and global daily counters are reserved atomically in one Firestore document. They are disabled only when `ENVIRONMENT=development` and `GUEST_DAILY_QUOTAS_ENABLED` is not `true`, so local RAG evaluation is unrestricted. All other environments enforce them even if the flag is false or missing. Guest concurrency is process-local and assumes the documented single-process deployment. Firebase App Check is not currently enforced and is a follow-up hardening option.
- `GET /auth/usage` returns registered tier usage or, for an anonymous token, the effective guest allowance remaining after UID, client-IP, and global reservations. In unrestricted development it returns `limited: false` with `query_limit` and `remaining` set to `null`. Reading usage does not reserve capacity; each admitted production query reserves before retrieval or provider work, and the reservation remains consumed if later RAG work fails.
- The frontend may simulate progressive text display, but the backend query endpoint returns one complete JSON response rather than an end-to-end stream.
