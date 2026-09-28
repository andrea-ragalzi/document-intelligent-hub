---
name: debug
description: Diagnose a non-RAG bug using evidence and one experiment at a time, without applying fixes. Explicit invocation only.
disable-model-invocation: true
---

Read-only phase. Follow `AGENTS.md` and the instructions for the relevant area. Do not spawn agents, use MCP, or switch models or tools spontaneously. Do not modify files or implement fixes.

Read the traceback, logs, or error; reconstruct the call path and distinguish symptoms from root causes. Formulate at most 3 hypotheses, each with supporting and opposing evidence. Use diagnostics, targeted tests, and the terminal when appropriate; suggest or run **one** discriminating experiment at a time. Do not run costly LLM/API evaluations without explicit request. After two failed attempts at the same problem, stop and reassess the diagnosis.

Report the observed and expected behavior, call path, evidence, hypotheses, experiment, and root cause with its confidence level. Once the root cause is sufficiently demonstrated, stop: the user decides whether to approve it and invoke `/implement`.
