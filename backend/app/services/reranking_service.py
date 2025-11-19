"""
Reranking Service Module - Versione 2 (Logarithmic TF Score)

- Migliorato: Il punteggio TF non è più normalizzato sulla lunghezza del documento,
  risolvendo il problema della penalizzazione ingiusta dei chunk lunghi ma pertinenti.
- Nuovo: Il punteggio TF utilizza un boost logaritmico sulla frequenza totale.
- Pulizia: Aggiunto un set base di stop word universali per migliorare la qualità delle keyword.
"""

from typing import List, Set, Tuple
import re
import math
from collections import Counter
from langchain_core.documents import Document

# Stop word universali, agnostiche e comuni (lunghezza > 2)
# Questi sono termini funzionali comuni che possono inquinare il TF-scoring.
UNIVERSAL_STOP_WORDS = {"the", "and", "for", "with", "from", "that", "this", "which"}


class RerankingService:
    """
    Service for lightweight document reranking with an improved, language-agnostic keyword scoring.

    Hybrid Scoring Approach:
    - 60% vector similarity (from initial retrieval order)
    - 40% Logarithmic Term Frequency Score (keyword coverage + frequency boost)
    """

    def __init__(self, vector_weight: float = 0.6, keyword_weight: float = 0.4):
        """
        Initialize the reranking service.
        """
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        # Pre-compila il pattern una sola volta per l'efficienza
        self._word_pattern = re.compile(r"\b\w+\b")

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

        total_tf_count = 0
        keywords_matched = 0

        for kw in keywords:
            count = keyword_counts.get(kw, 0)
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

    def rerank_documents(
        self,
        documents: List[Document],
        original_query: str,
        alternative_queries: List[str],
        top_n: int = 7,
    ) -> List[Document]:
        """
        Rerank documents using hybrid scoring: vector similarity + improved TF-inspired keyword score.
        """
        if not documents:
            return []

        # 1. Estrazione Keywords
        all_queries = [original_query] + alternative_queries
        keywords = self._extract_keywords(all_queries)

        print(
            f"DEBUG [Reranking]: Using {len(keywords)} language-agnostic keywords for reranking"
        )
        print(f"DEBUG [Reranking]: Sample keywords: {list(keywords)[:5]}")

        # 2. Scoring di ogni documento
        scored_docs: List[Tuple[float, Document]] = []
        total_docs = len(documents)

        for i, doc in enumerate(documents):

            # Vector Similarity Score (basato sulla posizione)
            # Rank-based decay: 1.0 per il primo, decresce linearmente fino a quasi 0.0
            vector_score = 1.0 - (i / total_docs)

            # Keyword Score: basato sulla Term Frequency (TF) migliorata
            keyword_score = self._calculate_tf_score(doc.page_content, keywords)

            # Combined score: weighted sum
            combined_score = (
                self.vector_weight * vector_score + self.keyword_weight * keyword_score
            )

            scored_docs.append((combined_score, doc))

        # 3. Ordinamento e Selezione Top N
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        top_docs = [doc for score, doc in scored_docs[:top_n]]

        print(f"DEBUG [Reranking]: Reranked {total_docs} → {len(top_docs)} documents")
        print(
            f"DEBUG [Reranking]: Top 3 scores: {[round(scored_docs[i][0], 3) for i in range(min(3, len(scored_docs)))]}"
        )

        return top_docs


# Singleton instance
reranking_service = RerankingService()
