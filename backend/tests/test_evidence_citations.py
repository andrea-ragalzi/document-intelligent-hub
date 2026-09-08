"""Tests for server-side validation of LLM-selected RAG evidence."""

from unittest.mock import Mock

from langchain_core.documents import Document

from app.services.answer_generation_service import AnswerGenerationService


def _service() -> AnswerGenerationService:
    return AnswerGenerationService(
        llm=Mock(),
        repository=Mock(),
        language_service=Mock(),
        translation_service=Mock(),
        query_expansion_service=Mock(),
        reranking_service=Mock(),
    )


def _document(filename: str, page_number: int | str | None, content: str) -> Document:
    metadata: dict[str, int | str] = {"original_filename": filename}
    if page_number is not None:
        metadata["page_number"] = page_number
    return Document(page_content=content, metadata=metadata)


def test_only_llm_selected_context_ids_become_citations() -> None:
    """Unrelated reranked chunks must not automatically appear in Sources."""
    context = {
        "C1": _document("alice.pdf", 3, "The Cat sits on a bough."),
        "C2": _document("alice.pdf", 7, "An unrelated later scene."),
        "C3": _document("alice.pdf", 4, "Alice treats the Cat with respect."),
        "C4": _document("alice.pdf", 2, "Another unrelated scene."),
        "C5": _document("alice.pdf", 8, "A different scene."),
    }

    citations = _service()._citations_from_evidence_ids(context, ["C1", "C3"])

    assert citations == [
        {"filename": "alice.pdf", "page_number": 3},
        {"filename": "alice.pdf", "page_number": 4},
    ]


def test_unknown_evidence_ids_are_ignored_and_do_not_create_citations() -> None:
    context = {"C1": _document("alice.pdf", 3, "Supported fact.")}

    citations = _service()._citations_from_evidence_ids(context, ["C999", "C1", "made-up"])

    assert citations == [{"filename": "alice.pdf", "page_number": 3}]


def test_duplicate_chunks_on_the_same_page_become_one_citation() -> None:
    context = {
        "C1": _document("alice.pdf", 3, "First chunk on page three."),
        "C2": _document("alice.pdf", "3", "Second chunk on page three."),
    }

    assert _service()._citations_from_evidence_ids(context, ["C1", "C2"]) == [
        {"filename": "alice.pdf", "page_number": 3}
    ]


def test_missing_page_metadata_safely_falls_back_to_filename_only() -> None:
    context = {"C1": _document("notes.txt", None, "Supported text.")}

    assert _service()._citations_from_evidence_ids(context, ["C1"]) == [
        {"filename": "notes.txt", "page_number": None}
    ]


def test_empty_evidence_never_falls_back_to_all_reranked_chunks() -> None:
    context = {
        "C1": _document("alice.pdf", 3, "Supported fact."),
        "C2": _document("alice.pdf", 7, "Unrelated fact."),
    }

    assert _service()._citations_from_evidence_ids(context, []) == []


def test_distinct_selected_evidence_is_not_arbitrarily_truncated() -> None:
    context = {
        f"C{page}": _document("brief.pdf", page, f"Distinct claim {page}.")
        for page in range(1, 5)
    }

    citations = _service()._citations_from_evidence_ids(
        context, ["C1", "C2", "C3", "C4"]
    )

    assert citations == [
        {"filename": "brief.pdf", "page_number": 1},
        {"filename": "brief.pdf", "page_number": 2},
        {"filename": "brief.pdf", "page_number": 3},
        {"filename": "brief.pdf", "page_number": 4},
    ]
