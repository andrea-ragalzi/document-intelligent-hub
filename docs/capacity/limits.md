# Capacity limits — local audit

| Resource | Current enforced application limit | Provider/deployment limit | Observed usage | Risk | Recommended public-demo limit | Evidence/source |
|---|---:|---|---|---|---:|---|
| Query text | 3–1,000 characters | UNVERIFIED | Not load-tested at maximum | bounded | retain | CODE_VERIFIED `QueryConstants` |
| Query history | 14 messages; 2,000 chars/message; 12,000 chars total | Firestore rule permits 100 stored messages/document | UNVERIFIED under full route | stored history can reach Firestore document-size limit | 14 sent; 20 stored messages | CODE_VERIFIED constants/rules; PROPOSED stored cap |
| Files/user | Firestore tier config; fallback FREE=5, PRO=50, UNLIMITED has no product limit | UNVERIFIED | UNVERIFIED | remote config may differ | tier-specific | CODE_VERIFIED fallback; PROPOSED |
| File size | Firestore tier config; fallback FREE=10 MB, PRO=50 MB, UNLIMITED has no product limit | UNVERIFIED | UNVERIFIED | provider and storage capacity still apply | tier-specific | CODE_VERIFIED tier service; PROPOSED |
| Extracted text | 500,000 chars/document | UNVERIFIED | UNVERIFIED | parser path unmeasured | retain | CODE_VERIFIED |
| Chunks/document | 500 | Chroma local volume unbounded in app | 17 chunks used 315,556 B additional disk | storage grows without global quota | 300 chunks | MEASURED_LOCAL artifact; PROPOSED |
| Expensive operations | 1/request type/user plus 2 global process slots | no hosted guard | HTTP benchmark UNVERIFIED | no queue; controlled 429 at capacity | 2 global RAG/uploads | CODE_VERIFIED |
| Daily queries | fallback FREE=20, PRO=500, UNLIMITED=500 | UNVERIFIED | UNVERIFIED | remote tier config controls cost | 20/day | CODE_VERIFIED; PROPOSED |
| Chroma storage | NO_LIMIT_FOUND global/user | Railway volume UNVERIFIED | existing local store not inspected | persistent volume exhaustion | 100 MB/user | PROPOSED |
| Firebase/Firestore | USER_DECLARED free tier intended | exact quotas UNVERIFIED | UNVERIFIED | reads/writes and document-size cap | monitor before public launch | USER_DECLARED |
| Railway/Vercel/Resend | USER_DECLARED free/current demo tiers intended | exact plan resources/quotas UNVERIFIED | no hosted test | availability/egress/email quota | verify before publication | USER_DECLARED |
