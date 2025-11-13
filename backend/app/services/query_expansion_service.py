# backend/app/services/query_expansion_service.py

"""
Query Expansion Service Module

Generates alternative query variations to improve retrieval recall.
Uses multi-query generation to capture different phrasings and keywords.
"""

from typing import List

from app.core.config import settings
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

# Prompt template for generating alternative queries
MULTI_QUERY_PROMPT = (
    "You are a helpful assistant that generates multiple alternative versions of a user's "
    "query to retrieve the most relevant documents from a vector store. "
    "Generate 3 distinct queries for the following user question, ensuring they are diverse "
    "in terms of keywords and phrasing. Return the queries as a newline-separated list (one query per line). "
    "Original Query: {query}"
)


class QueryExpansionService:
    """
    Service for generating alternative query variations.
    
    This service uses LLM to create diverse query phrasings that help
    retrieve more relevant documents by covering different keyword combinations
    and semantic angles.
    """
    
    def __init__(self):
        """Initialize the query expansion service with LLM."""
        # Extract API key securely
        api_key_value = (
            settings.OPENAI_API_KEY.get_secret_value()
            if isinstance(settings.OPENAI_API_KEY, SecretStr)
            else str(settings.OPENAI_API_KEY)
        )
        
        # Use higher temperature for creative query generation
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0.7,
            api_key=SecretStr(api_key_value),
        )
    
    def generate_alternative_queries(self, query: str, num_queries: int = 3) -> List[str]:
        """
        Generate alternative phrasings of a user query.
        
        This method creates diverse query variations to improve retrieval recall
        by capturing different ways users might express the same information need.
        
        Args:
            query: The original user query
            num_queries: Number of alternative queries to generate (default: 3)
            
        Returns:
            List of alternative query strings (up to num_queries items)
        """
        try:
            prompt = MULTI_QUERY_PROMPT.format(query=query)
            response_content = self.llm.invoke(prompt).content

            # Handle both string and list responses
            if isinstance(response_content, list):
                response = "\n\n".join(str(item) for item in response_content)
            else:
                response = str(response_content)

            # Parse alternative queries from response
            alt_queries = [
                q.strip()
                for q in response.split("\n")
                if q.strip() and len(q.strip()) > 5
            ]

            # Limit to requested number
            result = alt_queries[:num_queries]
            
            print(f"DEBUG [QueryExpansion]: Generated {len(result)} alternative queries")
            return result

        except Exception as e:
            print(f"Error generating alternative queries: {e}")
            return []
    
    def expand_query_pool(self, original_query: str) -> List[str]:
        """
        Create a full query pool including the original and alternatives.
        
        Args:
            original_query: The user's original query
            
        Returns:
            List containing original query + alternative queries
        """
        alternatives = self.generate_alternative_queries(original_query)
        return [original_query] + alternatives


# Singleton instance
query_expansion_service = QueryExpansionService()
