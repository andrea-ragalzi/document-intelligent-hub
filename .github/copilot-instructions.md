# AI Agent Instructions - Document Intelligent Hub

## Architecture Overview

This is a **full-stack multi-tenant RAG (Retrieval-Augmented Generation) system** built with FastAPI (backend) and Next.js 16 (frontend). The system enables secure, AI-powered Q&A over user-uploaded PDF documents with conversation memory, automatic use case detection, and multilingual support.

**Core Stack:**

- Backend: FastAPI + LangChain + ChromaDB (vector store) + HuggingFace embeddings (local)
- Frontend: Next.js 16 (App Router) + React 19 + TypeScript + Zustand + TanStack Query
- Auth: Firebase Authentication + Firestore
- Deployment: Docker + docker-compose

## Project Structure

```
backend/
  app/
    core/         # Config, logging (structured logging with loguru)
    db/           # ChromaDB client (HuggingFace embeddings - all-MiniLM-L6-v2)
    routers/      # FastAPI endpoints (rag_router.py)
    schemas/      # Pydantic models (rag.py, use_cases.py)
    services/     # Business logic (see Service Layer Architecture below)
  tests/          # pytest with fixtures, mocked OpenAI calls
  main.py         # FastAPI app entry point with CORS & logging middleware

frontend/
  app/            # Next.js App Router pages (dashboard, login, signup)
    api/chat/     # Edge runtime API for streaming responses
  components/     # React components (Chat, Upload, Sidebar, Modals)
  stores/         # Zustand stores (uiStore.ts for UI state)
  hooks/          # Custom hooks (useRAGChat, useConversations, etc.)
  contexts/       # React contexts (AuthContext for Firebase)
  lib/            # Utils, Firebase config, types, constants
```

## Service Layer Architecture (Backend)

The backend uses a **modular service architecture** where `rag_service.py` orchestrates specialized services:

- **`rag_service.py`** - Main orchestrator for document indexing, retrieval, and answer generation
- **`use_case_detection_service.py`** - Auto-detects query intent (CU1-CU6) using pattern matching
- **`prompt_template_service.py`** - Generates optimized prompts based on use case (4-section modular structure)
- **`language_service.py`** - Detects document/query language (supports 20+ languages)
- **`translation_service.py`** - Translates queries/responses for multilingual support
- **`query_expansion_service.py`** - Generates alternative query phrasings for better retrieval
- **`reranking_service.py`** - Uses Cohere to rerank retrieved documents by relevance

**Key Pattern:** Each service is self-contained with its own LLM instance and configuration. The RAG service imports and delegates to specialized services rather than handling everything inline.

## Multi-Tenancy & Data Isolation

**ChromaDB Metadata Filtering:** Every document is tagged with `user_id` metadata. All queries filter by `user_id` to ensure strict tenant isolation:

```python
# Indexing (app/services/rag_service.py)
metadata = {
    "user_id": user_id,
    "filename": file.filename,
    "chunk_index": i,
    "document_language": detected_language,
}

# Querying (app/db/chroma_client.py via Chroma)
retriever = vectorstore.as_retriever(
    search_kwargs={"filter": {"user_id": user_id}, "k": 10}
)
```

**CRITICAL:** Never modify or remove `user_id` filtering logic - it's the security boundary.

## Use Case Optimization System (CU1-CU6)

The system automatically detects query intent and applies optimized prompts to overcome LLM limitations like "constraint neglect":

**6 Use Cases:**

- **CU1:** Professional content generation (reports, emails)
- **CU2:** Code development/debugging (generates executable code)
- **CU3:** Data analysis/summarization (structured outputs)
- **CU4:** Creative brainstorming (lists with exact quantities - e.g., "10 people")
- **CU5:** Structured planning (roadmaps, outlines)
- **CU6:** Strategic business documents (SWOT, PESTEL)

**Auto-Detection Flow:**

1. User query → `use_case_detection_service.py` analyzes patterns/keywords
2. Detected use case → `prompt_template_service.py` generates 4-section prompt
3. Prompt structure: PERSONALITY → SPECIFIC REQUEST → CONSTRAINTS → ADDITIONAL CONTEXT
4. Constraints repeated 3+ times for emphasis (e.g., "EXACTLY 10 items - NON-NEGOTIABLE")

**Example:** Query "list of 10 people" → Auto-detects CU4 → Enforces exact count → Returns 10 specific names (not generic categories).

See `USE_CASE_GUIDE.md` for full documentation.

## Conversation Memory System

**Hybrid memory approach** (see `CONVERSATION_MEMORY.md`):

1. **Short-term (Buffer):** Last 7 exchanges (14 messages) sent with each query
   - Frontend: `useRAGChat.ts` prepares `conversation_history` array
   - Backend: `rag_service.py` injects history between system prompt and RAG context
2. **Long-term (Summarization):** Auto-generates summary every 20 messages
   - Endpoint: `POST /rag/summarize/`
   - Summary stored in Firestore: `conversations/{id}.summary`
   - LLM extracts key facts, topics, ongoing issues

**Prompt Injection:**

```
[System Instruction] → [Conversation History] → [RAG Context] → [New Question]
```

## Testing Strategy

### Backend (pytest)

- **Fixtures:** `conftest.py` mocks OpenAI LLM calls (NOT embeddings - they're local/free)
- **Run:** `pytest -v` or `make test-backend`
- **Coverage:** `pytest --cov=app --cov-report=html` (target: 80%+)
- **Key tests:** `test_use_case_detection.py`, `test_rag_endpoints.py`, `test_document_crud.py`

### Frontend (Vitest)

- **Config:** `vitest.config.ts` with React Testing Library
- **Run:** `npm run test` or `npm run test:ui` (UI mode)
- **Coverage:** Explicitly includes tested files in `coverage.include` array
- **Pattern:** Focus on pure logic (stores, utils) - avoid complex Firebase/Router integration

**Coverage Notes:**

- Backend: HuggingFace embeddings run locally (fast, no mocking needed)
- Frontend: Exclude pages, contexts, and hooks with heavy Firebase/network dependencies

## Development Workflows

### Local Development (Recommended)

```bash
# Backend (Poetry environment)
cd backend
poetry install
poetry run uvicorn main:app --reload --host 0.0.0.0

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Docker Development

```bash
# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Access shells
docker-compose exec backend sh
docker-compose exec frontend sh
```

### Running Tests

```bash
# All tests with coverage
./run-coverage.sh

# Backend only
cd backend && pytest --cov=app --cov-report=term

# Frontend only
cd frontend && npm run test:coverage

# Use VS Code tasks: "Run All Tests with Coverage"
```

**IMPORTANT:** The backend uses `poetry` for dependency management. Always use `poetry run` or activate the virtual environment with `poetry shell` before running Python commands.

## State Management (Frontend)

**Separation of Concerns:**

- **Zustand (`stores/uiStore.ts`):** UI-only state (modals, alerts, current conversation ID)
- **TanStack Query:** Server state (conversations, documents) with caching & auto-refetch
- **React Hooks:** Custom hooks wrap business logic (e.g., `useRAGChat`, `useConversations`)

**Pattern Example:**

```typescript
// UI state (Zustand)
const { openRenameModal, closeRenameModal } = useUIStore();

// Server state (TanStack Query)
const { data: conversations, isLoading } = useConversations(userId);

// Business logic (Hook)
const { handleQuerySubmit, chatHistory } = useRAGChat();
```

**Never mix:** Don't store server data in Zustand or UI flags in TanStack Query.

## UX Patterns (Frontend Lists)

### Automatic Selection Mode

Lists (ConversationList, DocumentList) use **automatic selection mode** - no manual "Manage Mode" button:

- **Normal State:** Click/tap loads item
- **Selection State:** Automatically activates when any item is selected
- **Bulk Action Bar:** Appears conditionally when `selectedItems.length > 0`

### Context Menus (Single Item Actions)

- **Desktop:** Kebab icon (hidden, visible on hover) → Dropdown menu with calculated position
- **Mobile:** Long-press (500ms) → Bottom sheet action menu (slides from bottom)
- **Implementation:** Uses React Portal (`createPortal`) to render at `document.body` level (solves z-index issues)

```tsx
// Key pattern: Execute action FIRST, then close menu
onClick={(e) => {
  e.stopPropagation();
  onAction(item.id);          // ← Execute first
  setOpenMenuId(null);         // ← Close after
}}
```

### Mobile Gestures

- **Long-press detection:** 500ms timeout triggers menu open
- **Drag-to-dismiss:** Mobile menu can be dragged down >100px to close
- **Touch events:** Only on drag handle (top bar), not menu content - prevents interference with button clicks

### List Ordering

Conversations are sorted with priority:

1. **Pinned items first** (isPinned: true)
2. **Then by timestamp** (most recent first)

```tsx
const sorted = [...items].sort((a, b) => {
  if (a.isPinned && !b.isPinned) return -1;
  if (!a.isPinned && b.isPinned) return 1;
  return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
});
```

## API Conventions

### Request/Response Patterns

- **Authentication:** User ID from Firebase Auth (`uid`) passed as `user_id` in request body
- **Conversation History:** Array of `{role: "user"|"assistant", content: string}` objects
- **Streaming:** Frontend uses Vercel AI SDK format (`0:"char"\n`) in `app/api/chat/route.ts`
- **Error Handling:** Backend returns `{detail: "error message"}`, frontend displays in chat

### Key Endpoints

```
POST /rag/upload/        # Upload PDF (multipart/form-data)
POST /rag/query/         # Query with optional conversation_history & use_case
POST /rag/summarize/     # Generate conversation summary
GET  /rag/documents/     # List user's documents (filtered by user_id)
DELETE /rag/documents/{filename}  # Delete document by filename
```

## Configuration

### Environment Variables (.env)

```bash
# Backend (required)
OPENAI_API_KEY=sk-...              # For LLM calls (NOT embeddings)
CHROMA_DB_PATH=chroma_db           # Vector store persistence
EMBEDDING_MODEL=text-embedding-ada-002  # (unused - HuggingFace used instead)
LLM_MODEL=gpt-3.5-turbo            # Or gpt-4

# Frontend (required)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/rag
NEXT_PUBLIC_FIREBASE_API_KEY=...  # Firebase config
```

**Note:** Embeddings use local HuggingFace model (`all-MiniLM-L6-v2`) - no API key needed, fast, free, private.

## Coding Standards & Conventions

**General Principles:**

- All code, comments, and documentation must be in **English**
- Prioritize clean, readable, maintainable code
- Keep comments essential and non-verbose

### Python (Backend)

**1. Code Style:**

- Strictly adhere to **PEP 8** standard (line length, naming conventions, indentation)
- Use **Type Hinting** for all functions, classes, and variables (MyPy compatibility)
- Prefer `async def` and `await` for I/O-bound operations

**2. FastAPI Patterns:**

- Use Pydantic models for data validation and serialization
- Use dependency injection with `Depends()` for shared logic
- Define schemas in `schemas/` directory
- Keep routers thin - business logic belongs in `services/`

**3. Example:**

```python
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

class QueryRequest(BaseModel):
    user_id: str
    query: str
    conversation_history: Optional[list] = None

async def query_documents(request: QueryRequest) -> dict:
    """Process RAG query with proper typing and async."""
    # Implementation
    pass
```

### TypeScript (Frontend)

**1. Modern Features:**

- Use **arrow functions** (`=>`) for all function expressions
- Leverage destructuring and spread/rest operators
- Use `const` by default, `let` only when reassignment needed

**2. Type Safety:**

- Fully leverage TypeScript: `interface`, `type`, generics
- Define types in `lib/types.ts` and import consistently
- Avoid `any` - use `unknown` or proper types

**3. React/Next.js:**

- Use functional components with Hooks (no class components)
- Follow Next.js App Router conventions
- Server Components by default, Client Components when needed (`'use client'`)

**4. Example:**

```typescript
interface ConversationProps {
  conversations: SavedConversation[];
  onLoad: (conv: SavedConversation) => void;
}

export const ConversationList: React.FC<ConversationProps> = ({
  conversations,
  onLoad,
}) => {
  const [selected, setSelected] = useState<string[]>([]);

  const handleSelect = (id: string) => {
    setSelected(prev => [...prev, id]);
  };

  return (/* JSX */);
};
```

## Common Patterns & Conventions

### Logging (Backend)

- Use structured logging: `from app.core.logging import logger`
- Patterns: `logger.info()`, `logger.error()`, `logger.bind(ACCESS=True).info()` for requests
- Emojis for readability: `🚀`, `✅`, `❌`, `📁`, `🧠`

### Error Handling

- Backend: Raise `HTTPException(status_code=..., detail="...")`
- Frontend: Display errors in chat UI (never crash, show `[API ERROR]` messages)

### Type Safety

- Backend: Use Pydantic schemas (`schemas/rag.py`)
- Frontend: Define types in `lib/types.ts`, import consistently

### File Naming

- Backend: Snake case (`rag_service.py`, `use_case_detection_service.py`)
- Frontend: Pascal case for components (`ChatSection.tsx`), camel case for utilities (`conversationsService.ts`)

## Known Gotchas

1. **PDF Parsing:** UnstructuredPDFLoader can fail on minimal/corrupted PDFs (500 error) - not a code bug
2. **CORS:** Backend allows `*` origins in development - restrict in production
3. **ChromaDB Path:** Must exist on startup (created in `main.py` if missing)
4. **Firebase Contexts:** Components using `useAuth()` must be inside `<AuthProvider>`
5. **Poetry vs pip:** Backend uses Poetry - don't run `pip install` directly

## When Adding Features

1. **New Service:** Create in `backend/app/services/`, import in `rag_service.py`, add tests
2. **New Endpoint:** Add to `routers/rag_router.py`, define schema in `schemas/rag.py`
3. **New UI Component:** Add to `frontend/components/`, use Zustand for local state
4. **New Hook:** Add to `frontend/hooks/`, keep it pure (testable)
5. **Database Change:** Remember multi-tenancy - always filter by `user_id`

## Debugging Tips

- **Backend not starting:** Check `OPENAI_API_KEY` in `.env`
- **No documents returned:** Verify `user_id` matches between upload and query
- **Import errors:** Run `poetry install` in backend directory
- **Tests failing:** Check mocked fixtures in `backend/tests/conftest.py`
- **Frontend build errors:** Delete `.next` folder and rebuild

## References

- Full docs: GitHub Wiki (link in README.md)
- Conversation memory: `CONVERSATION_MEMORY.md`
- Use case system: `USE_CASE_GUIDE.md`
- Testing checklist: `TESTING_CHECKLIST.md`
- Makefile: `make help` for all available commands
