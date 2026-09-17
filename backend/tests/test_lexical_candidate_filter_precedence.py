"""Regression coverage for lexical file-filter precedence."""

from unittest.mock import Mock

from app.repositories.vector_store_repository import VectorStoreRepository


def test_include_filter_takes_precedence_over_exclude_filter() -> None:
    collection = Mock()
    collection.get.side_effect = [
        {
            "ids": ["allowed-hit", "other-hit"],
            "documents": ["needle allowed", "needle other"],
            "metadatas": [
                {
                    "source": "user-1",
                    "original_filename": "allowed.pdf",
                    "page_number": 1,
                },
                {
                    "source": "user-1",
                    "original_filename": "other.pdf",
                    "page_number": 1,
                },
            ],
        },
        {"metadatas": []},
        {"ids": [], "documents": [], "metadatas": []},
    ]
    repository = VectorStoreRepository(Mock(), collection)

    candidates = repository.lexical_candidate_search(
        "user-1",
        ["needle"],
        include_files=["allowed.pdf"],
        exclude_files=["allowed.pdf"],
    )

    assert [candidate.metadata["original_filename"] for candidate in candidates] == [
        "allowed.pdf"
    ]
