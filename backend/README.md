# Backend

The backend is a Python 3.12 FastAPI service for authenticated PDF ingestion, document management, and retrieval-augmented question answering. It owns request validation, Firebase token verification, document processing, ChromaDB persistence, RAG orchestration, usage tracking, and support integrations.

## Responsibilities

- Expose REST endpoints for authentication, document lifecycle operations, RAG queries, usage, language discovery, feedback, and bug reports.
- Turn uploaded PDFs into owned, searchable chunks and persist them in ChromaDB.
- Retrieve only the authenticated user's context, generate an answer with OpenAI, and return source filenames.
- Coordinate Firebase Admin, Firestore, local HuggingFace embeddings, and optional Resend email delivery.

## Architecture

The implementation is organized under `backend/app/`:

- `routers/` contains the HTTP boundary. `documents_router.py`, `query_router.py`, `auth_router.py`, and `support_router.py` declare endpoints, dependencies, request handling, and response mapping.
- `services/` contains application workflows. `rag_orchestrator_service.py` coordinates specialized services for indexing, query processing, answer generation, document management, and conversation summaries.
- `repositories/` contains vector-store data access. `VectorStoreRepository` is the only application layer that performs ChromaDB collection operations; `dependencies.py` wires it into FastAPI.
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
→ repository or external integration
→ Pydantic response model / JSON response
```

For example, `POST /rag/upload/` is handled by `app/routers/documents_router.py`, delegates to `RAGService.index_document()`, and reaches `DocumentIndexingService` and `VectorStoreRepository`. `POST /rag/query/` is handled by `app/routers/query_router.py`, parses file filters, calls `RAGService.answer_query()`, and returns `QueryResponse` from `app/schemas/rag_schema.py`.

## RAG Flow

The implementation is split between the following services:

```text
PDF upload
→ documents_router.py validation and temporary upload handling
→ DocumentIndexingService.index_document()
→ UnstructuredPDFLoader (element parsing)
→ DocumentClassifierService classification and structural-density check
→ structural or fixed-size chunking
→ metadata enrichment (user, filename, language, section, timestamp)
→ HuggingFace embeddings in db/chroma_client.py
→ VectorStoreRepository.add_documents() / ChromaDB indexing
```

```text
RAG query
→ query_router.py extracts include/exclude file filters with QueryParserService
→ RAGService.answer_query() conditionally reformulates conversational queries
→ QueryProcessingService classification/reformulation
→ AnswerGenerationService language handling and query preparation
→ QueryExpansionService generates alternative queries
→ VectorStoreRepository.get_retriever() applies user/file metadata filters
→ retrieval results are deduplicated and reranked by RerankingService
→ AnswerGenerationService builds the prompt with context and conversation history
→ OpenAI chat model generates the answer
→ source filenames are extracted and returned in QueryResponse
```

The answer path translates non-English queries to English for retrieval when needed, then translates the answer back to the requested/query language. The API returns a complete JSON response; it does not stream tokens from the model.

## Authentication & User Isolation

- `app/core/auth.py::verify_firebase_token` reads the `Authorization: Bearer <token>` header and calls Firebase Admin `auth.verify_id_token()`.
- The verified Firebase `uid` is injected as `user_id` through `Depends(verify_firebase_token)` in protected routers. Client-supplied ownership is not used for document operations.
- `DocumentIndexingService._prepare_chunks_with_metadata()` writes the verified user ID to each chunk's `source` metadata field and stores `original_filename` alongside language and section metadata.
- `VectorStoreRepository` applies `source=<user_id>` when listing, retrieving, and deleting chunks. Optional filename filters are combined with the same ownership condition.

This is application-level isolation inside a shared ChromaDB collection. The guarantee depends on every access path using the verified user ID and repository filters.

Relevant files: `app/core/auth.py`, `app/core/firebase.py`, `app/routers/documents_router.py`, `app/routers/query_router.py`, `app/services/document_indexing_service.py`, and `app/repositories/vector_store_repository.py`.

## External Integrations

| Integration                       | Purpose                                                                           | Main locations                                                                                                                                                     |
| --------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Firebase Admin                    | Verify ID tokens; access Firebase Auth and custom claims                          | `app/core/firebase.py`, `app/core/auth.py`, `app/routers/auth_router.py`                                                                                           |
| Firestore                         | Store application configuration, usage counters, and invitation/registration data | `app/routers/auth_router.py`, `app/services/usage_tracking_service.py`                                                                                             |
| ChromaDB                          | Persist embedded chunks and perform metadata-filtered retrieval/deletion          | `app/db/chroma_client.py`, `app/repositories/vector_store_repository.py`                                                                                           |
| HuggingFace Sentence Transformers | Generate local `all-MiniLM-L6-v2` document/query embeddings                       | `app/db/chroma_client.py`                                                                                                                                          |
| OpenAI                            | Query parsing, reformulation/expansion, and answer generation                     | `app/services/rag_orchestrator_service.py`, `query_parser_service.py`, `query_processing_service.py`, `query_expansion_service.py`, `answer_generation_service.py` |
| Resend                            | Send bug-report, feedback, and invitation emails when configured                    | `app/services/email_service.py`, `app/routers/support_router.py`, `app/routers/auth_router.py`                                                                     |

## Configuration

The backend loads the ignored `backend/.env.development.local` first and then fills any remaining local secrets from `backend/.env` when started through `main.py`. Existing process variables remain authoritative. Local development expects the dedicated DEV service-account file at `backend/app/config/firebase-service-account.dev.json`. Deployment images exclude both environment files, and Railway supplies the PROD credential through `FIREBASE_CREDENTIALS`; never commit either credential.

| Variable                          | Controls                                                                |
| --------------------------------- | ----------------------------------------------------------------------- |
| `OPENAI_API_KEY`                  | OpenAI calls used by query processing, expansion, and answer generation |
| `LLM_MODEL`                       | Main OpenAI chat model used by the RAG services                         |
| `CHROMA_DB_PATH`                  | Persistent ChromaDB storage path                                        |
| `FIREBASE_CREDENTIALS`            | Firebase service-account JSON supplied as an environment value          |
| `FIREBASE_SERVICE_ACCOUNT_PATH`   | Alternate path to a Firebase service-account JSON file                  |
| `RAG_SYSTEM_PROMPT_PATH`          | Override path for the RAG system prompt                                 |
| `CLASSIFICATION_PROMPT_PATH`      | Override path for the classification prompt                             |
| `QUERY_REFORMULATION_PROMPT_PATH` | Override path for the query-reformulation prompt                        |
| `ENVIRONMENT`                     | Selects production CORS behavior when set to `production`               |
| `ALLOWED_ORIGINS`                 | Comma-separated production CORS origins                                 |
| `RESEND_API_KEY`                  | Enables backend-only Resend email delivery                              |
| `RESEND_FROM_EMAIL`               | Verified Resend sender address                                          |
| `REPORT_RECIPIENT_EMAIL`          | Fixed recipient for support and invitation notifications                |

If prompt files are absent, `app/core/config.py` falls back to built-in prompt text. For local customization, copy the tracked files in `config/*.txt.example` to the corresponding ignored `.txt` filenames.

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

The repository contains unit and integration-style tests, but these commands are not a claim that the current suite passes in every environment. Firebase, OpenAI, Resend, and local model availability affect parts of the suite.

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

- Run Uvicorn from `backend/`: `.env`, the default prompt paths, and the relative `CHROMA_DB_PATH` are resolved from the backend working directory.
- Firebase initialization is attempted at startup. Without valid Firebase credentials the process can start, but protected/authentication routes are unavailable.
- Registration without an invitation assigns the constrained FREE tier. Optional elevated access uses `app_config/settings.unlimited_emails` or an unused `invitation_codes` document; the assigned tier is stored as a Firebase custom claim.
- Startup preloads the local HuggingFace embedding model and creates the persistent ChromaDB directory if needed; the first run can be slow and may require model download access.
- ChromaDB contains the local search index rather than the original PDFs. Deleting `CHROMA_DB_PATH` loses indexed chunks and requires the documents to be uploaded again.
- Development CORS allows all origins. Setting `ENVIRONMENT=production` switches to the comma-separated `ALLOWED_ORIGINS` list.
- The frontend may simulate progressive text display, but the backend query endpoint returns one complete JSON response rather than an end-to-end stream.
