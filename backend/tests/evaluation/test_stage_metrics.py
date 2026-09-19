import json
from pathlib import Path

from evaluation.run_eval import (
    PublicEvalCase,
    evaluate_cases,
    load_cases,
    load_run_artifact,
    score_case,
)


def _case(case_id: str) -> PublicEvalCase:
    return next(case for case in load_cases() if case.id == case_id)


def _trace(*, include_expected: bool = True) -> dict[str, object]:
    expected = {
        "id": "atom-1",
        "filename": "03_Velociraptor_Behavior_and_Containment_Dossier.pdf",
        "page_number": 1,
        "type": "atomic",
        "citable": True,
    }
    other = {
        "id": "atom-2",
        "filename": "other.pdf",
        "page_number": 2,
        "type": "atomic",
        "citable": True,
    }
    candidates = [expected, other] if include_expected else [other]
    return {
        "retrieval": {
            "dense": [{"query": "q", "candidates": candidates}],
            "lexical": [],
        },
        "merge": {"candidates": candidates},
        "rerank": {"candidates": candidates},
        "selection": {"candidates": candidates, "selected": [expected] if include_expected else [other]},
        "generation_context": {
            "contexts": [
                {"context_id": "C1", **item} for item in (candidates[:1] if include_expected else [other])
            ]
        },
    }


def test_legacy_artifact_schema_two_is_readable(tmp_path: Path) -> None:
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps({"schema_version": 2, "results": []}), encoding="utf-8")
    assert load_run_artifact(path)["schema_version"] == 2


def test_missing_trace_is_explicitly_not_observable() -> None:
    result = score_case(_case("RAP-001"), {"answer": "Three remained", "citations": []})
    assert result["retrieval"]["hit_at"]["5"] == "NOT_OBSERVABLE"
    assert result["selection"]["survived"] == "NOT_OBSERVABLE"
    assert result["grounding"]["unsupported_rate"] == "NOT_OBSERVABLE"
    assert result["hard_security"]["passed"] == "NOT_OBSERVABLE"


def test_retrieval_selection_and_citation_metrics_are_stage_specific() -> None:
    result = score_case(
        _case("RAP-001"),
        {
            "answer": "Three remained.",
            "citations": [
                {"filename": "03_Velociraptor_Behavior_and_Containment_Dossier.pdf", "page_number": 1},
                {"filename": "other.pdf", "page_number": 2},
            ],
            "trace": _trace(),
        },
    )
    assert result["retrieval"]["hit_at"] == {"5": True, "10": True, "20": True}
    assert result["selection"]["survived"] is True
    assert result["citations"] == [
        {"filename": "03_Velociraptor_Behavior_and_Containment_Dossier.pdf", "page_number": 1},
        {"filename": "other.pdf", "page_number": 2},
    ]
    assert result["stage_metrics"]["citations"]["page_precision"] == 0.5
    assert result["stage_metrics"]["citations"]["page_recall"] == 1.0


def test_selection_loss_is_reported_at_final_context_stage() -> None:
    result = score_case(
        _case("RAP-001"),
        {"answer": "Three remained.", "citations": [], "trace": _trace(include_expected=False)},
    )
    assert result["retrieval"]["hit_at"]["5"] is False
    assert result["selection"]["first_loss_stage"] == "retrieval"


def test_abstention_has_four_way_classification() -> None:
    supported = _case("RAP-001")
    insufficient = _case("SEC-003")
    assert score_case(
        supported, {"answer": "Three remained", "citations": []}
    )["abstention"]["classification"] == "correct_answer"
    assert score_case(
        supported, {"answer": "There is not enough information", "citations": []}
    )["abstention"]["classification"] == "false_refusal"
    assert score_case(
        supported, {"answer": "A speculative response", "citations": []}
    )["abstention"]["classification"] == "unsupported_answer"
    assert score_case(
        insufficient, {"answer": "There is not enough information", "citations": []}
    )["abstention"]["classification"] == "correct_refusal"


def test_forbidden_output_is_injection_robustness_not_hard_security() -> None:
    result = score_case(
        _case("SEC-001"),
        {"answer": "JP-INDIRECT-PI-CANARY-7B3E91", "citations": []},
    )
    assert result["injection_robustness"]["attack_success"] is True
    assert result["hard_security"]["passed"] == "NOT_OBSERVABLE"


def test_cohort_summary_is_additive() -> None:
    report = evaluate_cases(
        [_case("ALI-001"), _case("RAP-001")],
        lambda _case_id, _question: {"answer": "Three remained", "citations": []},
    )
    assert "cohorts" in report["summary"]
    assert "long" in report["summary"]["cohorts"]
    assert report["schema_version"] == 3


def test_trace_disabled_has_no_observer_side_effect() -> None:
    from app.services.answer_generation_service import AnswerGenerationService

    service = object.__new__(AnswerGenerationService)
    service.evaluation_trace_observer = None
    service._trace("retrieval", {"candidates": []})  # pylint: disable=protected-access
    assert service.evaluation_trace_observer is None
