"""Bounded, deterministic routing for queries with exact evidence requirements.

This module intentionally recognizes only narrow, language-explicit task shapes.
Anything unclear is routed to the existing RAG path.
"""

from dataclasses import dataclass
from enum import Enum
import re

from app.schemas.rag_schema import ConversationMessage, DocumentInfo


class QueryRoute(str, Enum):
    DIRECT_LOOKUP = "direct_lookup"
    DIRECT_EXTRACT = "direct_extract"
    COMPUTE = "compute"
    RAG = "rag"


class ComputeOperation(str, Enum):
    COUNT = "count"
    SUM = "sum"
    DIFFERENCE = "difference"
    AVERAGE = "average"
    PERCENTAGE = "percentage"
    MIN = "min"
    MAX = "max"
    SORT = "sort"
    DATE_DIFFERENCE = "date_difference"


@dataclass(frozen=True)
class QueryRouteDecision:
    """One route decision; no planner or route retry is permitted."""

    route: QueryRoute
    reason: str
    term: str | None = None
    filename: str | None = None
    field_label: str | None = None
    operation: ComputeOperation | None = None


class DeterministicQueryRouter:
    """Recognize only task shapes whose result can later be fully validated."""

    _COUNT_DOCUMENTS = (
        re.compile(r"^how many documents (?:mention|contain) (?P<term>.+?)\??$", re.I),
        re.compile(r"^quanti documenti (?:menzionano|contengono) (?P<term>.+?)\??$", re.I),
    )
    _DOCUMENTS_MENTION = (
        re.compile(r"^which documents (?:mention|contain) (?P<term>.+?)\??$", re.I),
        re.compile(r"^quali documenti (?:menzionano|contengono) (?P<term>.+?)\??$", re.I),
    )
    _PAGES_MENTION = (
        re.compile(r"^(?:which page|where) (?:contains|is) (?P<term>.+?)(?: mentioned)?\??$", re.I),
        re.compile(r"^(?:in quale pagina|dove) (?:si trova|è|e) (?P<term>.+?)(?: menzionato)?\??$", re.I),
    )
    _EXTRACT = (
        re.compile(r"^(?:what is|show me) (?:the )?value of [\"']?(?P<label>[^\"']+?)[\"']? (?:in|from) (?P<filename>.+\.pdf)\??$", re.I),
        re.compile(r"^qual(?: è| e) il valore di [\"']?(?P<label>[^\"']+?)[\"']? (?:nel|dal) file (?P<filename>.+\.pdf)\??$", re.I),
    )

    def decide(
        self,
        query: str,
        documents: list[DocumentInfo],
        history: list[ConversationMessage],
    ) -> QueryRouteDecision:
        normalized = " ".join(query.split()).strip()
        if history:
            return QueryRouteDecision(QueryRoute.RAG, "conversation_history_requires_rag")
        if not normalized or len(normalized) > 300:
            return QueryRouteDecision(QueryRoute.RAG, "unsupported_query_shape")

        for pattern in self._COUNT_DOCUMENTS:
            match = pattern.fullmatch(normalized)
            if match and self._safe_term(match["term"]):
                return QueryRouteDecision(
                    QueryRoute.COMPUTE,
                    "explicit_document_count",
                    term=self._clean_term(match["term"]),
                    operation=ComputeOperation.COUNT,
                )
        for pattern in self._DOCUMENTS_MENTION:
            match = pattern.fullmatch(normalized)
            if match and self._safe_term(match["term"]):
                return QueryRouteDecision(
                    QueryRoute.DIRECT_LOOKUP,
                    "explicit_document_occurrence_lookup",
                    term=self._clean_term(match["term"]),
                )
        for pattern in self._PAGES_MENTION:
            match = pattern.fullmatch(normalized)
            if match and self._safe_term(match["term"]):
                return QueryRouteDecision(
                    QueryRoute.DIRECT_LOOKUP,
                    "explicit_page_occurrence_lookup",
                    term=self._clean_term(match["term"]),
                )
        for pattern in self._EXTRACT:
            match = pattern.fullmatch(normalized)
            if not match:
                continue
            filename = self._catalog_filename(match["filename"], documents)
            label = " ".join(match["label"].split())
            if filename and self._safe_term(label):
                return QueryRouteDecision(
                    QueryRoute.DIRECT_EXTRACT,
                    "explicit_labeled_value_in_explicit_file",
                    filename=filename,
                    field_label=label,
                )
        return QueryRouteDecision(QueryRoute.RAG, "unsupported_or_ambiguous")

    @staticmethod
    def _clean_term(value: str) -> str:
        return value.strip().strip("\"' ").rstrip("?.!")

    @classmethod
    def _safe_term(cls, value: str) -> bool:
        term = cls._clean_term(value)
        return 2 <= len(term) <= 120 and "\n" not in term

    @staticmethod
    def _catalog_filename(value: str, documents: list[DocumentInfo]) -> str | None:
        candidate = value.strip().rstrip("?.!")
        matches = [doc.filename for doc in documents if doc.filename.casefold() == candidate.casefold()]
        return matches[0] if len(matches) == 1 else None
