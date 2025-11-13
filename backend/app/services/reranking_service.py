# backend/app/services/reranking_service.py

"""
Reranking Service Module

Lightweight reranking algorithm that combines vector similarity with keyword matching.
Reduces large document pools to optimal context size for LLM generation.
"""

from typing import List, Set

from langchain_core.documents import Document


class RerankingService:
    """
    Service for lightweight document reranking.
    
    This service applies a hybrid scoring approach:
    - 60% vector similarity (from initial retrieval order)
    - 40% keyword density (matching query terms)
    
    This helps select the most relevant documents without expensive LLM calls.
    """
    
    def __init__(self, vector_weight: float = 0.6, keyword_weight: float = 0.4):
        """
        Initialize the reranking service.
        
        Args:
            vector_weight: Weight for vector similarity score (default: 0.6)
            keyword_weight: Weight for keyword density score (default: 0.4)
        """
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
    
    def _extract_keywords(self, queries: List[str], min_length: int = 3) -> Set[str]:
        """
        Extract significant keywords from a list of queries.
        
        Args:
            queries: List of query strings
            min_length: Minimum word length to be considered a keyword
            
        Returns:
            Set of lowercase keywords
        """
        keywords = set()
        
        for query in queries:
            words = query.lower().split()
            # Filter words: remove short words and punctuation
            keywords.update([
                w.strip('.,!?;:()[]{}"\'') 
                for w in words 
                if len(w) > min_length
            ])
        
        return keywords
    
    def rerank_documents(
        self,
        documents: List[Document],
        original_query: str,
        alternative_queries: List[str],
        top_n: int = 7,
    ) -> List[Document]:
        """
        Rerank documents using hybrid scoring: vector similarity + keyword density.
        
        This method combines:
        1. Vector similarity (implied by retrieval order)
        2. Keyword matching against all query variations
        
        Args:
            documents: List of documents from vector search
            original_query: The user's original query
            alternative_queries: Alternative query phrasings
            top_n: Number of top documents to return (default: 7)
            
        Returns:
            List of top N reranked documents
        """
        if not documents:
            return []
        
        # Extract keywords from all queries
        all_queries = [original_query] + alternative_queries
        keywords = self._extract_keywords(all_queries)
        
        print(f"DEBUG [Reranking]: Using {len(keywords)} keywords for reranking")
        print(f"DEBUG [Reranking]: Sample keywords: {list(keywords)[:10]}")
        
        # Score each document
        scored_docs = []
        for i, doc in enumerate(documents):
            content_lower = doc.page_content.lower()
            
            # Vector similarity score (based on retrieval order)
            # Earlier documents have higher similarity
            vector_score = 1.0 - (i / len(documents))
            
            # Keyword density score
            keyword_matches = sum(1 for kw in keywords if kw in content_lower)
            keyword_density = keyword_matches / len(keywords) if keywords else 0
            
            # Combined score: weighted sum
            combined_score = (
                self.vector_weight * vector_score + 
                self.keyword_weight * keyword_density
            )
            
            scored_docs.append((combined_score, doc))
        
        # Sort by score descending
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        # Select top N documents
        top_docs = [doc for score, doc in scored_docs[:top_n]]
        
        print(f"DEBUG [Reranking]: Reranked {len(documents)} → {len(top_docs)} documents")
        print(f"DEBUG [Reranking]: Top 5 scores: {[round(scored_docs[i][0], 3) for i in range(min(5, len(scored_docs)))]}")
        
        return top_docs
    
    def calculate_relevance_score(
        self,
        document: Document,
        keywords: Set[str],
        position: int,
        total_docs: int
    ) -> float:
        """
        Calculate relevance score for a single document.
        
        Args:
            document: The document to score
            keywords: Set of query keywords
            position: Document position in retrieval results (0-indexed)
            total_docs: Total number of documents retrieved
            
        Returns:
            Combined relevance score (0.0 to 1.0)
        """
        content_lower = document.page_content.lower()
        
        # Vector similarity (based on position)
        vector_score = 1.0 - (position / total_docs) if total_docs > 0 else 0.0
        
        # Keyword density
        keyword_matches = sum(1 for kw in keywords if kw in content_lower)
        keyword_density = keyword_matches / len(keywords) if keywords else 0.0
        
        # Combined score
        return self.vector_weight * vector_score + self.keyword_weight * keyword_density


# Singleton instance
reranking_service = RerankingService()
