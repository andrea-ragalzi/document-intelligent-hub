# backend/app/services/rag_service.py

"""
RAG Service Module - Main Orchestrator

Coordinates document indexing, retrieval, and answer generation.
Delegates specialized tasks to dedicated service modules for better maintainability.
"""

import os
from typing import List, Optional, Tuple

# Core imports
from app.core.config import settings
from app.db.chroma_client import (
    COLLECTION_NAME,
    get_chroma_client,
    get_embedding_function,
)
from app.schemas.rag import CATEGORIES, ConversationMessage, QueryClassification
from app.schemas.use_cases import UseCaseType

# Specialized service imports
from app.services.language_service import RETRIEVAL_TARGET_LANGUAGE, LanguageService
from app.services.prompt_template_service import prompt_template_service
from app.services.query_expansion_service import query_expansion_service
from app.services.reranking_service import reranking_service
from app.services.translation_service import translation_service
from app.services.use_case_detection_service import use_case_detection_service

# FastAPI and document processing
from fastapi import UploadFile
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_community.vectorstores import Chroma
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
    Main RAG Service - Orchestrator
    
    Coordinates document indexing, retrieval, and answer generation.
    Delegates specialized tasks to dedicated service modules.
    """
    
    def __init__(self):
        """Initialize the RAG service with all required components."""
        # Initialize core components
        self.embedding_function = get_embedding_function()
        self.chroma_client = get_chroma_client()

        # Initialize language service for answer translation
        self.language_service = LanguageService(target_lang=RETRIEVAL_TARGET_LANGUAGE)

        # Extract API key securely
        self.api_key_value = (
            settings.OPENAI_API_KEY.get_secret_value()
            if isinstance(settings.OPENAI_API_KEY, SecretStr)
            else str(settings.OPENAI_API_KEY)
        )

        # LLM for final answer generation (low temperature for factual accuracy)
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0.0,
            api_key=SecretStr(self.api_key_value),
        )

        # LLM for query classification (higher temperature)
        self.query_gen_llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0.7,
            api_key=SecretStr(self.api_key_value),
        )

        # Initialize Chroma Vector Store
        self.vector_store = Chroma(
            client=self.chroma_client,
            collection_name=COLLECTION_NAME,
            embedding_function=self.embedding_function,
        )

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

            if isinstance(result, dict) and "category_tag" in result:
                return result["category_tag"].upper()
            else:
                print(f"Classification parsing failed. Result: {result}")
                return "GENERAL_SEARCH"

        except Exception as e:
            print(f"Error classifying query: {e}")
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
                    print(f"DEBUG: Auto-detected document language: {doc_language}")
                elif doc_language is None:
                    doc_language = "EN"  # Default fallback

                # Add structural and language metadata to every chunk
                chunk.metadata["chapter_title"] = current_chapter
                chunk.metadata["source"] = user_id
                chunk.metadata["original_filename"] = file.filename
                chunk.metadata["original_language_code"] = doc_language  # Use document language

                final_chunks.append(chunk)

            # 5. Index the chunks (in their original language)
            if final_chunks:
                for i in range(0, len(final_chunks), EMBEDDING_DOC_BATCH_SIZE):
                    batch = final_chunks[i : i + EMBEDDING_DOC_BATCH_SIZE]
                    self.vector_store.add_documents(batch)
                    total_chunks_indexed += len(batch)

            # Ensure doc_language is not None before returning
            final_doc_language = doc_language if doc_language else "EN"
            print(f"DEBUG: Indexed {total_chunks_indexed} chunks in language: {final_doc_language}")
            return total_chunks_indexed, final_doc_language
        except Exception as e:
            # Print the error for debugging and re-raise it or handle as preferred.
            print(f"Indexing error (service level): {e}")
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
        print(f"DEBUG: Query Language Code: {query_language_code}")

        # 2. Assume document language is EN by default for first pass
        # We'll do a quick translation if query is not in English
        document_language = "EN"  # Default assumption
        
        # If query is not in English, translate it for better sample retrieval
        query_for_sample = query
        if query_language_code != "EN":
            query_for_sample = translation_service.translate_query_to_language(query, "EN")
            print(f"DEBUG: Translated query for sampling: {query_for_sample}")
        
        # 3. Initial retrieval to determine actual document language from chunks
        temp_retriever = self.vector_store.as_retriever(
            search_kwargs={"filter": {"source": user_id}, "k": 5}
        )
        sample_docs = temp_retriever.invoke(query_for_sample)  # Use translated query
        
        print(f"DEBUG: Sample retrieval returned {len(sample_docs)} documents")
        
        # Extract document language from retrieved chunks' metadata
        if sample_docs:
            # Get the most common language from retrieved documents
            lang_counts = {}
            for doc in sample_docs:
                lang = doc.metadata.get("original_language_code", "EN")
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
            
            if lang_counts:
                document_language = max(lang_counts, key=lambda k: lang_counts[k])
                print(f"DEBUG: Language distribution in sample: {lang_counts}")
                print(f"DEBUG: Detected document language from retrieval: {document_language}")
        else:
            print("DEBUG: WARNING - No documents found in sample retrieval!")
        
        # 4. Translate the user query to the DOCUMENT LANGUAGE for accurate retrieval
        if query_language_code == document_language:
            translated_query_for_retrieval = query
            print("DEBUG: Query already in document language, no translation needed")
        else:
            translated_query_for_retrieval = translation_service.translate_query_to_language(
                query, document_language
            )
            print(f"DEBUG: Translated Query for Retrieval ({document_language}): {translated_query_for_retrieval}")

        # 4. Classify the query (using the original query)
        query_tag = self._classify_query(query)
        print(f"DEBUG: Query Classified as: {query_tag}")

        # 5. Generate Alternative Queries based on the translated query
        alternative_queries = query_expansion_service.generate_alternative_queries(
            translated_query_for_retrieval
        )
        print(f"DEBUG: Generated {len(alternative_queries)} alternative queries")

        # List of all queries to execute: Translated Query + Alternative Queries
        all_queries = [translated_query_for_retrieval] + alternative_queries

        # 5. Setup Retrieval with larger pool (k=30 for better coverage of scattered information)
        retriever = self.vector_store.as_retriever(
            search_kwargs={"filter": {"source": user_id}, "k": 30}
        )

        # 6. Execute retrieval for all queries and collect results (Fase 1: Ricerca Parallela)
        all_retrieved_docs = []
        doc_ids = set()

        for q in all_queries:
            docs = retriever.invoke(q)
            print(f"DEBUG: Query '{q[:50]}...' retrieved {len(docs)} documents")

            for doc in docs:
                # Simple check to uniquely identify documents by content and metadata
                metadata_tuple = tuple(sorted(doc.metadata.items()))
                doc_id = hash((doc.page_content, metadata_tuple))

                if doc_id not in doc_ids:
                    all_retrieved_docs.append(doc)
                    doc_ids.add(doc_id)

        print(f"DEBUG: Retrieved {len(all_retrieved_docs)} unique documents from parallel search")

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
            print(
                f"DEBUG: Retrieval failed for user_id='{user_id}'. Fallback answer sent."
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
        
        print(f"DEBUG: Final context prepared with {len(context_docs)} chunks from {len(source_documents)} documents")

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
            print(f"DEBUG: Including {len(recent_history)} messages in conversation history")

        # 9. Create Final Prompt with Use Case Optimization
        # Auto-detect use case if not explicitly provided
        if use_case is None:
            detected_use_case = use_case_detection_service.detect_use_case(query)
            if detected_use_case:
                use_case = detected_use_case
                print(f"DEBUG: Auto-detected use case: {use_case}")
        
        if use_case:
            print(f"DEBUG: Using optimized prompt for use case: {use_case}")
            
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
            
            print(f"DEBUG: Generated optimized prompt with constraints - Quantity: {quantity}, Format: {constraints.format_constraint}, Response Language: {query_lang_name}")
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
            print(f"LLM Invocation Error: {e}")
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
        """
        try:
            # Get the collection
            collection = self.chroma_client.get_collection(name=COLLECTION_NAME)

            # Query with filter to get documents for this user
            results = collection.get(where={"source": user_id}, limit=1000)

            if not results or not results.get("metadatas"):
                return 0

            # Count unique filenames
            unique_files = set()
            metadatas = results.get("metadatas", [])
            if metadatas:
                for metadata in metadatas:
                    if metadata and "original_filename" in metadata:
                        unique_files.add(metadata["original_filename"])

            return len(unique_files)

        except Exception as e:
            print(f"Error getting document count for user {user_id}: {e}")
            return 0

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
            
            # Generate summary using the query generation LLM (higher temperature for natural language)
            summary = str(self.query_gen_llm.invoke(summary_prompt).content)
            
            print(f"DEBUG: Generated conversation summary ({len(summary)} chars)")
            return summary.strip()
            
        except Exception as e:
            print(f"Error generating conversation summary: {e}")
            return ""


# Initialize the service instance (Singleton)
rag_service = RAGService()
