"""
Document Indexing Service

Handles PDF processing, chunking, language detection, and embedding generation.
Extracted from RAGService as part of service splitting (200-300 lines per service).

Responsibilities:
- Load and parse PDF documents
- Classify documents and apply appropriate chunking strategy
- Detect document language (auto or manual)
- Generate embeddings and store in vector database
- Provide language preview for user confirmation
"""

import os
import time
import aiofiles
from typing import List, Optional, Tuple

from app.core.logging import logger
from app.repositories.vector_store_repository import VectorStoreRepository
from app.services.document_classifier_service import (
    DocumentCategory,
    DocumentClassifierService,
)
from app.services.language_service import LanguageService
from fastapi import UploadFile
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.documents import Document
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter


class DocumentIndexingService:
    """
    Specialized service for document indexing operations.
    
    Part of RAGService refactoring to maintain 200-300 lines per service.
    """
    
    def __init__(
        self,
        repository: VectorStoreRepository,
        language_service: LanguageService,
        classifier_service: DocumentClassifierService
    ):
        """
        Initialize DocumentIndexingService with required dependencies.
        
        Args:
            repository: Vector store repository for document storage
            language_service: Service for language detection
            classifier_service: Service for document classification
        """
        self.repository = repository
        self.language_service = language_service
        self.classifier_service = classifier_service
    
    async def index_document(
        self, 
        file: UploadFile, 
        user_id: str,
        document_language: Optional[str] = None
    ) -> Tuple[int, str]:
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

            async with aiofiles.open(temp_file_path, "wb") as f:
                await f.write(content)

            # 2. Load PDF using UnstructuredPDFLoader
            loader = UnstructuredPDFLoader(temp_file_path, mode="elements")
            documents = loader.load()

            # 3. Classify document to determine chunking strategy
            full_text_preview = " ".join([doc.page_content for doc in documents[:15]])[:5000]
            category = self.classifier_service.classify_document(
                file.filename or "unknown",
                full_text_preview[:1000]
            )
            logger.info(f"📄 Initial classification: {category.value}")

            # 4. Apply chunking strategy based on classification with fallback
            chunks = self._apply_chunking_strategy(documents, category, full_text_preview)

            # 5. Process and filter chunks
            chunks = filter_complex_metadata(chunks)
            
            # 6. Prepare chunks with metadata
            final_chunks = self._prepare_chunks_with_metadata(
                chunks, user_id, file.filename or "unknown.pdf", doc_language
            )
            
            # Update doc_language if it was auto-detected
            if doc_language is None and final_chunks:
                doc_language = final_chunks[0].metadata.get("original_language_code", "EN")

            # 7. Index the chunks (in their original language) - OPTIMIZED WITH BATCH UPSERT
            if final_chunks:
                total_chunks_indexed = self._batch_index_chunks(final_chunks)

            # Ensure doc_language is not None before returning
            final_doc_language = doc_language if doc_language else "EN"
            logger.info(f"✅ Indexed {total_chunks_indexed} chunks in language: {final_doc_language}")
            return total_chunks_indexed, final_doc_language
            
        except Exception as e:
            logger.error(f"❌ Indexing error (service level): {e}")
            raise e
        finally:
            # 8. Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(os.path.abspath(temp_file_path))

    def _apply_chunking_strategy(
        self,
        documents: List[Document],
        category: DocumentCategory,
        full_text_preview: str
    ) -> List[Document]:
        """
        Apply appropriate chunking strategy based on document classification.
        
        Args:
            documents: Loaded document pages
            category: Document category from classification
            full_text_preview: Preview text for structural analysis
            
        Returns:
            List of chunked documents
        """
        use_structural_chunking = False
        
        if category == DocumentCategory.AUTORITA_STRUTTURALE:
            use_structural_chunking = True
            strategy_reason = "Direct Classification (AUTORITA_STRUTTURALE)"
        else:
            # Fallback: Check structural density
            if self.classifier_service.has_structural_density(full_text_preview):
                logger.info("🔄 Fallback triggered: High structural density detected")
                use_structural_chunking = True
                strategy_reason = "Fallback: High Structural Density"
            else:
                strategy_reason = "Direct Classification (INFORMATIVO_NON_STRUTTURATO)"
        
        logger.info(
            f"🧠 Chunking Strategy: {'STRUCTURAL' if use_structural_chunking else 'FIXED-SIZE'} "
            f"| Reason: {strategy_reason}"
        )
        
        if use_structural_chunking:
            # Structural chunking (semantic)
            text_splitter = RecursiveCharacterTextSplitter.from_language(
                language=Language.MARKDOWN, chunk_size=1024, chunk_overlap=100
            )
            chunks = text_splitter.split_documents(documents)
            logger.info(f"🪓 Applied STRUCTURAL chunking: {len(chunks)} chunks")
        else:
            # Standard fixed-size chunking
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
            chunks = text_splitter.split_documents(documents)
            logger.info(f"🪓 Applied FIXED-SIZE chunking: {len(chunks)} chunks")
        
        return chunks

    def _prepare_chunks_with_metadata(
        self,
        chunks: List[Document],
        user_id: str,
        filename: str,
        doc_language: Optional[str]
    ) -> List[Document]:
        """
        Add metadata to chunks including user_id, language, chapter tracking, and timestamp.
        
        Args:
            chunks: Chunked documents
            user_id: User identifier for multi-tenancy
            filename: Original filename
            doc_language: Document language (None = auto-detect)
            
        Returns:
            Chunks with complete metadata
        """
        final_chunks: List[Document] = []
        current_chapter = "Document Start"
        uploaded_at = int(time.time() * 1000)  # Milliseconds timestamp
        detected_language = doc_language

        for chunk in chunks:
            # Track hierarchical structure from document elements
            element_type = chunk.metadata.get("type", "NarrativeText")

            # Update chapter tracking when encountering titles or headers
            if "Title" in element_type or "Header" in element_type:
                current_chapter = chunk.page_content.strip()
                chunk.metadata["element_type"] = element_type

            # Use provided language or auto-detect from content
            if detected_language is None and len(chunk.page_content) > 50:
                # Auto-detect language from first substantial chunk
                detected_lang_code = self.language_service.detect_language(chunk.page_content)
                detected_language = detected_lang_code.upper()
                logger.debug(f"🌍 Auto-detected document language: {detected_language}")
            elif detected_language is None:
                detected_language = "EN"  # Default fallback

            # Add structural, language, and user metadata to every chunk
            chunk.metadata["chapter_title"] = current_chapter
            chunk.metadata["source"] = user_id
            chunk.metadata["original_filename"] = filename
            chunk.metadata["original_language_code"] = detected_language
            chunk.metadata["uploaded_at"] = uploaded_at

            final_chunks.append(chunk)

        return final_chunks

    def _batch_index_chunks(self, chunks: List[Document]) -> int:
        """
        Index chunks in optimized batches for better throughput.
        
        Args:
            chunks: Chunks to index
            
        Returns:
            Total number of chunks indexed
        """
        start_time = time.time()
        total_chunks_indexed = 0
        
        # Optimized batch size for better throughput
        OPTIMIZED_BATCH_SIZE = 500
        total_batches = (len(chunks) + OPTIMIZED_BATCH_SIZE - 1) // OPTIMIZED_BATCH_SIZE
        
        logger.info(
            f"📊 Starting embedding generation for {len(chunks)} chunks in {total_batches} batches"
        )
        
        # Process in batches for better progress visibility
        for batch_idx, i in enumerate(range(0, len(chunks), OPTIMIZED_BATCH_SIZE), 1):
            batch = chunks[i : i + OPTIMIZED_BATCH_SIZE]
            batch_start = time.time()
            
            # Single upsert operation for entire batch via repository
            self.repository.add_documents(batch)
            
            batch_time = time.time() - batch_start
            total_chunks_indexed += len(batch)
            throughput = len(batch) / batch_time if batch_time > 0 else 0
            
            logger.info(
                f"⚡ Batch {batch_idx}/{total_batches}: {len(batch)} chunks in {batch_time:.2f}s "
                f"({throughput:.1f} chunks/s)"
            )
        
        elapsed = time.time() - start_time
        overall_throughput = len(chunks) / elapsed if elapsed > 0 else 0
        logger.info(
            f"🚀 Processed {len(chunks)} chunks in {elapsed:.2f}s "
            f"({overall_throughput:.1f} chunks/s overall)"
        )
        
        return total_chunks_indexed

    async def detect_document_language_preview(
        self,
        file: UploadFile
    ) -> Tuple[str, float]:
        """
        Detect language from PDF preview without full indexing.
        
        Used for pre-upload language confirmation UI.
        
        Args:
            file: The uploaded PDF file
            
        Returns:
            Tuple of (language_code, confidence_score)
        """
        temp_file_path = f"/tmp/{file.filename}"
        
        try:
            content = await file.read()
            if not content:
                raise ValueError("The uploaded file is empty.")

            async with aiofiles.open(temp_file_path, "wb") as f:
                await f.write(content)

            # Load first pages only for preview
            loader = UnstructuredPDFLoader(temp_file_path, mode="elements")
            documents = loader.load()
            
            # Extract preview text (first 3 pages or 2000 chars)
            preview_text = " ".join([doc.page_content for doc in documents[:3]])[:2000]
            
            if len(preview_text) < 50:
                logger.warning("⚠️ Not enough text for language detection")
                return "EN", 0.5  # Default fallback
            
            # Detect language (confidence not available, assume high confidence if detected)
            detected_lang = self.language_service.detect_language(preview_text)
            confidence = 0.9  # langdetect has high accuracy
            
            logger.info(f"🌍 Preview language detected: {detected_lang} (confidence: {confidence:.2f})")
            return detected_lang.upper(), confidence
            
        except Exception as e:
            logger.error(f"❌ Language detection error: {e}")
            raise e
        finally:
            if os.path.exists(temp_file_path):
                os.remove(os.path.abspath(temp_file_path))
