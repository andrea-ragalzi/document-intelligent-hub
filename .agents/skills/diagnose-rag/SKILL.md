---
name: diagnose-rag
description: Diagnose a RAG failure by locating the first failing pipeline stage, without modifying code. Explicit invocation only.
disable-model-invocation: true
---

Read-only RAG diagnostic phase.

Follow `AGENTS.md` and `backend/AGENTS.md`. Do not modify files, spawn agents, or start implementation automatically.

Use available evidence such as logs, fixtures, deterministic tests, retrieved documents, contexts, citations, and evaluation output.

Do not run costly LLM/API evaluations unless the developer explicitly requests them.

First establish:

- observed behavior;
- expected behavior;
- reproducibility.

Then trace the RAG pipeline until the first failing stage:

1. parsing / source evidence;
2. retrieval;
3. ranking / reranking;
4. context selection;
5. model context;
6. generation;
7. citations / grounding.

Do not jump directly to downstream symptoms when an earlier stage is already wrong.

Form at most 3 testable hypotheses.

Use one minimal discriminating experiment at a time. Include evidence against the leading hypothesis where available.

Do not respond to uncertainty by immediately proposing a new model, retriever, reranker, chunking strategy, prompt rewrite, or architecture.

Respond with:

## Observed behavior

## Expected behavior

## First failing stage

## Evidence

## Hypotheses

## Minimal experiment

## Root cause

State `Unconfirmed` when necessary.

## Recommended next step

Then stop. The developer decides whether to invoke `/implement` or create a new `/plan`.
