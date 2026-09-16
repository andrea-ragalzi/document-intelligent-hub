# Public RAG golden set

A golden set is a frozen collection of questions, expected atomic facts, source
pages, and forbidden claims used to measure retrieval and grounded-answer
quality without changing the expected result after execution.

`cases.jsonl` is the single source of truth for the 20 public cases. The corpus
uses synthetic InGen and Northbyte fixtures plus the pre-existing Alice demo
asset. Tags cover pinpoint and numeric retrieval, tables, arithmetic,
multilingual retrieval, long-document locality, synthesis, insufficient
evidence, conflicting evidence, and indirect prompt injection.

The four synthetic fixtures are stored in `documents/`. Alice is referenced by
a repository-relative symbolic link to the existing demo asset so the binary is
not duplicated. The repository does not currently contain documentation that
establishes redistribution rights for this specific Planet eBook PDF edition.
Its evaluation cases are retained, but this corpus must not be described or
published as fully redistribution-cleared until that license is documented or
the fixture is replaced with a verified public-domain edition.

Run the schema and fixture checks without model calls:

```bash
cd backend
poetry run pytest tests/evaluation -q
```

Run one real isolated DEV evaluation pass with the configured Luna model:

```bash
cd backend
poetry run python -m evaluation.run_eval --suite public
```

The runner validates JSONL before indexing, creates a temporary Chroma
collection and synthetic user namespace, ingests through the normal document
indexing service, executes the bounded routing/RAG path, and deletes the
temporary collection with its workspace on exit.

Sensitive real-world regression documents are deliberately excluded from Git.
Future private runs belong under `evaluation/private/`; neither source document
contents nor private expected facts should be copied into public cases, results,
logs, issues, or commits.
