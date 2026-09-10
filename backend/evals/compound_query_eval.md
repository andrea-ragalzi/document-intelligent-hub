# Compound-query comparison set

This is an optional manual evaluation set. Run the same prompts against the
baseline and compound-query branches, recording answer coverage, source
relevance, unsupported claims, latency, LLM calls, input tokens, and final
context chunk count.

| Group | Queries |
| --- | --- |
| Simple (5) | Who is Alice?; What happens when the Cat disappears?; Who is Dennis Nedry?; Chi è Alan Grant?; ¿Quién es Alice? |
| Compound (5) | Who is Alice and what happens when the Cat disappears?; What does Alice ask the Cat and how does he answer?; Who is Dennis Nedry and was he authorized?; Chi è Alice e cosa fa il Gatto?; ¿Quién es Alice y qué ocurre con el Gato? |
| Compare (3) | Compare Alice before and after the Cat disappears.; What differs between Dennis Nedry's access and authorization?; Confronta la reazione di Alice prima e dopo la scomparsa del Gatto. |
| Ambiguous/false positive (2) | Explain the relationship between Alice and the Cat.; And him? |

Expected invariant: simple queries use the existing single-query path and all
answers use one final generation call. Compound queries may use two retrieval
queries, one reranking pass, and one final generation call. Retrieval changes
must improve coverage without changing grounding or response-language rules.
