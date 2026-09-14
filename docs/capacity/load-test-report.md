# Local load-test report

**Evidence scope:** `MEASURED_LOCAL_COMPONENT`. The run used a temporary Chroma directory, synthetic tenant/document data, real `all-MiniLM-L6-v2` CPU embeddings and Chroma similarity search. The final OpenAI answer was replaced with a fixed 80 ms fake. It did **not** measure FastAPI HTTP routing, PDF parsing/chunking, Firestore, provider calls, or Railway. The global two-slot non-queuing guard is `CODE_VERIFIED` by unit tests; `MEASURED_LOCAL_HTTP` remains unavailable.

Command:

```sh
cd backend && poetry run python tests/load/run_local_benchmark.py
```

Raw results: `docs/capacity/artifacts/local-benchmark-20260914T140019Z.{json,csv}`. Host: 20 logical CPUs; process RSS after model load was about 958 MiB.

| Concurrency | Requests | Errors | RPS | p50 | p95 | p99 | max |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 5 | 0 | 11.3 | 88.5 ms | 89.7 ms | 89.7 ms | 89.7 ms |
| 2 | 10 | 0 | 107.4 | 90.7 ms | 93.1 ms | 93.1 ms | 93.1 ms |
| 5 | 25 | 0 | 229.5 | 105.8 ms | 108.2 ms | 109.0 ms | 109.0 ms |
| 10 | 50 | 0 | 356.1 | 134.8 ms | 139.2 ms | 140.4 ms | 140.4 ms |
| 20 | 100 | 0 | 496.5 | 185.0 ms | 196.0 ms | 199.3 ms | 201.4 ms |

Ingestion of 17 synthetic chunks took 177.5 ms and increased isolated Chroma disk use by 315,556 bytes. No HTTP 429, 5xx, or timeout can be reported because this was a direct repository benchmark. The measured maximum is 20 direct retrieval workers; safe hosted capacity is **UNVERIFIED**. The p95 slope from 108 ms at 5 to 196 ms at 20 indicates rising local contention, but no saturation threshold was reached.

The intended near-limit PDF and full FastAPI/Locust workload were not completed in this run. They are required before calling any concurrency level public-demo-safe.
