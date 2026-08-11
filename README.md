# Document Intelligent Hub

Document Intelligent Hub is an independently built, full-stack application for people and teams who need to search private PDF collections and ask questions grounded in their own documents. Its core is a Python 3.12 and FastAPI REST API that authenticates users with Firebase, indexes document content in ChromaDB with local HuggingFace embeddings, and returns RAG-generated answers with the source filenames used as context.

The project is full-stack but intentionally backend-heavy. It demonstrates authenticated API design, third-party integrations, document-processing workflows, application-level user isolation, maintainable service boundaries, and automated testing around an applied Retrieval-Augmented Generation (RAG) system.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=flat&logo=next.js)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat&logo=typescript)](https://www.typescriptlang.org/)

## What It Does

- Authenticated users can upload, manage, and search private PDF collections.
- Natural-language questions are answered from retrieved document context, with source filenames returned for grounding.
- File-aware and multilingual queries support conversations over indexed documents.
- Saved conversations are persisted in Firestore through the client application.

## Backend Engineering Highlights

- **REST API design:** FastAPI routers and Pydantic schemas define authentication, document, query, usage, and support contracts, with OpenAPI documentation available at runtime.
- **Authentication boundary:** Firebase Admin verifies bearer tokens; protected routes derive the user ID from the verified token rather than trusting a client-selected owner.
- **Backend integrations:** the service coordinates Firebase, Firestore, OpenAI, ChromaDB, local HuggingFace embeddings, and SendGrid-backed support workflows.
- **Maintainable boundaries:** HTTP handling, schemas, application services, vector-store access, configuration, and dependency construction are separated under `backend/app/`.
- **Multi-user isolation:** indexed chunks carry the verified Firebase user ID in metadata, and repository operations apply that metadata filter when listing, retrieving, and deleting documents.
- **Document processing:** PDF parsing, document classification, adaptive chunking, language detection, metadata enrichment, batch indexing, and cleanup are isolated in dedicated services.
- **Applied RAG:** query parsing, conditional reformulation, expansion, filtered retrieval, local reranking, answer generation, and source extraction form an explicit pipeline.
- **Automated tests:** pytest covers backend services, repositories, authentication helpers, and API behavior; Vitest and React Testing Library cover frontend hooks, stores, and components.

## Key Capabilities

- Structural or fixed-size chunking selected from document characteristics
- Persistent vector storage with optional filename filters
- Lightweight rank-and-term-frequency reranking
- Language detection, translated retrieval, and configurable answer language
- Responsive Next.js client for document management and chat

## Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│ Next.js 16 + TypeScript                                     │
│                                                             │
│ • Firebase Authentication                                   │
│ • Firestore conversation persistence                        │
│ • Document management and chat UI                           │
└───────────────────────┬─────────────────────────────────────┘
                        │ REST API + Firebase bearer token
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ FastAPI + Pydantic                                          │
│                                                             │
│ Routers → Services → Repository                             │
│    │          │          │                                  │
│    │          │          └─ ChromaDB                        │
│    │          ├─ OpenAI chat models                         │
│    │          └─ HuggingFace embeddings                     │
│    └─ Firebase Admin / Firestore                             │
└─────────────────────────────────────────────────────────────┘
```

Firebase handles identity, while Firestore stores conversations and backend usage/configuration data. ChromaDB stores PDF chunks and embeddings. OpenAI is used for language-model operations; document embeddings are generated locally with HuggingFace Sentence Transformers.

## RAG Pipeline

### Document Indexing

```text
Authenticated PDF upload
→ file validation and temporary-file handling
→ element extraction with UnstructuredPDFLoader
→ document classification and structural-density check
→ structural or fixed-size chunking
→ ownership, filename, language, section, and timestamp metadata
→ local HuggingFace embeddings
→ batched ChromaDB indexing
```

### Query and Answer Generation

```text
Firebase token verification
→ natural-language file-filter extraction
→ conditional query reformulation from conversation context
→ query-language detection and retrieval-language handling
→ alternative-query generation
→ ChromaDB retrieval filtered by verified user metadata
→ duplicate removal and local reranking
→ prompt construction with retrieved context and conversation history
→ OpenAI answer generation
→ source-filename extraction and API response
```

The API returns source filenames, not page-level citations or retrieval scores.

## Tech Stack

| Area                 | Technologies                                                                                            |
| -------------------- | ------------------------------------------------------------------------------------------------------- |
| Backend              | Python 3.12, FastAPI, Uvicorn, Pydantic Settings                                                        |
| RAG and integrations | LangChain, OpenAI, ChromaDB, HuggingFace Sentence Transformers, Unstructured, Firebase Admin, Firestore |
| Frontend             | Next.js 16, React 19, TypeScript, Firebase, TanStack Query, Zustand, Tailwind CSS                       |
| Testing              | pytest, pytest-asyncio, pytest-cov, Vitest, React Testing Library                                       |
| Quality and tooling  | Poetry, mypy, Pylint, ESLint, Prettier, pre-commit, Docker Compose                                      |

## Testing

The repository contains backend and frontend test suites. This documentation pass did not execute the complete suites, so it does not claim a current pass count or coverage percentage.

Backend:

```bash
cd backend
poetry run pytest

# Optional coverage report
poetry run pytest --cov=app --cov-report=term
```

Frontend:

```bash
cd frontend
npm run test:run

# Optional coverage report
npm run test:coverage
```

## Run Locally

Prerequisites: Python 3.12, Poetry, Node.js with npm, an OpenAI API key, and a Firebase project with web and Admin SDK configuration.

1. Prepare the ignored local configuration files:

   - `backend/.env`, using `backend/.env.example` as a starting point
   - `backend/app/config/firebase-service-account.json`
   - `frontend/.env.local`

2. Install and start the backend:

   ```bash
   cd backend
   poetry install
   poetry run uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```

3. In another terminal, install and start the frontend:

   ```bash
   cd frontend
   npm ci
   npm run dev
   ```

4. Open:

   - Frontend: http://127.0.0.1:3000
   - FastAPI documentation: http://127.0.0.1:8000/docs

See the [backend handbook](backend/README.md) and [frontend handbook](frontend/README.md) for component-specific details.

## Repository Structure

```text
document-intelligent-hub/
├── backend/
│   ├── app/
│   │   ├── core/          # Settings, authentication, Firebase, logging
│   │   ├── db/            # ChromaDB and embedding configuration
│   │   ├── repositories/  # Vector-store persistence and filtering
│   │   ├── routers/       # FastAPI endpoints
│   │   ├── schemas/       # Pydantic API contracts
│   │   └── services/      # Document, query, RAG, usage, and support logic
│   ├── tests/             # Backend pytest suite
│   └── main.py            # FastAPI entry point
├── frontend/
│   ├── app/               # Next.js pages and chat API route
│   ├── components/        # UI components
│   ├── hooks/             # Client and server-state workflows
│   ├── lib/               # Firebase, API, and conversation integrations
│   └── test/              # Frontend Vitest suite
├── docker-compose.yml
└── README.md
```

## Current Status & Limitations

- Full RAG usage requires external Firebase and OpenAI configuration.
- The FastAPI backend returns a complete JSON answer. The frontend then emits that completed text character by character, so this is not end-to-end model streaming.
- Dockerfiles and a Compose configuration are present, but the complete clean-clone deployment workflow has not yet been verified.
- Source attribution is currently filename-level rather than page-level citation.

## Component Documentation

- [Backend handbook](backend/README.md)
- [Frontend handbook](frontend/README.md)

## Author

**Andrea Ragalzi**

- GitHub: [@andrea-ragalzi](https://github.com/andrea-ragalzi)
- Email: andrea.ragalzi.code@gmail.com

## License

This project is licensed under the [MIT License](LICENSE).
