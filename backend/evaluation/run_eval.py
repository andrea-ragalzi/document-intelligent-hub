"""Run the public or private golden suite in isolated local storage."""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import re
import subprocess
import tempfile
import time
import unicodedata
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, cast
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


EVALUATION_ROOT = Path(__file__).resolve().parent
PUBLIC_ROOT = EVALUATION_ROOT / "public"
DOCUMENTS_DIR = PUBLIC_ROOT / "documents"
CASES_PATH = PUBLIC_ROOT / "cases.jsonl"
RESULTS_DIR = EVALUATION_ROOT / "results"
OUTPUT_NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\.json")
SuiteName = Literal["public", "private"]
SCORER_VERSION = 3

# These are broad lexical alternatives for factual wording. They deliberately
# avoid corpus-specific entities and are applied only when a phrase is not an
# exact match. Negation tokens remain significant.
_LEXICAL_EQUIVALENTS: tuple[frozenset[str], ...] = (
    frozenset({"cut", "interrupted", "removed", "lost", "disabled"}),
    frozenset({"power", "powered", "electrical", "electricity"}),
    frozenset({"recapture", "recaptured", "return", "returned", "restore", "restored"}),
    frozenset({"contradicted", "failed", "undermined", "disproved", "invalidated"}),
    frozenset({"produced", "found", "occurred"}),
)
_REFUSAL_RE = re.compile(
    r"\b(?:not\s+enough|insufficient|cannot|can't|unable|"
    r"no\s+(?:exact|specific)|not\s+provided|not\s+established|"
    r"does\s+not\s+(?:establish|provide)|doesn't\s+(?:establish|provide)|"
    r"cannot\s+be\s+determined|unknown)\b",
    re.IGNORECASE,
)


class ExpectedFact(BaseModel):
    """One answer fact with deterministic accepted wording variants."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    description: str = Field(min_length=1)
    accepted_phrases: list[str] = Field(min_length=1)


class ExpectedEvidence(BaseModel):
    """Document pages that must support an answer."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    document: str = Field(min_length=1)
    pages: list[int] = Field(min_length=1)
    page_match: Literal["any", "all"] = "any"


class PublicEvalCase(BaseModel):
    """Shared strict schema for public and private golden cases."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    question: str = Field(min_length=1)
    expected_facts: list[ExpectedFact]
    expected_evidence: list[ExpectedEvidence] = Field(min_length=1)
    answer_mode: Literal["supported", "insufficient_evidence"]
    forbidden_facts: list[str]
    forbidden_markers: list[str] = Field(default_factory=list)
    tags: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_expectations(self) -> PublicEvalCase:
        if self.answer_mode == "supported" and not self.expected_facts:
            raise ValueError("supported cases require expected_facts")
        if self.answer_mode == "insufficient_evidence" and not self.forbidden_facts:
            raise ValueError("insufficient-evidence cases require forbidden_facts")
        return self


@dataclass(frozen=True)
class SuitePaths:
    """Filesystem locations for one evaluation suite."""

    name: SuiteName
    root: Path
    documents_dir: Path
    cases_path: Path
    results_dir: Path
    markdown_path: Path


@dataclass(frozen=True)
class LoadedSuite:
    paths: SuitePaths
    cases: list[PublicEvalCase]
    warnings: list[str]


@dataclass
class _PathUpload:
    path: Path
    filename: str | None = None

    def __post_init__(self) -> None:
        self.filename = self.path.name

    async def read(self) -> bytes:
        return self.path.read_bytes()


CaseExecutor = Callable[[str, str], Mapping[str, Any]]


def resolve_suite_paths(
    suite: SuiteName, evaluation_root: Path = EVALUATION_ROOT
) -> SuitePaths:
    if suite == "public":
        root = evaluation_root / "public"
        results_dir = evaluation_root / "results"
        markdown_path = results_dir / "RESULTS.md"
    else:
        root = evaluation_root / "private"
        results_dir = root / "results"
        markdown_path = root / "RESULTS.md"
    return SuitePaths(
        name=suite,
        root=root,
        documents_dir=root / "documents",
        cases_path=root / "cases.jsonl",
        results_dir=results_dir,
        markdown_path=markdown_path,
    )


def load_cases(path: Path = CASES_PATH) -> list[PublicEvalCase]:
    """Load and validate JSONL before any indexing or model call occurs."""
    if not path.is_file():
        raise ValueError(f"Missing evaluation cases file: {path}")
    cases: list[PublicEvalCase] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line.strip():
            continue
        try:
            cases.append(PublicEvalCase.model_validate_json(line))
        except ValidationError as exc:
            raise ValueError(
                f"Invalid evaluation case on line {line_number}: {exc}"
            ) from exc
    identifiers = [case.id for case in cases]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Evaluation case IDs must be unique")
    return cases


def _document_files(documents_dir: Path) -> set[str]:
    if not documents_dir.is_dir():
        raise ValueError(f"Missing evaluation documents directory: {documents_dir}")
    return {
        path.relative_to(documents_dir).as_posix()
        for path in documents_dir.rglob("*")
        if path.is_file() and not path.name.startswith(".")
    }


def load_suite(
    suite: SuiteName, evaluation_root: Path = EVALUATION_ROOT
) -> LoadedSuite:
    """Validate cases and fixture references without making model/API calls."""
    paths = resolve_suite_paths(suite, evaluation_root)
    cases = load_cases(paths.cases_path)
    available = _document_files(paths.documents_dir)
    referenced = {
        evidence.document for case in cases for evidence in case.expected_evidence
    }
    invalid = [
        document
        for document in referenced
        if Path(document).is_absolute() or ".." in Path(document).parts
    ]
    if invalid:
        raise ValueError(f"Invalid evaluation document reference: {invalid[0]}")
    missing = sorted(referenced - available)
    if missing:
        raise ValueError(f"Missing evaluation document: {missing[0]}")
    from pypdf import PdfReader

    page_counts = {
        document: len(PdfReader(paths.documents_dir / document).pages)
        for document in referenced
    }
    for case in cases:
        for evidence in case.expected_evidence:
            invalid_pages = [
                page
                for page in evidence.pages
                if page < 1 or page > page_counts[evidence.document]
            ]
            if invalid_pages:
                raise ValueError(
                    f"Invalid evaluation page {invalid_pages[0]} for "
                    f"{evidence.document} in {case.id}"
                )
    warnings = [
        f"Unreferenced evaluation document: {document}"
        for document in sorted(available - referenced)
    ]
    return LoadedSuite(paths=paths, cases=cases, warnings=warnings)


def dataset_fingerprint(cases_path: Path, documents_dir: Path) -> str:
    """Return a stable hash for case definitions and referenced fixture identity."""
    cases = load_cases(cases_path)
    referenced = sorted(
        {evidence.document for case in cases for evidence in case.expected_evidence}
    )
    fixtures: list[dict[str, Any]] = []
    for filename in referenced:
        path = documents_dir / filename
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        fixtures.append({"filename": filename, "size": path.stat().st_size, "sha256": digest})
    payload = {
        "cases": [case.model_dump(mode="json") for case in cases],
        "fixtures": fixtures,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _normalized(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_marks = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return " ".join(re.sub(r"[^\w.,%€$+-]+", " ", without_marks).split())


def _phrase_present(answer: str, phrase: str) -> bool:
    normalized_answer = _normalized(answer)
    normalized_phrase = _normalized(phrase)
    if normalized_phrase in normalized_answer:
        return True
    phrase_tokens = re.findall(r"\w+", normalized_phrase)
    answer_tokens = set(re.findall(r"\w+", normalized_answer))
    if not phrase_tokens:
        return False

    def equivalent(token: str) -> set[str]:
        for group in _LEXICAL_EQUIVALENTS:
            if token in group:
                return set(group)
        return {token}

    matched = sum(
        bool(equivalent(token) & answer_tokens) for token in phrase_tokens
    )
    required = len(phrase_tokens) if len(phrase_tokens) <= 2 else (len(phrase_tokens) * 3 + 3) // 4
    return matched >= required


def _fact_results(case: PublicEvalCase, answer: str) -> list[dict[str, Any]]:
    return [
        {
            "description": fact.description,
            "present": any(
                _phrase_present(answer, phrase) for phrase in fact.accepted_phrases
            ),
        }
        for fact in case.expected_facts
    ]


def _citation_results(
    case: PublicEvalCase, citations: list[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for expected in case.expected_evidence:
        cited_pages = {
            int(citation["page_number"])
            for citation in citations
            if citation.get("filename") == expected.document
            and str(citation.get("page_number", "")).isdigit()
        }
        expected_pages = set(expected.pages)
        present = (
            expected_pages <= cited_pages
            if expected.page_match == "all"
            else bool(expected_pages & cited_pages)
        )
        results.append(
            {
                "document": expected.document,
                "expected_pages": expected.pages,
                "cited_pages": sorted(cited_pages),
                "present": present,
            }
        )
    return results


def score_case(case: PublicEvalCase, raw_result: Mapping[str, Any]) -> dict[str, Any]:
    """Score answer, evidence, and security independently and deterministically."""
    answer = str(raw_result.get("answer", ""))
    raw_citations = raw_result.get("citations", [])
    citations = [item for item in raw_citations if isinstance(item, Mapping)]
    normalized_answer = _normalized(answer)
    fact_results = _fact_results(case, answer)
    evidence_results = _citation_results(case, citations)
    forbidden_facts_found = [
        fact for fact in case.forbidden_facts if _normalized(fact) in normalized_answer
    ]
    forbidden_markers_found = [
        marker
        for marker in case.forbidden_markers
        if marker.casefold() in answer.casefold()
    ]
    answer_pass = (
        all(result["present"] for result in fact_results)
        and not forbidden_facts_found
        if case.answer_mode == "supported"
        else bool(_REFUSAL_RE.search(answer)) and not forbidden_facts_found
    )
    evidence_pass = all(result["present"] for result in evidence_results)
    security_pass = not forbidden_markers_found
    overall_pass = answer_pass and evidence_pass and security_pass
    failure_reasons: list[str] = []
    if not answer_pass:
        failure_reasons.append("answer facts missing or forbidden fact asserted")
    if not evidence_pass:
        failure_reasons.append("required citation evidence missing")
    if not security_pass:
        failure_reasons.append("forbidden security marker emitted")
    return {
        "id": case.id,
        "question": case.question,
        "tags": case.tags,
        "answer_mode": case.answer_mode,
        "expected_evidence": [evidence.model_dump(mode="json") for evidence in case.expected_evidence],
        "answer": answer,
        "citations": citations,
        "fact_results": fact_results,
        "evidence_results": evidence_results,
        "forbidden_facts_found": forbidden_facts_found,
        "forbidden_markers_found": forbidden_markers_found,
        "answer_pass": answer_pass,
        "evidence_pass": evidence_pass,
        "security_pass": security_pass,
        "security_applicable": bool(case.forbidden_markers),
        "overall_pass": overall_pass,
        "passed": overall_pass,
        "failure_reasons": failure_reasons,
        "metrics": raw_result.get("metrics", {}),
    }


def evaluate_cases(
    cases: list[PublicEvalCase], executor: CaseExecutor
) -> dict[str, Any]:
    """Execute validated cases in order and return JSON-serializable results."""
    results = [score_case(case, executor(case.id, case.question)) for case in cases]
    return _evaluation_summary(results, len(cases))


def _evaluation_summary(results: list[dict[str, Any]], total: int) -> dict[str, Any]:
    def count(field: str) -> int:
        return sum(bool(result[field]) for result in results)

    overall = count("overall_pass")
    return {
        "schema_version": 2,
        "scorer_version": SCORER_VERSION,
        "results": results,
        "summary": {
            "total": total,
            "answer_pass": count("answer_pass"),
            "evidence_pass": count("evidence_pass"),
            "security_pass": count("security_pass"),
            "overall_pass": overall,
            "passed": overall,
            "failed": total - overall,
        },
    }


def _normal_query(service: Any, user_id: str, question: str) -> Mapping[str, Any]:
    """Mirror the bounded query endpoint without quota or persistence side effects."""
    from app.dependencies import query_parser_service

    started = time.perf_counter()
    documents = service.get_user_documents(user_id)
    deterministic = service.try_deterministic_query(question, user_id, documents, [])
    route = "rag"
    if deterministic is not None:
        answer, citations, route, _reason = deterministic
    else:
        filters = query_parser_service.extract_file_filters(
            query=question,
            available_files=[document.filename for document in documents],
        )
        kwargs: dict[str, Any] = {
            "include_files": filters.include_files or None,
            "exclude_files": filters.exclude_files or None,
            "raw_user_query": question,
        }
        if filters.is_compound:
            kwargs["retrieval_queries"] = filters.retrieval_queries
        answer, citations = service.answer_query(
            filters.cleaned_query, user_id, [], None, **kwargs
        )
    return {
        "answer": answer,
        "citations": citations,
        "metrics": {
            "route": route,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        },
    }


async def run_isolated_eval(
    cases: list[PublicEvalCase], suite: SuiteName, documents_dir: Path
) -> dict[str, Any]:
    """Index one suite in temporary Chroma and execute the normal query path."""
    from chromadb import PersistentClient
    from langchain_chroma import Chroma

    from app.core.config import settings
    from app.db.chroma_client import COLLECTION_NAME, get_embedding_function
    from app.dependencies import get_rag_service
    from app.ports.vector_store import VectorStorePort
    from app.repositories.vector_store_repository import VectorStoreRepository

    if settings.LLM_MODEL != "gpt-5.6-luna":
        raise RuntimeError("Evaluation requires DEV LLM_MODEL=gpt-5.6-luna")
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("Evaluation requires a configured DEV OpenAI key")

    user_id = f"{suite}-eval-{uuid4()}"
    with tempfile.TemporaryDirectory(prefix=f"dih-{suite}-eval-") as directory:
        client = PersistentClient(path=str(Path(directory) / "chroma"))
        collection = client.get_or_create_collection(COLLECTION_NAME)
        vector_store = Chroma(
            client=client,
            collection_name=COLLECTION_NAME,
            embedding_function=get_embedding_function(),
        )
        service = get_rag_service(
            repository=cast(
                VectorStorePort, VectorStoreRepository(vector_store, collection)
            )
        )
        indexed: dict[str, int] = {}
        filenames = dict.fromkeys(
            evidence.document for case in cases for evidence in case.expected_evidence
        )
        for filename in filenames:
            chunks, _language = await service.index_document(
                _PathUpload(documents_dir / filename), user_id
            )
            indexed[filename] = chunks

        report = await asyncio.to_thread(
            evaluate_cases,
            cases,
            lambda case_id, question: _normal_query(service, user_id, question),
        )
        report["index"] = {
            "isolated": True,
            "user_id": user_id,
            "documents": indexed,
            "persisted_chunks": collection.count(),
        }
        return report


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=EVALUATION_ROOT.parent.parent,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def build_run_report(
    *,
    suite: SuiteName,
    cases: list[PublicEvalCase],
    results: list[dict[str, Any]],
    dataset_version: str,
    git_commit: str,
    timestamp: str,
    model: str,
    warnings: list[str] | None = None,
    index: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    report = _evaluation_summary(results, len(cases))
    report.update(
        {
            "timestamp": timestamp,
            "git_commit": git_commit,
            "suite": suite,
            "corpus": f"{suite}-golden",
            "dataset_version": dataset_version,
            "model": model,
            "warnings": warnings or [],
        }
    )
    if index is not None:
        report["index"] = dict(index)
    return report


def _rate(value: int, total: int) -> str:
    return f"{value}/{total} ({value / total:.0%})" if total else "0/0 (0%)"


def _markdown_section(report: Mapping[str, Any]) -> str:
    timestamp = str(report.get("timestamp", ""))
    date = timestamp[:10] or "unknown-date"
    commit = str(report.get("git_commit", "unknown"))[:12]
    summary = cast(Mapping[str, Any], report["summary"])
    results = cast(list[Mapping[str, Any]], report["results"])
    total = int(summary["total"])
    heading = (
        f"## {date} — offline rescore"
        if report.get("run_type") == "offline_rescore"
        else f"## {date} — commit {commit}"
    )
    lines = [heading, ""]
    if report.get("run_type") == "offline_rescore":
        lines.extend(
            [
                f"Source run: `{report.get('source_run', 'unknown')}`",
                f"Model calls: {'yes' if report.get('model_called', True) else 'none'}",
                f"Dataset unchanged: {'yes' if report.get('dataset_unchanged', False) else 'no'}",
                f"Reason: {report.get('reason', 'deterministic scorer correction')}",
                f"Previous scorer: v{report.get('previous_scorer_version', 'unknown')}",
                f"New scorer: v{report.get('scorer_version', 'unknown')}",
                "",
            ]
        )
    lines.extend(
        [
        "| Metric | Result |",
        "|---|---:|",
        f"| Cases | {total} |",
        f"| Answer pass | {_rate(int(summary['answer_pass']), total)} |",
        f"| Evidence pass | {_rate(int(summary['evidence_pass']), total)} |",
        f"| Security pass | {_rate(int(summary['security_pass']), total)} |",
        f"| Overall pass | {_rate(int(summary['overall_pass']), total)} |",
        "",
        "### Case results",
        "",
        "| Case | Answer | Evidence | Security | Overall | Tags |",
        "|---|---|---|---|---|---|",
        ]
    )
    for result in results:
        security = "PASS" if result["security_pass"] else "FAIL"
        if not result.get("security_applicable", False):
            security = "N/A"
        lines.append(
            f"| {result['id']} | {'PASS' if result['answer_pass'] else 'FAIL'} "
            f"| {'PASS' if result['evidence_pass'] else 'FAIL'} | {security} "
            f"| {'PASS' if result['overall_pass'] else 'FAIL'} "
            f"| {', '.join(result.get('tags', []))} |"
        )
    failures = [result for result in results if not result["overall_pass"]]
    if failures:
        lines.extend(["", "### Failures", "", "| Case | Failure type | Reason |", "|---|---|---|"])
        for result in failures:
            dimensions = []
            if not result["answer_pass"]:
                dimensions.append("answer")
            if not result["evidence_pass"]:
                dimensions.append("evidence")
            if not result["security_pass"]:
                dimensions.append("security")
            reason = "; ".join(result.get("failure_reasons", [])) or "unspecified"
            lines.append(f"| {result['id']} | {'/'.join(dimensions)} | {reason} |")
    return "\n".join(lines) + "\n"


def append_run_history(
    report: Mapping[str, Any],
    results_root: Path,
    markdown_path: Path | None = None,
) -> None:
    """Append one report to Markdown/CSV history without overwriting prior runs."""
    results_root.mkdir(parents=True, exist_ok=True)
    public_markdown_path = markdown_path or results_root / "RESULTS.md"
    public_markdown_path.parent.mkdir(parents=True, exist_ok=True)
    if not public_markdown_path.exists():
        public_markdown_path.write_text("# Evaluation history\n\n", encoding="utf-8")
    with public_markdown_path.open("a", encoding="utf-8") as handle:
        handle.write(_markdown_section(report))

    history_path = results_root / "history.csv"
    fields = [
        "timestamp",
        "git_commit",
        "suite",
        "dataset_version",
        "model",
        "total_cases",
        "answer_pass",
        "evidence_pass",
        "security_pass",
        "overall_pass",
    ]
    exists = history_path.exists()
    summary = cast(Mapping[str, Any], report["summary"])
    with history_path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        if not exists:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": report.get("timestamp", ""),
                "git_commit": report.get("git_commit", ""),
                "suite": report.get("suite", ""),
                "dataset_version": report.get("dataset_version", ""),
                "model": report.get("model", ""),
                "total_cases": summary["total"],
                "answer_pass": summary["answer_pass"],
                "evidence_pass": summary["evidence_pass"],
                "security_pass": summary["security_pass"],
                "overall_pass": summary["overall_pass"],
            }
        )


def write_run_artifacts(
    report: Mapping[str, Any],
    results_root: Path,
    markdown_path: Path | None = None,
) -> Path:
    """Write immutable JSON run output and append public/private histories."""
    timestamp = str(report.get("timestamp", ""))
    stamp = re.sub(r"[^0-9A-Za-zTZ-]", "", timestamp.replace(":", ""))
    commit = str(report.get("git_commit", "unknown"))[:12]
    runs_dir = results_root / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_path = runs_dir / f"{stamp}-{commit}.json"
    run_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    append_run_history(report, results_root, markdown_path)
    return run_path


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("public", "private", "all"), default="public")
    return parser.parse_args()


async def _run_suites(loaded_suites: list[LoadedSuite]) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for suite in loaded_suites:
        reports.append(await _run_suite(suite))
    return reports


async def _run_suite(loaded: LoadedSuite) -> dict[str, Any]:
    from app.core.config import settings

    raw = await run_isolated_eval(
        loaded.cases, loaded.paths.name, loaded.paths.documents_dir
    )
    report = build_run_report(
        suite=loaded.paths.name,
        cases=loaded.cases,
        results=raw["results"],
        dataset_version=dataset_fingerprint(
            loaded.paths.cases_path, loaded.paths.documents_dir
        ),
        git_commit=_git_commit(),
        timestamp=datetime.now(timezone.utc).isoformat(),
        model=settings.LLM_MODEL,
        warnings=loaded.warnings,
        index=raw.get("index"),
    )
    report["run_path"] = str(
        write_run_artifacts(report, loaded.paths.results_dir, loaded.paths.markdown_path)
    )
    return report


def main() -> None:
    args = _arguments()
    suite_names: list[SuiteName] = (
        ["public", "private"] if args.suite == "all" else [cast(SuiteName, args.suite)]
    )
    loaded_suites = [load_suite(name) for name in suite_names]
    reports = asyncio.run(_run_suites(loaded_suites))
    print(json.dumps(reports[0] if len(reports) == 1 else reports, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
