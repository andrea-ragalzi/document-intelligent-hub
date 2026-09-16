from unittest.mock import Mock

from langchain_chroma import Chroma

from app.repositories.vector_store_repository import VectorStoreRepository
from langchain_core.documents import Document


def test_temporary_page_context_uses_only_retrieved_pages() -> None:
    collection = Mock()
    fragments = [
        (str(index), text, {"original_filename": "report.pdf", "page_number": 2})
        for index, text in enumerate(
            ["Incident", "Duration", "Affected users", "INC-205", "47", "130"],
            1,
        )
    ]
    collection.get.return_value = {
        "ids": [item[0] for item in fragments],
        "documents": [item[1] for item in fragments],
        "metadatas": [item[2] for item in fragments],
    }
    repository = VectorStoreRepository(Mock(spec=Chroma), collection)
    retrieved = [
        Document(
            page_content="130",
            metadata={"original_filename": "report.pdf", "page_number": 2},
        )
    ]

    contexts = repository.get_temporary_page_contexts("user", retrieved)

    assert len(contexts) == 1
    assert contexts[0].metadata["context_aggregation"] is True
    assert "INC-205" in contexts[0].page_content
    assert "47" in contexts[0].page_content
    assert "130" in contexts[0].page_content


def test_pellet_query_parent_context_keeps_compliance_and_diameter_together() -> None:
    """Parser parent evidence remains available as temporary retrieval context."""
    collection = Mock()
    collection.get.return_value = {
        "ids": ["title", "standard", "diameter"],
        "documents": [
            "Il pellet utilizzato dovrà essere conforme alle caratteristiche descritte dalle norme:",
            "EN plus / UNI EN 16961-2 classe A1 oppure A2; Ö-Norm M 7135; DIN plus 51731",
            "Il fabbricante consiglia pellet del diametro di 6 mm.",
        ],
        "metadatas": [
            {
                "original_filename": "Extraflame HP22 Pellet Burner (1)_260916_114524(1).pdf",
                "page_number": 24,
                "category": "Title",
            },
            {
                "original_filename": "Extraflame HP22 Pellet Burner (1)_260916_114524(1).pdf",
                "page_number": 24,
                "parent_id": "pellet-specification",
                "category": "NarrativeText",
            },
            {
                "original_filename": "Extraflame HP22 Pellet Burner (1)_260916_114524(1).pdf",
                "page_number": 24,
                "parent_id": "pellet-specification",
                "category": "NarrativeText",
            },
        ],
    }
    repository = VectorStoreRepository(Mock(spec=Chroma), collection)
    retrieved = [
        Document(
            page_content="Il fabbricante consiglia pellet del diametro di 6 mm.",
            metadata={
                "original_filename": "Extraflame HP22 Pellet Burner (1)_260916_114524(1).pdf",
                "page_number": 24,
                "parent_id": "pellet-specification",
            },
        )
    ]

    contexts = repository.get_temporary_page_contexts("user", retrieved)

    parent_context = next(
        context
        for context in contexts
        if context.metadata.get("context_parent_id") == "pellet-specification"
    )
    assert "UNI EN 16961-2" in parent_context.page_content
    assert "diametro di 6 mm" in parent_context.page_content


def test_long_narrative_parent_does_not_become_temporary_context() -> None:
    """A parser parent is provenance, not proof that all prose is one fact."""
    collection = Mock()
    long_fragments = ["policy coverage " * 40, "policy exclusions " * 40]
    collection.get.return_value = {
        "ids": ["one", "two"],
        "documents": long_fragments,
        "metadatas": [
            {
                "original_filename": "policy.pdf",
                "page_number": 6,
                "parent_id": "narrative-section",
                "category": "NarrativeText",
            }
            for _ in long_fragments
        ],
    }
    repository = VectorStoreRepository(Mock(spec=Chroma), collection)
    retrieved = [
        Document(
            page_content=long_fragments[0],
            metadata={
                "original_filename": "policy.pdf",
                "page_number": 6,
                "parent_id": "narrative-section",
            },
        )
    ]

    contexts = repository.get_temporary_page_contexts("user", retrieved)

    assert not any(
        context.metadata.get("context_parent_id") == "narrative-section"
        for context in contexts
    )
