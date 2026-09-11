"""
Query Processing Service

Handles query classification and reformulation for improved retrieval.
Extracted from RAGService as part of service splitting (200-300 lines per service).

Responsibilities:
- Classify queries to optimize retrieval strategy
- Reformulate ambiguous/incomplete queries using conversation history
- Detect conversational patterns and query intent
"""

import re

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from app.core.config import settings
from app.core.constants import QueryConstants
from app.core.logging import logger
from app.schemas.rag_schema import ConversationMessage, QueryClassification

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
        input_variables=["categories", "query"],
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
            llm: Configured LLM for reformulation
            query_gen_llm: Configured LLM for query generation/classification
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
            classification_prompt = _build_classification_prompt().partial(
                categories=str(CATEGORIES),
            )

            structured_llm = self.query_gen_llm.with_structured_output(
                QueryClassification
            )
            result = structured_llm.invoke(
                classification_prompt.format(query=query)
            )
            if not isinstance(result, QueryClassification):
                result = QueryClassification.model_validate(result)
            return result.category_tag.upper()

        except (ValueError, KeyError, RuntimeError, TypeError) as e:
            logger.error(f"❌ Error classifying query: {e}")
            return "GENERAL_SEARCH"

    def reformulate_query(
        self, query: str, conversation_history: list[ConversationMessage]
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
        if not self.requires_conversation_context(query, conversation_history):
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
        self, query: str, conversation_history: list[ConversationMessage]
    ) -> bool:
        """
        Check if query needs reformulation based on length and patterns.

        Args:
            query: User's query
            conversation_history: Conversation history

        Returns:
            True if reformulation is needed
        """
        return self.requires_conversation_context(query, conversation_history)

    def requires_conversation_context(
        self, query: str, conversation_history: list[ConversationMessage]
    ) -> bool:
        """Return whether this turn needs history to resolve a reference."""
        query_lower = query.lower().strip()
        min_length = QueryConstants.MIN_QUERY_LENGTH_FOR_REFORMULATION
        is_short = len(query) < min_length
        has_conversational_pattern = any(
            pattern in query_lower for pattern in QueryConstants.CONVERSATIONAL_PATTERNS
        )

        if not ((is_short or has_conversational_pattern) and conversation_history):
            return False

        # A short question with a named subject is already self-contained.
        words = re.findall(r"\b[A-ZÀ-ÖØ-Þ][\w-]*\b", query)
        has_named_subject = len(words) > 1 or (len(words) == 1 and not query.startswith(words[0]))
        return not has_named_subject

    def _attempt_reformulation(
        self, query: str, conversation_history: list[ConversationMessage]
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
        self, conversation_history: list[ConversationMessage]
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
            role_label = "U" if msg.role == "user" else "A"
            history_context.append(f"{role_label}|{msg.content}")

        return "\n".join(history_context)

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
