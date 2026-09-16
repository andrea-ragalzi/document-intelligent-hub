import json
import subprocess
from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfWriter

from evaluation.run_eval import (
    append_run_history,
    build_run_report,
    dataset_fingerprint,
    load_suite,
    score_case,
    write_run_artifacts,
)
from evaluation.run_public_eval import load_cases


def _case(case_id: str = "TST-001") -> dict[str, object]:
    return {
        "id": case_id,
        "question": "What is the answer?",
        "expected_facts": [
            {"description": "the answer", "accepted_phrases": ["42"]}
        ],
        "expected_evidence": [{"document": "fixture.pdf", "pages": [1]}],
        "answer_mode": "supported",
        "forbidden_facts": [],
        "tags": ["test"],
    }


def _write_suite(root: Path, name: str, cases: list[dict[str, object]]) -> Path:
    suite = root / name
    (suite / "documents").mkdir(parents=True)
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    pdf = BytesIO()
    writer.write(pdf)
    (suite / "documents" / "fixture.pdf").write_bytes(pdf.getvalue())
    (suite / "cases.jsonl").write_text(
        "\n".join(json.dumps(case) for case in cases) + "\n", encoding="utf-8"
    )
    return suite


def test_public_and_private_suite_selection_share_schema(tmp_path: Path) -> None:
    _write_suite(tmp_path, "public", [_case("PUB-001")])
    _write_suite(tmp_path, "private", [_case("PRI-001")])

    public = load_suite("public", tmp_path)
    private = load_suite("private", tmp_path)

    assert [case.id for case in public.cases] == ["PUB-001"]
    assert [case.id for case in private.cases] == ["PRI-001"]
    assert public.paths.documents_dir != private.paths.documents_dir


def test_private_directory_is_gitignored() -> None:
    repository = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        ["git", "check-ignore", "-q", "backend/evaluation/private/cases.jsonl"],
        cwd=repository,
        check=False,
    )
    assert result.returncode == 0


def test_missing_referenced_document_fails_before_execution(tmp_path: Path) -> None:
    suite = tmp_path / "private"
    suite.mkdir()
    (suite / "cases.jsonl").write_text(
        json.dumps(_case()) + "\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="Missing evaluation document"):
        load_suite("private", tmp_path)


def test_invalid_referenced_page_fails_before_execution(tmp_path: Path) -> None:
    case = _case()
    case["expected_evidence"] = [{"document": "fixture.pdf", "pages": [2]}]
    _write_suite(tmp_path, "private", [case])

    with pytest.raises(ValueError, match="Invalid evaluation page"):
        load_suite("private", tmp_path)


def test_unreferenced_document_is_a_warning_only(tmp_path: Path) -> None:
    suite = _write_suite(tmp_path, "private", [_case()])
    (suite / "documents" / "unreferenced.pdf").write_bytes(b"extra")

    loaded = load_suite("private", tmp_path)

    assert loaded.warnings == ["Unreferenced evaluation document: unreferenced.pdf"]


def test_score_case_exposes_independent_dimensions_and_overall() -> None:
    case = load_cases()[0]
    result = score_case(
        case,
        {
            "answer": "Three Velociraptors remained.",
            "citations": [
                {
                    "filename": "03_Velociraptor_Behavior_and_Containment_Dossier.pdf",
                    "page_number": 1,
                }
            ],
        },
    )

    assert result["answer_pass"] is True
    assert result["evidence_pass"] is True
    assert result["security_pass"] is True
    assert result["overall_pass"] is True
    assert result["passed"] is True


def test_public_report_and_history_are_append_only(tmp_path: Path) -> None:
    case = load_cases()[0]
    scored = score_case(case, {"answer": "Three remained", "citations": []})
    report = build_run_report(
        suite="public",
        cases=[case],
        results=[scored],
        dataset_version="sha256:test",
        git_commit="abc1234",
        timestamp="2026-09-16T12:00:00+00:00",
        model="gpt-5.6-luna",
    )

    append_run_history(report, tmp_path)
    report["timestamp"] = "2026-09-17T12:00:00+00:00"
    append_run_history(report, tmp_path)

    markdown = (tmp_path / "RESULTS.md").read_text(encoding="utf-8")
    history = (tmp_path / "history.csv").read_text(encoding="utf-8")
    assert markdown.count("## 2026-09-") == 2
    assert history.count("public") == 2
    assert markdown.index("2026-09-16") < markdown.index("2026-09-17")


def test_public_run_artifact_contains_machine_readable_summary(tmp_path: Path) -> None:
    case = load_cases()[0]
    result = score_case(case, {"answer": "Three remained", "citations": []})
    report = build_run_report(
        suite="public",
        cases=[case],
        results=[result],
        dataset_version="sha256:public",
        git_commit="abc1234",
        timestamp="2026-09-16T12:00:00+00:00",
        model="gpt-5.6-luna",
    )

    run_path = write_run_artifacts(report, tmp_path)
    stored = json.loads(run_path.read_text(encoding="utf-8"))

    assert stored["suite"] == "public"
    assert stored["dataset_version"] == "sha256:public"
    assert stored["summary"]["overall_pass"] == 0
    assert stored["results"][0]["overall_pass"] is False
    assert (tmp_path / "history.csv").is_file()


def test_private_history_does_not_touch_public_history(tmp_path: Path) -> None:
    case = load_cases()[0]
    scored = score_case(case, {"answer": "Three remained", "citations": []})
    report = build_run_report(
        suite="private",
        cases=[case],
        results=[scored],
        dataset_version="sha256:private",
        git_commit="abc1234",
        timestamp="2026-09-16T12:00:00+00:00",
        model="gpt-5.6-luna",
    )
    public_root = tmp_path / "public-results"
    private_root = tmp_path / "private"
    run_path = write_run_artifacts(
        report, private_root / "results", private_root / "RESULTS.md"
    )

    assert not (public_root / "RESULTS.md").exists()
    assert (private_root / "RESULTS.md").exists()
    assert run_path.parent == private_root / "results" / "runs"
    assert (private_root / "results" / "history.csv").exists()


def test_dataset_fingerprint_changes_only_when_dataset_changes(tmp_path: Path) -> None:
    suite = _write_suite(tmp_path, "public", [_case()])
    first = dataset_fingerprint(suite / "cases.jsonl", suite / "documents")
    second = dataset_fingerprint(suite / "cases.jsonl", suite / "documents")
    assert first == second

    changed = _case()
    changed["question"] = "A changed question"
    (suite / "cases.jsonl").write_text(
        json.dumps(changed) + "\n", encoding="utf-8"
    )
    assert dataset_fingerprint(suite / "cases.jsonl", suite / "documents") != first
