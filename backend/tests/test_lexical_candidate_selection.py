"""Focused unit tests for bounded lexical and page-context candidates."""

from unittest.mock import Mock

from app.repositories.vector_store_repository import VectorStoreRepository


def _results(items: list[tuple[str, str, dict]]) -> dict:
    return {
        "ids": [item[0] for item in items],
        "documents": [item[1] for item in items],
        "metadatas": [item[2] for item in items],
    }


def _metadata(filename: str, *, category: str = "Title") -> dict:
    return {
        "source": "user-1",
        "original_filename": filename,
        "page_number": 1,
        "category": category,
    }


def test_table_aggregate_keeps_atomic_tcar_identifiers_and_results() -> None:
    filename = "Rapporto Ispezione Veicoli Tour.pdf"
    direct = _results(
        [
            ("car-01", "T-CAR 01", _metadata(filename)),
            ("car-02", "T-CAR 02", _metadata(filename)),
        ]
    )
    fragments = _results(
        [
            ("heading", "Test Override Manuale", _metadata(filename)),
            ("car-01", "T-CAR 01", _metadata(filename)),
            ("failed-01", "FALLITO", _metadata(filename)),
            ("car-02", "T-CAR 02", _metadata(filename)),
            ("passed-02", "SUCCESSO", _metadata(filename)),
            ("car-03", "T-CAR 03", _metadata(filename)),
            ("failed-03", "FALLITO", _metadata(filename)),
            ("car-04", "T-CAR 04", _metadata(filename)),
            ("failed-04", "FALLITO", _metadata(filename)),
        ]
    )
    collection = Mock()
    collection.get.side_effect = [direct, {"metadatas": []}, fragments]
    repository = VectorStoreRepository(Mock(), collection)

    candidates = repository.lexical_candidate_search("user-1", ["T-CAR"])
    aggregate = next(
        candidate
        for candidate in candidates
        if candidate.metadata.get("context_aggregation") is True
    )

    assert "T-CAR 01" in aggregate.page_content
    assert "T-CAR 02" in aggregate.page_content
    assert "SUCCESSO" in aggregate.page_content
    assert aggregate.page_content.count("FALLITO") == 3


def test_normal_prose_page_is_not_aggregated() -> None:
    filename = "Manuale d'Uso del Sistema V4.1.pdf"
    direct = _results(
        [
            (
                "answer",
                "SRI_LOCKOUT_F1 avvia la Fase 1, blocca i veicoli e reindirizza l'energia.",
                _metadata(filename, category="NarrativeText"),
            )
        ]
    )
    prose = _results(
        [
            (
                f"paragraph-{index}",
                "Questo è un normale paragrafo tecnico completo e autosufficiente "
                f"della documentazione operativa numero {index}.",
                _metadata(filename, category="NarrativeText"),
            )
            for index in range(8)
        ]
    )
    collection = Mock()
    collection.get.side_effect = [direct, {"metadatas": []}, prose]
    repository = VectorStoreRepository(Mock(), collection)

    candidates = repository.lexical_candidate_search("user-1", ["SRI_LOCKOUT_F1"])

    assert not any(
        candidate.metadata.get("context_aggregation") is True
        for candidate in candidates
    )


def test_lexical_candidates_have_a_global_bound() -> None:
    collection = Mock()

    def get(**kwargs):
        term = kwargs.get("where_document", {}).get("$contains")
        if term:
            return _results(
                [
                    (
                        f"{term}-{index}",
                        f"{term} relevant candidate {index}",
                        _metadata(f"{term}-{index}.pdf", category="NarrativeText"),
                    )
                    for index in range(40)
                ]
            )
        return {"metadatas": []}

    collection.get.side_effect = get
    repository = VectorStoreRepository(Mock(), collection)

    candidates = repository.lexical_candidate_search(
        "user-1", ["VELO", "T-CAR", "SRI_LOCKOUT_F1"]
    )

    assert len(candidates) <= 60
