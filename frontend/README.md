# Frontend

The frontend is a Next.js 16 client for authentication, document management, chat, conversation management, and client-side UI state. It uses Firebase Web SDK for identity and Firestore conversations, and calls the FastAPI backend for document and RAG operations.

## Responsibilities

- Render login, registration, protected dashboard, document upload/list/delete, and chat interfaces.
- Keep Firebase authentication state and pass the current user's ID token to protected API calls.
- Manage the active chat, saved conversations, language selection, usage/tier display, and UI feedback.
- Coordinate browser-side calls to the FastAPI API and persist conversations through Firestore.

## Architecture

- `app/` contains Next.js routes and the server-side `/api/chat` adapter. The dashboard composes the main client workflows.
- `components/` contains UI components for authentication, documents, chat, sidebars, modals, and status messages.
- `hooks/` contains client workflows such as document operations, authentication-derived data, chat, server status, and usage/tier queries.
- `lib/` contains Firebase initialization, API constants, Firestore conversation functions, shared types, and language metadata.
- `contexts/AuthContext.tsx` provides the authenticated Firebase user and ID-token accessor.
- `stores/uiStore.ts` contains shared UI state such as the current conversation, modal visibility, save status, and server status.
- `providers/QueryProvider.tsx` configures TanStack Query for cached server state.
- `test/` contains Vitest and React Testing Library tests.

## Backend Communication

The backend base URL is defined by `NEXT_PUBLIC_API_BASE_URL` and consumed as `API_BASE_URL` in `lib/constants.ts`. It should include the `/rag` path used by the FastAPI RAG router. Direct calls are implemented in hooks and small API helpers:

| Frontend path                | Backend interaction                                                                      |
| ---------------------------- | ---------------------------------------------------------------------------------------- |
| `hooks/useDocumentStatus.ts` | Check whether the user has indexed documents (`/rag/documents/check`)                    |
| `hooks/useDocuments.ts`      | List and delete one/all user documents (`/rag/documents/list`, `/delete`, `/delete-all`) |
| `hooks/useDocumentUpload.ts` | Upload and index a PDF (`/rag/upload/`)                                                  |
| `hooks/useQueryUsage.ts`     | Read authenticated usage and tier data (`/auth/usage`)                                   |
| `hooks/useRegistration.ts`   | Register a Firebase user and refresh custom claims (`/auth/register`)                    |
| `lib/languages.ts`           | Load supported languages (`/rag/languages/`)                                             |
| `app/api/chat/route.ts`      | Forward the active chat query to `/rag/query/`                                           |

Protected hooks call `useAuth().getIdToken()` and attach `Authorization: Bearer <token>`. The Next.js chat route receives the same authorization header from `useChatAI`, converts the AI SDK message list to the backend's `conversation_history` shape, and forwards it to FastAPI. Registration is a special case: it sends the Firebase ID token in the `/auth/register` request body and then forces a token refresh.

Most document and usage requests run directly from the browser. Therefore, `localhost` refers to the device running the browser; when testing from a tablet or phone, set `NEXT_PUBLIC_API_BASE_URL` to a backend address reachable on the LAN.

## Authentication

- `lib/firebase.ts` lazily initializes Firebase Auth and Firestore from the `NEXT_PUBLIC_FIREBASE_*` configuration.
- `contexts/AuthContext.tsx` listens with `onAuthStateChanged`, exposes the current `User`, and provides email/password sign-in, email/password sign-up, Google sign-in, logout, and `getIdToken()`.
- `components/ProtectedRoute.tsx` guards the dashboard until authentication is ready.
- `hooks/useUserTier.ts` reads the Firebase `tier` custom claim with `getIdTokenResult()`. `hooks/useRegistration.ts` forces a token refresh after backend registration so a newly assigned claim is available to the client.

## Conversations

Conversations are stored in the Firestore `conversations` collection by `lib/conversationsService.ts`. The service creates, loads, updates, renames, and deletes conversation documents and filters loads by `userId`. Firestore rules also require an authenticated non-anonymous owner for conversation access.

The active dashboard uses `hooks/queries/useConversationsQuery.ts` with TanStack Query. `app/dashboard/page.tsx` loads a selected conversation into the AI SDK message state and automatically saves completed chat history, creating a conversation when needed or updating the current one. `app/api/chat/route.ts` sends previous messages (excluding the current question) to FastAPI as `conversation_history`.

`hooks/useConversations.ts` and the `rag_conversations` local-storage key provide the older fallback/migration path. Firestore remains the primary store in the active dashboard flow.

## State Management

- **TanStack Query:** caches Firestore conversation lists/mutations and backend usage data. `providers/QueryProvider.tsx` sets shared stale time, retry, and garbage-collection defaults.
- **Zustand:** `stores/uiStore.ts` holds cross-component UI state, including the current conversation ID, save progress, modal state, alerts, and server-online state.
- **React context and local state:** `AuthContext` owns Firebase session state; `useChatAI` owns the active AI SDK messages/input; components and hooks use React state for local forms, upload progress, and transient UI state.

## Configuration

Create the ignored `frontend/.env.development.local` from the tracked `frontend/.env.example`. It must contain only the dedicated DEV Firebase Web app configuration; Vercel owns the independent production values.

| Variable                                   | Controls                                                            |
| ------------------------------------------ | ------------------------------------------------------------------- |
| `NEXT_PUBLIC_API_BASE_URL`                 | FastAPI base URL used by browser hooks and the Next.js chat adapter |
| `NEXT_PUBLIC_FIREBASE_API_KEY`             | Firebase Web SDK project configuration                              |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`         | Firebase Auth domain                                                |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID`          | Firebase project identifier                                         |
| `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET`      | Firebase storage bucket configuration                               |
| `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | Firebase messaging sender configuration                             |
| `NEXT_PUBLIC_FIREBASE_APP_ID`              | Firebase Web app identifier                                         |

These `NEXT_PUBLIC_*` values are client-side configuration and are bundled by Next.js; do not place backend secrets in the frontend environment file.

Publish the tracked `firestore.rules` in the Firebase project before testing conversation persistence; the rules restrict conversation access to the authenticated owner.

## Running Locally

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:3000` unless a different port is supplied. For example, `npm run dev -- --port 3010` starts the development server on port 3010. The backend must be running at the configured API URL; see the [backend handbook](../backend/README.md) for its Poetry setup.

## Testing

The frontend tests use Vitest with a `jsdom` environment and React Testing Library:

```bash
cd frontend
npm run test:run
npm run test:coverage
```

Firebase Auth lifecycle coverage runs only through the local emulator and never against DEV or
production Firebase:

```bash
npm run test:firebase-auth-emulator
```

The command uses the isolated `demo-dih-auth` project and refuses to run when the Auth Emulator
is not configured.

Tests are under `test/`. The commands above document the available workflows; they do not claim that the current suite passes in every environment.

## Important Code Paths

| Path                                                  | Purpose                                                                               |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `app/dashboard/page.tsx`                              | Composes authenticated dashboard, documents, chat, conversations, usage, and UI state |
| `contexts/AuthContext.tsx`                            | Firebase session listener and ID-token access                                         |
| `lib/firebase.ts`                                     | Lazy Firebase Auth/Firestore initialization                                           |
| `lib/constants.ts`                                    | Backend API base URL and conversation storage key                                     |
| `hooks/useDocuments.ts`, `hooks/useDocumentUpload.ts` | Document list/delete and PDF upload flows                                             |
| `hooks/useChatAI.ts`                                  | Active chat state and AI SDK request setup                                            |
| `app/api/chat/route.ts`                               | Server-side adapter from AI SDK messages to FastAPI `/rag/query/`                     |
| `lib/conversationsService.ts`                         | Firestore conversation CRUD and local-storage migration helpers                       |
| `hooks/queries/useConversationsQuery.ts`              | Active conversation queries and mutations                                             |
| `stores/uiStore.ts`                                   | Shared UI/conversation save state                                                     |
| `hooks/useQueryUsage.ts`, `hooks/useUserTier.ts`      | Backend usage data and Firebase tier claims                                           |
| `test/`                                               | Vitest component, hook, store, and integration-style tests                            |

## Common Development Gotchas

- Restart the Next.js dev server after changing `frontend/.env.local`; public environment variables are loaded at startup/build time.
- From a tablet or phone, `localhost` points to that device. Use the development machine's LAN address in `NEXT_PUBLIC_API_BASE_URL` and ensure the backend is reachable there.
- The backend must be reachable both for direct browser requests (documents, usage, languages) and for the Next.js chat adapter.
- The FastAPI response is complete before `app/api/chat/route.ts` emits characters with a short delay; this is simulated progressive display, not end-to-end token streaming.
