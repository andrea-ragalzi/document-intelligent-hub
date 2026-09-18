from pathlib import Path
from typing import Any

import pytest

from evaluation.structured_sufficiency_runner import (
    ALICE_AGGREGATE_FIELDS,
    CASE_FIELDS,
    COMMON_AGGREGATE_FIELDS,
    IncrementalArtifact,
    ObservabilityFailure,
    build_case_artifact,
    load_artifact,
    validate_complete_artifact,
)
from evaluation.run_eval import score_case
from evaluation.structured_sufficiency_harness import fixed_cases


def _case(case_id: str) -> dict[str, Any]:
    result = {field: None for field in CASE_FIELDS}
    result.update(
        {
            "case_id": case_id,
            "cohort": "alice-14" if case_id.startswith("ALI-") else "short-16",
            "question": f"Question for {case_id}",
            "normal_evidence_ids": [],
            "rescue_triggered": False,
            "extraction_records": [],
            "extraction_validation_results": [],
            "final_citations": [],
            "error": None,
        }
    )
    return result


def _aggregates() -> dict[str, dict[str, Any]]:
    return {
        "alice-14": {field: 0 for field in ALICE_AGGREGATE_FIELDS},
        "short-16": {field: 0 for field in COMMON_AGGREGATE_FIELDS},
    }


def _ids() -> list[str]:
    return [f"ALI-{index:03d}" for index in range(1, 15)] + [
        f"SHORT-{index:03d}" for index in range(1, 17)
    ]


def test_artifact_path_exists_before_evaluation_and_flushes_each_case(
    tmp_path: Path,
) -> None:
    path = tmp_path / "nested" / "artifact.json"
    writer = IncrementalArtifact(path, _ids(), allowed_root=tmp_path)

    assert path.is_file()
    assert load_artifact(path)["cases"] == []

    writer.record_case(_case("ALI-001"))

    assert [item["case_id"] for item in load_artifact(path)["cases"]] == ["ALI-001"]


def test_artifact_path_is_confined_to_the_allowed_directory(tmp_path: Path) -> None:
    with pytest.raises(ObservabilityFailure, match="under results"):
        IncrementalArtifact(tmp_path.parent / "artifact.json", _ids(), allowed_root=tmp_path)


def test_partial_results_survive_a_later_failure(tmp_path: Path) -> None:
    path = tmp_path / "artifact.json"
    writer = IncrementalArtifact(path, _ids(), allowed_root=tmp_path)
    writer.record_case(_case("ALI-001"))
    writer.record_failure("later case failed", status="evaluation_failure")

    artifact = load_artifact(path)

    assert artifact["status"] == "evaluation_failure"
    assert artifact["cases"][0]["case_id"] == "ALI-001"
    assert artifact["errors"] == ["later case failed"]


def test_finalized_artifact_reloads_with_all_30_cases(tmp_path: Path) -> None:
    path = tmp_path / "artifact.json"
    writer = IncrementalArtifact(path, _ids(), allowed_root=tmp_path)
    for case_id in _ids():
        writer.record_case(_case(case_id))

    artifact = writer.finalize(_aggregates())

    assert artifact == load_artifact(path)
    assert artifact["status"] == "complete"
    assert len(artifact["cases"]) == 30


def test_missing_case_is_observability_failure(tmp_path: Path) -> None:
    writer = IncrementalArtifact(
        tmp_path / "artifact.json", _ids(), allowed_root=tmp_path
    )
    for case_id in _ids()[:-1]:
        writer.record_case(_case(case_id))
    writer.payload["status"] = "complete"
    writer.payload["cohort_aggregates"] = _aggregates()

    with pytest.raises(ObservabilityFailure, match="case set is incomplete"):
        validate_complete_artifact(writer.payload, _ids())


def test_missing_case_metric_is_observability_failure(tmp_path: Path) -> None:
    writer = IncrementalArtifact(
        tmp_path / "artifact.json", _ids(), allowed_root=tmp_path
    )
    cases = [_case(case_id) for case_id in _ids()]
    del cases[0]["citation_recall"]
    writer.payload.update(
        {"status": "complete", "cases": cases, "cohort_aggregates": _aggregates()}
    )

    with pytest.raises(ObservabilityFailure, match="citation_recall"):
        validate_complete_artifact(writer.payload, _ids())


def test_missing_cohort_metric_is_observability_failure(tmp_path: Path) -> None:
    writer = IncrementalArtifact(
        tmp_path / "artifact.json", _ids(), allowed_root=tmp_path
    )
    aggregates = _aggregates()
    del aggregates["alice-14"]["extraction_recall"]
    writer.payload.update(
        {
            "status": "complete",
            "cases": [_case(case_id) for case_id in _ids()],
            "cohort_aggregates": aggregates,
        }
    )

    with pytest.raises(ObservabilityFailure, match="extraction_recall"):
        validate_complete_artifact(writer.payload, _ids())


def test_case_projection_persists_baseline_and_final_comparison() -> None:
    case = fixed_cases()[0]
    answer = "The Rabbit took a watch out of its waistcoat-pocket."
    raw = {
        "answer": answer,
        "citations": [],
        "metrics": {"latency_ms": 12.5},
        "trace": {
            "normal_answer": {"value": answer},
            "normal_evidence_ids": {"value": ["forged"]},
            "valid_normal_evidence_ids": {"value": []},
            "normal_citations": {"value": []},
            "rescue_triggered": {"value": False},
            "rescue_reason": {"value": "no_atomic_candidates"},
            "rescue_answer": {"value": None},
            "extraction_records": {"value": []},
            "validation_results": {"value": []},
            "verified_spans_reaching_generation": {"value": []},
            "reranked_atomic_ids": {"value": []},
            "final_answer": {"value": answer},
            "final_citations": {"value": []},
        },
    }

    result = build_case_artifact(case, raw, score_case(case, raw))

    assert CASE_FIELDS <= set(result)
    assert result["normal_answer"] == answer
    assert result["normal_evidence_ids"] == ["forged"]
    assert result["valid_normal_evidence_ids"] == []
    assert result["valid_normal_citation_count"] == 0
    assert result["rescue_triggered"] is False
    assert result["final_answer"] == answer
