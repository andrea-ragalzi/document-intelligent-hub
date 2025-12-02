"""
Query Expansion Service Module

Generates alternative query variations to improve retrieval recall.
Uses multi-query generation to capture different phrasings and keywords.
"""

from typing import List

from app.core.config import settings
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

# Prompt template for generating alternative queries in English, focusing on key Italian terms.
MULTI_QUERY_PROMPT = (
    "You are an assistant that generates alternative, atomic versions of a user's query "
    "to maximize retrieval. Generate 5 distinct queries for the following question. "
    "Ensure some queries are very short and focus only on PROPER NOUNS, IDs, and CRITICAL TERMS "
    "(e.g., JURASSIC-LOCK, Ammontare, Nome Fondo). "
    "Return the queries as a newline-separated list (one query per line). "
    "Example Output: \nQuery 1\nQuery 2\nQuery 3\n"
    "Original Query (Italian): {query}"
)


class QueryExpansionService:
    """
    Service for generating alternative query variations.

    This service uses LLM to create diverse query phrasings that help
    retrieve more relevant documents by covering different keyword combinations
    and semantic angles.
    """

    def __init__(self) -> None:
        """Initialize the query expansion service with LLM."""
        # Extract API key securely
        api_key_value = (
            settings.OPENAI_API_KEY.get_secret_value()
            if isinstance(settings.OPENAI_API_KEY, SecretStr)
            else str(settings.OPENAI_API_KEY)
        )

        # Use higher temperature for creative, diverse query generation
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0.8,  # Increased temperature for diversity
            api_key=SecretStr(api_key_value),
        )

    def generate_alternative_queries(
        self, query: str, num_queries: int = 5
    ) -> List[str]:
        """
        Generate alternative phrasings of a user query.

        This method creates diverse query variations to improve retrieval recall
        by capturing different ways users might express the same information need.
        It is aggressive in generating atomic queries based on key entity names.

        Args:
            query: The original user query
            num_queries: Number of alternative queries to generate (default is 5)

        Returns:
            List of alternative query strings (up to num_queries items)
        """
        try:
            # Format the prompt with the original query
            prompt = MULTI_QUERY_PROMPT.format(query=query)
            # Invoke the LLM to get the expanded queries
            response_content = self.llm.invoke(prompt, max_tokens=150).content

            # Handle parsing response content (list or string)
            if isinstance(response_content, list):
                response_text = "\n\n".join(str(item) for item in response_content)
            else:
                response_text = str(response_content)

            # Parse alternative queries from response, splitting by newline
            # Filter out empty or too short strings
            alt_queries = [
                q.strip()
                for q in response_text.split("\n")
                if q.strip() and len(q.strip()) > 5
            ]

            # Limit to requested number (default 5)
            result = alt_queries[:num_queries]

            print(
                f"DEBUG [QueryExpansion]: Generated {len(result)} alternative queries in English"
            )
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
        # Generate 5 alternatives, resulting in a pool of 6 (original + 5 alternatives)
        alternatives = self.generate_alternative_queries(original_query, num_queries=5)
        return [original_query] + alternatives


# Singleton instance
query_expansion_service = QueryExpansionService()
