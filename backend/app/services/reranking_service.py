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
        self._identifier_pattern = re.compile(r"\b[\w]+(?:[_-][\w]+)+\b")

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

        # 1. Estrazione Keywords
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

        document_coverage = self._document_coverage(documents, keywords)
        page_aggregates = [
            document
            for document in documents
            if document.metadata.get("context_aggregation") is True
        ]
        replaceable_atomic_ids = {
            id(document)
            for document in documents
            if document.metadata.get("context_aggregation") is not True
            and any(
                self._aggregate_preserves_atomic(aggregate, document)
                for aggregate in page_aggregates
            )
        }

        # 2. Scoring di ogni documento
        scored_docs: List[Tuple[float, Document]] = []
        total_docs = len(documents)

        for i, doc in enumerate(documents):

            # Vector Similarity Score (basato sulla posizione)
            # Rank-based decay: 1.0 per il primo, decresce linearmente fino a quasi 0.0
            vector_score = 1.0 - (i / total_docs)

            # Keyword Score: basato sulla Term Frequency (TF) migliorata
            keyword_score = self._calculate_tf_score(doc.page_content, keywords)
            subquery_score = max(
                (
                    self._calculate_tf_score(doc.page_content, query_keywords)
                    for query_keywords in subquery_keywords
                    if query_keywords
                ),
                default=0.0,
            )
            metadata_score = self._metadata_score(doc, keywords)
            filename = str(doc.metadata.get("original_filename", ""))
            document_score = document_coverage.get(filename, 0.0)
            identifier_score = self._identifier_score(doc, all_queries)
            context_score = (
                0.5
                if doc.metadata.get("context_aggregation") is True and keyword_score > 0
                else 0.0
            )

            # Combined score: weighted sum
            combined_score = (
                self.vector_weight * vector_score
                + self.keyword_weight * keyword_score
                + self.metadata_weight * max(metadata_score, document_score)
                + 0.35 * identifier_score
                + 0.25 * subquery_score
                + context_score
            )
            doc.metadata["rerank_score"] = round(combined_score, 6)

            scored_docs.append((combined_score, doc))

        # 3. Ordinamento e Selezione Top N
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        top_docs: List[Document] = []
        seen_content: set[str] = set()

        # Compound questions need one strong candidate for each independently
        # retrievable fact before global relevance fills the remaining positions.
        for query_group in required_query_groups or []:
            group_keywords = self._extract_keywords([query_group])
            if not group_keywords:
                continue
            group_candidates = sorted(
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
            eligible_candidates = [
                candidate
                for candidate in group_candidates
                if candidate[0] > 0
                and id(candidate[1]) not in replaceable_atomic_ids
            ]
            if not eligible_candidates:
                continue
            candidate = eligible_candidates[0][1]
            supported_groups = candidate.metadata.setdefault(
                "supported_query_groups", []
            )
            if query_group not in supported_groups:
                supported_groups.append(query_group)
            normalized_content = " ".join(candidate.page_content.lower().split())
            if normalized_content not in seen_content:
                seen_content.add(normalized_content)
                top_docs.append(candidate)
            if len(top_docs) == top_n:
                break

        eligible_scored_docs = [
            (score, document)
            for score, document in scored_docs
            if id(document) not in replaceable_atomic_ids
        ]
        best_score = eligible_scored_docs[0][0] if eligible_scored_docs else 0.0
        covered_keywords: set[str] = set()
        selected_filenames: set[str] = set()
        for document in top_docs:
            covered_keywords.update(
                self._content_keyword_matches(document, keywords)
            )
            selected_filenames.add(
                str(document.metadata.get("original_filename", ""))
            )

        requests_multiple_sources = bool(
            MULTI_SOURCE_REQUEST_PATTERN.search(original_query)
        )

        for score, document in eligible_scored_docs:
            if len(top_docs) == top_n:
                break
            normalized_content = " ".join(document.page_content.lower().split())
            if normalized_content in seen_content:
                continue
            if top_docs:
                content_matches = self._content_keyword_matches(document, keywords)
                contributes_new_support = bool(content_matches - covered_keywords)
                filename = str(document.metadata.get("original_filename", ""))
                contributes_requested_source = (
                    requests_multiple_sources
                    and filename not in selected_filenames
                    and score >= best_score * 0.7
                )
                if score < best_score * 0.55 or not (
                    contributes_new_support or contributes_requested_source
                ):
                    continue
            seen_content.add(normalized_content)
            top_docs.append(document)
            covered_keywords.update(
                self._content_keyword_matches(document, keywords)
            )
            selected_filenames.add(
                str(document.metadata.get("original_filename", ""))
            )

        print(f"DEBUG [Reranking]: Reranked {total_docs} → {len(top_docs)} documents")
        top_3_scores = [
            round(scored_docs[i][0], 3) for i in range(min(3, len(scored_docs)))
        ]
        print(f"DEBUG [Reranking]: Top 3 scores: {top_3_scores}")

        return top_docs

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
