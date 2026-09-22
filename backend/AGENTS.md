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

Keep business logic out of routers.

Keep FastAPI/HTTP concerns out of services.

Keep provider-specific details such as Firebase, ChromaDB, LLM SDKs, and external APIs out of application logic when an existing port or infrastructure boundary applies.

Construct concrete dependencies in the composition root rather than inside services.

Do not create ports, repositories, or abstractions merely for symmetry. They must protect a real responsibility or boundary.

Use explicit Python typing and preserve the repository's strict MyPy expectations.

## Testing

Use pytest and TDD for backend behavior changes.

For bugs, first create the smallest deterministic regression test that reproduces the failure.

Mock/fake true external boundaries, not the application logic under test.

Run focused tests first, then the relevant regression suite, Ruff, and MyPy.

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
