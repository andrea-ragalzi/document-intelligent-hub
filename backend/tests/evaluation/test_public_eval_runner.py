import json
from collections.abc import Mapping
from typing import Any

from evaluation.run_public_eval import CASES_PATH, evaluate_cases, load_cases


def test_runner_executes_cases_loaded_from_jsonl_in_dataset_order() -> None:
    cases = load_cases(CASES_PATH)
    executed: list[str] = []

    def executor(case_id: str, question: str) -> Mapping[str, Any]:
        executed.append(case_id)
        return {"answer": f"answer for {question}", "citations": []}

    report = evaluate_cases(cases, executor)

    assert executed == [case.id for case in cases]
    assert [result["id"] for result in report["results"]] == executed
    assert report["summary"]["total"] == 23
    json.dumps(report)


def test_runner_marks_forbidden_security_output_as_failure() -> None:
    case = next(case for case in load_cases(CASES_PATH) if case.id == "SEC-001")

    report = evaluate_cases(
        [case],
        lambda _case_id, _question: {
            "answer": "JP-INDIRECT-PI-CANARY-7B3E91",
            "citations": [],
        },
    )

    result = report["results"][0]
    assert result["passed"] is False
    assert result["forbidden_markers_found"] == ["JP-INDIRECT-PI-CANARY-7B3E91"]


def test_runner_accepts_a_grounded_paraphrase_without_an_llm_judge() -> None:
    case = next(case for case in load_cases(CASES_PATH) if case.id == "RAP-001")

    report = evaluate_cases(
        [case],
        lambda _case_id, _question: {
            "answer": "Three Velociraptors remained.",
            "citations": [
                {
                    "filename": "03_Velociraptor_Behavior_and_Containment_Dossier.pdf",
                    "page_number": 1,
                }
            ],
        },
    )

    assert report["results"][0]["passed"] is True
