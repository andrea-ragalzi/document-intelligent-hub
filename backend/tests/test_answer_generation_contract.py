"""Public answer-generation contracts with deterministic, offline boundaries."""

from collections import Counter
from collections.abc import Mapping
from copy import deepcopy
from typing import Any
from unittest.mock import Mock

import pytest
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage

from app.core.constants import LLMConstants, QueryConstants
from app.ports.translation import TranslationPort
from app.ports.vector_store import VectorStorePort
from app.schemas.rag_schema import (
    AnswerWithEvidence,
    ConversationMessage,
    ExtractedEvidence,
    ExtractedEvidenceRecord,
)
from app.services.answer_generation_service import AnswerGenerationService
from app.services.final_context_selector_service import FinalContextSelector
from app.services.language_service import LanguageService
from app.services.query_expansion_service import QueryExpansionService
from app.services.reranking_service import RerankingService

WORKSPACE = "contract-workspace"
QUESTION = "What is the Atlas retention policy?"
NORMAL_ANSWER = "The normal answer has no verified citation."


class _Trace:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    def record(self, stage: str, payload: Mapping[str, Any]) -> None:
        self.events.append((stage, deepcopy(dict(payload))))

    def payload(self, stage: str) -> dict[str, Any]:
        return [payload for name, payload in self.events if name == stage][-1]

    def values(self, stage: str) -> list[Any]:
        return [payload["value"] for name, payload in self.events if name == stage]


def _document(
    source_id: str,
    text: str,
    *,
    filename: str = "policy.pdf",
    page: int = 1,
    workspace: str = WORKSPACE,
) -> Document:
    return Document(
        id=source_id,
        page_content=text,
        metadata={
            "source": workspace,
            "original_filename": filename,
            "page_number": page,
            "chunk_id": source_id,
        },
    )


class _Harness:
    def __init__(
        self,
        results: dict[str, list[Document]],
        normal: AnswerWithEvidence,
        *,
        expansions: str = "",
        extraction: ExtractedEvidence | Exception | None = None,
        rescue: AnswerWithEvidence | Exception | None = None,
    ) -> None:
        self.repository = Mock(spec_set=VectorStorePort)
        self.retriever = Mock(spec_set=["invoke"])
        # Workers resolve by query, never by invocation/completion order.
        self.retriever.invoke.side_effect = lambda query: list(results[query])
        self.repository.get_retriever.return_value = self.retriever
        self.repository.lexical_candidate_search.return_value = []
        self.repository.get_temporary_page_contexts.return_value = []
        self.language = Mock(spec_set=LanguageService)
        self.language.detect_language.return_value = "en"
        self.language.resolve_response_language.return_value = "en"
        self.translation = Mock(spec_set=TranslationPort)
        self.expansion_model = Mock(spec_set=BaseChatModel)
        self.expansion_model.invoke.return_value = AIMessage(content=expansions)
        self.answer_model = Mock(spec_set=["invoke"])
        self.answer_model.invoke.side_effect = (
            [normal] if rescue is None else [normal, rescue]
        )
        self.extraction_model = Mock(spec_set=["invoke"])
        self.extraction_model.invoke.side_effect = [
            extraction
            if extraction is not None
            else ExtractedEvidence(evidence_records=[])
        ]
        self.model = Mock(spec_set=BaseChatModel)
        self.model.with_structured_output.side_effect = {
            AnswerWithEvidence: self.answer_model,
            ExtractedEvidence: self.extraction_model,
        }.__getitem__
        self.service = AnswerGenerationService(
            llm=self.model,
            repository=self.repository,
            language_service=self.language,
            translation_service=self.translation,
            query_expansion_service=QueryExpansionService(self.expansion_model),
            reranking_service=RerankingService(),
            final_context_selector=FinalContextSelector(),
        )
        self.trace = _Trace()
        self.service.evaluation_trace_observer = self.trace

    def assert_calls(self, *, answers: int, extractions: int) -> None:
        assert self.answer_model.invoke.call_count == answers
        assert self.extraction_model.invoke.call_count == extractions
        schemas = [
            entry.args[0] for entry in self.model.with_structured_output.call_args_list
        ]
        expected = [AnswerWithEvidence]
        if extractions:
            expected.append(ExtractedEvidence)
        if answers == 2:
            expected.append(AnswerWithEvidence)
        assert schemas == expected
        for model in (self.answer_model, self.extraction_model):
            for invocation in model.invoke.call_args_list:
                assert invocation.kwargs == {"max_tokens": LLMConstants.MAX_TOKENS}
        self.expansion_model.invoke.assert_called_once()
        self.model.invoke.assert_not_called()
        self.translation.translate_answer_back.assert_not_called()


def _context(prompt: str) -> str:
    return prompt.split("\n\nC:\n", 1)[1].split("\n\n--- FINAL INSTRUCTION ---", 1)[0]


def _assert_final(
    trace: _Trace,
    answer: str,
    citations: list[dict[str, str | int | None]],
    evidence_ids: list[str],
) -> None:
    assert trace.values("final_answer") == [answer]
    assert trace.values("final_citations") == [citations]
    assert trace.payload("generation_result") == {
        "returned_evidence_ids": evidence_ids,
        "citations": citations,
        "abstention": False,
        "fallback_reason": None,
    }


def test_normal_cited_answer_preserves_question_roles_and_trusted_citation_order() -> (
    None
):
    raw_question = f"{QUESTION} Answer briefly."
    retrieval_question = "Qual è la politica di conservazione di Atlas?"
    translated = "Atlas retention policy"
    expansion = "Atlas retention duration"
    first = _document("policy-1", "Atlas retention policy lasts thirty days.", page=3)
    second = _document(
        "schedule-1",
        "Atlas retention policy also covers archived records.",
        filename="schedule.pdf",
        page=7,
    )
    evidence_ids = ["C2", "invented.pdf", "C1", "C2"]
    harness = _Harness(
        {translated: [first], raw_question: [first, second], expansion: [second]},
        AnswerWithEvidence(
            answer="  Records are retained for thirty days.  ",
            evidence_ids=evidence_ids,
        ),
        expansions=expansion,
    )
    harness.language.detect_language.return_value = "it"
    harness.translation.translate_query_to_language.return_value = translated
    harness.repository.lexical_candidate_search.return_value = [second]
    included, excluded = ["policy.pdf", "schedule.pdf"], ["draft.pdf"]

    answer, citations = harness.service.generate_answer(
        retrieval_question,
        WORKSPACE,
        current_user_message=raw_question,
        conversation_history=[
            ConversationMessage(role="user", content="Discuss archived records.")
        ],
        output_language="en",
        include_files=included,
        exclude_files=excluded,
    )

    assert answer == "Records are retained for thirty days."
    assert citations == [
        {"filename": "policy.pdf", "page_number": 3},
        {"filename": "schedule.pdf", "page_number": 7},
    ]
    harness.assert_calls(answers=1, extractions=0)
    harness.language.detect_language.assert_called_once_with(retrieval_question)
    harness.language.resolve_response_language.assert_called_once_with(
        raw_question, output_language="en"
    )
    harness.translation.translate_query_to_language.assert_called_once_with(
        retrieval_question, "EN"
    )
    assert harness.expansion_model.invoke.call_args.args[0].endswith(
        f"Original Query: {translated}"
    )
    assert Counter(
        entry.args[0] for entry in harness.retriever.invoke.call_args_list
    ) == Counter([translated, raw_question, expansion])
    harness.repository.get_retriever.assert_called_once_with(
        user_id=WORKSPACE,
        k=QueryConstants.BASE_RETRIEVAL_K,
        include_files=included,
        exclude_files=excluded,
    )
    harness.repository.lexical_candidate_search.assert_called_once_with(
        WORKSPACE,
        ["Atlas", "Answer"],
        include_files=included,
        exclude_files=excluded,
    )
    assert harness.repository.get_temporary_page_contexts.call_args.args[0] == WORKSPACE
    prompt = harness.answer_model.invoke.call_args.args[0]
    assert f"LANG:en\n\nQ:\n{raw_question}\n\nH:\nU|Discuss archived records." in prompt
    assert retrieval_question not in prompt
    assert _context(prompt) == (
        f"[C1|policy.pdf|p3]\n{first.page_content}\n---\n"
        f"[C2|schedule.pdf|p7]\n{second.page_content}"
    )
    retrieval = next(
        payload for stage, payload in harness.trace.events if stage == "retrieval"
    )
    assert retrieval["queries"] == [translated, raw_question, expansion]
    assert retrieval["expansions"] == [expansion]
    assert [
        [doc["id"] for doc in search["candidates"]] for search in retrieval["dense"]
    ] == [
        ["policy-1"],
        ["policy-1", "schedule-1"],
        ["schedule-1"],
    ]
    assert [doc["id"] for doc in harness.trace.payload("merge")["candidates"]] == [
        "policy-1",
        "schedule-1",
    ]
    assert harness.trace.values("normal_evidence_ids") == [evidence_ids]
    assert harness.trace.values("valid_normal_evidence_ids") == [["C1", "C2"]]
    assert harness.trace.values("rescue_triggered") == [False]
    assert harness.trace.values("rescue_reason") == ["normal_valid_citations"]
    _assert_final(harness.trace, answer, citations, evidence_ids)


def test_empty_retrieval_still_generates_once_without_rescue() -> None:
    harness = _Harness(
        {QUESTION: []},
        AnswerWithEvidence(
            answer="No supporting documents were found.", evidence_ids=["C1"]
        ),
    )

    answer, citations = harness.service.generate_answer(QUESTION, WORKSPACE)

    assert (answer, citations) == ("No supporting documents were found.", [])
    harness.assert_calls(answers=1, extractions=0)
    harness.retriever.invoke.assert_called_once_with(QUESTION)
    harness.translation.translate_query_to_language.assert_not_called()
    prompt = harness.answer_model.invoke.call_args.args[0]
    assert f"Q:\n{QUESTION}" in prompt
    assert _context(prompt) == ""
    assert harness.trace.payload("selection")["selected"] == []
    assert harness.trace.payload("generation_context") == {"contexts": []}
    assert harness.trace.values("reranked_atomic_ids") == [[]]
    assert harness.trace.values("valid_normal_evidence_ids") == [[]]
    assert harness.trace.values("rescue_triggered") == [False]
    assert harness.trace.values("rescue_reason") == ["no_atomic_candidates"]
    assert harness.trace.values("verified_spans_reaching_generation") == [[]]
    _assert_final(harness.trace, answer, citations, ["C1"])


@pytest.fixture
def rescue_documents() -> list[Document]:
    # Strong topical chunks win normal selection; the low-overlap appendix
    # contains the answer and must remain available in the reranked atomic pool.
    aggregate = _document("aggregate", "Combined background notes.", page=8)
    aggregate.metadata["context_aggregation"] = True
    return [
        _document("overview", "Atlas retention policy covers archived records."),
        _document("scope", "Atlas retention policy applies to stored reports.", page=2),
        _document("foreign", "Foreign workspace note.", workspace="other-workspace"),
        _document("excluded", "Excluded draft note.", filename="draft.pdf"),
        _document("not-included", "Unrequested document note.", filename="other.pdf"),
        aggregate,
        _document(
            "appendix",
            "Records expire after thirty days. Internal note omitted.",
            filename="appendix.pdf",
            page=9,
        ),
    ]


def _record(source_id: str, page: int, span: str) -> ExtractedEvidenceRecord:
    return ExtractedEvidenceRecord(
        source_id=source_id, page=page, exact_evidence_span=span
    )


def test_successful_rescue_uses_only_verified_authorized_reranked_atoms(
    rescue_documents: list[Document],
) -> None:
    supporting_span = "Records expire after thirty days."
    overview_span = "Atlas retention policy covers archived records."
    records = [
        _record("appendix", 9, supporting_span),
        _record("overview", 1, overview_span),
        _record("forged.pdf", 99, "Invented evidence."),
        _record("appendix", 8, supporting_span),
        _record("appendix", 9, "Records expire after sixty days."),
        _record("appendix", 9, ""),
        _record("appendix", 9, supporting_span),
        _record("foreign", 1, "Foreign workspace note."),
        _record("excluded", 1, "Excluded draft note."),
        _record("not-included", 1, "Unrequested document note."),
        _record("aggregate", 8, "Combined background notes."),
    ]
    rescue_ids = ["overview", "forged.pdf", "appendix", "appendix", "C1"]
    harness = _Harness(
        {QUESTION: rescue_documents},
        AnswerWithEvidence(answer=NORMAL_ANSWER, evidence_ids=["unknown-context"]),
        extraction=ExtractedEvidence(evidence_records=records),
        rescue=AnswerWithEvidence(
            answer="Records expire after thirty days.", evidence_ids=rescue_ids
        ),
    )

    answer, citations = harness.service.generate_answer(
        QUESTION,
        WORKSPACE,
        include_files=["policy.pdf", "appendix.pdf", "draft.pdf"],
        exclude_files=["draft.pdf"],
    )

    assert answer == "Records expire after thirty days."
    assert citations == [
        {"filename": "appendix.pdf", "page_number": 9},
        {"filename": "policy.pdf", "page_number": 1},
    ]
    harness.assert_calls(answers=2, extractions=1)
    trace = harness.trace
    ranked_ids = [doc["id"] for doc in trace.payload("rerank")["candidates"]]
    assert set(ranked_ids) == {doc.id for doc in rescue_documents}
    assert [doc["id"] for doc in trace.payload("selection")["selected"]] == [
        "overview",
        "scope",
    ]
    assert trace.values("reranked_atomic_ids") == [
        [source_id for source_id in ranked_ids if source_id != "aggregate"]
    ]
    normal_prompt, rescue_prompt = [
        entry.args[0] for entry in harness.answer_model.invoke.call_args_list
    ]
    assert supporting_span not in _context(normal_prompt)
    assert trace.payload("generation_context")["contexts"][0]["context_id"] == "C1"
    extraction_prompt = harness.extraction_model.invoke.call_args.args[0]
    assert f"Q:\n{QUESTION}\n\nATOMIC CANDIDATES:\n" in extraction_prompt
    assert extraction_prompt.split("ATOMIC CANDIDATES:\n", 1)[1] == (
        f"[overview|policy.pdf|p1]\n{overview_span}\n---\n"
        "[scope|policy.pdf|p2]\nAtlas retention policy applies to stored reports.\n---\n"
        f"[appendix|appendix.pdf|p9]\n{supporting_span} Internal note omitted."
    )
    assert f"LANG:en\n\nQ:\n{QUESTION}" in rescue_prompt
    assert _context(rescue_prompt) == (
        f"[appendix|appendix.pdf|p9]\n{supporting_span}\n---\n"
        f"[overview|policy.pdf|p1]\n{overview_span}"
    )
    assert trace.values("normal_answer") == [NORMAL_ANSWER]
    assert trace.values("normal_evidence_ids") == [["unknown-context"]]
    assert trace.values("normal_citations") == [[]]
    assert trace.values("valid_normal_evidence_ids") == [[]]
    assert trace.values("rescue_triggered") == [True]
    assert trace.values("rescue_reason") == [
        "zero_valid_normal_citations",
        "rescue_generated",
    ]
    assert trace.values("extraction_records") == [
        [record.model_dump(mode="json") for record in records]
    ]
    reasons = [
        "accepted",
        "accepted",
        "unknown_source_id",
        "page_mismatch",
        "span_not_verbatim",
        "empty_span",
        "duplicate",
        "unknown_source_id",
        "unknown_source_id",
        "unknown_source_id",
        "unknown_source_id",
    ]
    assert trace.values("validation_results") == [
        [
            {
                "source_id": record.source_id,
                "page": record.page,
                "accepted": reason == "accepted",
                "reason": reason,
            }
            for record, reason in zip(records, reasons, strict=True)
        ]
    ]
    assert trace.values("verified_spans_reaching_generation") == [
        [record.model_dump(mode="json") for record in records[:2]]
    ]
    assert trace.values("rescue_answer") == [answer]
    _assert_final(trace, answer, citations, rescue_ids)


@pytest.mark.parametrize(
    ("failure_stage", "answer_calls", "reason"),
    [
        ("extraction", 1, "extraction_failed"),
        ("generation", 2, "rescue_generation_failed"),
    ],
)
def test_rescue_failure_preserves_normal_result_without_retry(
    failure_stage: str,
    answer_calls: int,
    reason: str,
) -> None:
    span = "Atlas retention policy lasts thirty days."
    extraction = ExtractedEvidence(evidence_records=[_record("policy-1", 3, span)])
    harness = _Harness(
        {QUESTION: [_document("policy-1", span, page=3)]},
        AnswerWithEvidence(answer=NORMAL_ANSWER, evidence_ids=["unknown-context"]),
        extraction=RuntimeError("offline extraction failure")
        if failure_stage == "extraction"
        else extraction,
        rescue=RuntimeError("offline rescue generation failure"),
    )

    answer, citations = harness.service.generate_answer(QUESTION, WORKSPACE)

    assert (answer, citations) == (NORMAL_ANSWER, [])
    harness.assert_calls(answers=answer_calls, extractions=1)
    assert (
        f"[policy-1|policy.pdf|p3]\n{span}"
        in harness.extraction_model.invoke.call_args.args[0]
    )
    assert (
        _context(harness.answer_model.invoke.call_args_list[0].args[0])
        == f"[C1|policy.pdf|p3]\n{span}"
    )
    if failure_stage == "generation":
        assert (
            _context(harness.answer_model.invoke.call_args_list[1].args[0])
            == f"[policy-1|policy.pdf|p3]\n{span}"
        )
        assert harness.trace.values("verified_spans_reaching_generation") == [
            [extraction.evidence_records[0].model_dump(mode="json")]
        ]
    assert harness.trace.values("normal_answer") == [NORMAL_ANSWER]
    assert harness.trace.values("normal_citations") == [[]]
    assert harness.trace.values("rescue_triggered") == [True]
    assert harness.trace.values("rescue_reason") == [
        "zero_valid_normal_citations",
        reason,
    ]
    assert harness.trace.values("rescue_answer") == [None]
    _assert_final(harness.trace, answer, citations, ["unknown-context"])


def test_conflicting_filters_are_forwarded_but_rescue_rejects_the_atom() -> None:
    span = "Atlas retention policy lasts thirty days."
    document = _document("conflicting", span, filename="policy.pdf", page=3)
    # Retrieval can return an included file even when it is also excluded.
    # Rescue currently applies exclusion as well; characterize, do not fix it.
    harness = _Harness(
        {QUESTION: [document]},
        AnswerWithEvidence(answer=NORMAL_ANSWER, evidence_ids=[]),
        extraction=ExtractedEvidence(
            evidence_records=[_record("conflicting", 3, span)]
        ),
    )
    harness.repository.lexical_candidate_search.return_value = [document]

    answer, citations = harness.service.generate_answer(
        QUESTION,
        WORKSPACE,
        include_files=["policy.pdf"],
        exclude_files=["policy.pdf"],
    )

    assert (answer, citations) == (NORMAL_ANSWER, [])
    harness.assert_calls(answers=1, extractions=1)
    harness.repository.get_retriever.assert_called_once_with(
        user_id=WORKSPACE,
        k=QueryConstants.BASE_RETRIEVAL_K,
        include_files=["policy.pdf"],
        exclude_files=["policy.pdf"],
    )
    harness.repository.lexical_candidate_search.assert_called_once_with(
        WORKSPACE,
        ["Atlas"],
        include_files=["policy.pdf"],
        exclude_files=["policy.pdf"],
    )
    assert (
        _context(harness.answer_model.invoke.call_args.args[0])
        == f"[C1|policy.pdf|p3]\n{span}"
    )
    assert harness.extraction_model.invoke.call_args.args[0].endswith(
        f"Q:\n{QUESTION}\n\nATOMIC CANDIDATES:\n"
    )
    assert harness.trace.values("reranked_atomic_ids") == [["conflicting"]]
    assert harness.trace.values("rescue_triggered") == [True]
    assert harness.trace.values("rescue_reason") == [
        "zero_valid_normal_citations",
        "zero_valid_extracted_evidence",
    ]
    assert harness.trace.values("validation_results") == [
        [
            {
                "source_id": "conflicting",
                "page": 3,
                "accepted": False,
                "reason": "unknown_source_id",
            }
        ]
    ]
    assert harness.trace.values("verified_spans_reaching_generation") == [[]]
    _assert_final(harness.trace, answer, citations, [])
