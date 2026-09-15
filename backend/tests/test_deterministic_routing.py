"""Regression coverage for the bounded deterministic query routes."""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel

from app.repositories.vector_store_repository import VectorStoreRepository
from app.schemas.rag_schema import ConversationMessage, DocumentInfo
from app.services.deterministic_compute_service import DeterministicComputeService
from app.services.deterministic_evidence_service import (
    DeterministicEvidenceService,
    GroundedEvidence,
)
from app.services.query_routing_service import (
    ComputeOperation,
    DeterministicQueryRouter,
    QueryRoute,
)
from app.services.rag_orchestrator_service import RAGService


def _documents() -> list[DocumentInfo]:
    return [
        DocumentInfo(filename="ledger.pdf", chunks_count=2, language="en"),
        DocumentInfo(filename="archive.pdf", chunks_count=1, language="it"),
    ]


def _evidence(value: str = "10") -> GroundedEvidence:
    return GroundedEvidence(value=value, filename="ledger.pdf", page_number=2, source_id="c1")


class TestRouter:
    def test_routes_clear_document_lookup_in_english_and_italian(self) -> None:
        router = DeterministicQueryRouter()
        english = router.decide("Which documents mention turbine?", _documents(), [])
        italian = router.decide("Quali documenti contengono turbina?", _documents(), [])

        assert english.route is QueryRoute.DIRECT_LOOKUP
        assert english.term == "turbine"
        assert italian.route is QueryRoute.DIRECT_LOOKUP

    def test_routes_clear_page_lookup(self) -> None:
        decision = DeterministicQueryRouter().decide("Which page contains warranty?", _documents(), [])

        assert decision.route is QueryRoute.DIRECT_LOOKUP
        assert decision.reason == "explicit_page_occurrence_lookup"

    def test_routes_unique_explicit_labeled_value_only(self) -> None:
        decision = DeterministicQueryRouter().decide(
            "What is the value of Account status in ledger.pdf?", _documents(), []
        )

        assert decision.route is QueryRoute.DIRECT_EXTRACT
        assert decision.field_label == "Account status"
        assert decision.filename == "ledger.pdf"

    @pytest.mark.parametrize(
        "query",
        [
            "Explain why the system failed",
            "What does my policy cover?",
            "how much my latest payslip?",
            "What was the amount?",
            "Quanto vale la cosa?",
        ],
    )
    def test_uncertain_or_semantic_shapes_fall_back_to_rag(self, query: str) -> None:
        decision = DeterministicQueryRouter().decide(query, _documents(), [])

        assert decision.route is QueryRoute.RAG

    def test_conversation_follow_up_always_falls_back_to_rag(self) -> None:
        decision = DeterministicQueryRouter().decide(
            "And the previous one?",
            _documents(),
            [ConversationMessage(role="user", content="What was the total?")],
        )

        assert decision.route is QueryRoute.RAG

    def test_explicit_document_count_routes_to_bounded_compute(self) -> None:
        decision = DeterministicQueryRouter().decide("How many documents mention turbine?", _documents(), [])

        assert decision.route is QueryRoute.COMPUTE
        assert decision.operation is ComputeOperation.COUNT


class TestEvidenceService:
    def test_labeled_value_requires_same_chunk_label_and_value_with_metadata(self) -> None:
        repository = Mock(spec=VectorStoreRepository)
        repository.exact_occurrence_search.return_value = [
            Document(
                page_content="Account status: Active",
                metadata={"original_filename": "ledger.pdf", "page_number": 2, "chunk_id": "c1"},
            )
        ]

        evidence = DeterministicEvidenceService(repository).labeled_value(
            "u1", "ledger.pdf", "Account status"
        )

        assert evidence == GroundedEvidence("Active", "ledger.pdf", 2, "c1")

    def test_multiple_plausible_labeled_values_do_not_select_one(self) -> None:
        repository = Mock(spec=VectorStoreRepository)
        repository.exact_occurrence_search.return_value = [
            Document(page_content="Balance: 10", metadata={"original_filename": "ledger.pdf", "page_number": 1}),
            Document(page_content="Balance: 20", metadata={"original_filename": "ledger.pdf", "page_number": 2}),
        ]

        assert DeterministicEvidenceService(repository).labeled_value("u1", "ledger.pdf", "Balance") is None

    def test_missing_or_invalid_metadata_does_not_fabricate_citation(self) -> None:
        repository = Mock(spec=VectorStoreRepository)
        repository.exact_occurrence_search.return_value = [Document(page_content="Status: Active", metadata={})]

        assert DeterministicEvidenceService(repository).labeled_value("u1", "ledger.pdf", "Status") is None


class TestComputeService:
    @pytest.mark.parametrize(
        ("operation", "values", "expected"),
        [
            (ComputeOperation.COUNT, ["1", "1"], 2),
            (ComputeOperation.SUM, ["2", "3"], Decimal("5")),
            (ComputeOperation.DIFFERENCE, ["9", "4"], Decimal("5")),
            (ComputeOperation.AVERAGE, ["2", "4"], Decimal("3")),
            (ComputeOperation.PERCENTAGE, ["1", "4"], Decimal("25")),
            (ComputeOperation.MIN, ["2", "4"], Decimal("2")),
            (ComputeOperation.MAX, ["2", "4"], Decimal("4")),
            (ComputeOperation.SORT, ["4", "2"], [Decimal("2"), Decimal("4")]),
        ],
    )
    def test_allowed_operations_preserve_evidence(
        self, operation: ComputeOperation, values: list[str], expected: object
    ) -> None:
        evidence = [_evidence(str(index)) for index in range(len(values))]
        result = DeterministicComputeService().compute(operation, [Decimal(value) for value in values], evidence)

        assert result.value == expected
        assert result.evidence == evidence

    def test_date_difference_and_invalid_compute_are_bounded(self) -> None:
        service = DeterministicComputeService()
        evidence = [_evidence("2026-01-01"), _evidence("2026-01-04")]

        assert service.date_difference(date(2026, 1, 1), date(2026, 1, 4), evidence).value == 3
        with pytest.raises(ValueError):
            service.compute(ComputeOperation.DIFFERENCE, [Decimal("1")], [_evidence()])


def test_ordinary_rag_bypasses_removed_classification_call() -> None:
    repository = Mock(spec=VectorStoreRepository)
    service = RAGService(
        repository=repository,
        llm=Mock(spec=BaseChatModel),
        query_gen_llm=Mock(spec=BaseChatModel),
        translation_service=Mock(),
        query_expansion_service=Mock(),
    )
    service.language_service = Mock()
    service.language_service.resolve_response_language.return_value = "en"
    service.language_service.detect_language.return_value = "en"
    service.query_processing_service.reformulate_query = Mock(return_value="Explain the failure")
    service.query_processing_service.classify_query = Mock(return_value="GENERAL_SEARCH")
    service.answer_generation_service.generate_answer = Mock(return_value=("answer", []))

    service.answer_query("Explain the failure", "u1")

    service.query_processing_service.classify_query.assert_not_called()


def test_direct_lookup_returns_grounded_citations_without_touching_llm() -> None:
    repository = Mock(spec=VectorStoreRepository)
    repository.exact_occurrence_search.return_value = [
        Document(
            page_content="The turbine inspection is complete.",
            metadata={"original_filename": "ledger.pdf", "page_number": 4, "chunk_id": "c4"},
        )
    ]
    llm = Mock(spec=BaseChatModel)
    service = RAGService(
        repository=repository,
        llm=llm,
        query_gen_llm=Mock(spec=BaseChatModel),
        translation_service=Mock(),
        query_expansion_service=Mock(),
    )

    result = service.try_deterministic_query("Which documents mention turbine?", "u1", _documents(), [])

    assert result == (
        '"turbine" appears in: ledger.pdf.',
        [{"filename": "ledger.pdf", "page_number": 4}],
        "direct_lookup",
        "explicit_document_occurrence_lookup",
    )
    llm.assert_not_called()
