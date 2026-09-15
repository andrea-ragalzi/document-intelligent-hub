"""Small, citation-preserving evidence operations for deterministic routes."""

from dataclasses import dataclass
import re

from langchain_core.documents import Document

from app.ports.vector_store import VectorStorePort


@dataclass(frozen=True)
class GroundedEvidence:
    value: str
    filename: str
    page_number: int | None
    source_id: str | None

    def citation(self) -> dict[str, str | int | None]:
        return {"filename": self.filename, "page_number": self.page_number}


class DeterministicEvidenceService:
    """Read only exact occurrence evidence; never synthesize provenance."""

    def __init__(self, repository: VectorStorePort) -> None:
        self.repository = repository

    def occurrences(
        self, user_id: str, term: str, filename: str | None = None
    ) -> list[GroundedEvidence]:
        documents = self.repository.exact_occurrence_search(user_id, term, filename)
        evidence: list[GroundedEvidence] = []
        for document in documents:
            parsed = self._from_document(document)
            if parsed is not None:
                evidence.append(parsed)
        return evidence

    def labeled_value(
        self, user_id: str, filename: str, label: str
    ) -> GroundedEvidence | None:
        values: list[GroundedEvidence] = []
        for document in self.repository.exact_occurrence_search(user_id, label, filename):
            value = self._value_from_labeled_line(document.page_content, label)
            parsed = self._from_document(document, value=value) if value else None
            if parsed is not None:
                values.append(parsed)
        unique = {(item.value, item.filename, item.page_number) for item in values}
        if len(unique) != 1:
            return None
        return values[0]

    @staticmethod
    def _value_from_labeled_line(content: str, label: str) -> str | None:
        escaped = re.escape(label)
        match = re.search(rf"(?im)^\s*{escaped}\s*[:|]\s*([^\n|]+?)\s*$", content)
        return match.group(1).strip() if match else None

    @staticmethod
    def _from_document(document: Document, value: str | None = None) -> GroundedEvidence | None:
        filename = document.metadata.get("original_filename")
        if not isinstance(filename, str) or not filename:
            return None
        raw_page = document.metadata.get("page_number")
        try:
            page = int(raw_page) if raw_page is not None else None
        except (TypeError, ValueError):
            return None
        source_id = document.metadata.get("chunk_id") or document.metadata.get("element_id")
        return GroundedEvidence(
            value=value if value is not None else document.page_content,
            filename=filename,
            page_number=page,
            source_id=str(source_id) if source_id else None,
        )
