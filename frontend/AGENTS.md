# Frontend instructions

The frontend uses Next.js, React, and TypeScript.

Before changing Next.js-specific behavior, read the relevant documentation for the installed version in:

`node_modules/next/dist/docs/`

Treat those docs as the source of truth for routing, rendering, Server/Client Components, caching, data fetching, Route Handlers, and other Next.js behavior.

Preserve the existing structure:

* `app/`: routes, pages, layouts, and Next.js framework boundaries;
* `components/`: presentation and reusable UI;
* `hooks/`: reusable client workflows and stateful behavior;
* `lib/`: shared technical infrastructure and API/Firebase utilities;
* `contexts/`: contextual dependencies such as authentication;
* `stores/`: genuinely shared application/UI state.

Keep components focused on presentation and interaction.

Do not put substantial API orchestration or reusable business logic directly in components.

Keep hooks focused on one workflow or responsibility.

Prefer local or derived state over new global state. Do not duplicate server state unnecessarily in stores.

Keep Client Component boundaries as narrow as practical.

For async workflows, handle stale responses, overlapping requests, loading, and failures deliberately. Late obsolete responses must not overwrite newer state.

## Testing

Use Vitest and React Testing Library with TDD for frontend behavior changes.

Test observable user behavior and state transitions rather than implementation details.

Add regression tests for confirmed async/race-condition bugs.

Before finishing, run as appropriate:

`npm run test:run`
`npm run lint`
`npm run format:check`
`npm run type-check`

Run `npm run build` for significant frontend changes.

Update frontend documentation when setup, architecture, authentication, API integration, configuration, or important workflows change.
