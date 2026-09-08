"""Lightweight hybrid reranking for semantically retrieved document chunks."""

import math
import re
from collections import Counter
from typing import Any, List, Set, Tuple

from langchain_core.documents import Document

# Stop word universali, agnostiche e comuni (lunghezza > 2)
# Questi sono termini funzionali comuni che possono inquinare il TF-scoring.
UNIVERSAL_STOP_WORDS = {
    "the", "and", "for", "with", "from", "that", "this", "which",
    "che", "cosa", "quale", "quali", "qual", "chi", "come", "perche", "perché",
    "del", "dello", "della", "dei", "degli", "delle", "alla", "allo", "alle",
    "nel", "nello", "nella", "nei", "nelle", "una", "uno", "sono", "hanno",
    "invece", "questo", "questa", "quello", "quella", "esattamente", "presenta",
}
MULTI_SOURCE_REQUEST_PATTERN = re.compile(
    r"\b(?:quali\s+documenti|which\s+documents|which\s+sources)\b", re.IGNORECASE
)


class RerankingService:
    """
    Service for lightweight document reranking with an improved, language-agnostic keyword scoring.

    Hybrid Scoring Approach:
    - 40% vector rank signal from the initial semantic retrieval
    - 45% lexical coverage and phrase matches in the chunk
    - 15% title and document-level relevance signal
    """

    def __init__(
        self,
        vector_weight: float = 0.4,
        keyword_weight: float = 0.45,
        metadata_weight: float = 0.15,
    ) -> None:
        """
        Initialize the reranking service.
        """
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        self.metadata_weight = metadata_weight
        # Pre-compila il pattern una sola volta per l'efficienza
        self._word_pattern = re.compile(r"\b\w+\b")
        # ``\w`` includes underscores. Excluding separators from each segment
        # makes the expression unambiguous and avoids exponential backtracking.
        self._identifier_pattern = re.compile(r"\b[^\W_-]+(?:[_-][^\W_-]+)+\b")

    @staticmethod
    def _stem(token: str) -> str:
        """Apply a tiny language-neutral suffix normalization for title matching."""
        return token[:-1] if len(token) > 4 and token[-1] in "aeiou" else token

    def _extract_keywords(self, queries: List[str], min_length: int = 3) -> Set[str]:
        """
        Extract significant keywords from a list of queries.

        This method is LANGUAGE-AGNOSTIC, using a small set of universal stop words
        in addition to minimum length filtering.

        Args:
            queries: List of query strings
            min_length: Minimum word length to be considered a keyword

        Returns:
            Set of lowercase, cleaned keywords
        """
        keywords = set()

        for query in queries:
            words = self._word_pattern.findall(query.lower())
            # Filtering: min length AND not in universal stop word list
            keywords.update(
                [
                    w
                    for w in words
                    if len(w) >= min_length and w not in UNIVERSAL_STOP_WORDS
                ]
            )

        return keywords

    def _calculate_tf_score(self, document_content: str, keywords: Set[str]) -> float:
        """
        Calculate a Term Frequency (TF) score using a combination of unique match coverage
        and a logarithmic frequency boost. This is less sensitive alla lunghezza del documento.

        New Logic: Base Coverage Score + Logarithmic Frequency Boost.

        Args:
            document_content: The text of the document chunk.
            keywords: The set of keywords extracted from the query.

        Returns:
            Relevance score (0.0 or higher)
        """
        if not keywords:
            return 0.0

        # Tokenizza il contenuto del documento usando il pattern pre-compilato
        doc_tokens = self._word_pattern.findall(document_content.lower())

        # Conta le occorrenze dei token del documento che sono anche keyword
        keyword_counts = Counter(doc_tokens)
        stemmed_counts = Counter(self._stem(token) for token in doc_tokens)

        total_tf_count = 0
        keywords_matched = 0

        for kw in keywords:
            count = max(keyword_counts.get(kw, 0), stemmed_counts.get(self._stem(kw), 0))
            if count > 0:
                total_tf_count += count
                keywords_matched += 1

        if keywords_matched > 0:
            # 1. Punteggio di Copertura (Unique Match Coverage) - 0.0 a 1.0
            unique_match_ratio = keywords_matched / len(keywords)

            # 2. Boost Logaritmico sulla Frequenza
            # +1 per evitare log(0). 0.1 è un fattore di scaling per mantenere il boost piccolo.
            frequency_boost = math.log(total_tf_count + 1) * 0.1

            # Combined Score: La copertura è la base, il boost logaritmico fornisce l'intensità.
            # Questo evita la penalizzazione sulla lunghezza del documento.
            return unique_match_ratio * (1.0 + frequency_boost)

        return 0.0

    def _metadata_score(self, document: Document, keywords: Set[str]) -> float:
        """Score filename and section metadata without treating it as answer content."""
        metadata: dict[str, Any] = document.metadata
        title = " ".join(
            str(metadata.get(field, ""))
            for field in ("original_filename", "chapter_title")
        )
        title_tokens = self._word_pattern.findall(title.lower())
        if not title_tokens or not keywords:
            return 0.0

        title_stems = {self._stem(token) for token in title_tokens}
        matches = sum(1 for keyword in keywords if self._stem(keyword) in title_stems)
        return matches / len(keywords)

    def _identifier_score(self, document: Document, queries: List[str]) -> float:
        """Boost exact technical IDs only when the full identifier is in the chunk."""
        identifiers = {
            identifier.lower()
            for query in queries
            for identifier in self._identifier_pattern.findall(query)
            if any(character.isdigit() for character in identifier) or "_" in identifier
        }
        if not identifiers:
            return 0.0

        document_text = document.page_content.lower()
        return 1.0 if any(identifier in document_text for identifier in identifiers) else 0.0

    @staticmethod
    def _document_coverage(documents: List[Document], keywords: Set[str]) -> dict[str, float]:
        """Capture facts split across structural chunks in the same source document."""
        grouped_text: dict[str, list[str]] = {}
        for document in documents:
            filename = str(document.metadata.get("original_filename", ""))
            grouped_text.setdefault(filename, []).append(document.page_content.lower())

        if not keywords:
            return {filename: 0.0 for filename in grouped_text}

        return {
            filename: sum(keyword in " ".join(texts) for keyword in keywords) / len(keywords)
            for filename, texts in grouped_text.items()
        }

    def rerank_documents(
        self,
        documents: List[Document],
        original_query: str,
        alternative_queries: List[str],
        top_n: int = 7,
        *,
        required_query_groups: List[str] | None = None,
    ) -> List[Document]:
        """
        Rerank documents using hybrid scoring:
        vector similarity + improved TF-inspired keyword score.
        """
        if not documents:
            return []

        # Expansion variants improve recall, but must not redefine relevance:
        # their generated vocabulary can otherwise outrank a direct answer to
        # the user's original question.
        all_queries = [original_query]
        keywords = self._extract_keywords(all_queries)
        subquery_keywords = [
            self._extract_keywords([query]) for query in required_query_groups or []
        ]

        print(
            f"DEBUG [Reranking]: Using {len(keywords)} language-agnostic keywords for reranking"
        )
        print(f"DEBUG [Reranking]: Sample keywords: {list(keywords)[:5]}")

        replaceable_atomic_ids = self._replaceable_atomic_ids(documents)
        scored_docs = self._score_documents(
            documents, keywords, subquery_keywords, all_queries
        )
        top_docs, seen_content = self._select_required_group_documents(
            documents,
            required_query_groups or [],
            replaceable_atomic_ids,
            top_n,
        )
        eligible_scored_docs = [
            (score, document)
            for score, document in scored_docs
            if id(document) not in replaceable_atomic_ids
        ]
        self._extend_with_distinct_evidence(
            top_docs,
            seen_content,
            eligible_scored_docs,
            keywords,
            original_query,
            top_n,
        )

        print(f"DEBUG [Reranking]: Reranked {len(documents)} → {len(top_docs)} documents")
        top_3_scores = [
            round(scored_docs[i][0], 3) for i in range(min(3, len(scored_docs)))
        ]
        print(f"DEBUG [Reranking]: Top 3 scores: {top_3_scores}")

        return top_docs

    def _replaceable_atomic_ids(self, documents: List[Document]) -> set[int]:
        """Find atomic chunks fully preserved by an aggregate from the same page."""
        page_aggregates = [
            document
            for document in documents
            if document.metadata.get("context_aggregation") is True
        ]
        return {
            id(document)
            for document in documents
            if document.metadata.get("context_aggregation") is not True
            and any(
                self._aggregate_preserves_atomic(aggregate, document)
                for aggregate in page_aggregates
            )
        }

    def _score_documents(
        self,
        documents: List[Document],
        keywords: Set[str],
        subquery_keywords: List[Set[str]],
        queries: List[str],
    ) -> List[Tuple[float, Document]]:
        """Apply hybrid relevance scoring while preserving initial vector rank."""
        coverage = self._document_coverage(documents, keywords)
        scored_documents = [
            self._score_document(
                document,
                index,
                len(documents),
                keywords,
                subquery_keywords,
                queries,
                coverage,
            )
            for index, document in enumerate(documents)
        ]
        scored_documents.sort(key=lambda item: item[0], reverse=True)
        return scored_documents

    def _score_document(  # pylint: disable=too-many-arguments
        self,
        document: Document,
        index: int,
        total_documents: int,
        keywords: Set[str],
        subquery_keywords: List[Set[str]],
        queries: List[str],
        coverage: dict[str, float],
    ) -> Tuple[float, Document]:
        """Calculate and record the combined relevance score for one chunk."""
        vector_score = 1.0 - (index / total_documents)
        keyword_score = self._calculate_tf_score(document.page_content, keywords)
        subquery_score = max(
            (
                self._calculate_tf_score(document.page_content, query_keywords)
                for query_keywords in subquery_keywords
                if query_keywords
            ),
            default=0.0,
        )
        metadata_score = self._metadata_score(document, keywords)
        filename = str(document.metadata.get("original_filename", ""))
        identifier_score = self._identifier_score(document, queries)
        context_score = (
            0.5
            if document.metadata.get("context_aggregation") is True
            and keyword_score > 0
            else 0.0
        )
        combined_score = (
            self.vector_weight * vector_score
            + self.keyword_weight * keyword_score
            + self.metadata_weight * max(metadata_score, coverage.get(filename, 0.0))
            + 0.35 * identifier_score
            + 0.25 * subquery_score
            + context_score
        )
        document.metadata["rerank_score"] = round(combined_score, 6)
        return combined_score, document

    def _select_required_group_documents(
        self,
        documents: List[Document],
        query_groups: List[str],
        replaceable_atomic_ids: set[int],
        top_n: int,
    ) -> Tuple[List[Document], set[str]]:
        """Reserve one strong evidence candidate for each compound-query part."""
        selected: List[Document] = []
        seen_content: set[str] = set()
        for query_group in query_groups:
            candidate = self._best_group_candidate(
                documents, query_group, replaceable_atomic_ids
            )
            if candidate is None:
                continue
            supported_groups = candidate.metadata.setdefault(
                "supported_query_groups", []
            )
            if query_group not in supported_groups:
                supported_groups.append(query_group)
            normalized_content = self._normalize_content(candidate)
            if normalized_content not in seen_content:
                seen_content.add(normalized_content)
                selected.append(candidate)
            if len(selected) == top_n:
                break
        return selected, seen_content

    def _best_group_candidate(
        self,
        documents: List[Document],
        query_group: str,
        replaceable_atomic_ids: set[int],
    ) -> Document | None:
        """Return the strongest eligible chunk for one retrieval subquery."""
        group_keywords = self._extract_keywords([query_group])
        if not group_keywords:
            return None
        candidates = sorted(
            (
                (
                    self._calculate_tf_score(document.page_content, group_keywords)
                    + self._metadata_score(document, group_keywords),
                    document,
                )
                for document in documents
            ),
            key=lambda candidate: candidate[0],
            reverse=True,
        )
        return next(
            (
                document
                for score, document in candidates
                if score > 0 and id(document) not in replaceable_atomic_ids
            ),
            None,
        )

    def _extend_with_distinct_evidence(  # pylint: disable=too-many-arguments
        self,
        selected: List[Document],
        seen_content: set[str],
        scored_documents: List[Tuple[float, Document]],
        keywords: Set[str],
        original_query: str,
        top_n: int,
    ) -> None:
        """Fill remaining positions only with evidence adding distinct support."""
        best_score = scored_documents[0][0] if scored_documents else 0.0
        covered_keywords, selected_filenames = self._selection_coverage(
            selected, keywords
        )
        requests_multiple_sources = bool(
            MULTI_SOURCE_REQUEST_PATTERN.search(original_query)
        )
        for score, document in scored_documents:
            if len(selected) == top_n:
                break
            normalized_content = self._normalize_content(document)
            if normalized_content in seen_content:
                continue
            content_matches = self._content_keyword_matches(document, keywords)
            filename = str(document.metadata.get("original_filename", ""))
            if selected and not self._adds_distinct_support(
                score,
                best_score,
                content_matches,
                covered_keywords,
                filename,
                selected_filenames,
                requests_multiple_sources,
            ):
                continue
            seen_content.add(normalized_content)
            selected.append(document)
            covered_keywords.update(content_matches)
            selected_filenames.add(filename)

    @staticmethod
    def _adds_distinct_support(  # pylint: disable=too-many-arguments
        score: float,
        best_score: float,
        content_matches: Set[str],
        covered_keywords: Set[str],
        filename: str,
        selected_filenames: Set[str],
        requests_multiple_sources: bool,
    ) -> bool:
        """Decide whether another ranked chunk adds material answer support."""
        contributes_new_support = bool(content_matches - covered_keywords)
        contributes_requested_source = (
            requests_multiple_sources
            and filename not in selected_filenames
            and score >= best_score * 0.7
        )
        return score >= best_score * 0.55 and (
            contributes_new_support or contributes_requested_source
        )

    def _selection_coverage(
        self, selected: List[Document], keywords: Set[str]
    ) -> Tuple[Set[str], Set[str]]:
        """Collect covered query terms and filenames for selected evidence."""
        covered_keywords: Set[str] = set()
        selected_filenames: Set[str] = set()
        for document in selected:
            covered_keywords.update(self._content_keyword_matches(document, keywords))
            selected_filenames.add(str(document.metadata.get("original_filename", "")))
        return covered_keywords, selected_filenames

    @staticmethod
    def _normalize_content(document: Document) -> str:
        """Normalize chunk text for exact duplicate suppression."""
        return " ".join(document.page_content.lower().split())

    def _content_keyword_matches(
        self, document: Document, keywords: Set[str]
    ) -> Set[str]:
        """Return query keywords supported by chunk text, excluding title-only hits."""
        document_stems = {
            self._stem(token)
            for token in self._word_pattern.findall(document.page_content.lower())
        }
        return {
            keyword
            for keyword in keywords
            if self._stem(keyword) in document_stems
        }

    @staticmethod
    def _page_key(document: Document) -> Tuple[str, str]:
        """Identify a source page so its aggregate replaces atomic fragments."""
        return (
            str(document.metadata.get("original_filename", "")),
            str(document.metadata.get("page_number", "")),
        )

    @classmethod
    def _aggregate_preserves_atomic(
        cls, aggregate: Document, atomic: Document
    ) -> bool:
        """Replace an atomic chunk only when the same-page aggregate contains it."""
        if cls._page_key(aggregate) != cls._page_key(atomic):
            return False
        aggregate_text = " ".join(aggregate.page_content.lower().split())
        atomic_text = " ".join(atomic.page_content.lower().split())
        return bool(atomic_text) and atomic_text in aggregate_text


# Singleton instance
reranking_service = RerankingService()
