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

