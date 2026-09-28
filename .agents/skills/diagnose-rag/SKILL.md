---
name: diagnose-rag
description: Diagnose a RAG failure down to the first failing stage, without modifying code. Explicit invocation only.
disable-model-invocation: true
---

Read-only phase. Follow `AGENTS.md` and especially `backend/AGENTS.md`. Do not spawn agents, use MCP, or switch models or tools spontaneously. Do not proceed to `/implement` on your own.

1. Reproduce the issue using available logs, fixtures, or targeted tests. Do not run costly LLM/API evaluations without explicit request. Collect observable evidence and the expected result.
2. Trace the data flow and find the **first** failing stage: (1) parsing/source evidence, (2) retrieval, (3) ranking/reranking, (4) context selection, (5) model context, (6) generation, (7) citations/grounding.
3. Formulate at most 3 testable hypotheses. Propose and, if possible, run **one** minimal experiment at a time to distinguish them. If evidence is insufficient, state what is missing; after two failed attempts, stop and reassess the diagnosis.
4. Name the most likely root cause only when evidence supports it. Do not modify code or immediately propose a new model, chunking, retriever, reranker, complete prompt rewrite, or RAG architecture.

Respond with: `Observed behavior`, `Expected behavior`, `First failing stage`, `Evidence`, `Hypotheses`, `Minimal experiment`, `Root cause`, `Recommended next step`. Then stop so the user can understand and approve the diagnosis before a new `/implement`.
