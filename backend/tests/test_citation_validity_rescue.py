import inspect
from collections.abc import Mapping
from typing import Any
from unittest.mock import Mock

from langchain_core.documents import Document

from app.repositories.vector_store_repository import VectorStoreRepository
from app.schemas.rag_schema import (
    AnswerWithEvidence,
    ExtractedEvidence,
    ExtractedEvidenceRecord,
)
from app.services.answer_generation_service import AnswerGenerationService


class _Trace:
    def __init__(self) -> None:
        self.values: dict[str, dict[str, Any]] = {}

    def record(self, stage: str, payload: Mapping[str, Any]) -> None:
        self.values[stage] = dict(payload)


def _atom(
    source_id: str = "atom-1",
    *,
    user_id: str = "tenant-1",
    filename: str = "alice.pdf",
    page: int = 4,
    text: str = "The Rabbit took a watch out of its waistcoat-pocket.",
) -> Document:
    return Document(
        id=source_id,
        page_content=text,
        metadata={
            "source": user_id,
            "original_filename": filename,
            "page_number": page,
            "chunk_id": source_id,
        },
    )


def _service(
    normal: AnswerWithEvidence | Mapping[str, Any] | Exception,
    *,
    extraction: ExtractedEvidence | Mapping[str, Any] | Exception | None = None,
    rescue: AnswerWithEvidence | Mapping[str, Any] | Exception | None = None,
) -> tuple[AnswerGenerationService, Mock, Mock, _Trace]:
    llm = Mock()
    answer_llm = Mock()
    extractor_llm = Mock()
    answers = [normal]
    if rescue is not None:
        answers.append(rescue)
    answer_llm.invoke.side_effect = answers
    extractor_llm.invoke.side_effect = [
        extraction
        if extraction is not None
        else ExtractedEvidence(evidence_records=[])
    ]
    llm.with_structured_output.side_effect = (
        lambda schema: extractor_llm if schema is ExtractedEvidence else answer_llm
    )
    service = AnswerGenerationService(
        llm=llm,
        repository=Mock(spec=VectorStoreRepository),
        language_service=Mock(),
        translation_service=Mock(),
        query_expansion_service=Mock(),
        reranking_service=Mock(),
    )
    trace = _Trace()
    service.evaluation_trace_observer = trace
    return service, answer_llm, extractor_llm, trace


def _generate(
    service: AnswerGenerationService,
    *,
    selected: list[Document] | None = None,
    candidates: list[Document] | None = None,
) -> tuple[str, list[dict[str, str | int | None]]]:
    return service._generate_llm_response(
        "question",
        "question",
        selected or [_atom()],
        [],
        "en",
        user_id="tenant-1",
        include_files=None,
        exclude_files=None,
        reranked_atomic_candidates=candidates,
    )


def _insufficient_extraction() -> ExtractedEvidence:
    return ExtractedEvidence(
        evidence_records=[
            ExtractedEvidenceRecord(
                source_id="atom-1", page=4, exact_evidence_span="took a watch"
            )
        ]
    )


def test_baseline_normal_schema_and_prompt_are_unchanged() -> None:
    assert tuple(AnswerWithEvidence.model_fields) == ("answer", "evidence_ids")
    service = AnswerGenerationService.__new__(AnswerGenerationService)
    prompt = service._build_final_prompt("context", "", "question", "en")
    assert "`answer` and `evidence_ids`" in prompt
    assert "`decision`" not in prompt


def test_valid_normal_citation_returns_baseline_answer_without_extraction() -> None:
    service, answer_llm, extractor_llm, trace = _service(
        AnswerWithEvidence(answer="Baseline answer", evidence_ids=["C1"])
    )
    answer, citations = _generate(service, candidates=[_atom()])
    assert answer == "Baseline answer"
    assert citations == [{"filename": "alice.pdf", "page_number": 4}]
    assert answer_llm.invoke.call_count == 1
    extractor_llm.invoke.assert_not_called()
    assert trace.values["rescue_triggered"]["value"] is False
    assert trace.values["rescue_reason"]["value"] == "normal_valid_citations"


def test_zero_valid_citations_with_atomic_candidates_calls_extractor_once() -> None:
    service, _answer_llm, extractor_llm, trace = _service(
        AnswerWithEvidence(answer="Baseline answer", evidence_ids=[])
    )
    _generate(service, candidates=[_atom()])
    extractor_llm.invoke.assert_called_once()
    assert trace.values["rescue_triggered"]["value"] is True


def test_forged_normal_evidence_id_counts_as_zero_valid_citations() -> None:
    service, _answer_llm, extractor_llm, trace = _service(
        AnswerWithEvidence(answer="Baseline answer", evidence_ids=["forged"])
    )
    _generate(service, candidates=[_atom()])
    extractor_llm.invoke.assert_called_once()
    assert trace.values["valid_normal_evidence_ids"]["value"] == []


def test_no_atomic_candidates_never_triggers_rescue() -> None:
    service, answer_llm, extractor_llm, trace = _service(
        AnswerWithEvidence(answer="Baseline answer", evidence_ids=[])
    )
    answer, citations = _generate(service, candidates=[])
    assert answer == "Baseline answer"
    assert citations == []
    assert answer_llm.invoke.call_count == 1
    extractor_llm.invoke.assert_not_called()
    assert trace.values["rescue_reason"]["value"] == "no_atomic_candidates"


def test_extractor_receives_atomic_candidates_only() -> None:
    aggregate = _atom("aggregate", text="aggregate-only marker")
    aggregate.metadata["context_aggregation"] = True
    service, _answer_llm, extractor_llm, _trace = _service(
        AnswerWithEvidence(answer="Baseline answer", evidence_ids=[])
    )
    _generate(
        service,
        candidates=[_atom(text="atomic marker"), aggregate],
    )
    prompt = extractor_llm.invoke.call_args.args[0]
    assert "atomic marker" in prompt
    assert "aggregate-only marker" not in prompt


def test_exact_span_validation_rejects_forgery_page_scope_and_duplicates() -> None:
    service, _answer_llm, _extractor_llm, _trace = _service(
        AnswerWithEvidence(answer="Baseline", evidence_ids=["C1"])
    )
    allowed = service._authorized_atomic_candidates(
        [_atom()],
        user_id="tenant-1",
        include_files=["alice.pdf"],
        exclude_files=None,
    )
    records = [
        ExtractedEvidenceRecord(
            source_id="atom-1", page=4, exact_evidence_span="took a watch"
        ),
        ExtractedEvidenceRecord(
            source_id="forged", page=4, exact_evidence_span="took a watch"
        ),
        ExtractedEvidenceRecord(
            source_id="atom-1", page=9, exact_evidence_span="took a watch"
        ),
        ExtractedEvidenceRecord(
            source_id="atom-1", page=4, exact_evidence_span="rewritten"
        ),
        ExtractedEvidenceRecord(
            source_id="atom-1", page=4, exact_evidence_span=""
        ),
        ExtractedEvidenceRecord(
            source_id="atom-1", page=4, exact_evidence_span="took a watch"
        ),
    ]
    verified, results = service._validate_extracted_evidence(records, allowed)
    assert list(verified) == ["atom-1"]
    assert [result["reason"] for result in results] == [
        "accepted",
        "unknown_source_id",
        "page_mismatch",
        "span_not_verbatim",
        "empty_span",
        "duplicate",
    ]


def test_wrong_document_tenant_and_aggregate_are_excluded_from_allowlist() -> None:
    wrong_document = _atom("wrong-document", filename="other.pdf")
    wrong_tenant = _atom("wrong-tenant", user_id="tenant-2")
    aggregate = _atom("aggregate")
    aggregate.metadata["context_aggregation"] = True
    service, _answer_llm, _extractor_llm, _trace = _service(
        AnswerWithEvidence(answer="Baseline", evidence_ids=["C1"])
    )
    assert service._authorized_atomic_candidates(
        [wrong_document, wrong_tenant, aggregate],
        user_id="tenant-1",
        include_files=["alice.pdf"],
        exclude_files=None,
    ) == {}


def test_extraction_failure_preserves_original_normal_result() -> None:
    service, answer_llm, extractor_llm, trace = _service(
        AnswerWithEvidence(answer="Original baseline answer", evidence_ids=[]),
        extraction={"evidence_records": [{"source_id": "invalid"}]},
    )
    answer, citations = _generate(service, candidates=[_atom()])
    assert answer == "Original baseline answer"
    assert citations == []
    assert answer_llm.invoke.call_count == 1
    assert extractor_llm.invoke.call_count == 1
    assert trace.values["rescue_reason"]["value"] == "extraction_failed"


def test_zero_valid_extracted_evidence_preserves_original_result() -> None:
    service, answer_llm, _extractor_llm, trace = _service(
        AnswerWithEvidence(answer="Original baseline answer", evidence_ids=[]),
        extraction=ExtractedEvidence(
            evidence_records=[
                ExtractedEvidenceRecord(
                    source_id="forged", page=4, exact_evidence_span="forged"
                )
            ]
        ),
    )
    answer, citations = _generate(service, candidates=[_atom()])
    assert answer == "Original baseline answer"
    assert citations == []
    assert answer_llm.invoke.call_count == 1
    assert trace.values["rescue_reason"]["value"] == "zero_valid_extracted_evidence"


def test_rescue_citations_use_validated_source_ids_only() -> None:
    service, answer_llm, extractor_llm, trace = _service(
        AnswerWithEvidence(answer="Baseline answer", evidence_ids=[]),
        extraction=_insufficient_extraction(),
        rescue=AnswerWithEvidence(
            answer="Rescued answer", evidence_ids=["atom-1", "forged"]
        ),
    )
    answer, citations = _generate(service, candidates=[_atom()])
    assert answer == "Rescued answer"
    assert citations == [{"filename": "alice.pdf", "page_number": 4}]
    assert answer_llm.invoke.call_count == 2
    assert extractor_llm.invoke.call_count == 1
    assert trace.values["verified_spans_reaching_generation"]["value"] == [
        {
            "source_id": "atom-1",
            "page": 4,
            "exact_evidence_span": "took a watch",
        }
    ]
    assert trace.values["final_citations"]["value"] == citations


def test_rescue_generation_failure_preserves_original_result() -> None:
    service, _answer_llm, _extractor_llm, trace = _service(
        AnswerWithEvidence(answer="Original baseline answer", evidence_ids=[]),
        extraction=_insufficient_extraction(),
        rescue=RuntimeError("provider failed"),
    )
    answer, citations = _generate(service, candidates=[_atom()])
    assert answer == "Original baseline answer"
    assert citations == []
    assert trace.values["rescue_reason"]["value"] == "rescue_generation_failed"


def test_router_has_no_evaluator_gold_data_dependency() -> None:
    source = inspect.getsource(AnswerGenerationService)
    assert "expected_facts" not in source
    assert "expected_evidence" not in source
    assert "fact_coverage" not in source
    assert "answer_pass" not in source


def test_trace_records_normal_and_rescue_answers() -> None:
    service, _answer_llm, _extractor_llm, trace = _service(
        AnswerWithEvidence(answer="Baseline answer", evidence_ids=[]),
        extraction=_insufficient_extraction(),
        rescue=AnswerWithEvidence(answer="Rescued answer", evidence_ids=["atom-1"]),
    )
    _generate(service, candidates=[_atom()])
    assert trace.values["normal_answer"]["value"] == "Baseline answer"
    assert trace.values["normal_evidence_ids"]["value"] == []
    assert trace.values["valid_normal_evidence_ids"]["value"] == []
    assert trace.values["rescue_triggered"]["value"] is True
    assert trace.values["rescue_answer"]["value"] == "Rescued answer"
    assert trace.values["final_answer"]["value"] == "Rescued answer"
