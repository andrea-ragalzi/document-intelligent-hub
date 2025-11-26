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

from app.core.constants import QueryConstants
from app.core.logging import logger
from app.schemas.rag_schema import ConversationMessage, QueryClassification
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser

# Query categories for classification
CATEGORIES = [
    "GENERAL_SEARCH",
    "SPECIFIC_INFORMATION",
    "COMPARISON",
    "SUMMARY",
    "EXPLANATION"
]


def _build_classification_prompt():
    """Build classification prompt from settings."""
    from app.core.config import settings
    from langchain_core.prompts import PromptTemplate
    
    return PromptTemplate(
        input_variables=["categories", "format_instructions", "query"],
        template=settings.CLASSIFICATION_PROMPT_TEMPLATE
    )


class QueryProcessingService:
    """
    Specialized service for query processing operations.
    
    Part of RAGService refactoring to maintain 200-300 lines per service.
    """
    
    def __init__(
        self,
        llm: BaseChatModel,
        query_gen_llm: BaseChatModel
    ):
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
                    return result["category_tag"].upper()
                elif "category" in result:
                    # Fallback: LLM used wrong key name
                    logger.warning(f"⚠️ LLM returned 'category' instead of 'category_tag': {result}")
                    return result["category"].upper()
                else:
                    logger.error(f"❌ Classification parsing failed - missing both keys. Result: {result}")
                    return "GENERAL_SEARCH"
            else:
                logger.error(f"❌ Classification parsing failed - not a dict. Result: {result}")
                return "GENERAL_SEARCH"

        except Exception as e:
            logger.error(f"❌ Error classifying query: {e}")
            return "GENERAL_SEARCH"

    def reformulate_query(
        self, 
        query: str, 
        conversation_history: List[ConversationMessage]
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
        # Check if reformulation is needed
        query_lower = query.lower().strip()
        needs_reformulation = (
            len(query) < QueryConstants.MIN_QUERY_LENGTH_FOR_REFORMULATION or  # Very short query
            any(pattern in query_lower for pattern in QueryConstants.CONVERSATIONAL_PATTERNS)  # Contains conversational connector
        )
        
        if not needs_reformulation or not conversation_history:
            logger.debug("✅ Query is complete and self-contained, no reformulation needed")
            return query
        
        logger.info("🔄 Query appears incomplete/ambiguous, attempting reformulation...")
        logger.debug(f"   Original query: {query}")
        
        # Build conversation context (last 3 exchanges maximum)
        history_context = []
        for msg in conversation_history[-6:]:  # Last 3 exchanges = 6 messages
            role_label = "User" if msg.role == "user" else "Assistant"
            history_context.append(f"{role_label}: {msg.content}")
        
        history_text = "\n".join(history_context) if history_context else "No previous context"
        
        # Build reformulation prompt from settings
        from app.core.config import settings
        reformulation_prompt = settings.QUERY_REFORMULATION_PROMPT.format(
            history=history_text,
            query=query
        )

        try:
            # Use cost-effective LLM (gpt-3.5-turbo) for this simple task
            response = self.llm.invoke(reformulation_prompt)
            reformulated_query = str(response.content).strip()
            
            # Validate reformulation (basic sanity check)
            if len(reformulated_query) < 10 or len(reformulated_query) > 300:
                logger.warning("⚠️ Reformulation produced suspicious result, using original query")
                return query
            
            logger.info("✅ Query reformulated successfully")
            logger.debug(f"   Original: {query}")
            logger.debug(f"   Reformulated: {reformulated_query}")
            
            return reformulated_query
            
        except Exception as e:
            logger.error(f"❌ Query reformulation failed: {e}")
            logger.info("   Falling back to original query")
            return query
