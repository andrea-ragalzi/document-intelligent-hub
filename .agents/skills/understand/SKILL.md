---
name: understand
description: Explain a recent implementation or diff and test the developer's understanding without modifying code. Explicit invocation only.
disable-model-invocation: true
---

Read-only learning phase.

Follow `AGENTS.md` and the instructions for the relevant area. Do not modify files, spawn agents, or start another phase automatically.

Start from the implementation, diff, feature, or files identified by the developer.

Explain concretely:

- the problem being solved;
- the entry point;
- the main call path;
- important inputs and outputs;
- state changes and side effects;
- key invariants;
- failure modes;
- tests that demonstrate the behavior;
- important design decisions;
- what remains uncertain.

Keep the explanation limited to the relevant implementation rather than teaching the whole repository.

Clearly distinguish behavior demonstrated by code/tests from assumptions or inferred intent.

End with 3–5 short questions that test whether the developer understands the behavior and can safely modify it.

Do not answer those questions immediately.

Wait for the developer's answers.
