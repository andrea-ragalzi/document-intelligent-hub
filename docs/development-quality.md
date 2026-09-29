# Development quality contract

`make quality` is the completion gate for implementers, independent reviewers and local
developers. It uses the locked Poetry environment in `backend/`, installed npm dependencies
in `frontend/`, Python 3.12+, Node 22 and Make. Install with `make install-backend
install-frontend` first. The gate does not install dependencies, rewrite source, call paid
RAG evaluations or require production credentials. Coverage/build/cache artifacts are normal.
Use `make -k quality` to collect independent area failures after one target fails; a nonzero
result still blocks completion. Never override targets, flags or environments to bypass gates.

## Existing architecture

The backend is pragmatic ports and adapters, not a pure framework-free domain model:
routers handle HTTP/auth/status mapping, services coordinate application workflows, ports
provide application-facing contracts, repositories implement vector operations, and
infrastructure implements storage, translation, email and usage providers. `dependencies.py`
wires concrete dependencies; `core/` and `db/` also contain framework/provider lifecycle
code. Pydantic contracts and LangChain `Document` are intentionally shared. Existing
Firebase-coupled services and compatibility exports are documented in `backend/AGENTS.md`;
import tests freeze their known exceptions instead of reorganizing production code.

The frontend uses Next App Router, presentation components, shared and feature-local hooks,
`lib/` API/Firebase helpers, `AuthContext`, `QueryProvider`, React Query conversation state,
and Zustand UI state. Document/chat custom hooks are established patterns too. There is no
universal API client or requirement to move every request to React Query. Preserve the
server chat adapter, client boundaries, auth-token access, cache invalidation and race guards.

## Gates and ownership

| Target | Checks |
| --- | --- |
| `quality-tooling` | Deterministic size-checker regression tests |
| `quality-backend` | Size, Ruff (app/entrypoint/tests/guardrail Python), strict MyPy using `mypy.ini`, Pylint score >=9 with errors/fatals blocking regardless of score, Lizard CCN <=25 and function NLOC <=200, full non-emulator pytest with XML coverage |
| `quality-frontend` | Size, ESLint-boundary regression tests, zero-warning ESLint (existing complexity <=15), Prettier, strict TypeScript, Vitest with existing coverage thresholds, production build |

`make quality` runs all three. CI calls the same targets in its existing area jobs, without
rerunning the suites or build. Root guardrail/instruction changes trigger both jobs; PRs
against develop and main are checked. Secret-history scanning, Docker build, Auth Emulator,
Codecov upload and release promotion checks remain additional layers. Zed's full-quality
task calls the same command. Focused checks accelerate iteration but never replace it.

Frontend coverage retains its existing scope and thresholds: lines/statements 80%,
functions 90%, branches 85%. Backend coverage is reported; no numeric floor existed, so
none is fabricated here. `mypy.ini` already takes precedence over the older `[tool.mypy]`
section in `pyproject.toml`; the command now selects it explicitly. Do not introduce
another type checker: the old Zed basedpyright task had no locked dependency.
Pylint receives all Python files explicitly: directory discovery omitted namespace
subdirectories, and ignoring `__init__.py` previously skipped the application package.

No Sonar properties file or scan action is checked in; the workflow contains a SonarCloud
immutable-action reference comment. Preserve any externally managed Sonar checks as an
additional layer. This gate neither replaces nor claims to configure that integration.
Branch protection and required external statuses are repository-host settings, not enforced
by these files.

## Maintainability limits

`quality/check_size.py` counts physical lines, including comments and blanks, in backend
`app/` plus `main.py`, and frontend `app/components/hooks/lib/contexts/stores/providers`.
It includes new/untracked files. Dependencies, build output, test fixtures, evaluation
artifacts and tooling are outside these production roots; `generated/`, `migrations/`
and `.d.ts` declarations are excluded. Do not put handwritten code in an excluded location.

- Over 400 lines: visible REVIEW notice and explicit ownership/cohesion assessment in review.
- Over 600: failure unless `quality/size-exceptions.json` records an exact path, ceiling
  and concrete justification. Five pre-existing files have frozen no-growth ceilings.
- Removed/renamed files and files reduced to <=600 must lose their stale exceptions.
- Review functions over 100 lines. Lizard fails Python functions over 200 non-comment lines
  or CCN 25; ESLint fails JS/TS functions above complexity 15. Frontend function length
  (including JSX) remains a review concern rather than a reason for mechanical splitting.

When authorized maintenance shrinks an oversized file, lower its ceiling to the new size.
Never regenerate a baseline, widen an exception, compress code or split by line count merely
to pass. Exceptions and suppressions require a configuration-scoped task and reviewer rationale.

## Automated boundaries and limits

Python AST tests recursively reject services importing HTTP, routers, composition root,
persistence adapters and selected provider SDKs except named legacy edges; ports/schemas
cannot import application services or those outer layers. Routers cannot import Chroma/db
or concrete repositories. Relative imports and aliases are resolved; stale exceptions fail.
Existing provider-client construction tests remain. Dynamic imports and indirect wrappers
are not a security sandbox and need review.

ESLint rejects static imports/re-exports from hooks/stores into route/component modules,
from client workflow roots into `app/`, and from API routes into client workflow roots,
covering the repository's `@/` and relative paths. See the
[ESLint rule's static-import scope](https://eslint.org/docs/latest/rules/no-restricted-imports).
Dynamic imports, transitive server/client leaks, fetching hidden inside JSX and correct
business ownership still require review.

Ruff's F rules and zero-warning ESLint catch unused imports/locals; existing Pylint also
reports unused/unreachable code. These do not establish that exported code is reachable.
[Vulture](https://github.com/jendrikseipp/vulture) was considered: framework registration,
protocol methods and compatibility exports need reachability/allowlist review; its high
confidence mode mostly overlaps existing local checks.
[Knip](https://knip.dev/) would add unused-export/file/dependency reachability analysis,
but introduces another tool and entrypoint/ignore policy. Neither is added in this bounded
change. A dedicated audited cleanup can adopt one if its findings justify that cost; do not
silently whitelist all findings. Unused public APIs, superseded hooks, duplicate logic and
unnecessary dependencies remain explicit reviewer responsibilities.

## Initial validation debt

The newly activated frontend coverage gate exposes existing debt (253 tests pass):
lines 74.23% versus 80%, statements 72.23% versus 80%, functions 63.33% versus 90%,
branches 63.33% versus 85%. These thresholds and their scope are unchanged. The gate
intentionally returns nonzero until the debt is addressed; do not treat a test-only pass
as completion or turn coverage off to get a green build.

In particular, `ConversationList` contains an unused preview helper and selection/bulk-delete
handlers with no reachable selection-entry action. Resolving that requires an explicitly
scoped production cleanup plus tests for uncovered reachable behavior. This workflow change
keeps application source unchanged rather than fabricating coverage of unreachable handlers.

## Additional verification

Changes to Firebase authentication/lifecycle require `cd frontend && npm run
test:firebase-auth-emulator` (Java 21 and local Firebase tooling). Firestore rule changes
require `cd frontend && npm run test:firestore-rules`. Deployment/container changes require
the relevant Docker build. The ordinary gate excludes emulator tests intentionally; no
live Firebase or paid LLM evaluation is a completion prerequisite unless the task requires it.

A reviewer stays read-only, independently inspects the entire diff and executes the gate.
BLOCKER and IMPORTANT findings yield CHANGES_REQUIRED even when tests pass. See root
`AGENTS.md` and `.opencode/commands/review.md` for the checklist and reporting contract.
OpenCode permissions deny edits; they are not an OS sandbox because allowed checks execute
repository code. Inspect changed check scripts before running them. A malicious agent able
to edit checks or instructions cannot be contained by those same repository files.
