"""Deterministic coverage for bounded adaptive final-context selection."""

from langchain_core.documents import Document

from app.services.final_context_selector_service import FinalContextSelector


def _doc(score: float, text: str, filename: str = "a.pdf", page: int = 1) -> Document:
    return Document(
        page_content=text,
        metadata={
            "rerank_score": score,
            "original_filename": filename,
            "page_number": page,
            "chunk_id": f"{filename}-{page}-{text[:8]}",
        },
    )


def test_dominant_candidate_fills_minimum() -> None:
    selected = FinalContextSelector().select([
        _doc(0.90, "dominant evidence", page=1),
        _doc(0.40, "supporting evidence", page=2),
        _doc(0.30, "other evidence", page=3),
    ])
    assert [document.metadata["page_number"] for document in selected] == [1, 2]


def test_threshold_selects_all_strong_nonredundant_candidates() -> None:
    selected = FinalContextSelector().select([
        _doc(0.80, "one", page=1), _doc(0.75, "two", page=2),
        _doc(0.70, "three", page=3), _doc(0.60, "four", page=4),
        _doc(0.30, "five", page=5),
    ])
    assert [document.metadata["page_number"] for document in selected] == [1, 2, 3, 4]


def test_similar_scores_prefer_new_source() -> None:
    selected = FinalContextSelector().select([
        _doc(0.90, "source A primary", "a.pdf", 1),
        _doc(0.88, "source A related", "a.pdf", 2),
        _doc(0.86, "source B complementary", "b.pdf", 1),
    ])
    assert [document.metadata["original_filename"] for document in selected][:2] == ["a.pdf", "b.pdf"]


def test_one_source_does_not_require_diversity() -> None:
    selected = FinalContextSelector().select([
        _doc(0.90, "first", page=1), _doc(0.85, "second", page=2), _doc(0.80, "third", page=3),
    ])
    assert len(selected) == 3
    assert {document.metadata["original_filename"] for document in selected} == {"a.pdf"}


def test_exact_redundancy_is_skipped_when_other_evidence_exists() -> None:
    selected = FinalContextSelector().select([
        _doc(0.90, "same evidence", "a.pdf", 1),
        _doc(0.89, "same evidence", "a.pdf", 2),
        _doc(0.40, "independent fallback", "a.pdf", 3),
    ])
    assert [document.metadata["page_number"] for document in selected] == [1, 3]


def test_returns_fewer_than_minimum_safely() -> None:
    only = _doc(0.90, "only")
    assert FinalContextSelector().select([only]) == [only]
    assert FinalContextSelector().select([]) == []


def test_caps_at_five() -> None:
    selected = FinalContextSelector().select([
        _doc(0.90 - index * 0.01, f"evidence {index}", page=index)
        for index in range(8)
    ])
    assert len(selected) == 5


def test_selection_is_deterministic_and_preserves_metadata() -> None:
    candidates = [
        _doc(0.90, "alpha", "a.pdf", 1),
        _doc(0.87, "beta", "b.pdf", 2),
        _doc(0.85, "gamma", "a.pdf", 3),
    ]
    selector = FinalContextSelector()
    first = selector.select(candidates)
    second = selector.select(candidates)
    assert first == second
    assert first[0].metadata["chunk_id"] == candidates[0].metadata["chunk_id"]
    assert first[0].metadata["original_filename"] == "a.pdf"
    assert first[0].metadata["page_number"] == 1
