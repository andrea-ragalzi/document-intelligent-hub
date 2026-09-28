---
name: understand
description: Explain a recently implemented diff or feature and check the user's understanding, without modifying code.
disable-model-invocation: true
---

Read-only phase. Follow `AGENTS.md` and the instructions for the relevant area. Do not spawn agents, use MCP, or switch models or tools spontaneously. Do not modify files.

Starting from the specified diff or feature, explain: the problem it solves, entry point, call path, input and output data, invariants, side effects, failure modes, tests that demonstrate the behavior, and what the user should be able to change independently. Distinguish what the code proves from what remains uncertain. Keep the explanation concrete and limited to the files involved.

Then ask 3–5 short questions to check the user's understanding of the behavior and decisions. **Do not answer the questions immediately** and do not proceed to another phase; wait for the user's answers.
