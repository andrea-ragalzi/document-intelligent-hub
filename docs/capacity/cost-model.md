# Cost model — local audit

`USER_DECLARED`: production uses paid OpenAI `gpt-5.6-luna`; local embeddings are CPU-hosted and add no OpenAI embedding charge. `PROVIDER_DOCUMENTED` on 2026-09-14: OpenAI model documentation lists $0.20/input MTok and $1.20/output MTok for `gpt-5.6-luna`. Cached-input and long-context pricing were not independently verified, so all estimates conservatively charge every input token at the full input rate.

Formula: `cost = (input_tokens × 0.20 + output_tokens × 1.20) / 1,000,000` USD. Actual token use is `UNVERIFIED`; no key was supplied and no live provider call was made.

| Scenario | Assumed tokens (in/out) | Cost | Evidence |
|---|---:|---:|---|
| Typical RAG query | 3,000 / 500 | $0.00120 | CALCULATED |
| High-context query | 12,000 / 1,000 | $0.00360 | CALCULATED |
| Typical 5-query session | 15,000 / 2,500 | $0.00600 | CALCULATED |
| 10 users × 5 queries | 150,000 / 25,000 | $0.060 | CALCULATED |
| 50 users × 5 queries | 750,000 / 125,000 | $0.300 | CALCULATED |
| 100 users × 5 queries | 1,500,000 / 250,000 | $0.600 | CALCULATED |
| 500 users × 5 queries | 7,500,000 / 1,250,000 | $3.00 | CALCULATED |

Document ingestion OpenAI cost is $0 under the current code path because embeddings are local. PDF parsing/compute and Railway volume costs are `UNVERIFIED`. Firebase/Firestore, Railway, Vercel, and Resend are `USER_DECLARED` free-tier intended; exact quotas and baseline infrastructure cost are `UNVERIFIED`.
