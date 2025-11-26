"""
Conversation Service

Handles conversation history summarization for long-term memory.
Extracted from RAGService as part of service splitting (200-300 lines per service).

Responsibilities:
- Generate concise conversation summaries
- Extract key facts and topics from history
- Support long-term memory in RAG conversations
"""

from typing import List

from app.core.logging import logger
from app.schemas.rag_schema import ConversationMessage
from langchain_core.language_models import BaseChatModel


class ConversationService:
    """
    Specialized service for conversation management operations.
    
    Part of RAGService refactoring to maintain 200-300 lines per service.
    Handles summarization for long conversation histories.
    """
    
    def __init__(self, query_gen_llm: BaseChatModel):
        """
        Initialize ConversationService.
        
        Args:
            query_gen_llm: LLM for summary generation (gpt-4o-mini for cost efficiency)
        """
        self.query_gen_llm = query_gen_llm
    
    def generate_conversation_summary(self, conversation_history: List[ConversationMessage]) -> str:
        """
        Generate a concise summary of conversation history for long-term memory.
        
        This is used when the history becomes too long (e.g., > 20 messages).
        The summary extracts key facts, topics, and ongoing issues to maintain
        context without sending full history to LLM.
        
        Args:
            conversation_history: List of conversation messages to summarize
        
        Returns:
            Concise summary string (3-5 sentences)
        """
        try:
            # Build conversation text
            conversation_text = "\n".join([
                f"{msg.role.upper()}: {msg.content}"
                for msg in conversation_history
            ])
            
            # Summarization prompt
            summary_prompt = f"""You are a conversation summarizer. Generate a concise summary of the following conversation.

Extract:
- Key facts and information discussed
- Main topics and questions
- Ongoing issues or unresolved questions
- Important context for future queries

CONVERSATION:
{conversation_text}

SUMMARY (3-5 sentences):"""
            
            # Use cost-effective LLM (gpt-4o-mini) for summarization
            response = self.query_gen_llm.invoke(summary_prompt)
            summary = str(response.content).strip()
            
            logger.info(f"✅ Generated conversation summary ({len(summary)} chars)")
            logger.debug(f"   Summary: {summary[:100]}...")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Conversation summarization failed: {e}")
            return "Unable to generate summary."
