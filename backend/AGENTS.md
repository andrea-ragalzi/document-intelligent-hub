# Backend instructions

The backend is a FastAPI application using pragmatic ports-and-adapters architecture.

Preserve the existing architecture:

* `routers/`: HTTP/API concerns only;
* `services/`: application logic and workflow orchestration;
* `ports/`: abstractions required by application logic;
* `repositories/`: storage-oriented operations;
* `infrastructure/`: concrete external/provider implementations;
* `schemas/`: API/application data contracts;
* `dependencies.py`: composition root and dependency wiring.

`core/` owns configuration, logging and HTTP authentication/security helpers;
`db/chroma_client.py` owns Chroma/embedding lifecycle. These are not a generic domain
layer. Reuse `schemas/` contracts and existing ports (including LangChain `Document`)
rather than introducing parallel models. Services may use existing parsing/ranking
libraries; do not invent a universal infrastructure wrapper for every library.

Keep business logic out of routers.

Keep FastAPI/HTTP concerns out of services.

Keep provider-specific details such as Firebase, ChromaDB, LLM SDKs, and external APIs out of application logic when an existing port or infrastructure boundary applies.

Construct concrete dependencies in the composition root rather than inside services.

Inject `VectorStorePort`, file-storage, usage and translation contracts where present.
Do not reach through them to Chroma/Firestore or import routers/dependencies into services.
HTTP status/response mapping belongs in routers; reuse `core.auth` dependencies and
`core.logging.logger`. Preserve exception propagation/fallback semantics, tenant filters
and redacted logging; never log tokens, document content or raw provider errors.

Legacy exceptions are not precedents: `tier_limit_service` and
`demo_document_state_service` still touch Firebase; translation/email/file-storage/usage
service modules retain compatibility re-exports. Existing auth/document routers also
contain provider operations. Do not extend those leaks or remove compatibility APIs
without checking callers. The exact service import exceptions are tested in
`tests/test_architecture_boundaries.py`.

Do not create ports, repositories, or abstractions merely for symmetry. They must protect a real responsibility or boundary.

Use explicit Python typing and preserve the repository's strict MyPy expectations.

## Testing

Use pytest and TDD for backend behavior changes.

For bugs, first create the smallest deterministic regression test that reproduces the failure.

Mock/fake true external boundaries, not the application logic under test.

Run focused tests first; final completion requires root `make quality` even for test-only
changes. `make quality-backend` is the backend subset, not a completion substitute.
The canonical MyPy configuration is explicitly `mypy.ini` (the existing CI behavior).

Run backend verification through `poetry run` with `backend/` as the working directory.

## RAG

For RAG failures, identify the first failing stage before changing architecture:

1. parsing/source evidence;
2. retrieval;
3. ranking/reranking;
4. context selection;
5. model context;
6. generation;
7. citations/grounding.

Do not introduce a new retrieval, chunking, ranking, model, or prompt architecture before the failing stage is demonstrated.

Prefer the smallest experiment that can confirm or falsify the diagnosis.

Update backend documentation when API behavior, architecture, configuration, environment variables, or RAG behavior changes.
