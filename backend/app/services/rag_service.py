# backend/app/services/rag_service.py

import os
from typing import List, Tuple
from fastapi import UploadFile
from pydantic import SecretStr
from openai import OpenAI  # Import diretto del client OpenAI per traduzione query

# --- INTERNAL SERVICE IMPORT ---
from app.services.language_service import LanguageService, RETRIEVAL_TARGET_LANGUAGE

# LangChain Imports
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.output_parsers import JsonOutputParser

# Internal Imports
from app.core.config import settings
from app.db.chroma_client import (
    get_chroma_client,
    get_embedding_function,
    COLLECTION_NAME,
)
from app.schemas.rag import QueryClassification, CATEGORIES

# --- CONSTANTS & CONFIGURATION ---

# NEW CONSTANT: Document limit for each embedding batch (fixes the size error)
EMBEDDING_DOC_BATCH_SIZE = 2000

# Prompt Template for generating alternative queries
MULTI_QUERY_PROMPT = (
    "You are a helpful assistant that generates multiple alternative versions of a user's "
    "query to retrieve the most relevant documents from a vector store. "
    "Generate 3 distinct queries for the following user question, ensuring they are diverse "
    "in terms of keywords and phrasing. Return the queries as a newline-separated list (one query per line). "
    "Original Query: {query}"
)

# System Instruction to prevent hallucination and enforce compliance (LLM-based, still necessary)
SYSTEM_INSTRUCTION = (
    "You are an intelligent document compliance assistant. "
    "Your main objective is to answer user questions truthfully and solely based on "
    "the provided context (source documents). "
    "If the answer cannot be found in the context, clearly state: 'I cannot answer this question based on the documents provided.' "
    "Provide the answer directly, WITHOUT adding conversational intros or outros."
)

# Prompt for query classification (LLM-based, still necessary for structured output)
CLASSIFICATION_PROMPT = PromptTemplate.from_template(
    """You are a query classification agent. Your task is to classify the user's question 
    into one of the following categories: {categories}. 
    Analyze the following query and return a single JSON object strictly following the provided schema.
    Query: {query}
    """
)

# Prompt Template for the final LLM call (LLM-based, still necessary for RAG)
RAG_PROMPT_TEMPLATE = (
    f"{SYSTEM_INSTRUCTION}\n\n" "Context: {context}\n\n" "Question: {question}"
)

# --- RAG SERVICE CLASS ---


class RAGService:
    def __init__(self):
        # Initialize core components
        self.embedding_function = get_embedding_function()
        self.chroma_client = get_chroma_client()

        # Initialize Language Service
        self.language_service = LanguageService(target_lang=RETRIEVAL_TARGET_LANGUAGE)

        # Estrai la chiave API in modo sicuro
        self.api_key_value = (
            settings.OPENAI_API_KEY.get_secret_value()
            if isinstance(settings.OPENAI_API_KEY, SecretStr)
            else str(settings.OPENAI_API_KEY)
        )

        # LLM per la generazione finale (bassa temperatura per conformità ai fatti)
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0.0,
            api_key=SecretStr(self.api_key_value),
        )

        # LLM separato (temperatura più alta) per la generazione e classificazione delle query
        self.query_gen_llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0.7,
            api_key=SecretStr(self.api_key_value),
        )

        # Inizializza il client OpenAI per le chiamate dirette (traduzione query)
        self.openai_client = OpenAI(api_key=self.api_key_value)

        # Initialize the Chroma Vector Store (LangChain compatible wrapper)
        self.vector_store = Chroma(
            client=self.chroma_client,
            collection_name=COLLECTION_NAME,
            embedding_function=self.embedding_function,
        )

    def _translate_query_with_llm(self, query: str) -> str:
        """
        Traduce la query in inglese usando l'LLM di OpenAI.
        Costo minimo, massima affidabilità per il Retrieval.
        """
        prompt = (
            f"Translate the following user query to a standard, concise English search phrase. "
            f"If the query is already in English, return it unchanged. Query: '{query}'"
        )

        try:
            response = self.openai_client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
            # Ritorna la traduzione pulita, altrimenti la query originale
            content = response.choices[0].message.content
            return content.strip() if content else query

        except Exception as e:
            print(
                f"Error translating query with OpenAI LLM: {e}. Falling back to original query."
            )
            return query  # Fallback alla query originale in caso di errore LLM

    async def index_document(self, file: UploadFile, user_id: str) -> int:
        """
        Loads a PDF, splits it into chunks, creates embeddings in the original language,
        and saves them to ChromaDB.
        Tags each chunk with the user_id for isolation (Multi-Tenancy).
        """

        # 1. Save the uploaded content to a temporary file
        temp_file_path = f"/tmp/{file.filename}"
        total_chunks_indexed = 0

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

            # 4. Prepare chunks (NO TRANSLATION DURING INDEXING - IN LINGUA ORIGINALE)
            final_chunks: List[Document] = []

            # NUOVO: Variabili per tracciare la gerarchia
            current_chapter = "Document Start"

            for chunk in chunks:
                # -------------------------------------------------------------
                # 1. TRACCIAMENTO DELLA STRUTTURA GERARCHICA
                # -------------------------------------------------------------
                # UnstructuredPDFLoader assegna il tipo di elemento in metadata['type']
                element_type = chunk.metadata.get("type", "NarrativeText")

                # Se l'elemento è un titolo o un capitolo, aggiorna il tracciamento.
                # 'Title' o 'Header' (h1, h2, h3, etc.) indicano una nuova sezione.
                if "Title" in element_type or "Header" in element_type:
                    current_chapter = chunk.page_content.strip()
                    # Aggiungi un metadato per il tipo di elemento
                    chunk.metadata["element_type"] = element_type

                # -------------------------------------------------------------
                # 2. RILEVAMENTO LINGUA E METADATI COMUNI
                # -------------------------------------------------------------
                # Detect language (for logging/metadata only, not for content modification)
                detected_lang_code = "EN"
                if len(chunk.page_content) > 50:
                    detected_lang_code = self.language_service.detect_language(
                        chunk.page_content
                    )

                # Add crucial structural metadata to every chunk
                chunk.metadata["chapter_title"] = current_chapter

                # Add Multi-Tenancy metadata
                chunk.metadata["source"] = user_id
                chunk.metadata["original_filename"] = file.filename
                chunk.metadata["original_language_code"] = detected_lang_code

                final_chunks.append(chunk)

            # 5. Index the chunks (in their original language)
            if final_chunks:
                for i in range(0, len(final_chunks), EMBEDDING_DOC_BATCH_SIZE):
                    batch = final_chunks[i : i + EMBEDDING_DOC_BATCH_SIZE]
                    self.vector_store.add_documents(batch)
                    total_chunks_indexed += len(batch)

            return total_chunks_indexed
        except Exception as e:
            # Print the error for debugging and re-raise it or handle as preferred.
            print(f"Indexing error (service level): {e}")
            raise e
        finally:
            # 6. Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(os.path.abspath(temp_file_path))

    def _generate_alternative_queries(self, query: str) -> List[str]:
        """Generates 3 alternative search queries to improve RAG relevance."""
        try:
            prompt = MULTI_QUERY_PROMPT.format(query=query)
            response_content = self.query_gen_llm.invoke(prompt).content

            if isinstance(response_content, list):
                response = "\n\n".join(str(item) for item in response_content)
            else:
                response = str(response_content)

            alt_queries = [
                q.strip()
                for q in response.split("\n")
                if q.strip() and len(q.strip()) > 5
            ]

            return alt_queries[:3]

        except Exception as e:
            print(f"Error generating alternative queries: {e}")
            return []

    def _classify_query(self, query: str) -> str:
        """Classifies the query to specialize the retrieval (still uses LLM for structured output)."""
        try:
            parser = JsonOutputParser(pydantic_object=QueryClassification)

            classification_prompt = CLASSIFICATION_PROMPT.partial(
                categories=str(CATEGORIES),
                format_instructions=parser.get_format_instructions(),
            )

            chain = classification_prompt | self.query_gen_llm | parser

            # Classify using the original query for the most direct intent analysis
            # Ensure the output is a dictionary before accessing category_tag
            result = chain.invoke({"query": query})

            if isinstance(result, dict) and "category_tag" in result:
                return result["category_tag"].upper()
            else:
                # Se il parsing fallisce ma il risultato non è un errore esplicito
                print(
                    f"Classification failed to parse 'category_tag' correctly. Result: {result}"
                )
                return "GENERAL_SEARCH"

        except Exception as e:
            # Questo è il blocco che cattura l'errore 'dict' object has no attribute 'category_tag'
            print(f"Error classifying query: {e}")
            return "GENERAL_SEARCH"  # Safe fallback

    def answer_query(self, query: str, user_id: str) -> Tuple[str, List[str]]:
        """
        Retrieves relevant documents for a specific user and generates an answer
        using the LLM, leveraging the robust embedding model.
        """

        # 1. Detect the original query language code (L_query)
        original_language_code = self.language_service.detect_language(query).upper()
        print(f"DEBUG: Original Query Language Code: {original_language_code}")

        # 2. Translate the user query to English for accurate retrieval
        # Utilizza l'LLM (più affidabile) per la traduzione della query.
        translated_query_for_retrieval = self._translate_query_with_llm(query)
        print(
            f"DEBUG: Translated Query for Retrieval: {translated_query_for_retrieval}"
        )

        # 3. Classify the query (using the original query - costs LLM call)
        query_tag = self._classify_query(query)
        print(f"DEBUG: Query Classified as: {query_tag}")

        # 4. Generate Alternative Queries based on the English translation (costs LLM call)
        alternative_queries = self._generate_alternative_queries(
            translated_query_for_retrieval
        )

        # List of all queries to execute: English Translation + Alternative Queries
        all_queries = [translated_query_for_retrieval] + alternative_queries

        # 5. Setup Retrieval (k=60 - maximum pool)
        retriever = self.vector_store.as_retriever(
            search_kwargs={"filter": {"source": user_id}, "k": 60}
        )

        # 6. Execute retrieval for all queries and collect results
        all_retrieved_docs = []
        doc_ids = set()

        for q in all_queries:
            docs = retriever.invoke(q)

            for doc in docs:
                # Simple check to uniquely identify documents by content and metadata
                metadata_tuple = tuple(sorted(doc.metadata.items()))
                doc_id = hash((doc.page_content, metadata_tuple))

                if doc_id not in doc_ids:
                    all_retrieved_docs.append(doc)
                    doc_ids.add(doc_id)

        # 7. Final Context Selection (top_k=25)
        top_k_for_llm = 25
        context_docs = all_retrieved_docs[:top_k_for_llm]

        # ... (fallback handling) ...
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
                fallback_answer, original_language_code
            )
            return translated_fallback, source_documents

        # Prepare context and sources (Context is in its ORIGINAL language)
        # Riscrivi il contesto per includere la struttura del capitolo
        context = "\n---\n".join(
            [
                f"[SECTION: {doc.metadata.get('chapter_title', 'N/A')}]\n{doc.page_content}"
                for doc in context_docs
            ]
        )
        source_documents = list(
            set(doc.metadata.get("original_filename", "N/A") for doc in context_docs)
        )

        # 8. Create Final Prompt (English Query + Context in Original Language)
        # Il prompt ora passa la gerarchia all'LLM
        final_prompt = RAG_PROMPT_TEMPLATE.format(
            context=context, question=translated_query_for_retrieval
        )

        # 9. Generate Response from LLM (Response will be in English first - costs LLM call)
        try:
            english_answer = str(self.llm.invoke(final_prompt).content)
        except Exception as e:
            print(f"LLM Invocation Error: {e}")
            english_answer = "An error occurred during LLM processing."

        # 10. Translate Final Answer back to the user's original language code (L_query)
        final_answer = self.language_service.translate_answer_back(
            english_answer, original_language_code
        )

        return final_answer, source_documents


# Initialize the service instance (Singleton)
rag_service = RAGService()
