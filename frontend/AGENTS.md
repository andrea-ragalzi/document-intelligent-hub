# Frontend instructions

The frontend uses Next.js, React, and TypeScript.

Before changing Next.js-specific behavior, read the relevant documentation for the installed version in:

`node_modules/next/dist/docs/`

Treat those docs as the source of truth for routing, rendering, Server/Client Components, caching, data fetching, Route Handlers, and other Next.js behavior.

Preserve the existing structure:

- `app/`: routes, pages, layouts, and Next.js framework boundaries;
- `components/`: presentation and reusable UI;
- `hooks/`: reusable client workflows and stateful behavior;
- `lib/`: shared technical infrastructure and API/Firebase utilities;
- `contexts/`: contextual dependencies such as authentication;
- `stores/`: genuinely shared application/UI state.
- `providers/`: shared provider lifecycle (`QueryProvider`).

Feature-local helpers and hooks may stay beside their component, as in `DocumentModal/`
and `BugReportModal/`; reuse them before adding a parallel top-level abstraction.
Conversation server state uses `hooks/queries/useConversationsQuery.ts`, its query keys,
optimistic rollback/invalidation and `lib/conversationsService.ts`. Zustand `uiStore`
owns UI/save state, not another conversation cache. Document/chat workflows already use
custom hooks; do not migrate them to a new fetching architecture as incidental cleanup.

Use `AuthContext` token access, `lib/firebase.ts` initialization, existing `lib/*Service`
and `documentApi` helpers, and `API_BASE_URL`. Preserve account cache cleanup and stale
response guards. Shared types belong in `lib/types.ts` where applicable; preserve strict
TypeScript, use `unknown` with narrowing instead of new untyped escape hatches.

Keep components focused on presentation and interaction.

Do not put substantial API orchestration or reusable business logic directly in components.

Keep hooks focused on one workflow or responsibility.

Prefer local or derived state over new global state. Do not duplicate server state unnecessarily in stores.

Keep Client Component boundaries as narrow as practical.

`app/api/chat/route.ts` is the server adapter to FastAPI, not a second RAG implementation.
Keep server route modules out of client hooks/components and client hooks/UI out of API
routes. Preserve intentional `use client` boundaries and server-safe initialization.

For async workflows, handle stale responses, overlapping requests, loading, and failures deliberately. Late obsolete responses must not overwrite newer state.

## Testing

Use Vitest and React Testing Library with TDD for frontend behavior changes.

Test observable user behavior and state transitions rather than implementation details.

Add regression tests for confirmed async/race-condition bugs.

Final completion requires root `make quality`. `make quality-frontend` runs the frontend
subset: zero-warning ESLint, Prettier, TypeScript, Vitest with existing coverage thresholds,
size checks and the production build. Do not replace it with a passing focused test.

Update frontend documentation when setup, architecture, authentication, API integration, configuration, or important workflows change.
