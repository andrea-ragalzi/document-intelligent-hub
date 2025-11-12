# Project Structure

This document provides an overview of the project's directory structure and organization.

## Repository Structure

```
document-intelligent-hub/
├── .github/
│   └── wiki/                    # GitHub Wiki (this documentation)
├── backend/                     # FastAPI Backend
│   ├── app/
│   │   ├── core/               # Core configuration
│   │   ├── db/                 # Database clients (ChromaDB)
│   │   ├── routers/            # API endpoints
│   │   ├── schemas/            # Pydantic models
│   │   └── services/           # Business logic
│   ├── tests/                  # Backend tests
│   ├── chroma_db/              # ChromaDB persistence
│   ├── main.py                 # FastAPI application entry
│   ├── pyproject.toml          # Python dependencies (Poetry)
│   └── pytest.ini              # Pytest configuration
├── frontend/                    # Next.js Frontend
│   ├── app/                    # Next.js App Router
│   │   ├── api/               # API routes
│   │   ├── login/             # Login page
│   │   ├── signup/            # Signup page
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Home page
│   │   └── globals.css        # Global styles
│   ├── components/             # React components
│   ├── contexts/               # React contexts
│   ├── hooks/                  # Custom hooks
│   │   └── queries/           # TanStack Query hooks
│   ├── lib/                    # Utility libraries
│   ├── providers/              # React providers
│   ├── public/                 # Static assets
│   ├── stores/                 # Zustand stores
│   ├── test/                   # Frontend tests
│   ├── package.json            # Node dependencies
│   ├── tsconfig.json           # TypeScript config
│   ├── tailwind.config.js      # Tailwind CSS config
│   └── vitest.config.ts        # Vitest config
├── docker-compose.yml           # Docker orchestration
├── Makefile                     # Build commands
├── LICENSE                      # Project license
└── README.md                    # Main documentation
```

## Backend Structure

### `/backend/app/`

Core application code organized by concern:

```
app/
├── __init__.py
├── core/
│   ├── __init__.py
│   └── config.py              # Environment configuration
├── db/
│   ├── __init__.py
│   └── chroma_client.py       # ChromaDB client initialization
├── routers/
│   ├── __init__.py
│   └── rag_router.py          # RAG API endpoints
├── schemas/
│   ├── __init__.py
│   └── rag.py                 # Pydantic request/response models
└── services/
    ├── __init__.py
    ├── language_service.py    # Multi-language support
    └── rag_service.py         # RAG business logic
```

### Key Backend Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app initialization, CORS, middleware |
| `app/core/config.py` | Environment variables and configuration |
| `app/db/chroma_client.py` | ChromaDB setup and collection management |
| `app/routers/rag_router.py` | `/upload`, `/query` endpoints |
| `app/services/rag_service.py` | Document processing, embeddings, retrieval |
| `app/services/language_service.py` | Language detection and switching |

## Frontend Structure

### `/frontend/app/`

Next.js 16 App Router structure:

```
app/
├── api/
│   └── chat/
│       └── route.ts           # Streaming chat API route
├── login/
│   └── page.tsx              # Login page
├── signup/
│   └── page.tsx              # Signup page
├── layout.tsx                 # Root layout with providers
├── page.tsx                   # Main chat interface
└── globals.css                # Global styles
```

### `/frontend/components/`

React components organized by feature:

```
components/
├── AlertMessage.tsx           # Alert notifications
├── ChatMessageDisplay.tsx     # Individual chat message
├── ChatSection.tsx            # Main chat interface
├── ConfirmModal.tsx           # Confirmation dialogs
├── ConversationList.tsx       # Saved conversations sidebar
├── LoginForm.tsx              # Login form
├── ProtectedRoute.tsx         # Auth route guard
├── RenameModal.tsx            # Rename conversation modal
├── SaveModal.tsx              # (Deprecated) Save modal
├── Sidebar.tsx                # Left sidebar container
├── SignupForm.tsx             # Signup form
├── UploadSection.tsx          # Document upload UI
└── UserProfile.tsx            # User profile dropdown
```

### `/frontend/hooks/`

Custom React hooks:

```
hooks/
├── queries/
│   └── useConversationsQuery.ts  # TanStack Query hooks
├── useChatAI.ts                  # Vercel AI SDK integration
├── useConversations.ts           # (Deprecated) Old conversation hook
├── useDocumentUpload.ts          # Document upload logic
├── useRAGChat.ts                 # (Deprecated) Old RAG hook
├── useTheme.ts                   # Dark/light theme
└── useUserId.ts                  # Firebase auth user ID
```

### `/frontend/stores/`

Zustand state management:

```
stores/
└── uiStore.ts                 # UI state (modals, alerts, flags)
```

### `/frontend/lib/`

Utility libraries:

```
lib/
├── constants.ts               # App constants
├── conversationsService.ts    # Firestore CRUD operations
├── env.config.ts              # Safe env variable loading
├── firebase.ts                # Firebase initialization
└── types.ts                   # TypeScript type definitions
```

### `/frontend/providers/`

React context providers:

```
providers/
└── QueryProvider.tsx          # TanStack Query client provider
```

### `/frontend/contexts/`

React contexts:

```
contexts/
└── AuthContext.tsx            # Firebase authentication context
```

## Configuration Files

### Frontend Configuration

| File | Purpose |
|------|---------|
| `package.json` | Node.js dependencies and scripts |
| `tsconfig.json` | TypeScript compiler options |
| `next.config.ts` | Next.js configuration |
| `tailwind.config.js` | Tailwind CSS customization |
| `postcss.config.js` | PostCSS plugins |
| `vitest.config.ts` | Vitest testing configuration |
| `.env.local` | Environment variables (not in git) |

### Backend Configuration

| File | Purpose |
|------|---------|
| `pyproject.toml` | Poetry dependencies and project metadata |
| `pytest.ini` | Pytest configuration |
| `.env` | Environment variables (not in git) |

### Root Configuration

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Multi-container Docker setup |
| `Makefile` | Build and deployment commands |
| `.gitignore` | Git ignore patterns |

## Data Directories

### Backend Data

```
backend/
├── chroma_db/                 # ChromaDB vector database
│   ├── chroma.sqlite3        # SQLite database
│   └── {collection-uuid}/    # Document embeddings
└── htmlcov/                   # Coverage reports
```

### Frontend Data

```
frontend/
├── .next/                     # Next.js build output
├── coverage/                  # Test coverage reports
└── public/                    # Static files
```

## Testing Structure

### Backend Tests

```
backend/tests/
├── __init__.py
├── conftest.py                # Pytest fixtures
└── test_rag_endpoints.py      # API endpoint tests
```

### Frontend Tests

```
frontend/test/
├── setup.ts                   # Vitest setup
├── components/                # Component tests
│   ├── ChatSection.test.tsx
│   └── ...
└── hooks/                     # Hook tests
    ├── useChatAI.test.ts
    └── ...
```

## Key Architectural Patterns

### Backend Patterns

1. **Layered Architecture**
   - Routers (API layer)
   - Services (Business logic)
   - Schemas (Data validation)
   - DB clients (Data access)

2. **Dependency Injection**
   - FastAPI dependency system
   - Shared ChromaDB client

3. **Async/Await**
   - Streaming responses
   - Non-blocking I/O

### Frontend Patterns

1. **Component Composition**
   - Small, reusable components
   - Props-based communication
   - Container/Presentational split

2. **Custom Hooks**
   - Reusable logic
   - Separation of concerns
   - Easy testing

3. **State Management**
   - Zustand for UI state
   - TanStack Query for server state
   - Context for auth

4. **Type Safety**
   - TypeScript throughout
   - Strict type checking
   - Shared type definitions

## File Naming Conventions

### Frontend

- **Components**: PascalCase (e.g., `ChatSection.tsx`)
- **Hooks**: camelCase with 'use' prefix (e.g., `useChatAI.ts`)
- **Utilities**: camelCase (e.g., `firebase.ts`)
- **Types**: camelCase (e.g., `types.ts`)
- **Tests**: `*.test.tsx` or `*.test.ts`

### Backend

- **Modules**: snake_case (e.g., `rag_service.py`)
- **Classes**: PascalCase (e.g., `RAGService`)
- **Functions**: snake_case (e.g., `process_document`)
- **Tests**: `test_*.py`

## Import Aliases

### Frontend

```typescript
// Configured in tsconfig.json
import { Component } from "@/components/Component";
import { useHook } from "@/hooks/useHook";
import { Type } from "@/lib/types";
import { useStore } from "@/stores/uiStore";
```

**Alias:** `@` → `frontend/`

### Backend

```python
# Relative imports within app/
from app.core.config import settings
from app.db.chroma_client import get_chroma_client
from app.services.rag_service import RAGService
```

## Build Outputs

### Frontend Build

```bash
npm run build
```

Output: `.next/` directory
- Static pages
- Server components
- API routes
- Assets

### Backend Build

```bash
poetry build
```

Output: `dist/` directory
- Wheel package
- Source distribution

## Next Steps

- [Frontend Architecture](Frontend-Architecture) - Deep dive into frontend
- [Backend Architecture](Backend-Architecture) - Deep dive into backend
- [Development Workflow](Development-Workflow) - Development guide
- [API Reference](API-Endpoints) - API documentation
