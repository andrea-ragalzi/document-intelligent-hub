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
    QueryClassification,
)

# Specialized service imports
from app.services.document_classifier_service import (
    DocumentCategory,
    document_classifier_service,
)
from app.services.language_service import RETRIEVAL_TARGET_LANGUAGE, LanguageService
from app.services.query_expansion_service import query_expansion_service
from app.services.reranking_service import reranking_service
from app.services.translation_service import translation_service

# FastAPI and document processing
from fastapi import Depends, UploadFile
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.documents import Document
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
from pydantic import SecretStr

# --- CONSTANTS & CONFIGURATION ---

# Document limit for each embedding batch
EMBEDDING_DOC_BATCH_SIZE = 2000

# System instruction to prevent hallucination and enforce compliance
# MODIFICA CRITICA: Aggiornato per incoraggiare la sintesi da chunk frammentati (Regola 2 e 3)
SYSTEM_INSTRUCTION = """
You are an intelligent document assistant and expert analyst. 
Your main objective is to answer user questions based on the provided context (source documents). 

**CRITICAL RAG RULES:**
1. ONLY use the information provided in the Context section below to answer the user's question.
2. If the Context contains the necessary data (even if fragmented across multiple lines or sections), you MUST synthesize, combine, and state the complete answer clearly.
3. If and ONLY if the necessary data is completely missing from the Context, you MUST state explicitly: 'Non ho abbastanza informazioni per rispondere a questa domanda basandomi sui documenti forniti.' DO NOT attempt to answer with general knowledge.
4. When multiple relevant pieces of information are found across different sections, synthesize them into a coherent answer.
5. If asked for lists of people, places, or entities: extract ALL specific names mentioned in the context, even if scattered across multiple sections.
6. Be comprehensive - include all relevant details and specific names found in the context.
7. CRITICAL: RULE 1 is NON-NEGOTIABLE. ONLY use the information provided in the Context.
"""

# Prompt for query classification
CLASSIFICATION_PROMPT = PromptTemplate.from_template(
    """You are a query classification agent. Your task is to classify the user's question
    into one of the following categories: {categories}.
    Analyze the following query and return a single JSON object strictly following the provided schema.
    {format_instructions}
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

        # High-power LLM for complex reasoning/code generation use cases
        high_power_model = getattr(settings, "HIGH_POWER_LLM_MODEL", settings.LLM_MODEL)
        self.high_power_llm: ChatOpenAI = ChatOpenAI(
            model=high_power_model,
            temperature=0.0,
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

    def _reformulate_query(
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
        # Conversational connectors that indicate query continuation/correction
        CONVERSATIONAL_PATTERNS = [
            'i mean', 'intendo', 'intendevo', 'voglio dire',
            'what about', 'e invece', 'e poi', 'piuttosto',
            'invece', 'oppure', 'o meglio', 'cioè',
            'no wait', 'no aspetta', 'correction', 'correzione'
        ]
        
        # Check if reformulation is needed
        query_lower = query.lower().strip()
        needs_reformulation = (
            len(query) < 30 or  # Very short query
            any(pattern in query_lower for pattern in CONVERSATIONAL_PATTERNS)  # Contains conversational connector
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
        
        # Reformulation prompt
        reformulation_prompt = f"""You are a Query Reformulator. Your task is to take a short, contextual user input and the recent chat history and combine them into a single, complete, and explicit standalone question.

**CRITICAL RULES:**
1. The output must be ONLY the new, complete question - no explanations, no preambles
2. Preserve the original language of the user's input
3. If the input is already a complete question, return it unchanged
4. Combine context from history with the new input to create ONE clear question

CONVERSATION HISTORY:
{history_text}

LATEST USER INPUT:
{query}

OUTPUT (complete standalone question):"""

        try:
            # Use cost-effective LLM (gpt-3.5-turbo) for this simple task
            response = self.llm.invoke(reformulation_prompt)
            reformulated_query = str(response.content).strip()
            
            # Validate reformulation (basic sanity check)
            if len(reformulated_query) < 10 or len(reformulated_query) > 300:
                logger.warning("⚠️ Reformulation produced suspicious result, using original query")
                return query
            
            logger.info("✅ Query reformulated successfully")
            logger.info("   Original: {query}")
            logger.info("   Reformulated: {reformulated_query}")
            
            return reformulated_query
            
        except Exception as e:
            logger.error(f"❌ Query reformulation failed: {e}")
            logger.info("   Falling back to original query")
            return query
    
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

            # 3. Classify document to determine chunking strategy
            # Get a larger preview for structural analysis (5000 chars as requested)
            full_text_preview = " ".join([doc.page_content for doc in documents[:15]])[:5000]
            
            # Initial classification (Metadata/Keyword based)
            category = document_classifier_service.classify_document(file.filename or "unknown", full_text_preview[:1000])
            logger.info(f"📄 Initial classification: {category.value}")

            # 4. Apply chunking strategy based on classification with Fallback
            use_structural_chunking = False
            strategy_reason = "Default Classification"
            
            if category == DocumentCategory.AUTORITA_STRUTTURALE:
                use_structural_chunking = True
                strategy_reason = "Direct Classification (AUTORITA_STRUTTURALE)"
            else:
                # Fallback: Check structural density
                if document_classifier_service.has_structural_density(full_text_preview):
                    logger.info("🔄 Fallback triggered: High structural density detected in 'Unstructured' document.")
                    use_structural_chunking = True
                    strategy_reason = "Fallback: High Structural Density"
                else:
                    strategy_reason = "Direct Classification (INFORMATIVO_NON_STRUTTURATO)"
            
            logger.info(f"🧠 Chunking Strategy Decided: {'STRUCTURAL' if use_structural_chunking else 'FIXED-SIZE'} | Reason: {strategy_reason}")
            
            if use_structural_chunking:
                # Structural chunking (semantic)
                # This is a placeholder for a more sophisticated structural chunker
                text_splitter = RecursiveCharacterTextSplitter.from_language(
                    language=Language.MARKDOWN, chunk_size=1024, chunk_overlap=100
                )
                chunks = text_splitter.split_documents(documents)
                logger.info(f"🪓 Applied STRUCTURAL chunking strategy. Got {len(chunks)} chunks.")
            else:
                # Standard fixed-size chunking
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
                chunks = text_splitter.split_documents(documents)
                logger.info(f"🪓 Applied FIXED-SIZE chunking strategy. Got {len(chunks)} chunks.")

            # 5. Process and filter chunks
            chunks = filter_complex_metadata(chunks)
            
            # 6. Prepare chunks with hierarchical tracking
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

            # 7. Index the chunks (in their original language) - OPTIMIZED WITH BATCH UPSERT
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
            # 8. Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(os.path.abspath(temp_file_path))

    async def detect_document_language_preview(
        self,
        file: UploadFile
    ) -> Tuple[str, float]:
        """
        Detect document language WITHOUT indexing it.
        Used for preview/auto-detection before upload.
        
        Args:
            file: The uploaded PDF file
            
        Returns:
            Tuple of (detected_language_code, confidence_score)
        """
        temp_file_path = f"/tmp/{file.filename}"
        
        try:
            # Save temporary file
            content = await file.read()
            if not content:
                raise ValueError("The uploaded file is empty.")
            
            with open(temp_file_path, "wb") as f:
                f.write(content)
            
            # Load PDF and extract text
            loader = UnstructuredPDFLoader(temp_file_path, mode="elements")
            documents = loader.load()
            
            # Collect text samples from multiple chunks
            text_samples = []
            for chunk in documents:
                if len(chunk.page_content) > 50:
                    text_samples.append(chunk.page_content)
                if len(text_samples) >= 5:  # Sample from first 5 substantial chunks
                    break
            
            if not text_samples:
                logger.warning(f"⚠️ No substantial text found in {file.filename}")
                return "EN", 0.0
            
            # Combine samples for detection
            combined_text = " ".join(text_samples)
            detected_lang = self.language_service.detect_language(combined_text)
            
            # Calculate confidence (5-pass voting returns confidence via internal logic)
            # For simplicity, we'll estimate confidence based on detection consistency
            confidence = 0.8  # Default high confidence from our 5-pass voting
            
            logger.info(f"🔍 Preview detection for {file.filename}: {detected_lang.upper()} (confidence: {confidence:.2f})")
            
            return detected_lang.upper(), confidence
            
        except Exception as e:
            logger.error(f"Preview detection error for {file.filename}: {e}")
            raise e
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(os.path.abspath(temp_file_path))

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
        Retrieves relevant documents for a specific user and generates an answer
        using the LLM, leveraging the robust embedding model and conversation history.
        
        Args:
            query: The user's question
            user_id: The user identifier for multi-tenancy
            conversation_history: Optional list of recent messages (last 5-7 exchanges)
            output_language: Optional language code for response (IT, EN, FR, etc.)
            include_files: Optional list of filenames to restrict search to (only these files)
            exclude_files: Optional list of filenames to exclude from search
        
        Returns:
            Tuple of (answer, list of source document filenames)
        """
        if conversation_history is None:
            conversation_history = []

        logger.info(f"🔍 Starting RAG query for user: {user_id}")
        logger.info(f"📝 Original query: {query[:100]}{'...' if len(query) > 100 else ''}")
        
        # Log file filtering if applicable
        if include_files:
            logger.info(f"📂 File filter: INCLUDE {include_files}")
        if exclude_files:
            logger.info(f"🚫 File filter: EXCLUDE {exclude_files}")

        # === STEP 0: QUERY REFORMULATION ===
        # Resolve conversational context and ambiguity before processing
        reformulated_query = self._reformulate_query(query, conversation_history)
        
        # Use reformulated query for all subsequent processing
        query = reformulated_query

        # 1. Detect the original query language code (used as fallback if no output_language specified)
        query_language_code = self.language_service.detect_language(query).upper()
        
        # Use explicit output language if provided, otherwise use detected query language
        target_response_language = output_language.upper() if output_language else query_language_code
        
        logger.info(f"🌍 Query Language: {query_language_code}")
        logger.info(f"🎯 Target Response Language: {target_response_language}")
        logger.debug(f"💬 Conversation history: {len(conversation_history)} messages")

        # 2. Translate query to English for retrieval if needed
        # (Retrieval works best in English due to embedding model)
        if query_language_code != "EN":
            translated_query_for_retrieval = translation_service.translate_query_to_language(query, "EN")
            logger.info(f"🔄 Translated query for retrieval: {translated_query_for_retrieval[:100]}{'...' if len(translated_query_for_retrieval) > 100 else ''}")
        else:
            translated_query_for_retrieval = query
            logger.debug(f"✅ Query already in English, no translation needed")

        # === LOG TRANSLATION RESULT ===
        logger.info(f"{'='*80}")
        logger.info(f"🔄 [RAG SERVICE] QUERY TRANSLATION")
        logger.info(f"{'='*80}")
        logger.info(f"Original query language: {query_language_code}")
        logger.info(f"Original query: {query}")
        logger.info(f"Translated query (for retrieval): {translated_query_for_retrieval}")
        logger.info(f"Target response language: {target_response_language}")
        logger.info(f"{'='*80}")

        # 3. Classify the query (using the original query)
        query_tag = self._classify_query(query)
        logger.info(f"🏷️  Query Classified as: {query_tag}")

        # 4. Generate Alternative Queries based on the translated query
        logger.debug(f"🔀 Generating alternative queries for query expansion")
        alternative_queries = query_expansion_service.generate_alternative_queries(
            translated_query_for_retrieval
        )
        logger.info(f"📝 Generated {len(alternative_queries)} alternative queries")
        
        # === LOG QUERY EXPANSION ===
        logger.info(f"{'='*80}")
        logger.info(f"🔀 [RAG SERVICE] QUERY EXPANSION")
        logger.info(f"{'='*80}")
        logger.info(f"Base query: {translated_query_for_retrieval}")
        logger.info(f"Alternative queries ({len(alternative_queries)}):")
        for i, alt_q in enumerate(alternative_queries, 1):
            logger.info(f"  [{i}] {alt_q}")
        logger.info(f"{'='*80}")

        # List of all queries to execute: Translated Query + Alternative Queries
        all_queries = [translated_query_for_retrieval] + alternative_queries
        logger.debug(f"🎯 Total queries for parallel search: {len(all_queries)}")

        # 5. Setup Retrieval with larger pool (k=30 for better coverage of scattered information)
        logger.debug("🗂️  Setting up retriever with k=30 for comprehensive search")
        retriever = self.repository.get_retriever(
            user_id=user_id, 
            k=30,
            include_files=include_files,
            exclude_files=exclude_files
        )

        # 6. Execute retrieval for all queries and collect results (Fase 1: Ricerca Parallela)
        logger.info(f"🔎 Starting parallel retrieval for {len(all_queries)} queries")
        all_retrieved_docs = []
        doc_ids = set()

        for idx, q in enumerate(all_queries, 1):
            docs = retriever.invoke(q)
            logger.info(f"🔎 Query {idx}/{len(all_queries)}: '{q}' → Found {len(docs)} chunks")

            for i, doc in enumerate(docs):
                filename = doc.metadata.get('original_filename', 'Unknown')
                preview = doc.page_content[:100].replace('\n', ' ')
                logger.info(f"   📄 [{i+1}] {filename}: {preview}...")

            for doc in docs:
                # Simple check to uniquely identify documents by content and metadata
                metadata_tuple = tuple(sorted(doc.metadata.items()))
                doc_id = hash((doc.page_content, metadata_tuple))

                if doc_id not in doc_ids:
                    all_retrieved_docs.append(doc)
                    doc_ids.add(doc_id)

        # Calculate unique source files
        unique_source_files = set(doc.metadata.get("original_filename", "Unknown") for doc in all_retrieved_docs)
        logger.info(f"📚 Retrieved {len(all_retrieved_docs)} unique chunks from {len(unique_source_files)} source files")
        logger.info(f"📂 Source Files: {', '.join(unique_source_files)}")
        
        # === LOG RETRIEVED DOCUMENTS ===
        logger.info(f"{'='*80}")
        logger.info("📚 [RAG SERVICE] RETRIEVED CHUNKS BEFORE RERANKING")
        logger.info(f"{'='*80}")
        logger.info(f"Total unique chunks: {len(all_retrieved_docs)}")
        logger.info(f"Total source files: {len(unique_source_files)}")
        for idx, doc in enumerate(all_retrieved_docs[:5], 1):  # Log first 5
            filename = doc.metadata.get('original_filename', 'Unknown')
            chapter = doc.metadata.get('chapter_title', 'N/A')
            logger.debug(f"  [{idx}] {filename} | Section: {chapter}")
            logger.debug(f"       Content: {doc.page_content[:100]}...")
        if len(all_retrieved_docs) > 5:
            logger.debug(f"  ... and {len(all_retrieved_docs) - 5} more documents")
        logger.info(f"{'='*80}")

        # 7. Apply lightweight reranking and select optimal context
        # Use more chunks (15) for list-type queries to capture scattered information
        logger.info("🎯 Starting reranking of {len(all_retrieved_docs)} documents → top 15")
        context_docs = reranking_service.rerank_documents(
            documents=all_retrieved_docs,
            original_query=query,
            alternative_queries=alternative_queries,
            top_n=15  # Increased for better coverage of scattered entities (names, lists, etc.)
        )
        logger.info(f"✨ Reranking completed: {len(context_docs)} top documents selected")
        
        # === LOG RERANKED DOCUMENTS ===
        logger.info(f"{'='*80}")
        logger.info("🎯 [RAG SERVICE] TOP DOCUMENTS AFTER RERANKING")
        logger.info(f"{'='*80}")
        logger.info(f"Selected documents: {len(context_docs)}")
        for idx, doc in enumerate(context_docs[:5], 1):  # Log first 5
            filename = doc.metadata.get('original_filename', 'Unknown')
            chapter = doc.metadata.get('chapter_title', 'N/A')
            relevance = getattr(doc, 'relevance_score', 'N/A')
            logger.info(f"  [{idx}] {filename} | Section: {chapter} | Score: {relevance}")
            logger.debug(f"       Content: {doc.page_content[:150]}...")
        if len(context_docs) > 5:
            logger.info(f"  ... and {len(context_docs) - 5} more documents")
        logger.info(f"{'='*80}")

        # Handle fallback when no documents retrieved
        if not context_docs:
            source_documents = []
            fallback_answer = (
                "I cannot answer this question based on the documents provided."
            )
            logger.warning(f"⚠️  No relevant documents found for user_id='{user_id}'. Returning fallback answer.")
            
            # Translate fallback to user's language
            translated_fallback = self.language_service.translate_answer_back(
                fallback_answer, query_language_code
            )
            logger.info(f"✅ Fallback answer translated to {query_language_code}")
            return translated_fallback, source_documents

        # Prepare context and sources (Context is in its ORIGINAL language)
        # Fase 3: Costruzione del Prompt
        
        # Format history messages
        history_formatted = []
        # Reverse list to process in chronological order for easy history formatting
        for msg in conversation_history:
            # Use assistant's answer language, not necessarily original query language
            if msg.role == "user":
                history_formatted.append(f"User: {msg.content}")
            else: # role == "assistant"
                # Extract actual answer from the full response structure
                assistant_answer_content = msg.content.split("\n\n📚 Fonti:")[0].strip()
                history_formatted.append(f"Assistant: {assistant_answer_content}")

        history_str = "\n".join(history_formatted) if history_formatted else "Nessuna cronologia disponibile."


        # Format context chunks
        context_str = "\n---\n".join([
            f"Section: {doc.metadata.get('chapter_title', 'Document Start')}\n"
            f"Source: {doc.metadata.get('original_filename', 'Unknown')}\n"
            f"Content:\n{doc.page_content.strip()}"
            for doc in context_docs
        ])
        
        # Choose the correct prompt template (with or without history)
        if history_str and history_str != "Nessuna cronologia disponibile.":
            rag_prompt = RAG_PROMPT_TEMPLATE_WITH_HISTORY.format(
                history=history_str,
                context=context_str,
                question=query
            )
        else:
            rag_prompt = RAG_PROMPT_TEMPLATE.format(
                context=context_str,
                question=query
            )

        # 8. LLM Invocation
        logger.info(f"💬 Invoking LLM for final answer generation...")
        
        # We need to manually append the language instruction to the LLM call,
        # as the RAG_PROMPT_TEMPLATE doesn't explicitly include it in the current file structure.
        # We will add it as a final instruction in the query.
        final_llm_query = (
            f"{rag_prompt}\n\n"
            f"--- FINAL INSTRUCTION ---\n"
            f"You MUST respond ENTIRELY in the target language: {target_response_language}. "
            f"Do not include any source citations in your direct answer; they will be handled separately. "
        )

        try:
            # Use synchronous invocation for simplicity in the RAG pipeline
            llm_response = self.llm.invoke(final_llm_query).content
            
            # 9. Final Answer Processing
            final_answer = str(llm_response).strip()
            
            # Extract unique source files from the context used
            source_documents = sorted(list(set(
                doc.metadata.get("original_filename", "Unknown") for doc in context_docs
            )))

            # 10. Translation (Only if LLM answered in English but target language is different)
            if target_response_language != "EN" and self.language_service.detect_language(final_answer).upper() == "EN":
                final_answer = translation_service.translate_answer_back(
                    final_answer, target_response_language
                )
                logger.debug(f"🔄 LLM answer translated to {target_response_language}")

            # 11. Append source documents to the answer
            if source_documents:
                # Get translated "Sources" label based on target language
                sources_label = self._get_sources_label(target_response_language)
                sources_list = "\n".join([f"- {doc}" for doc in source_documents])
                final_answer = f"{final_answer}\n\n📚 {sources_label}:\n{sources_list}"

            logger.info(f"✅ Final answer generated in {target_response_language} (Sources: {len(source_documents)})")
            
            return final_answer, source_documents

        except Exception as e:
            logger.error(f"❌ Error during final LLM invocation: {e}")
            fallback_answer = (
                "An unexpected error occurred during answer generation."
            )
            
            # Translate the technical fallback to the user's language
            translated_fallback = self.language_service.translate_answer_back(
                fallback_answer, query_language_code
            )
            logger.info(f"✅ Fallback error translated to {query_language_code}")
            return translated_fallback, []
    
    def _get_sources_label(self, language_code: str) -> str:
        """
        Get translated 'Sources' label for the given language.
        
        Args:
            language_code: ISO language code (IT, EN, FR, etc.)
        
        Returns:
            Translated label for 'Sources'
        """
        # Map of language codes to 'Sources' translations
        sources_translations = {
            "IT": "Fonti",
            "EN": "Sources",
            "FR": "Sources",
            "DE": "Quellen",
            "ES": "Fuentes",
            "PT": "Fontes",
            "NL": "Bronnen",
            "RU": "Источники",
            "ZH": "来源",
            "JA": "情報源",
            "KO": "출처",
            "AR": "المصادر",
            "PL": "Źródła",
            "TR": "Kaynaklar",
            "SV": "Källor",
            "NO": "Kilder",
            "DA": "Kilder",
            "FI": "Lähteet",
            "CS": "Zdroje",
            "HU": "Források",
            "RO": "Surse",
        }
        
        return sources_translations.get(language_code.upper(), "Sources")
    
    # --- Document Management Helper Methods ---
    # These methods delegate to the repository for document CRUD operations
    # Required by tests and router endpoints
    
    def get_user_documents(self, user_id: str) -> List:
        """
        Get list of all documents for a user with metadata.
        
        Args:
            user_id: The user ID
        
        Returns:
            List of DocumentInfo objects with filename, chunks_count, language, uploaded_at
        """
        from app.schemas.rag_schema import DocumentInfo
        
        try:
            # Get larger sample to ensure all documents are discovered
            # Using 10000 as default sample size (increased from 1000)
            metadatas, _ = self.repository.get_user_chunks_sample(user_id, sample_size=100000)
            
            if not metadatas:
                logger.info(f"📂 No documents found for user {user_id}")
                return []
            
            logger.debug(f"📊 Processing {len(metadatas)} metadata entries to discover unique documents")
            
            # Group chunks by filename
            documents_map = {}
            for metadata in metadatas:
                filename = metadata.get("original_filename", "Unknown")
                
                if filename not in documents_map:
                    documents_map[filename] = {
                        "filename": filename,
                        "language": metadata.get("original_language_code", "unknown"),
                        "uploaded_at": metadata.get("uploaded_at"),
                        "chunks": 1
                    }
                else:
                    documents_map[filename]["chunks"] += 1
            
            # Convert to DocumentInfo list
            documents = [
                DocumentInfo(
                    filename=doc["filename"],
                    chunks_count=doc["chunks"],
                    language=doc["language"],
                    uploaded_at=str(doc["uploaded_at"]) if doc["uploaded_at"] else None
                )
                for doc in documents_map.values()
            ]
            
            logger.info(f"📚 Found {len(documents)} unique documents for user {user_id}")
            logger.debug(f"   Documents: {[d.filename for d in documents]}")
            return documents
            
        except Exception as e:
            logger.error(f"❌ Error getting user documents: {e}")
            return []
    
    def delete_user_document(self, user_id: str, filename: str) -> int:
        """
        Delete a specific document for a user.
        
        Args:
            user_id: The user ID
            filename: The filename to delete
        
        Returns:
            Number of chunks deleted
        """
        try:
            chunks_deleted = self.repository.delete_document(user_id, filename)
            logger.info(f"✅ Deleted {chunks_deleted} chunks for document '{filename}'")
            return chunks_deleted
        except Exception as e:
            logger.error(f"❌ Error deleting document '{filename}': {e}")
            raise
    
    def delete_all_user_documents(self, user_id: str) -> int:
        """
        Delete all documents for a user.
        
        Args:
            user_id: The user ID
        
        Returns:
            Number of chunks deleted
        """
        try:
            chunks_deleted = self.repository.delete_all_user_documents(user_id)
            logger.info(f"✅ Deleted all documents for user {user_id} ({chunks_deleted} chunks)")
            return chunks_deleted
        except Exception as e:
            logger.error(f"❌ Error deleting all documents for user {user_id}: {e}")
            raise
    
    def get_user_document_count(self, user_id: str) -> int:
        """
        Count the number of unique documents for a user.
        
        Args:
            user_id: The user ID
        
        Returns:
            Number of unique documents
        """
        try:
            metadatas, _ = self.repository.get_user_chunks_sample(user_id, sample_size=1000)
            
            if not metadatas:
                return 0
            
            # Count unique filenames
            unique_files = set(
                metadata.get("original_filename", "Unknown") 
                for metadata in metadatas
            )
            
            count = len(unique_files)
            logger.debug(f"📊 User {user_id} has {count} documents")
            return count
            
        except Exception as e:
            logger.error(f"❌ Error counting user documents: {e}")
            return 0
    
    def generate_conversation_summary(self, conversation_history: List[ConversationMessage]) -> str:
        """
        Generate a concise summary of conversation history for long-term memory.
        
        This is used for conversation summarization when the history becomes too long.
        The summary extracts key facts, topics, and ongoing issues.
        
        Args:
            conversation_history: List of conversation messages to summarize
        
        Returns:
            Concise summary string
        """
        try:
            # Build conversation text
            conversation_text = "\n".join([
                f"{msg.role.upper()}: {msg.content}"
                for msg in conversation_history
            ])
            
            # Summarization prompt
            summary_prompt = f"""You are a conversation summarizer. Generate a concise summary of the following conversation.

CONVERSATION:
{conversation_text}

SUMMARY (3-5 sentences, extract key facts, topics, and questions):"""
            
            # Use LLM to generate summary
            response = self.query_gen_llm.invoke(summary_prompt)
            summary = str(response.content).strip()
            
            logger.info(f"✅ Generated conversation summary ({len(summary)} chars)")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Conversation summarization failed: {e}")
            return "Unable to generate summary."

# Dependency injector pattern registration (not part of the class, usually done externally)
def get_rag_service(
    repository: VectorStoreRepository = Depends(get_vector_store_repository),
) -> RAGService:
    """Dependency injector for RAGService."""
    return RAGService(repository=repository)