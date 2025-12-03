"""
Query Processing Service

Handles query classification and reformulation for improved retrieval.
Extracted from RAGService as part of service splitting (200-300 lines per service).

Responsibilities:
- Classify queries to optimize retrieval strategy
- Reformulate ambiguous/incomplete queries using conversation history
- Detect conversational patterns and query intent
"""

from typing import List

from app.core.config import settings
from app.core.constants import QueryConstants
from app.core.logging import logger
from app.schemas.rag_schema import ConversationMessage, QueryClassification
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

# Query categories for classification
CATEGORIES = [
    "GENERAL_SEARCH",
    "SPECIFIC_INFORMATION",
    "COMPARISON",
    "SUMMARY",
    "EXPLANATION",
]


def _build_classification_prompt() -> PromptTemplate:
    """Build classification prompt from settings."""
    return PromptTemplate(
        input_variables=["categories", "format_instructions", "query"],
        template=settings.CLASSIFICATION_PROMPT_TEMPLATE,
    )


class QueryProcessingService:
    """
    Specialized service for query processing operations.

    Part of RAGService refactoring to maintain 200-300 lines per service.
    """

    def __init__(self, llm: BaseChatModel, query_gen_llm: BaseChatModel) -> None:
        """
        Initialize QueryProcessingService with LLM dependencies.

        Args:
            llm: Main LLM for reformulation (gpt-3.5-turbo or gpt-4)
            query_gen_llm: LLM for query generation/classification (gpt-4o-mini)
        """
        self.llm = llm
        self.query_gen_llm = query_gen_llm

    def classify_query(self, query: str) -> str:
        """
        Classify the query to specialize retrieval.

        Uses LLM to categorize the query for potential future optimizations.

        Args:
            query: The user query to classify

        Returns:
            Category tag string (e.g., 'GENERAL_SEARCH')
        """
        try:
            parser = JsonOutputParser(pydantic_object=QueryClassification)

            classification_prompt = _build_classification_prompt().partial(
                categories=str(CATEGORIES),
                format_instructions=parser.get_format_instructions(),
            )

            chain = classification_prompt | self.query_gen_llm | parser

            result = chain.invoke({"query": query})

            # Handle both 'category_tag' (correct) and 'category' (LLM mistake)
            if isinstance(result, dict):
                if "category_tag" in result:
                    return str(result["category_tag"]).upper()
                elif "category" in result:
                    # Fallback: LLM used wrong key name
                    logger.warning(
                        f"⚠️ LLM returned 'category' instead of 'category_tag': {result}"
                    )
                    return str(result["category"]).upper()
                else:
                    logger.error(
                        f"❌ Classification parsing failed - missing both keys. Result: {result}"
                    )
                    return "GENERAL_SEARCH"
            else:
                logger.error(
                    f"❌ Classification parsing failed - not a dict. Result: {result}"
                )
                return "GENERAL_SEARCH"

        except (ValueError, KeyError, RuntimeError, TypeError) as e:
            logger.error(f"❌ Error classifying query: {e}")
            return "GENERAL_SEARCH"

    def reformulate_query(
        self, query: str, conversation_history: List[ConversationMessage]
    ) -> str:
        """
        Reformulate ambiguous or contextual queries into complete, standalone questions.

        This function detects incomplete queries (e.g., "I mean", "what about", short phrases)
        and uses conversation history to expand them into full, explicit questions.

        Args:
            query: The user's potentially ambiguous query
            conversation_history: Recent conversation messages for context

        Returns:
            Reformulated complete question, or original query if no reformulation needed
        """
        if not self._needs_reformulation(query, conversation_history):
            logger.debug(
                "✅ Query is complete and self-contained, no reformulation needed"
            )
            return query

        logger.info(
            "🔄 Query appears incomplete/ambiguous, attempting reformulation..."
        )
        logger.debug(f"   Original query: {query}")

        return self._attempt_reformulation(query, conversation_history)

    def _needs_reformulation(
        self, query: str, conversation_history: List[ConversationMessage]
    ) -> bool:
        """
        Check if query needs reformulation based on length and patterns.

        Args:
            query: User's query
            conversation_history: Conversation history

        Returns:
            True if reformulation is needed
        """
        query_lower = query.lower().strip()
        min_length = QueryConstants.MIN_QUERY_LENGTH_FOR_REFORMULATION
        is_short = len(query) < min_length
        has_conversational_pattern = any(
            pattern in query_lower for pattern in QueryConstants.CONVERSATIONAL_PATTERNS
        )

        return (is_short or has_conversational_pattern) and bool(conversation_history)

    def _attempt_reformulation(
        self, query: str, conversation_history: List[ConversationMessage]
    ) -> str:
        """
        Attempt to reformulate query using LLM.

        Args:
            query: User's query
            conversation_history: Conversation history

        Returns:
            Reformulated query or original if reformulation fails
        """
        history_text = self._build_history_context(conversation_history)
        reformulation_prompt = self._build_reformulation_prompt(history_text, query)

        try:
            response = self.llm.invoke(reformulation_prompt)
            reformulated_query = str(response.content).strip()

            if self._is_valid_reformulation(reformulated_query):
                logger.info("✅ Query reformulated successfully")
                logger.debug(f"   Original: {query}")
                logger.debug(f"   Reformulated: {reformulated_query}")
                return reformulated_query

            logger.warning(
                "⚠️ Reformulation produced suspicious result, using original query"
            )
            return query

        except (ValueError, RuntimeError, TypeError, AttributeError) as e:
            logger.error(f"❌ Query reformulation failed: {e}")
            logger.info("   Falling back to original query")
            return query

    def _build_history_context(
        self, conversation_history: List[ConversationMessage]
    ) -> str:
        """
        Build conversation context from history.

        Args:
            conversation_history: Recent conversation messages

        Returns:
            Formatted history text
        """
        history_context = []
        for msg in conversation_history[-6:]:  # Last 3 exchanges = 6 messages
            role_label = "User" if msg.role == "user" else "Assistant"
            history_context.append(f"{role_label}: {msg.content}")

        return "\n".join(history_context) if history_context else "No previous context"

    def _build_reformulation_prompt(self, history_text: str, query: str) -> str:
        """
        Build reformulation prompt from settings.

        Args:
            history_text: Formatted conversation history
            query: User's query

        Returns:
            Reformulation prompt
        """
        prompt_template = str(settings.QUERY_REFORMULATION_PROMPT)
        return prompt_template.format(history=history_text, query=query)

    @staticmethod
    def _is_valid_reformulation(reformulated_query: str) -> bool:
        """
        Validate reformulated query length.

        Args:
            reformulated_query: Reformulated query string

        Returns:
            True if reformulation is valid
        """
        return 10 <= len(reformulated_query) <= 300
