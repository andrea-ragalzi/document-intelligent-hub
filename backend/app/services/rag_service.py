"""
RAG Service Module - Main Orchestrator

Coordinates document indexing, retrieval, and answer generation.
Delegates specialized tasks to dedicated service modules for better maintainability.
Uses Repository Pattern for data access abstraction.
"""

import os
from typing import List, Optional, Tuple

# Core imports
from app.core.config import settings
from app.core.logging import logger
from app.repositories.dependencies import get_vector_store_repository
from app.repositories.vector_store_repository import VectorStoreRepository
from app.schemas.rag_schema import (
    CATEGORIES,
    ConversationMessage,
    DocumentInfo,
    QueryClassification,
)
from app.schemas.use_cases import UseCaseType

# Specialized service imports
from app.services.language_service import RETRIEVAL_TARGET_LANGUAGE, LanguageService
from app.services.prompt_template_service import prompt_template_service
from app.services.query_expansion_service import query_expansion_service
from app.services.reranking_service import reranking_service
from app.services.translation_service import translation_service
from app.services.use_case_detection_service import use_case_detection_service

# FastAPI and document processing
from fastapi import Depends, UploadFile
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.documents import Document
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

# --- CONSTANTS & CONFIGURATION ---

# Document limit for each embedding batch
EMBEDDING_DOC_BATCH_SIZE = 2000

# System instruction to prevent hallucination and enforce compliance
SYSTEM_INSTRUCTION = (
    "You are an intelligent document assistant and expert analyst. "
    "Your main objective is to answer user questions based on the provided context (source documents). "
    "\n\nIMPORTANT RULES:\n"
    "1. Answer using information from the provided context\n"
    "2. If you can find ANY relevant information in the context, provide it even if partial\n"
    "3. Only say 'I cannot answer this question based on the documents provided' if the context contains NO relevant information at all\n"
    "4. When multiple relevant pieces of information are found across different sections, synthesize them into a coherent answer\n"
    "5. If asked for lists of people, places, or entities: extract ALL specific names mentioned in the context, even if scattered across multiple sections\n"
    "6. When creating lists, prioritize specific names over general categories or roles\n"
    "7. Be comprehensive - include all relevant details and specific names found in the context"
)

# Prompt for query classification
CLASSIFICATION_PROMPT = PromptTemplate.from_template(
    """You are a query classification agent. Your task is to classify the user's question 
    into one of the following categories: {categories}. 
    Analyze the following query and return a single JSON object strictly following the provided schema.
    Query: {query}
    """
)

# RAG prompt templates
RAG_PROMPT_TEMPLATE_WITH_HISTORY = (
    f"{SYSTEM_INSTRUCTION}\n\n"
    "Conversation History:\n{history}\n\n"
    "Context: {context}\n\n"
    "Question: {question}"
)

RAG_PROMPT_TEMPLATE = (
    f"{SYSTEM_INSTRUCTION}\n\n" 
    "Context: {context}\n\n" 
    "Question: {question}"
)

# --- RAG SERVICE CLASS ---


class RAGService:
    """
    Main RAG Service - Orchestrator (Refactored with Repository Pattern)
    
    Coordinates document indexing, retrieval, and answer generation.
    Delegates specialized tasks to dedicated service modules.
    
    Architecture Pattern: Dependency Injection + Repository Pattern
    - Receives VectorStoreRepository via constructor (data access abstraction)
    - Microservices-ready: easy to replace with remote services
    - Testable: dependencies can be mocked
    """
    
    def __init__(self, repository: VectorStoreRepository):
        """
        Initialize the RAG service with injected dependencies.
        
        Args:
            repository: Vector store repository for data access (injected via DI)
        
        Design Note:
            The repository is injected by the dependency injection system,
            not created here. This allows for:
            - Better testing (mock injection)
            - Microservices migration (remote data access)
            - Separation of business logic from data access
        """
        # Store injected repository
        self.repository: VectorStoreRepository = repository

        # Initialize language service for answer translation
        self.language_service: LanguageService = LanguageService(
            target_lang=RETRIEVAL_TARGET_LANGUAGE
        )

        # Extract API key securely from settings
        self.api_key_value: str = (
            settings.OPENAI_API_KEY.get_secret_value()
            if isinstance(settings.OPENAI_API_KEY, SecretStr)
            else str(settings.OPENAI_API_KEY)
        )

        # LLM for final answer generation (low temperature for factual accuracy)
        self.llm: ChatOpenAI = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0.0,  # Deterministic, factual responses
            api_key=SecretStr(self.api_key_value),
        )

        # LLM for query classification and summarization (higher temperature for creativity)
        self.query_gen_llm: ChatOpenAI = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0.7,  # More creative for classification/summarization
            api_key=SecretStr(self.api_key_value),
        )
        
        logger.debug("✅ RAGService initialized with dependency injection")

    def _classify_query(self, query: str) -> str:
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

            classification_prompt = CLASSIFICATION_PROMPT.partial(
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
    
    async def index_document(
        self, 
        file: UploadFile, 
        user_id: str,
        document_language: Optional[str] = None
    ) -> tuple[int, str]:
        """
        Load a PDF, split it into chunks, create embeddings, and save to ChromaDB.
        
        Documents are indexed in their original language (no translation).
        Each chunk is tagged with user_id for multi-tenancy isolation and 
        document language for multilingual retrieval optimization.
        
        Args:
            file: The uploaded PDF file
            user_id: The user identifier for multi-tenancy
            document_language: Optional language code (IT, EN, FR, etc.). Auto-detected if not provided.
            
        Returns:
            Tuple of (chunks_indexed, detected_or_specified_language)
        """
        # 1. Save the uploaded content to a temporary file
        temp_file_path = f"/tmp/{file.filename}"
        total_chunks_indexed = 0
        
        # Store the document language (user-provided or will be detected)
        doc_language = document_language.upper() if document_language else None

        try:
            content = await file.read()
            if not content:
                raise ValueError("The uploaded file is empty.")

            with open(temp_file_path, "wb") as f:
                f.write(content)

            # 2. Load PDF using UnstructuredPDFLoader
            loader = UnstructuredPDFLoader(temp_file_path, mode="elements")
            documents = loader.load()

            # 3. Process and filter chunks
            chunks: List[Document] = documents
            chunks = filter_complex_metadata(chunks)
            
            # 4. Prepare chunks with hierarchical tracking
            final_chunks: List[Document] = []
            current_chapter = "Document Start"
            
            # --- CRITICAL: Add uploaded_at timestamp to metadata ---
            import time
            uploaded_at = int(time.time() * 1000) # Milliseconds timestamp
            # --------------------------------------------------------

            for chunk in chunks:
                # Track hierarchical structure from document elements
                element_type = chunk.metadata.get("type", "NarrativeText")

                # Update chapter tracking when encountering titles or headers
                if "Title" in element_type or "Header" in element_type:
                    current_chapter = chunk.page_content.strip()
                    chunk.metadata["element_type"] = element_type

                # Use provided language or auto-detect from content
                if doc_language is None and len(chunk.page_content) > 50:
                    # Auto-detect language from first substantial chunk
                    detected_lang_code = self.language_service.detect_language(
                        chunk.page_content
                    )
                    doc_language = detected_lang_code.upper()
                    logger.debug(f" Auto-detected document language: {doc_language}")
                elif doc_language is None:
                    doc_language = "EN"  # Default fallback

                # Add structural, language, and user metadata to every chunk
                chunk.metadata["chapter_title"] = current_chapter
                chunk.metadata["source"] = user_id
                chunk.metadata["original_filename"] = file.filename
                chunk.metadata["original_language_code"] = doc_language  # Use document language
                chunk.metadata["uploaded_at"] = uploaded_at # CRITICAL for sorting in DocumentInfo

                final_chunks.append(chunk)

            # 5. Index the chunks (in their original language) - OPTIMIZED WITH BATCH UPSERT
            if final_chunks:
                import time
                
                start_time = time.time()
                
                # CRITICAL OPTIMIZATION 1: Reduce batch size for faster per-batch processing
                # Smaller batches = more frequent feedback, better memory management
                OPTIMIZED_BATCH_SIZE = 500  # Reduced from 2000 for better throughput
                total_batches = (len(final_chunks) + OPTIMIZED_BATCH_SIZE - 1) // OPTIMIZED_BATCH_SIZE
                
                logger.info(f"📊 Starting OPTIMIZED embedding generation for {len(final_chunks)} chunks in {total_batches} batches")
                
                # CRITICAL OPTIMIZATION 2: Batch upsert instead of individual adds
                # Process in smaller batches for better progress visibility
                for batch_idx, i in enumerate(range(0, len(final_chunks), OPTIMIZED_BATCH_SIZE), 1):
                    batch = final_chunks[i : i + OPTIMIZED_BATCH_SIZE]
                    batch_start = time.time()
                    
                    # Single upsert operation for entire batch (atomic write) via repository
                    self.repository.add_documents(batch)
                    
                    batch_time = time.time() - batch_start
                    total_chunks_indexed += len(batch)
                    throughput = len(batch) / batch_time if batch_time > 0 else 0
                    
                    logger.info(f"⚡ Batch {batch_idx}/{total_batches}: {len(batch)} chunks in {batch_time:.2f}s ({throughput:.1f} chunks/s)")
                
                elapsed = time.time() - start_time
                overall_throughput = len(final_chunks) / elapsed if elapsed > 0 else 0
                logger.info(f"🚀 OPTIMIZED: Processed {len(final_chunks)} chunks in {elapsed:.2f}s ({overall_throughput:.1f} chunks/s overall)")

            # Ensure doc_language is not None before returning
            final_doc_language = doc_language if doc_language else "EN"
            logger.info(f"✅ Indexed {total_chunks_indexed} chunks in language: {final_doc_language}")
            return total_chunks_indexed, final_doc_language
        except Exception as e:
            # Print the error for debugging and re-raise it or handle as preferred.
            logger.error(f"Indexing error (service level): {e}")
            raise e
        finally:
            # 6. Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(os.path.abspath(temp_file_path))

    def answer_query(
        self, 
        query: str, 
        user_id: str, 
        conversation_history: Optional[List[ConversationMessage]] = None,
        use_case: Optional[UseCaseType] = None
    ) -> Tuple[str, List[str]]:
        """
        Retrieves relevant documents for a specific user and generates an answer
        using the LLM, leveraging the robust embedding model and conversation history.
        
        Args:
            query: The user's question
            user_id: The user identifier for multi-tenancy
            conversation_history: Optional list of recent messages (last 5-7 exchanges)
            use_case: Optional use case type for optimized prompt generation (CU1-CU6)
        
        Returns:
            Tuple of (answer, list of source document filenames)
        """
        if conversation_history is None:
            conversation_history = []

        # 1. Detect the original query language code (for final answer translation)
        query_language_code = self.language_service.detect_language(query).upper()
        logger.debug(f" Query Language Code: {query_language_code}")

        # 2. Assume document language is EN by default for first pass
        # We'll do a quick translation if query is not in English
        document_language = "EN"  # Default assumption
        
        # If query is not in English, translate it for better sample retrieval
        query_for_sample = query
        if query_language_code != "EN":
            query_for_sample = translation_service.translate_query_to_language(query, "EN")
            logger.debug(f" Translated query for sampling: {query_for_sample}")
        
        # 3. Initial retrieval to determine actual document language from chunks
        retriever_temp = self.repository.get_retriever(user_id=user_id, k=5)
        sample_docs = retriever_temp.invoke(query_for_sample)  # Use translated query
        
        logger.debug(f" Sample retrieval returned {len(sample_docs)} documents")
        
        # Extract document language from retrieved chunks' metadata
        if sample_docs:
            # Get the most common language from retrieved documents
            lang_counts = {}
            for doc in sample_docs:
                lang = doc.metadata.get("original_language_code", "EN")
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
            
            if lang_counts:
                document_language = max(lang_counts, key=lambda k: lang_counts[k])
                logger.debug(f" Language distribution in sample: {lang_counts}")
                logger.debug(f" Detected document language from retrieval: {document_language}")
        else:
            logger.debug(" WARNING - No documents found in sample retrieval!")
        
        # 4. Translate the user query to the DOCUMENT LANGUAGE for accurate retrieval
        if query_language_code == document_language:
            translated_query_for_retrieval = query
            logger.debug(" Query already in document language, no translation needed")
        else:
            translated_query_for_retrieval = translation_service.translate_query_to_language(
                query, document_language
            )
            logger.debug(f" Translated Query for Retrieval ({document_language}): {translated_query_for_retrieval}")

        # 4. Classify the query (using the original query)
        query_tag = self._classify_query(query)
        logger.debug(f" Query Classified as: {query_tag}")

        # 5. Generate Alternative Queries based on the translated query
        alternative_queries = query_expansion_service.generate_alternative_queries(
            translated_query_for_retrieval
        )
        logger.debug(f" Generated {len(alternative_queries)} alternative queries")

        # List of all queries to execute: Translated Query + Alternative Queries
        all_queries = [translated_query_for_retrieval] + alternative_queries

        # 5. Setup Retrieval with larger pool (k=30 for better coverage of scattered information)
        retriever = self.repository.get_retriever(user_id=user_id, k=30)

        # 6. Execute retrieval for all queries and collect results (Fase 1: Ricerca Parallela)
        all_retrieved_docs = []
        doc_ids = set()

        for q in all_queries:
            docs = retriever.invoke(q)
            logger.debug(f" Query '{q[:50]}...' retrieved {len(docs)} documents")

            for doc in docs:
                # Simple check to uniquely identify documents by content and metadata
                metadata_tuple = tuple(sorted(doc.metadata.items()))
                doc_id = hash((doc.page_content, metadata_tuple))

                if doc_id not in doc_ids:
                    all_retrieved_docs.append(doc)
                    doc_ids.add(doc_id)

        logger.debug(f" Retrieved {len(all_retrieved_docs)} unique documents from parallel search")

        # 7. Apply lightweight reranking and select optimal context
        # Use more chunks (15) for list-type queries to capture scattered information
        context_docs = reranking_service.rerank_documents(
            documents=all_retrieved_docs,
            original_query=query,
            alternative_queries=alternative_queries,
            top_n=15  # Increased for better coverage of scattered entities (names, lists, etc.)
        )

        # Handle fallback when no documents retrieved
        if not context_docs:
            source_documents = []
            fallback_answer = (
                "I cannot answer this question based on the documents provided."
            )
            logger.info(f"DEBUG: Retrieval failed for user_id='{user_id}'. Fallback answer sent."
            )

            # The fallback must also be translated back to the user's language
            translated_fallback = self.language_service.translate_answer_back(
                fallback_answer, query_language_code
            )
            return translated_fallback, source_documents

        # Prepare context and sources (Context is in its ORIGINAL language)
        # Fase 3: Costruzione del Prompt Finale con Contesto Ottimizzato
        # Includi la struttura gerarchica per aiutare l'LLM nella sintesi multi-frammento
        context_parts = []
        for i, doc in enumerate(context_docs, 1):
            chapter = doc.metadata.get('chapter_title', 'N/A')
            element_type = doc.metadata.get('element_type', 'Content')
            
            # Formatta ogni chunk con numerazione e struttura chiara
            context_parts.append(
                f"[DOCUMENT {i}]\n"
                f"Section: {chapter}\n"
                f"Type: {element_type}\n"
                f"---\n"
                f"{doc.page_content}\n"
            )
        
        context = "\n".join(context_parts)
        
        source_documents = list(
            set(doc.metadata.get("original_filename", "N/A") for doc in context_docs)
        )
        
        logger.debug(f" Final context prepared with {len(context_docs)} chunks from {len(source_documents)} documents")

        # 8. Format conversation history if present (last 5-7 exchanges)
        history_text = ""
        if conversation_history:
            # Limit to last 7 exchanges (14 messages = 7 user + 7 assistant)
            recent_history = conversation_history[-14:]
            history_lines = []
            for msg in recent_history:
                role_label = "User" if msg.role == "user" else "Assistant"
                history_lines.append(f"{role_label}: {msg.content}")
            history_text = "\n".join(history_lines)
            logger.debug(f" Including {len(recent_history)} messages in conversation history")

        # 9. Create Final Prompt with Use Case Optimization
        # Auto-detect use case if not explicitly provided
        if use_case is None:
            detected_use_case = use_case_detection_service.detect_use_case(query)
            if detected_use_case:
                use_case = detected_use_case
                logger.debug(f" Auto-detected use case: {use_case}")
        
        if use_case:
            logger.debug(f" Using optimized prompt for use case: {use_case}")
            
            # Extract quantity from query if present
            quantity = prompt_template_service.extract_quantity_from_query(query)
            
            # Create constraints for this use case
            constraints = prompt_template_service.create_constraints_for_use_case(
                use_case=use_case,
                quantity=quantity
            )
            
            # Add conversation history to additional context if present
            additional_context = None
            if history_text:
                additional_context = f"Recent conversation history:\n{history_text}\n\nConsider this history when formulating your response."
            
            # Add language instruction for proper response language
            # The prompt will use the translated query for retrieval accuracy,
            # but we need to tell the LLM to respond in the ORIGINAL query language
            query_lang_name = translation_service.get_language_name(query_language_code)
            if additional_context:
                additional_context += f"\n\nIMPORTANT: The user asked the question in {query_lang_name}. You MUST respond in {query_lang_name}, not in English."
            else:
                additional_context = f"IMPORTANT: The user asked the question in {query_lang_name}. You MUST respond in {query_lang_name}, not in English."
            
            # Build optimized modular prompt
            # Use translated query for better context matching, but add language instruction
            final_prompt = prompt_template_service.build_modular_prompt(
                use_case=use_case,
                user_request=translated_query_for_retrieval,
                constraints=constraints,
                additional_context=additional_context,
                retrieved_context=context
            )
            
            logger.debug(f" Generated optimized prompt with constraints - Quantity: {quantity}, Format: {constraints.format_constraint}, Response Language: {query_lang_name}")
        else:
            # Fallback to standard prompts without use case optimization
            if history_text:
                final_prompt = RAG_PROMPT_TEMPLATE_WITH_HISTORY.format(
                    history=history_text,
                    context=context,
                    question=translated_query_for_retrieval
                )
            else:
                final_prompt = RAG_PROMPT_TEMPLATE.format(
                    context=context, 
                    question=translated_query_for_retrieval
                )

        # 10. Generate Response from LLM (Response will be in English first - costs LLM call)
        try:
            english_answer = str(self.llm.invoke(final_prompt).content)
        except Exception as e:
            logger.error(f"LLM Invocation Error: {e}")
            english_answer = "An error occurred during LLM processing."

        # 11. Translate Final Answer back to the user's query language
        # The answer is always returned in the language of the query, NOT the document language
        final_answer = self.language_service.translate_answer_back(
            english_answer, query_language_code
        )

        return final_answer, source_documents

    def get_user_document_count(self, user_id: str) -> int:
        """
        Returns the number of unique documents indexed for a specific user.
        
        NOTE: This function is inefficient for large datasets as it samples, 
        and is superseded by get_user_documents() for accurate counting.
        """
        try:
            # Get sample from repository
            metadatas, _ = self.repository.get_user_chunks_sample(user_id, sample_size=1000)

            if not metadatas:
                return 0

            # Count unique filenames
            unique_files = set()
            for metadata in metadatas:
                if metadata and "original_filename" in metadata:
                    unique_files.add(metadata["original_filename"])

            return len(unique_files)

        except Exception as e:
            logger.error(f"Error getting document count for user {user_id}: {e}")
            return 0

    def get_user_documents(self, user_id: str) -> List[DocumentInfo]:
        """
        Returns a list of all documents indexed for a specific user with metadata.
        
        OPTIMIZED: Uses strategic sampling to quickly discover all unique document names 
        and then uses 'count()' for precise chunk counting.
        
        Args:
            user_id: The user ID to filter documents
            
        Returns:
            List of DocumentInfo objects containing document information
        """
        try:
            logger.info(f"🔍 Getting documents for user: {user_id}")
            
            # 1. DISCOVERY: Use sampling to find all unique filenames (fast)
            unique_filenames: dict = {}  # filename -> metadata dict
            
            # Progressive sampling for document discovery
            sample_sizes = [2000, 10000, 50000] 
            
            for sample_size in sample_sizes:
                metadatas, _ = self.repository.get_user_chunks_sample(user_id, sample_size)
                
                if not metadatas:
                    break
                    
                newly_discovered_count = 0
                prev_unique_count = len(unique_filenames)
                
                # Process sample
                for metadata in metadatas:
                    if metadata:
                        filename = metadata.get("original_filename")
                        
                        if filename and filename not in unique_filenames:
                            # Store metadata from first chunk found for this file
                            unique_filenames[str(filename)] = dict(metadata)
                            newly_discovered_count += 1
                
                logger.info(f"📦 Sample {sample_size}: found {len(unique_filenames)} documents (+{newly_discovered_count} new)")

                # Break conditions
                if len(metadatas) < sample_size:
                    logger.info(f"✅ Reached end of data at {len(metadatas)} chunks")
                    break
                if newly_discovered_count == 0 and prev_unique_count > 0:
                    logger.info(f"✅ All documents discovered after {sample_size} chunks")
                    break
            
            # 2. COUNTING: Now count chunks for each document found
            document_list: List[DocumentInfo] = []
            for filename, sample_metadata in unique_filenames.items():
                
                # Count chunks for this specific file using repository
                exact_count = self.repository.count_document_chunks(user_id, filename)
                
                # Estrai lingua e data dal metadato campione salvato
                language = str(
                    sample_metadata.get("original_language_code") or 
                    sample_metadata.get("language") or 
                    "unknown"
                )
                uploaded_at_ts = sample_metadata.get("uploaded_at")
                uploaded_at = str(uploaded_at_ts) if uploaded_at_ts else None
                
                document_list.append(DocumentInfo(
                    filename=filename,
                    chunks_count=exact_count,
                    language=language,
                    uploaded_at=uploaded_at,
                ))
            
            logger.info(f"✅ Found {len(document_list)} unique documents with exact chunk counts.")
            
            # Opzionale: Ordina i documenti per data di upload (decrescente)
            document_list.sort(key=lambda doc: doc.uploaded_at or '0', reverse=True)
            
            return document_list

        except Exception as e:
            logger.error(f"❌ Error getting documents for user {user_id}: {e}")
            return []

    def delete_user_document(self, user_id: str, filename: str) -> int:
        """
        Deletes all chunks of a specific document for a user.
        
        OPTIMIZED: Uses ChromaDB's native where-based deletion instead of 
        fetching all IDs first, significantly faster for large documents.
        
        Args:
            user_id: The user ID who owns the document
            filename: The name of the document to delete
            
        Returns:
            Number of chunks deleted (estimated from pre-check)
        """
        try:
            # Use repository for deletion (optimized where-based deletion)
            chunks_deleted = self.repository.delete_document(user_id, filename)
            
            logger.info(f"✅ Deleted {chunks_deleted} chunks for document {filename} (user: {user_id})")
            return chunks_deleted

        except Exception as e:
            logger.error(f"❌ Error deleting document {filename} for user {user_id}: {e}")
            raise e

    def delete_all_user_documents(self, user_id: str) -> int:
        """
        Deletes all documents for a specific user.
        
        OPTIMIZED: Uses ChromaDB's native where-based deletion for instant removal.
        No need for batching - ChromaDB handles large deletions efficiently.
        
        Args:
            user_id: The user ID whose documents should be deleted
            
        Returns:
            Estimated number of chunks deleted
        """
        try:
            # Use repository for deletion (optimized single-operation deletion)
            chunks_deleted = self.repository.delete_all_user_documents(user_id)
            
            logger.info(f"✅ Deleted all documents for user {user_id} (~{chunks_deleted} chunks)")
            return chunks_deleted

        except Exception as e:
            logger.error(f"❌ Error deleting all documents for user {user_id}: {e}")
            raise e

    def generate_conversation_summary(self, conversation_history: List[ConversationMessage]) -> str:
        """
        Generates a concise summary of the conversation history using the LLM.
        This summary can be stored for long-term memory and injected in future sessions.
        
        Args:
            conversation_history: List of conversation messages to summarize
            
        Returns:
            A concise summary string highlighting key facts and topics discussed
        """
        if not conversation_history:
            return ""
        
        try:
            # Build conversation text
            conversation_text = "\n".join([
                f"{msg.role.capitalize()}: {msg.content}"
                for msg in conversation_history
            ])
            
            # Create summarization prompt
            summary_prompt = (
                "You are a conversation summarizer. Analyze the following conversation "
                "and generate a concise summary of:\n"
                "1. Key facts the user mentioned about themselves or their situation\n"
                "2. Main topics discussed\n"
                "3. Important questions asked and answers provided\n"
                "4. Any ongoing issues or follow-up items\n\n"
                "Keep the summary brief (max 200 words) and focused on context that would be "
                "useful for continuing the conversation later.\n\n"
                f"Conversation:\n{conversation_text}\n\n"
                "Summary:"
            )
            
            # Generate summary
            summary = str(self.query_gen_llm.invoke(summary_prompt).content)
            logger.debug(f"Generated conversation summary ({len(summary)} chars)")
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Error generating conversation summary: {e}")
            return ""


# --- Dependency Injection Factory ---

def get_rag_service(
    repository: VectorStoreRepository = Depends(get_vector_store_repository)
) -> RAGService:
    """
    FastAPI dependency function that provides RAGService instances.
    
    This factory function creates RAGService instances with proper
    dependency injection using the Repository Pattern, enabling:
    - Request-scoped service instances
    - Data access abstraction via repository
    - Easy mocking for tests
    - Microservices-ready architecture
    
    CRITICAL: The repository parameter uses Depends() to tell FastAPI
    how to resolve the nested dependency automatically.
    
    Args:
        repository: Injected VectorStoreRepository from get_vector_store_repository()
    
    Returns:
        RAGService: Configured RAG service instance with repository access
    
    Example usage in router:
        @router.post("/query/")
        def query(
            request: QueryRequest,
            rag_service: RAGService = Depends(get_rag_service)
        ):
            answer, sources = rag_service.answer_query(...)
            ...
    """
    return RAGService(repository=repository)


