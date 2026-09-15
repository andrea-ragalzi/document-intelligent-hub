"""Deterministic coverage for conservative PDF layout-row aggregation."""

import asyncio
import os
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

import pytest
from chromadb import PersistentClient
from fastapi import UploadFile
from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.db.chroma_client import COLLECTION_NAME, get_embedding_function
from app.repositories.vector_store_repository import VectorStoreRepository
from app.services.document_classifier_service import DocumentClassifierService
from app.services.document_indexing_service import (
    LAYOUT_ROW_KIND,
    DocumentIndexingService,
)
from app.services.language_service import LanguageService


def _element(
    text: str,
    *,
    x: float,
    y: float,
    element_id: str,
    parent_id: str,
    page: int = 1,
    category: str = "TableCell",
    table_id: str | None = "table-1",
) -> Document:
    """Build one parser-shaped element with a simple bounding box."""
    metadata = {
        "page_number": page,
        "element_id": element_id,
        "parent_id": parent_id,
        "category": category,
        "coordinates": {"points": ((x, y), (x, y + 8), (x + 40, y + 8), (x + 40, y))},
    }
    if table_id is not None:
        metadata["table_id"] = table_id
    return Document(page_content=text, metadata=metadata)


def _service() -> DocumentIndexingService:
    return DocumentIndexingService(Mock(), Mock(), Mock())


def test_payslip_net_pay_row_is_preserved_alongside_atomic_cells() -> None:
    """A label and its aligned amount become one provenance-marked aggregate."""
    label = _element("NET PAYABLE", x=48, y=481, element_id="net", parent_id="table")
    amount = _element("3,578.26", x=179, y=481, element_id="amount", parent_id="net")

    aggregates = _service()._build_layout_row_aggregates([label, amount])

    assert [document.page_content for document in aggregates] == [
        "NET PAYABLE | 3,578.26"
    ]
    assert aggregates[0].metadata["chunk_kind"] == LAYOUT_ROW_KIND
    assert aggregates[0].metadata["source_element_ids"] == "net,amount"
    assert [label.page_content, amount.page_content] == ["NET PAYABLE", "3,578.26"]


def test_provider_row_preserves_provider_and_plan_reference() -> None:
    """Aligned cells with a common parser parent remain in one row aggregate."""
    provider = _element(
        "Supplementary medical insurance - Asteria Assurance Europe S.A.",
        x=99,
        y=561,
        element_id="provider",
        parent_id="benefit-row",
    )
    reference = _element(
        "NORD-MED-04 / class NMP-2",
        x=340,
        y=565,
        element_id="reference",
        parent_id="benefit-row",
    )

    aggregates = _service()._build_layout_row_aggregates([provider, reference])

    assert len(aggregates) == 1
    assert "Asteria Assurance Europe" in aggregates[0].page_content
    assert "NORD-MED-04 / class NMP-2" in aggregates[0].page_content


def test_plan_table_row_attaches_values_to_aligned_plan_headers() -> None:
    """Column labels are attached only when every plan value aligns to a header."""
    documents = [
        _element("Benefit", x=48, y=100, element_id="benefit", parent_id="table"),
        _element("NMP-1 CORE", x=279, y=100, element_id="nmp1", parent_id="table"),
        _element("NMP-2 PLUS", x=376, y=100, element_id="nmp2", parent_id="table"),
        _element("NMP-3 PREMIER", x=473, y=100, element_id="nmp3", parent_id="table"),
        _element(
            "Specialist consultations",
            x=48,
            y=140,
            element_id="specialist",
            parent_id="table",
        ),
        _element(
            "70%; max EUR 800/year", x=279, y=140, element_id="core", parent_id="table"
        ),
        _element(
            "90%; max EUR 2,500/year",
            x=376,
            y=140,
            element_id="plus",
            parent_id="table",
        ),
        _element(
            "100%; max EUR 5,000/year",
            x=473,
            y=140,
            element_id="premier",
            parent_id="table",
        ),
    ]

    aggregates = _service()._build_layout_row_aggregates(documents)

    assert len(aggregates) == 1
    assert aggregates[0].page_content == (
        "Specialist consultations | NMP-1 CORE: 70%; max EUR 800/year | "
        "NMP-2 PLUS: 90%; max EUR 2,500/year | "
        "NMP-3 PREMIER: 100%; max EUR 5,000/year"
    )
    assert aggregates[0].metadata["layout_column_headers"] == (
        "NMP-1 CORE,NMP-2 PLUS,NMP-3 PREMIER"
    )


def test_ambiguous_or_narrative_layout_does_not_create_an_aggregate() -> None:
    """Geometry and source-relationship guards prevent invented table facts."""
    ambiguous = [
        _element("NET PAYABLE", x=48, y=481, element_id="net", parent_id="table"),
        _element("3,578.26", x=179, y=510, element_id="amount", parent_id="net"),
    ]
    narrative = [
        _element(
            "This is a normal paragraph",
            x=48,
            y=550,
            element_id="a",
            parent_id="p",
            category="NarrativeText",
            table_id=None,
        ),
        _element(
            "with adjacent prose",
            x=220,
            y=550,
            element_id="b",
            parent_id="p",
            category="NarrativeText",
            table_id=None,
        ),
    ]

    assert _service()._build_layout_row_aggregates(ambiguous) == []
    assert _service()._build_layout_row_aggregates(narrative) == []


def test_toc_entries_with_shared_layout_metadata_do_not_aggregate() -> None:
    """A TOC is not table evidence even when its entries align on one line."""
    toc = [
        _element(
            "Chapter 1: History",
            x=48,
            y=100,
            element_id="toc-left",
            parent_id="toc",
            category="ListItem",
            table_id=None,
        ),
        _element(
            "7",
            x=430,
            y=100,
            element_id="toc-page",
            parent_id="toc",
            category="ListItem",
            table_id=None,
        ),
    ]

    assert _service()._build_layout_row_aggregates(toc) == []


def test_headers_footers_and_mixed_stat_prose_require_table_evidence() -> None:
    """Visual alignment cannot turn furniture or prose into a table relationship."""
    documents = [
        _element(
            "EBERRON",
            x=48,
            y=20,
            element_id="header",
            parent_id="page",
            category="Header",
            table_id=None,
        ),
        _element(
            "12",
            x=500,
            y=20,
            element_id="footer",
            parent_id="page",
            category="Footer",
            table_id=None,
        ),
        _element(
            "Armor Class 18",
            x=48,
            y=200,
            element_id="stat",
            parent_id="stat-block",
            category="NarrativeText",
            table_id=None,
        ),
        _element(
            "The creature attacks twice.",
            x=250,
            y=200,
            element_id="prose",
            parent_id="stat-block",
            category="NarrativeText",
            table_id=None,
        ),
    ]

    assert _service()._build_layout_row_aggregates(documents) == []


def test_atomic_inputs_remain_available_when_no_aggregate_is_eligible() -> None:
    """Rejecting a relationship aggregate never changes the atomic source units."""
    atomic = [
        _element(
            "Narrative fragment",
            x=48,
            y=300,
            element_id="fragment-a",
            parent_id="paragraph",
            category="NarrativeText",
            table_id=None,
        ),
        _element(
            "continuation",
            x=250,
            y=300,
            element_id="fragment-b",
            parent_id="paragraph",
            category="NarrativeText",
            table_id=None,
        ),
    ]

    assert _service()._build_layout_row_aggregates(atomic) == []
    assert [document.page_content for document in atomic] == [
        "Narrative fragment",
        "continuation",
    ]


_fixture_directory = Path(
    os.getenv("DIH_SYNTHETIC_FIXTURE_DIR", "/home/andrea/Downloads")
)
_fixture_paths = [
    _fixture_directory / "Northbyte_Systems_Payslip_August_2026.pdf",
    _fixture_directory / "Asteria_Employee_Health_Benefits_Guide_2026.pdf",
]


@pytest.mark.skipif(
    not all(path.is_file() for path in _fixture_paths),
    reason="Synthetic PDF fixtures are supplied locally, not committed to the repository.",
)
def test_local_synthetic_pdfs_index_layout_rows_alongside_atomic_chunks() -> None:
    """Exercise parser, splitting, metadata simplification, and Chroma with the fixtures."""
    with TemporaryDirectory() as directory:
        client = PersistentClient(path=str(Path(directory) / "chroma"))
        collection = client.get_or_create_collection(COLLECTION_NAME)
        repository = VectorStoreRepository(
            Chroma(
                client=client,
                collection_name=COLLECTION_NAME,
                embedding_function=get_embedding_function(),
            ),
            collection,
        )
        service = DocumentIndexingService(
            repository, LanguageService(), DocumentClassifierService()
        )

        async def index_fixture(path: Path) -> None:
            await service.index_document(
                UploadFile(file=BytesIO(path.read_bytes()), filename=path.name),
                "fixture-layout-user",
            )

        asyncio.run(index_fixture(_fixture_paths[0]))
        asyncio.run(index_fixture(_fixture_paths[1]))
        result = collection.get(
            where={"source": "fixture-layout-user"},
            include=["documents", "metadatas"],
        )
        rows = [
            text
            for text, metadata in zip(result["documents"], result["metadatas"])
            if metadata.get("chunk_kind") == LAYOUT_ROW_KIND
        ]

        # The supplied PDFs expose positioned generic elements, not parser-marked
        # table/cell elements. They therefore retain atomic evidence only; a row
        # relationship must never be manufactured from their post-layout fragments.
        assert rows == []
        assert any(text == "NET PAYABLE" for text in result["documents"])
        assert any(text == "3,578.26" for text in result["documents"])
