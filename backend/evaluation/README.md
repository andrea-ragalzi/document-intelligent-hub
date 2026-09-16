# Document Intelligent Hub evaluation

The evaluation harness keeps two independent golden suites. The public suite
contains reproducible fixtures intended for GitHub and portfolio use. The
private suite is for local real-world regressions and is ignored in its
entirety by Git. Private filenames, questions, answers, snippets, metadata,
and results must never be copied into tracked files.

Place a safe fixture in `public/documents/` or a local-only fixture in
`private/documents/`. Add one JSON object per case to that suite's
`cases.jsonl`; every case must explicitly list the document it tests. The
runner does not invent cases. Unreferenced documents produce a warning, while
a missing referenced document fails validation before indexing or any model
call.

Both suites use the same strict schema and deterministic scorer. A result
reports independent `answer_pass`, `evidence_pass`, and `security_pass`
dimensions. `overall_pass` is their conjunction. Security is marked
not-applicable when a case has no forbidden security markers.

Run a suite from the backend directory:

```bash
poetry run python -m evaluation.run_eval --suite public
poetry run python -m evaluation.run_eval --suite private
poetry run python -m evaluation.run_eval --suite all
```

Each run uses a temporary Chroma collection and synthetic user namespace. The
machine-readable report is written to `results/runs/` for public runs or
`private/results/runs/` for private runs. Public runs append to
`results/RESULTS.md` and `results/history.csv`; private runs append only to
`private/RESULTS.md` and `private/results/history.csv`. Markdown history is
generated from the JSON report and never overwrites earlier runs.

Use `--suite all` to execute the suites independently. The public history then
keeps its complete public case table and adds private and combined summaries
containing aggregate counters only. Private case IDs, questions, answers,
citations, and document details remain exclusively under the ignored
`private/` directory.

The dataset fingerprint hashes case definitions and each referenced fixture's
identity. It changes when cases or fixture bytes change, making score
comparisons explicit rather than implying that a benchmark changed system
quality.

Do not put sensitive real documents in Git or Git LFS. Keep them under the
ignored `private/` tree. The public Alice fixture retains the existing warning:
the repository does not establish redistribution rights for the Planet eBook
edition, so it must not be described as redistribution-cleared without
separate licensing evidence.
