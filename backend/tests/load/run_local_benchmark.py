"""Isolated local capacity probe; never connects to production services."""
import concurrent.futures
import csv
import json
import os
import shutil
import statistics
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil
from langchain_core.documents import Document

ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = ROOT / "docs/capacity/artifacts"


def percentile(values, point):
    values = sorted(values)
    return values[max(0, min(len(values) - 1, round((len(values)-1) * point / 100)))]


def main():
    # Import after setting an isolated persistence path, before application singletons.
    run_dir = Path(tempfile.mkdtemp(prefix="dih-capacity-"))
    os.environ["CHROMA_DB_PATH"] = str(run_dir / "chroma")
    os.environ["DOCUMENT_STORAGE_PATH"] = str(run_dir / "originals")
    from app.db.chroma_client import get_chroma_client, get_embedding_function
    from app.db.chroma_client import COLLECTION_NAME
    from langchain_chroma import Chroma
    from app.repositories.vector_store_repository import VectorStoreRepository

    started = time.perf_counter()
    embeddings = get_embedding_function()
    client = get_chroma_client()
    collection = client.get_or_create_collection(COLLECTION_NAME)
    store = Chroma(client=client, collection_name=COLLECTION_NAME, embedding_function=embeddings)
    repository = VectorStoreRepository(store, collection)
    tenant = "capacity-synthetic-user"
    # Same fixed-size path as non-structural documents: 512 chars with 50 overlap.
    text = ("Synthetic capacity document: renewal terms, access controls, and retention policy. " * 90)
    chunks = [Document(page_content=text[i:i+512], metadata={"source": tenant, "original_filename": "synthetic.pdf", "original_language_code": "en", "chunk_index": n, "uploaded_at": 0}) for n, i in enumerate(range(0, len(text), 462))]
    before = sum(path.stat().st_size for path in run_dir.rglob("*") if path.is_file())
    ingest_start = time.perf_counter(); repository.add_documents(chunks); ingest_ms = (time.perf_counter()-ingest_start)*1000
    after = sum(path.stat().st_size for path in run_dir.rglob("*") if path.is_file())
    process = psutil.Process()
    rows=[]
    # Fake billable response is deliberately 80ms. Retrieval and CPU embeddings remain real.
    def query(_: int):
        started_query=time.perf_counter()
        docs=repository.similarity_search("What is the retention policy?", tenant, k=3)
        time.sleep(.08)
        return (time.perf_counter()-started_query)*1000, len(docs)
    for concurrency in (1,2,5,10,20):
        latencies=[]; errors=0; cpu_before=process.cpu_times(); rss_before=process.memory_info().rss
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures=[executor.submit(query, i) for i in range(concurrency*5)]
            for future in futures:
                try: latencies.append(future.result(timeout=30)[0])
                except Exception: errors += 1
        elapsed=sum(latencies)/1000 if concurrency == 1 else max(latencies)/1000
        rows.append({"concurrency":concurrency,"requests":concurrency*5,"successes":len(latencies),"errors":errors,"error_rate":errors/(concurrency*5),"rps":len(latencies)/elapsed if elapsed else 0,"min_ms":min(latencies),"p50_ms":percentile(latencies,50),"p95_ms":percentile(latencies,95),"p99_ms":percentile(latencies,99),"max_ms":max(latencies),"rss_before":rss_before,"rss_after":process.memory_info().rss,"cpu_seconds":(process.cpu_times().user-cpu_before.user)+(process.cpu_times().system-cpu_before.system)})
    result={"run_at":datetime.now(timezone.utc).isoformat(),"scope":"MEASURED_LOCAL: isolated direct repository/retrieval benchmark; OpenAI final-answer stage mocked at 80ms. It does not measure HTTP routing, Firestore, PDF parser, Railway, or OpenAI.","machine":{"cpu_count":psutil.cpu_count(),"rss_bytes":process.memory_info().rss},"ingestion":{"chunks":len(chunks),"text_chars":len(text),"elapsed_ms":ingest_ms,"storage_before_bytes":before,"storage_after_bytes":after,"storage_delta_bytes":after-before},"levels":rows,"elapsed_seconds":time.perf_counter()-started}
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS/f"local-benchmark-{stamp}.json").write_text(json.dumps(result,indent=2))
    with (ARTIFACTS/f"local-benchmark-{stamp}.csv").open("w",newline="") as file:
        writer=csv.DictWriter(file,fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    print(json.dumps({"artifact":str(ARTIFACTS/f"local-benchmark-{stamp}.json"),"result":result},indent=2))
    shutil.rmtree(run_dir)

if __name__ == "__main__": main()
