"""
RAG Service Module - Main Orchestrator (Refactored)

Thin orchestration layer that delegates to specialized services.
Refactored from 1020-line monolith to ~200-line orchestrator.

Architecture:
- DocumentIndexingService: PDF processing, chunking, embedding
- QueryProcessingService: Query classification and reformulation
- AnswerGenerationService: Retrieval, reranking, LLM invocation
- DocumentManagementService: CRUD operations for documents
- ConversationService: Conversation summarization
"""

from typing import List, Optional, Tuple

from app.core.config import settings
from app.core.logging import logger
from app.repositories.dependencies import get_vector_store_repository
from app.repositories.vector_store_repository import VectorStoreRepository
from app.schemas.rag_schema import ConversationMessage
from app.services.answer_generation_service import AnswerGenerationService
from app.services.conversation_service import ConversationService
from app.services.document_classifier_service import document_classifier_service

# Import specialized services
from app.services.document_indexing_service import DocumentIndexingService
from app.services.document_management_service import DocumentManagementService

# Existing services (used by specialized services)
from app.services.language_service import LanguageService
from app.services.query_expansion_service import query_expansion_service
from app.services.query_processing_service import QueryProcessingService
from app.services.reranking_service import reranking_service
from app.services.translation_service import translation_service
from fastapi import Depends, UploadFile
from langchain_openai import ChatOpenAI
from pydantic import SecretStr


class RAGService:
    """
    Main RAG Service - Orchestrator
    
    Thin coordination layer that delegates to specialized services.
    Maintains backward compatibility with existing API.
    
    Refactored from 1020 lines to ~200 lines by extracting:
    - DocumentIndexingService (340 lines)
    - QueryProcessingService (181 lines)
    - AnswerGenerationService (332 lines)
    - DocumentManagementService (167 lines)
    - ConversationService (82 lines)
    """
    
    def __init__(self, repository: VectorStoreRepository):
        """
        Initialize RAG service with repository and specialized services.
        
        Args:
            repository: Vector store repository for data access
        """
        self.repository = repository
        
        # Initialize LLMs
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0.0,
            api_key=SecretStr(settings.OPENAI_API_KEY)
        )
        
        self.query_gen_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
            api_key=SecretStr(settings.OPENAI_API_KEY)
        )
        
        # Initialize shared services
        self.language_service = LanguageService()
        
        # Initialize specialized services with dependencies
        self.indexing_service = DocumentIndexingService(
            repository=repository,
            language_service=self.language_service,
            classifier_service=document_classifier_service
        )
        
        self.query_processing_service = QueryProcessingService(
            llm=self.llm,
            query_gen_llm=self.query_gen_llm
        )
        
        self.answer_generation_service = AnswerGenerationService(
            llm=self.llm,
            repository=repository,
            language_service=self.language_service,
            translation_service=translation_service,
            query_expansion_service=query_expansion_service,
            reranking_service=reranking_service
        )
        
        self.document_management_service = DocumentManagementService(
            repository=repository
        )
        
        self.conversation_service = ConversationService(
            query_gen_llm=self.query_gen_llm
        )
        
        logger.info("✅ RAGService initialized with specialized services")
    
    # === DOCUMENT INDEXING OPERATIONS ===
    
    async def index_document(
        self,
        file: UploadFile,
        user_id: str,
        document_language: Optional[str] = None
    ) -> Tuple[int, str]:
        """
        Delegate to DocumentIndexingService.
        
        Args:
            file: Uploaded PDF file
            user_id: User identifier
            document_language: Optional language code
            
        Returns:
            Tuple of (chunks_indexed, detected_language)
        """
        return await self.indexing_service.index_document(file, user_id, document_language)
    
    async def detect_document_language_preview(
        self,
        file: UploadFile
    ) -> Tuple[str, float]:
        """
        Delegate to DocumentIndexingService.
        
        Args:
            file: Uploaded PDF file
            
        Returns:
            Tuple of (language_code, confidence)
        """
        return await self.indexing_service.detect_document_language_preview(file)
    
    # === QUERY PROCESSING & ANSWER GENERATION ===
    
    def answer_query(
        self,
        query: str,
        user_id: str,
        conversation_history: Optional[List[ConversationMessage]] = None,
        output_language: Optional[str] = None,
        include_files: Optional[List[str]] = None,
        exclude_files: Optional[List[str]] = None
    ) -> Tuple[str, List[str]]:
        """
        Process query and generate answer using RAG pipeline.
        
        Workflow:
        1. Reformulate query (QueryProcessingService)
        2. Classify query (QueryProcessingService)
        3. Generate answer (AnswerGenerationService)
        
        Args:
            query: User's question
            user_id: User identifier
            conversation_history: Optional conversation context
            output_language: Optional target language
            include_files: Optional file filter (include only)
            exclude_files: Optional file filter (exclude)
            
        Returns:
            Tuple of (answer_with_sources, source_filenames)
        """
        conversation_history = conversation_history or []
        
        # Step 1: Reformulate query if needed (handles conversational context)
        reformulated_query = self.query_processing_service.reformulate_query(
            query, conversation_history
        )
        
        # Step 2: Classify query (for future optimizations)
        query_tag = self.query_processing_service.classify_query(reformulated_query)
        logger.info(f"🏷️  Query classified as: {query_tag}")
        
        # Step 3: Generate answer with full RAG pipeline
        return self.answer_generation_service.generate_answer(
            query=reformulated_query,
            user_id=user_id,
            conversation_history=conversation_history,
            output_language=output_language,
            include_files=include_files,
            exclude_files=exclude_files
        )
    
    # === DOCUMENT MANAGEMENT OPERATIONS ===
    
    def get_user_documents(self, user_id: str) -> List:
        """
        Delegate to DocumentManagementService.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of DocumentInfo objects
        """
        return self.document_management_service.get_user_documents(user_id)
    
    def delete_user_document(self, user_id: str, filename: str) -> int:
        """
        Delegate to DocumentManagementService.
        
        Args:
            user_id: User identifier
            filename: Document filename to delete
            
        Returns:
            Number of chunks deleted
        """
        return self.document_management_service.delete_user_document(user_id, filename)
    
    def delete_all_user_documents(self, user_id: str) -> int:
        """
        Delegate to DocumentManagementService.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of chunks deleted
        """
        return self.document_management_service.delete_all_user_documents(user_id)
    
    def get_user_document_count(self, user_id: str) -> int:
        """
        Delegate to DocumentManagementService.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of unique documents
        """
        return self.document_management_service.get_user_document_count(user_id)
    
    # === CONVERSATION OPERATIONS ===
    
    def generate_conversation_summary(
        self,
        conversation_history: List[ConversationMessage]
    ) -> str:
        """
        Delegate to ConversationService.
        
        Args:
            conversation_history: List of conversation messages
            
        Returns:
            Concise summary string
        """
        return self.conversation_service.generate_conversation_summary(conversation_history)


# Dependency injector for FastAPI
def get_rag_service(
    repository: VectorStoreRepository = Depends(get_vector_store_repository),
) -> RAGService:
    """Dependency injector for RAGService."""
    return RAGService(repository=repository)
