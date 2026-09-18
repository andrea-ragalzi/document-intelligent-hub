"""Durable runner for the fixed structured-sufficiency experiment."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import tempfile
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from evaluation.run_eval import (
    DOCUMENTS_DIR,
    RESULTS_DIR,
    PublicEvalCase,
    _git_commit,
    _matches_expected,
    _normal_query,
    _trace_candidates,
    score_case,
)
from evaluation.structured_sufficiency_harness import ALICE_TARGETS, fixed_cases

BASELINE_SHA = "bbb52017008288310d7ab6a2240783264bbf1f11"
ARTIFACT_SCHEMA_VERSION = 2

CASE_FIELDS = frozenset(
    {
        "case_id",
        "cohort",
        "question",
        "normal_answer",
        "normal_decision",
        "normal_answer_pass",
        "normal_expected_fact_coverage",
        "normal_evidence_ids",
        "valid_normal_evidence_ids",
        "valid_normal_citation_count",
        "normal_citation_precision",
        "normal_citation_recall",
        "normal_abstention_classification",
        "rescue_triggered",
        "rescue_result",
        "rescue_reason",
        "rescue_answer",
        "rescue_improved_coverage",
        "extraction_records",
        "extraction_validation_results",
        "correct_evidence_available",
        "expected_span_extracted",
        "expected_span_validated",
        "verified_span_reached_rescue_generation",
        "verified_spans",
        "final_answer",
        "final_answer_pass",
        "final_expected_fact_coverage",
        "final_citations",
        "citation_precision",
        "citation_recall",
        "page_correctness",
        "abstention_classification",
        "first_loss_stage",
        "latency_ms",
        "error",
    }
)

COMMON_AGGREGATE_FIELDS = frozenset(
    {
        "total",
        "answer_pass",
        "mean_fact_coverage",
        "citation_precision",
        "citation_recall",
        "page_correctness",
        "false_abstentions",
        "answered_decisions",
        "insufficient_decisions",
        "rescue_triggers",
        "rescue_successes",
        "baseline_answer_pass",
        "baseline_mean_fact_coverage",
        "baseline_citation_precision",
        "baseline_citation_recall",
        "citation_precision_delta",
        "citation_recall_delta",
        "baseline_false_abstentions",
        "false_abstention_delta",
    }
)
ALICE_AGGREGATE_FIELDS = COMMON_AGGREGATE_FIELDS | {
    "extraction_precision",
    "extraction_recall",
    "first_loss_distribution",
}


class ObservabilityFailure(RuntimeError):
    """The durable evaluation artifact is missing required observations."""


def _artifact_path(path: Path, allowed_root: Path) -> Path:
    """Keep evaluation artifacts beneath their caller-approved directory."""
    root = allowed_root.resolve()
    resolved = path.resolve()
    if resolved.suffix != ".json" or not resolved.is_relative_to(root):
        raise ObservabilityFailure("artifact path must be a JSON file under results")
    return resolved


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        try:
            directory_fd = os.open(path.parent, os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        temporary.unlink(missing_ok=True)


def load_artifact(path: Path) -> dict[str, Any]:
    """Reload one artifact from disk; the caller never trusts stdout."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ObservabilityFailure(f"cannot reload artifact {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ObservabilityFailure("artifact root must be an object")
    return cast(dict[str, Any], value)


def _validate_case_ids(
    results: list[Any], expected_case_ids: Sequence[str]
) -> list[str]:
    raw_ids = [item.get("case_id") for item in results if isinstance(item, Mapping)]
    if not all(isinstance(case_id, str) for case_id in raw_ids):
        raise ObservabilityFailure("artifact contains an invalid case ID")
    ids = cast(list[str], raw_ids)
    if len(ids) != len(results) or len(ids) != len(set(ids)):
        raise ObservabilityFailure("artifact contains invalid or duplicate case IDs")
    if set(ids) != set(expected_case_ids) or len(ids) != len(expected_case_ids):
        missing = sorted(set(expected_case_ids) - set(ids))
        unexpected = sorted(set(ids) - set(expected_case_ids))
        raise ObservabilityFailure(
            f"artifact case set is incomplete: missing={missing}, unexpected={unexpected}"
        )
    return ids


def _validate_case_fields(results: list[Any]) -> None:
    for item in results:
        assert isinstance(item, Mapping)
        missing_fields = sorted(CASE_FIELDS - set(item))
        if missing_fields:
            raise ObservabilityFailure(
                f"case {item.get('case_id')} missing fields: {missing_fields}"
            )


def _validate_aggregate_fields(aggregates: Any) -> None:
    if not isinstance(aggregates, Mapping):
        raise ObservabilityFailure("cohort aggregates are missing")
    required = {
        "alice-14": ALICE_AGGREGATE_FIELDS,
        "short-16": COMMON_AGGREGATE_FIELDS,
    }
    for cohort, fields in required.items():
        value = aggregates.get(cohort)
        if not isinstance(value, Mapping):
            raise ObservabilityFailure(f"aggregate {cohort} is missing")
        missing_fields = sorted(fields - set(value))
        if missing_fields:
            raise ObservabilityFailure(
                f"aggregate {cohort} missing fields: {missing_fields}"
            )


def validate_complete_artifact(
    artifact: Mapping[str, Any], expected_case_ids: Sequence[str]
) -> None:
    """Require every case and metric needed for the acceptance decision."""
    if artifact.get("status") != "complete":
        raise ObservabilityFailure("artifact status is not complete")
    results = artifact.get("cases")
    if not isinstance(results, list):
        raise ObservabilityFailure("artifact cases must be a list")
    _validate_case_ids(results, expected_case_ids)
    _validate_case_fields(results)
    _validate_aggregate_fields(artifact.get("cohort_aggregates"))


class IncrementalArtifact:
    """Persist a complete snapshot after every evaluation state transition."""

    def __init__(
        self,
        path: Path,
        expected_case_ids: Sequence[str],
        *,
        allowed_root: Path = RESULTS_DIR,
    ) -> None:
        self.path = _artifact_path(path, allowed_root)
        self.expected_case_ids = list(expected_case_ids)
        self.payload: dict[str, Any] = {
            "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
            "experiment": "baseline-generation-citation-validity-rescue",
            "baseline_sha": BASELINE_SHA,
            "candidate_sha": _git_commit(),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "status": "in_progress",
            "expected_case_ids": self.expected_case_ids,
            "cases": [],
            "cohort_aggregates": None,
            "errors": [],
        }
        self._write()

    def _write(self) -> None:
        _atomic_write(self.path, self.payload)

    def record_case(self, result: Mapping[str, Any]) -> None:
        case_id = result.get("case_id")
        if case_id not in self.expected_case_ids:
            raise ObservabilityFailure(f"unexpected case ID: {case_id}")
        missing_fields = CASE_FIELDS - set(result)
        if missing_fields:
            raise ObservabilityFailure(
                f"case {case_id} missing fields: {sorted(missing_fields)}"
            )
        cases = cast(list[dict[str, Any]], self.payload["cases"])
        cases[:] = [item for item in cases if item.get("case_id") != case_id]
        cases.append(dict(result))
        self._write()

    def record_failure(self, message: str, *, status: str) -> None:
        cast(list[str], self.payload["errors"]).append(message)
        self.payload["status"] = status
        self._write()

    def finalize(self, aggregates: Mapping[str, Any]) -> dict[str, Any]:
        self.payload["cohort_aggregates"] = dict(aggregates)
        self.payload["completed_at"] = datetime.now(timezone.utc).isoformat()
        self.payload["status"] = "complete"
        self._write()
        reloaded = load_artifact(self.path)
        try:
            validate_complete_artifact(reloaded, self.expected_case_ids)
        except ObservabilityFailure as exc:
            self.payload["status"] = "observability_failure"
            cast(list[str], self.payload["errors"]).append(str(exc))
            self._write()
            raise ObservabilityFailure(f"OBSERVABILITY FAILURE: {exc}") from exc
        return reloaded


def _trace_value(trace: Mapping[str, Any], field: str, default: Any = None) -> Any:
    value = trace.get(field)
    if isinstance(value, Mapping) and "value" in value:
        return value["value"]
    return default if value is None else value


def _number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def _normal_citations(
    trace: Mapping[str, Any], evidence_ids: Sequence[str]
) -> list[dict[str, Any]]:
    generation = trace.get("generation_context")
    contexts = generation.get("contexts", []) if isinstance(generation, Mapping) else []
    selected = set(evidence_ids)
    citations: list[dict[str, Any]] = []
    seen: set[tuple[str, int | None]] = set()
    for context in contexts:
        if not isinstance(context, Mapping) or context.get("context_id") not in selected:
            continue
        filename = context.get("filename")
        page_value = context.get("page_number")
        page = (
            int(page_value)
            if isinstance(page_value, (int, str)) and str(page_value).isdigit()
            else None
        )
        if not isinstance(filename, str) or not filename:
            continue
        key = (filename, page)
        if key not in seen:
            seen.add(key)
            citations.append({"filename": filename, "page_number": page})
    return citations


def _expected_atomic_evidence_available(
    case: PublicEvalCase, trace: Mapping[str, Any], atomic_ids: Sequence[str]
) -> bool:
    allowlist = set(atomic_ids)
    for candidate in _trace_candidates(trace, "rerank"):
        source_id = candidate.get("id")
        if source_id in allowlist and any(
            _matches_expected(candidate, expected) for expected in case.expected_evidence
        ):
            return True
    return False


def _accepted_records(
    records: Sequence[Any], validation_results: Sequence[Any]
) -> list[Mapping[str, Any]]:
    accepted: list[Mapping[str, Any]] = []
    for record, validation in zip(records, validation_results, strict=False):
        if (
            isinstance(record, Mapping)
            and isinstance(validation, Mapping)
            and validation.get("accepted") is True
        ):
            accepted.append(record)
    return accepted


def _target_observations(
    case_id: str,
    extraction_records: Sequence[Any],
    accepted_records: Sequence[Mapping[str, Any]],
    verified_records: Sequence[Any],
) -> tuple[bool | None, bool | None, bool | None]:
    targets = ALICE_TARGETS.get(case_id)
    if targets is None:
        return None, None, None

    def spans(records: Sequence[Any]) -> list[str]:
        return [
            str(item.get("exact_evidence_span", ""))
            for item in records
            if isinstance(item, Mapping)
        ]

    extracted = spans(extraction_records)
    accepted = spans(accepted_records)
    verified = spans(verified_records)
    return (
        all(any(target in span for span in extracted) for target in targets),
        all(any(target in span for span in accepted) for target in targets),
        all(any(target in span for span in verified) for target in targets),
    )


def _trace_list(trace: Mapping[str, Any], field: str) -> list[Any]:
    value = _trace_value(trace, field, [])
    return value if isinstance(value, list) else []


def _artifact_first_loss(
    case_id: str,
    selection: Mapping[str, Any],
    *,
    current: Any,
    final_coverage: float | None,
    evidence_available: bool,
    rescue_triggered: bool,
    extracted: bool | None,
    validated: bool | None,
    reached: bool | None,
    valid_normal_evidence_ids: Sequence[str],
) -> Any:
    first_loss = current if current is not None else selection.get("first_loss_stage")
    if case_id in ALICE_TARGETS and final_coverage is not None and final_coverage < 1.0:
        if not evidence_available:
            first_loss = selection.get("first_loss_stage") or "reranked_atomic_candidates"
        elif not rescue_triggered:
            first_loss = "normal_generation"
        elif extracted is not True:
            first_loss = "extraction"
        elif validated is not True:
            first_loss = "validation"
        elif reached is not True:
            first_loss = "rescue_context"
        else:
            first_loss = "rescue_generation"
    if first_loss == "NOT_OBSERVABLE" and rescue_triggered and not valid_normal_evidence_ids:
        return "citation_validation"
    return first_loss


def build_case_artifact(
    case: PublicEvalCase,
    raw_result: Mapping[str, Any],
    scored: Mapping[str, Any],
) -> dict[str, Any]:
    """Project one scored result into the fixed experiment artifact schema."""
    trace_value = raw_result.get("trace")
    trace = trace_value if isinstance(trace_value, Mapping) else {}
    normal_answer = str(_trace_value(trace, "normal_answer", ""))
    normal_evidence_ids = [str(value) for value in _trace_list(trace, "normal_evidence_ids")]
    valid_normal_evidence_ids = [
        str(value) for value in _trace_list(trace, "valid_normal_evidence_ids")
    ]
    normal_citations = _trace_list(trace, "normal_citations")
    if not normal_citations:
        normal_citations = _normal_citations(trace, normal_evidence_ids)
    normal = score_case(
        case,
        {
            "answer": normal_answer,
            "citations": normal_citations,
            "trace": trace,
        },
    )
    normal_quality = cast(Mapping[str, Any], normal["stage_metrics"])["answer_quality"]
    normal_citation_metrics = cast(Mapping[str, Any], normal["stage_metrics"])[
        "citations"
    ]
    normal_abstention = cast(Mapping[str, Any], normal["stage_metrics"])[
        "abstention"
    ]
    final_quality = cast(Mapping[str, Any], scored["stage_metrics"])["answer_quality"]
    citations = cast(Mapping[str, Any], scored["stage_metrics"])["citations"]
    abstention = cast(Mapping[str, Any], scored["stage_metrics"])["abstention"]
    selection = cast(Mapping[str, Any], scored["stage_metrics"])["selection"]

    extraction_records = _trace_list(trace, "extraction_records")
    validation_results = _trace_list(trace, "validation_results")
    verified_records = _trace_list(trace, "verified_spans_reaching_generation")
    accepted = _accepted_records(extraction_records, validation_results)
    extracted, validated, reached = _target_observations(
        case.id, extraction_records, accepted, verified_records
    )
    atomic_ids = [str(value) for value in _trace_list(trace, "reranked_atomic_ids")]
    rescue_triggered = bool(_trace_value(trace, "rescue_triggered", False))
    rescue_reason = _trace_value(trace, "rescue_reason")
    rescue_answer_value = _trace_value(trace, "rescue_answer")
    rescue_answer = (
        str(rescue_answer_value) if isinstance(rescue_answer_value, str) else None
    )
    final_answer_value = _trace_value(trace, "final_answer", scored.get("answer", ""))
    final_answer = str(final_answer_value)
    correct_evidence_available = _expected_atomic_evidence_available(
        case, trace, atomic_ids
    )
    final_coverage = _number(final_quality["fact_coverage"])
    first_loss = _artifact_first_loss(
        case.id,
        selection,
        current=_trace_value(trace, "first_loss_stage"),
        final_coverage=final_coverage,
        evidence_available=correct_evidence_available,
        rescue_triggered=rescue_triggered,
        extracted=extracted,
        validated=validated,
        reached=reached,
        valid_normal_evidence_ids=valid_normal_evidence_ids,
    )
    normal_coverage = _number(normal_quality["fact_coverage"])
    rescue_improved = (
        rescue_triggered
        and final_coverage is not None
        and normal_coverage is not None
        and final_coverage > normal_coverage
    )
    metrics = raw_result.get("metrics")
    latency = metrics.get("latency_ms") if isinstance(metrics, Mapping) else None
    return {
        "case_id": case.id,
        "cohort": "alice-14" if case.id.startswith("ALI-") else "short-16",
        "question": case.question,
        "normal_answer": normal_answer,
        "normal_decision": None,
        "normal_answer_pass": normal["answer_pass"],
        "normal_expected_fact_coverage": normal_quality["fact_coverage"],
        "normal_evidence_ids": normal_evidence_ids,
        "valid_normal_evidence_ids": valid_normal_evidence_ids,
        "valid_normal_citation_count": len(normal_citations),
        "normal_citation_precision": normal_citation_metrics["page_precision"],
        "normal_citation_recall": normal_citation_metrics["page_recall"],
        "normal_abstention_classification": normal_abstention["classification"],
        "rescue_triggered": rescue_triggered,
        "rescue_result": rescue_reason,
        "rescue_reason": rescue_reason,
        "rescue_answer": rescue_answer,
        "rescue_improved_coverage": rescue_improved,
        "extraction_records": extraction_records,
        "extraction_validation_results": validation_results,
        "correct_evidence_available": correct_evidence_available,
        "expected_span_extracted": extracted,
        "expected_span_validated": validated,
        "verified_span_reached_rescue_generation": reached,
        "verified_spans": verified_records,
        "final_answer": final_answer,
        "final_answer_pass": scored["answer_pass"],
        "final_expected_fact_coverage": final_quality["fact_coverage"],
        "final_citations": scored["citations"],
        "citation_precision": citations["page_precision"],
        "citation_recall": citations["page_recall"],
        "page_correctness": scored["evidence_pass"],
        "abstention_classification": abstention["classification"],
        "first_loss_stage": first_loss,
        "latency_ms": latency,
        "error": None,
    }


def build_error_case_artifact(case: PublicEvalCase, exc: Exception) -> dict[str, Any]:
    """Keep a failed case observable while allowing later cases to complete."""
    result: dict[str, Any] = dict.fromkeys(CASE_FIELDS)
    result.update(
        {
            "case_id": case.id,
            "cohort": "alice-14" if case.id.startswith("ALI-") else "short-16",
            "question": case.question,
            "normal_evidence_ids": [],
            "valid_normal_evidence_ids": [],
            "valid_normal_citation_count": 0,
            "rescue_triggered": False,
            "extraction_records": [],
            "extraction_validation_results": [],
            "verified_spans": [],
            "final_citations": [],
            "error": {"type": type(exc).__name__, "message": str(exc)},
        }
    )
    return result


def _mean_numeric(results: Sequence[Mapping[str, Any]], field: str) -> float | None:
    values = [_number(result.get(field)) for result in results]
    observed = [value for value in values if value is not None]
    return sum(observed) / len(observed) if observed else None


def _coverage_improved(result: Mapping[str, Any]) -> bool:
    final = _number(result.get("final_expected_fact_coverage"))
    normal = _number(result.get("normal_expected_fact_coverage"))
    return final is not None and normal is not None and final > normal


def _extraction_aggregate(results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    validated_records = 0
    matching_validated_records = 0
    matched_targets = 0
    for result in results:
        case_id = str(result["case_id"])
        targets = ALICE_TARGETS[case_id]
        accepted_spans = [
            str(record.get("exact_evidence_span", ""))
            for record, validation in zip(
                cast(list[Any], result.get("extraction_records", [])),
                cast(list[Any], result.get("extraction_validation_results", [])),
                strict=False,
            )
            if isinstance(record, Mapping)
            and isinstance(validation, Mapping)
            and validation.get("accepted") is True
        ]
        validated_records += len(accepted_spans)
        matching_validated_records += sum(
            any(target in span for target in targets) for span in accepted_spans
        )
        matched_targets += sum(
            any(target in span for span in accepted_spans) for target in targets
        )
    available_targets = sum(
        len(ALICE_TARGETS[str(result["case_id"])])
        for result in results
        if result.get("rescue_triggered") is True
        and result.get("correct_evidence_available") is True
    )
    return {
        "extraction_precision": (
            matching_validated_records / validated_records if validated_records else 0.0
        ),
        "extraction_recall": (
            matched_targets / available_targets if available_targets else 0.0
        ),
        "first_loss_distribution": dict(
            Counter(str(result.get("first_loss_stage")) for result in results)
        ),
    }


def _cohort_aggregate(
    results: Sequence[Mapping[str, Any]], *, include_extraction: bool
) -> dict[str, Any]:
    rescue_results = [result for result in results if result.get("rescue_triggered") is True]
    citation_precision = _mean_numeric(results, "citation_precision")
    citation_recall = _mean_numeric(results, "citation_recall")
    baseline_citation_precision = _mean_numeric(results, "normal_citation_precision")
    baseline_citation_recall = _mean_numeric(results, "normal_citation_recall")
    false_abstentions = sum(
        result.get("abstention_classification") == "false_refusal"
        for result in results
    )
    baseline_false_abstentions = sum(
        result.get("normal_abstention_classification") == "false_refusal"
        for result in results
    )
    aggregate: dict[str, Any] = {
        "total": len(results),
        "answer_pass": sum(result.get("final_answer_pass") is True for result in results),
        "baseline_answer_pass": sum(
            result.get("normal_answer_pass") is True for result in results
        ),
        "mean_fact_coverage": _mean_numeric(results, "final_expected_fact_coverage"),
        "baseline_mean_fact_coverage": _mean_numeric(
            results, "normal_expected_fact_coverage"
        ),
        "citation_precision": citation_precision,
        "citation_recall": citation_recall,
        "page_correctness": (
            sum(result.get("page_correctness") is True for result in results) / len(results)
            if results
            else None
        ),
        "false_abstentions": false_abstentions,
        "answered_decisions": sum(
            result.get("normal_decision") == "answered" for result in results
        ),
        "insufficient_decisions": sum(
            result.get("normal_decision") == "insufficient_evidence"
            for result in results
        ),
        "rescue_triggers": len(rescue_results),
        "rescue_successes": sum(_coverage_improved(result) for result in rescue_results),
        "baseline_citation_precision": baseline_citation_precision,
        "baseline_citation_recall": baseline_citation_recall,
        "citation_precision_delta": (
            citation_precision - baseline_citation_precision
            if citation_precision is not None and baseline_citation_precision is not None
            else None
        ),
        "citation_recall_delta": (
            citation_recall - baseline_citation_recall
            if citation_recall is not None and baseline_citation_recall is not None
            else None
        ),
        "baseline_false_abstentions": baseline_false_abstentions,
        "false_abstention_delta": false_abstentions - baseline_false_abstentions,
    }
    if include_extraction:
        aggregate.update(_extraction_aggregate(results))
    return aggregate


def cohort_aggregates(results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    alice = [result for result in results if result.get("cohort") == "alice-14"]
    short = [result for result in results if result.get("cohort") == "short-16"]
    return {
        "alice-14": _cohort_aggregate(alice, include_extraction=True),
        "short-16": _cohort_aggregate(short, include_extraction=False),
    }


async def run_experiment(path: Path) -> dict[str, Any]:
    """Index once, persist each completed case, then validate the disk artifact."""
    from chromadb import PersistentClient
    from langchain_chroma import Chroma

    from app.core.config import settings
    from app.db.chroma_client import COLLECTION_NAME, get_embedding_function
    from app.dependencies import get_rag_service
    from app.ports.vector_store import VectorStorePort
    from app.repositories.vector_store_repository import VectorStoreRepository
    from evaluation.run_eval import _PathUpload

    cases = fixed_cases()
    writer = IncrementalArtifact(path, [case.id for case in cases])
    if settings.LLM_MODEL != "gpt-5.6-luna":
        message = "Evaluation requires DEV LLM_MODEL=gpt-5.6-luna"
        writer.record_failure(message, status="evaluation_failure")
        raise RuntimeError(message)
    if not settings.OPENAI_API_KEY:
        message = "Evaluation requires a configured DEV OpenAI key"
        writer.record_failure(message, status="evaluation_failure")
        raise RuntimeError(message)

    user_id = f"structured-sufficiency-eval-{uuid4()}"
    try:
        with tempfile.TemporaryDirectory(prefix="dih-structured-sufficiency-") as directory:
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
            filenames = dict.fromkeys(
                evidence.document for case in cases for evidence in case.expected_evidence
            )
            for filename in filenames:
                await service.index_document(_PathUpload(DOCUMENTS_DIR / filename), user_id)

            for case in cases:
                started = time.perf_counter()
                try:
                    raw = await asyncio.to_thread(
                        _normal_query, service, user_id, case.question
                    )
                    scored = score_case(case, raw)
                    result = build_case_artifact(case, raw, scored)
                except Exception as exc:  # noqa: BLE001 - failures belong in the artifact
                    result = build_error_case_artifact(case, exc)
                    result["latency_ms"] = round(
                        (time.perf_counter() - started) * 1000, 2
                    )
                writer.record_case(result)

        case_results = cast(list[dict[str, Any]], writer.payload["cases"])
        return writer.finalize(cohort_aggregates(case_results))
    except ObservabilityFailure:
        raise
    except Exception as exc:
        writer.record_failure(str(exc), status="evaluation_failure")
        raise


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    default_name = (
        "structured-sufficiency-rerun-"
        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + ".json"
    )
    parser.add_argument("--artifact", type=Path, default=RESULTS_DIR / default_name)
    return parser.parse_args()


def main() -> None:
    args = _arguments()
    try:
        artifact = asyncio.run(run_experiment(args.artifact))
    except ObservabilityFailure as exc:
        raise SystemExit(f"OBSERVABILITY FAILURE: {exc}") from exc
    print(
        json.dumps(
            {
                "artifact_path": str(args.artifact),
                "status": artifact["status"],
                "case_count": len(artifact["cases"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
