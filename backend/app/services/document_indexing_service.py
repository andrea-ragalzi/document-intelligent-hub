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

import asyncio
import multiprocessing
import os
import re
import tempfile
import time
from collections import defaultdict
from typing import Any, cast

from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.documents import Document
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.config.security_constants import PDF_PARSING_TIMEOUT_SECONDS
from app.core.logging import logger
from app.core.constants import ChunkingConstants
from app.ports.uploaded_file import UploadedFilePort
from app.ports.vector_store import VectorStorePort
from app.services.document_classifier_service import (
    DocumentCategory,
    DocumentClassifierService,
)
from app.services.language_service import LanguageService

MAX_EXTRACTED_DOCUMENT_TEXT = ChunkingConstants.MAX_EXTRACTED_DOCUMENT_TEXT
MAX_DOCUMENT_CHUNKS = ChunkingConstants.MAX_DOCUMENT_CHUNKS
MAX_DOCUMENT_PAGES = ChunkingConstants.MAX_DOCUMENT_PAGES
PARSER_PROCESS_SHUTDOWN_SECONDS = 1
LAYOUT_ROW_KIND = "layout_row"
_LAYOUT_EXCLUDED_CATEGORIES = {"Header", "Footer"}
_PARSER_TABLE_CATEGORIES = {"Table", "TableCell"}
_PLAN_HEADER_PATTERN = re.compile(r"^NMP-\d+\s+\S.*$")
_ROW_ALIGNMENT_TOLERANCE = 4.0
_COLUMN_ALIGNMENT_TOLERANCE = 24.0


def _write_temporary_pdf(descriptor: int, content: bytes) -> None:
    """Write and close a temporary PDF descriptor outside the event loop."""
    with os.fdopen(descriptor, "wb") as temp_file:
        temp_file.write(content)


def _get_pdf_page_count(temp_file_path: str) -> int:
    """Read the PDF page count before sending it to the heavy parser."""
    return len(PdfReader(temp_file_path).pages)


def _load_pdf_documents_worker(
    temp_file_path: str, connection: Any, max_pages: int | None
) -> None:
    """Run Unstructured in a disposable process so a timeout can stop it."""
    try:
        if max_pages is not None and _get_pdf_page_count(temp_file_path) > max_pages:
            connection.send(("page_limit", None))
            return
        documents = UnstructuredPDFLoader(temp_file_path, mode="elements").load()
        connection.send(("success", documents))
    except Exception as exc:
        connection.send(("error", type(exc).__name__))
    finally:
        connection.close()


def _stop_pdf_parser_process(process: Any) -> None:
    """Terminate and reap a parser worker before returning capacity."""
    if process.is_alive():
        process.terminate()
    process.join(PARSER_PROCESS_SHUTDOWN_SECONDS)
    if process.is_alive():
        process.kill()
        process.join()
    process.close()


class DocumentIndexingService:
    """
    Specialized service for document indexing operations.

    Part of RAGService refactoring to maintain 200-300 lines per service.
    """

    def __init__(
        self,
        repository: VectorStorePort,
        language_service: LanguageService,
        classifier_service: DocumentClassifierService,
    ) -> None:
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
        file: UploadedFilePort,
        user_id: str,
        document_language: str | None = None,
        document_metadata: dict[str, Any] | None = None,
        allow_unlimited_document: bool = False,
    ) -> tuple[int, str]:
        """
        Load a PDF, split it into chunks, create embeddings, and save to ChromaDB.

        Documents are indexed in their original language (no translation).
        Each chunk is tagged with user_id for multi-tenancy isolation and
        document language for multilingual retrieval optimization.

        Args:
            file: The uploaded PDF file
            user_id: The user identifier for multi-tenancy
            document_language: Optional language code (IT, EN, FR, etc.).
                               Auto-detected if not provided.
            document_metadata: Internal metadata applied to every indexed chunk.

        Returns:
            Tuple of (chunks_indexed, detected_or_specified_language)
        """
        doc_language = document_language.upper() if document_language else None
        temp_file_path = await self._create_temp_file_from_upload(file)

        try:
            documents = await self._load_pdf_documents_with_timeout(
                temp_file_path, None if allow_unlimited_document else MAX_DOCUMENT_PAGES
            )
            # PDF parsing, chunking, embedding and Chroma writes are synchronous
            # libraries. Run the complete CPU/blocking section outside FastAPI's
            # event loop so health checks and independent requests can progress.
            return await asyncio.to_thread(
                self._index_document_sync,
                documents,
                file.filename or "unknown.pdf",
                user_id,
                doc_language,
                document_metadata,
                allow_unlimited_document,
            )
        finally:
            self._cleanup_temp_file(temp_file_path)

    async def _load_pdf_documents_with_timeout(
        self, temp_file_path: str, max_pages: int | None
    ) -> list[Document]:
        """Load through a child process and terminate it when parsing exceeds its deadline."""
        parent_connection, child_connection = multiprocessing.Pipe(duplex=False)
        process = multiprocessing.Process(
            target=_load_pdf_documents_worker,
            args=(temp_file_path, child_connection, max_pages),
        )
        process.start()
        child_connection.close()
        try:
            completed = await asyncio.to_thread(
                parent_connection.poll, PDF_PARSING_TIMEOUT_SECONDS
            )
            if not completed:
                raise TimeoutError("PDF parsing timed out.")
            outcome, payload = parent_connection.recv()
            if outcome == "page_limit":
                raise ValueError("Document has too many pages.")
            if outcome != "success":
                raise ValueError("Unable to parse PDF.")
            return cast(list[Document], payload)
        finally:
            parent_connection.close()
            await asyncio.to_thread(_stop_pdf_parser_process, process)

    def _index_document_sync(
        self,
        documents: list[Document],
        filename: str,
        user_id: str,
        document_language: str | None,
        document_metadata: dict[str, Any] | None,
        allow_unlimited_document: bool,
    ) -> tuple[int, str]:
        """Execute the synchronous PDF-to-Chroma portion in a worker thread."""
        try:
            extracted_text_size = sum(len(doc.page_content or "") for doc in documents)
            if (
                not allow_unlimited_document
                and extracted_text_size > MAX_EXTRACTED_DOCUMENT_TEXT
            ):
                raise ValueError("Document contains too much extracted text.")
            full_text = " ".join(doc.page_content or "" for doc in documents)
            full_text_preview = full_text[:5000]
            detected_language = (
                document_language
                if document_language is not None
                else self.language_service.detect_language(full_text)
            )
            detected_language = detected_language.lower()
            category = self._classify_document(filename, full_text_preview)
            # Build aggregates from raw parser elements before recursive splitting
            # duplicates element metadata across prose fragments. Only explicit
            # parser table/cell evidence is eligible for a relationship aggregate.
            layout_rows = self._build_layout_row_aggregates(documents)
            chunks = self._apply_chunking_strategy(
                documents, category, full_text_preview
            )
            chunks.extend(layout_rows)
            chunks = filter_complex_metadata(chunks)
            if not allow_unlimited_document and len(chunks) > MAX_DOCUMENT_CHUNKS:
                raise ValueError(
                    "This PDF produces too many chunks to process. Try splitting it into smaller files."
                )
            final_chunks = self._prepare_chunks_with_metadata(
                chunks, user_id, filename, detected_language, document_metadata
            )
            resolved_language = detected_language
            total_chunks_indexed = (
                self._batch_index_chunks(final_chunks) if final_chunks else 0
            )
            logger.info(
                f"✅ Indexed {total_chunks_indexed} chunks in language: {resolved_language}"
            )
            return total_chunks_indexed, resolved_language
        except Exception as exc:
            # A vector adapter may have accepted one or more batches before an
            # exception.  Delete by the tenant-owned filename so retries never
            # inherit partial chunks, embeddings, or metadata.
            try:
                self.repository.delete_document(user_id, filename)
            except Exception as rollback_exc:  # pragma: no cover - diagnostic only
                logger.error(
                    "Document indexing rollback failed | Type: {}",
                    type(rollback_exc).__name__,
                )
            logger.error("Document indexing failed | Type: {}", type(exc).__name__)
            raise

    async def _create_temp_file_from_upload(self, file: UploadedFilePort) -> str:
        """
        Create a secure temporary file from uploaded PDF.

        Args:
            file: The uploaded PDF file

        Returns:
            Path to temporary file

        Raises:
            ValueError: If file is empty
        """
        temp_fd, temp_file_path = tempfile.mkstemp(suffix=".pdf", prefix="upload_")
        try:
            content = await file.read()
            if not content:
                raise ValueError("The uploaded file is empty.")

            descriptor = temp_fd
            temp_fd = -1
            await asyncio.to_thread(_write_temporary_pdf, descriptor, content)
            return temp_file_path
        except Exception:
            if temp_fd != -1:
                os.close(temp_fd)
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise

    def _classify_document(self, filename: str, text_preview: str) -> Any:
        """
        Classify document to determine chunking strategy.

        Args:
            filename: Document filename
            text_preview: Preview of document text

        Returns:
            Document category
        """
        category = self.classifier_service.classify_document(
            filename, text_preview[:1000]
        )
        logger.info(f"📄 Initial classification: {category.value}")
        return category

    def _resolve_document_language(
        self, doc_language: str | None, chunks: list[Any]
    ) -> str:
        """
        Resolve document language from user input or auto-detection.

        Args:
            doc_language: User-provided language code or None
            chunks: Prepared document chunks with metadata

        Returns:
            Final language code (defaults to EN)
        """
        if doc_language is None and chunks:
            return str(chunks[0].metadata.get("original_language_code", "EN"))
        return doc_language if doc_language else "EN"

    @staticmethod
    def _cleanup_temp_file(temp_file_path: str) -> None:
        """
        Clean up temporary file.

        Args:
            temp_file_path: Path to temporary file
        """
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    def _apply_chunking_strategy(
        self,
        documents: list[Document],
        category: DocumentCategory,
        full_text_preview: str,
    ) -> list[Document]:
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
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=512, chunk_overlap=50
            )
            chunks = text_splitter.split_documents(documents)
            logger.info(f"🪓 Applied FIXED-SIZE chunking: {len(chunks)} chunks")

        return chunks

    @staticmethod
    def _layout_box(document: Document) -> tuple[float, float, float, float] | None:
        """Return the parser bounding box when it is a usable four-corner polygon."""
        coordinates = document.metadata.get("coordinates")
        if not isinstance(coordinates, dict):
            return None
        points = coordinates.get("points")
        if not isinstance(points, (tuple, list)) or not points:
            return None
        try:
            x_values = [float(point[0]) for point in points]
            y_values = [float(point[1]) for point in points]
        except (TypeError, IndexError, ValueError):
            return None
        return min(x_values), min(y_values), max(x_values), max(y_values)

    @staticmethod
    def _normalized_layout_text(document: Document) -> str:
        return " ".join((document.page_content or "").split())

    @staticmethod
    def _parser_table_group_id(document: Document) -> str | None:
        """Return an explicit parser table identity for a raw table/cell element.

        Coordinates and ``parent_id`` alone describe layout, not a table. A group
        exists only when the parser has marked an element as a table/cell and also
        supplied a table identifier or table parent. A standalone table element is
        already an atomic source unit and needs no fabricated row aggregate.
        """
        metadata = document.metadata
        category = metadata.get("category")
        table_id = metadata.get("table_id")
        if (
            category in _PARSER_TABLE_CATEGORIES
            and isinstance(table_id, str)
            and table_id.strip()
        ):
            return f"table:{table_id}"
        if category in _PARSER_TABLE_CATEGORIES:
            parent_id = metadata.get("parent_id")
            if isinstance(parent_id, str) and parent_id.strip():
                return f"parent:{parent_id}"
        return None

    @staticmethod
    def _shares_layout_relationship(row: list[Document]) -> bool:
        """Require parser parent/child evidence before combining aligned cells."""
        element_ids = {
            str(document.metadata.get("element_id"))
            for document in row
            if document.metadata.get("element_id")
        }
        parent_ids = [
            str(document.metadata.get("parent_id"))
            for document in row
            if document.metadata.get("parent_id")
        ]
        return len(parent_ids) != len(set(parent_ids)) or any(
            parent_id in element_ids for parent_id in parent_ids
        )

    def _build_layout_row_aggregates(self, chunks: list[Document]) -> list[Document]:
        """Build aggregates only from raw parser elements explicitly marked as cells."""
        by_page: dict[
            tuple[str, str],
            list[tuple[int, Document, tuple[float, float, float, float]]],
        ] = defaultdict(list)
        for index, document in enumerate(chunks):
            if document.metadata.get("chunk_kind") == LAYOUT_ROW_KIND:
                continue
            if document.metadata.get("category") in _LAYOUT_EXCLUDED_CATEGORIES:
                continue
            table_group_id = self._parser_table_group_id(document)
            if table_group_id is None:
                continue
            if not self._normalized_layout_text(document):
                continue
            box = self._layout_box(document)
            page = document.metadata.get("page_number")
            if box is None or page is None:
                continue
            by_page[(str(page), table_group_id)].append((index, document, box))

        aggregates: list[Document] = []
        for page_elements in by_page.values():
            aggregates.extend(self._build_page_layout_rows(page_elements))
        return aggregates

    def _build_page_layout_rows(
        self,
        page_elements: list[tuple[int, Document, tuple[float, float, float, float]]],
    ) -> list[Document]:
        """Aggregate aligned cells on one page, retaining only strong layout evidence."""
        rows = self._group_layout_rows(page_elements)
        plan_headers: list[tuple[float, str]] = []
        aggregates: list[Document] = []
        seen_text: set[str] = set()
        for row in rows:
            result = self._layout_row_candidate(row, plan_headers, seen_text)
            if result is None:
                continue
            header_cells, aggregate = result
            if header_cells:
                plan_headers = header_cells
            if aggregate is not None:
                aggregates.append(aggregate)
        return aggregates

    @staticmethod
    def _group_layout_rows(
        page_elements: list[tuple[int, Document, tuple[float, float, float, float]]],
    ) -> list[list[tuple[int, Document, tuple[float, float, float, float]]]]:
        ordered = sorted(page_elements, key=lambda item: (item[2][1] + item[2][3], item[0]))
        rows: list[list[tuple[int, Document, tuple[float, float, float, float]]]] = []
        for item in ordered:
            center_y = (item[2][1] + item[2][3]) / 2
            if rows and abs(center_y - DocumentIndexingService._row_center(rows[-1])) <= _ROW_ALIGNMENT_TOLERANCE:
                rows[-1].append(item)
            else:
                rows.append([item])
        return rows

    @staticmethod
    def _row_center(row: list[tuple[int, Document, tuple[float, float, float, float]]]) -> float:
        return sum((entry[2][1] + entry[2][3]) / 2 for entry in row) / len(row)

    def _layout_row_candidate(
        self,
        row: list[tuple[int, Document, tuple[float, float, float, float]]],
        plan_headers: list[tuple[float, str]],
        seen_text: set[str],
    ) -> tuple[list[tuple[float, str]], Document | None] | None:
        row.sort(key=lambda item: item[2][0])
        documents = [item[1] for item in row]
        texts = [self._normalized_layout_text(document) for document in documents]
        header_cells = [
            ((box[0] + box[2]) / 2, text)
            for (_, _, box), text in zip(row, texts)
            if _PLAN_HEADER_PATTERN.fullmatch(text)
        ]
        if len(header_cells) >= 2:
            return header_cells, None
        if len(documents) < 2 or not self._shares_layout_relationship(documents):
            return None
        if not plan_headers and not any(any(character.isdigit() for character in text) for text in texts):
            return None
        aggregate_text = self._format_layout_row(row, texts, plan_headers)
        normalized = " ".join(aggregate_text.lower().split())
        if not aggregate_text or normalized in seen_text:
            return None
        seen_text.add(normalized)
        return [], self._layout_row_document(documents, aggregate_text, plan_headers)

    def _format_layout_row(
        self,
        row: list[tuple[int, Document, tuple[float, float, float, float]]],
        texts: list[str],
        plan_headers: list[tuple[float, str]],
    ) -> str:
        """Attach table values to headers only when every plan column aligns."""
        if not plan_headers:
            return " | ".join(texts)

        centers = [(box[0] + box[2]) / 2 for _, _, box in row]
        matches: dict[str, str] = {}
        matched_indices: set[int] = set()
        for header_center, header in plan_headers:
            candidates = [
                (abs(center - header_center), index)
                for index, center in enumerate(centers)
            ]
            distance, index = min(candidates)
            if distance > _COLUMN_ALIGNMENT_TOLERANCE or index in matched_indices:
                return " | ".join(texts)
            matched_indices.add(index)
            matches[header] = texts[index]

        label_parts = [
            text for index, text in enumerate(texts) if index not in matched_indices
        ]
        if not label_parts:
            return " | ".join(texts)
        return " | ".join(
            [" ".join(label_parts)]
            + [f"{header}: {matches[header]}" for _, header in plan_headers]
        )

    def _layout_row_document(
        self,
        documents: list[Document],
        text: str,
        plan_headers: list[tuple[float, str]],
    ) -> Document:
        """Create one aggregate while retaining citation-safe source provenance."""
        metadata = dict(documents[0].metadata)
        metadata.update(
            {
                "chunk_kind": LAYOUT_ROW_KIND,
                "element_type": LAYOUT_ROW_KIND,
                "source_element_ids": ",".join(
                    str(document.metadata["element_id"])
                    for document in documents
                    if document.metadata.get("element_id")
                ),
                "source_parent_ids": ",".join(
                    sorted(
                        {
                            str(document.metadata["parent_id"])
                            for document in documents
                            if document.metadata.get("parent_id")
                        }
                    )
                ),
                "source_categories": ",".join(
                    sorted(
                        {
                            str(document.metadata["category"])
                            for document in documents
                            if document.metadata.get("category")
                        }
                    )
                ),
            }
        )
        if plan_headers:
            metadata["layout_column_headers"] = ",".join(
                header for _, header in plan_headers
            )
        return Document(page_content=text, metadata=metadata)

    def _prepare_chunks_with_metadata(
        self,
        chunks: list[Document],
        user_id: str,
        filename: str,
        doc_language: str | None,
        document_metadata: dict[str, Any] | None = None,
    ) -> list[Document]:
        """
        Add metadata to chunks including user_id, language, chapter tracking, and timestamp.

        Args:
            chunks: Chunked documents
            user_id: User identifier for multi-tenancy
            filename: Original filename
            doc_language: Document language (None = auto-detect)
            document_metadata: Internal metadata applied to every chunk.

        Returns:
            Chunks with complete metadata
        """
        final_chunks: list[Document] = []
        current_chapter = "Document Start"
        uploaded_at = int(time.time() * 1000)  # Milliseconds timestamp
        detected_language = doc_language.lower() if doc_language else "en"

        for chunk in chunks:
            # Track hierarchical structure from document elements
            element_type = chunk.metadata.get("type", "NarrativeText")

            # Update chapter tracking when encountering titles or headers
            if "Title" in element_type or "Header" in element_type:
                current_chapter = chunk.page_content.strip()
                chunk.metadata["element_type"] = element_type

            # Add structural, language, and user metadata to every chunk
            chunk.metadata["chapter_title"] = current_chapter
            chunk.metadata["source"] = user_id
            chunk.metadata["original_filename"] = filename
            chunk.metadata["original_language_code"] = detected_language
            chunk.metadata["uploaded_at"] = uploaded_at
            if document_metadata:
                chunk.metadata.update(document_metadata)

            final_chunks.append(chunk)

        return final_chunks

    def _batch_index_chunks(self, chunks: list[Document]) -> int:
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
        optimized_batch_size = 500
        total_batches = (len(chunks) + optimized_batch_size - 1) // optimized_batch_size

        logger.info(
            f"📊 Starting embedding generation for {len(chunks)} chunks in {total_batches} batches"
        )

        # Process in batches for better progress visibility
        for batch_idx, i in enumerate(range(0, len(chunks), optimized_batch_size), 1):
            batch = chunks[i : i + optimized_batch_size]
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
        self, file: UploadedFilePort
    ) -> tuple[str, float]:
        """
        Detect language from PDF preview without full indexing.

        Used for pre-upload language confirmation UI.

        Args:
            file: The uploaded PDF file

        Returns:
            Tuple of (language_code, confidence_score)
        """
        # Create a secure temporary file with PDF suffix
        # This prevents path injection attacks by not using user-controlled filename
        temp_fd, temp_file_path = tempfile.mkstemp(suffix=".pdf", prefix="preview_")

        try:
            content = await file.read()
            if not content:
                raise ValueError("The uploaded file is empty.")

            # Close the descriptor before passing the file to the loader. The
            # blocking write runs outside the application event loop.
            descriptor = temp_fd
            temp_fd = -1
            await asyncio.to_thread(_write_temporary_pdf, descriptor, content)

            documents = await self._load_pdf_documents_with_timeout(
                temp_file_path, MAX_DOCUMENT_PAGES
            )
            return await asyncio.to_thread(
                self._detect_document_language_from_documents, documents
            )

        except Exception as exc:
            logger.error(
                "Document language detection failed | Type: {}", type(exc).__name__
            )
            raise
        finally:
            if temp_fd != -1:
                os.close(temp_fd)
            # Clean up the secure temporary file
            # temp_file_path is from tempfile.mkstemp(), already an absolute path
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def _detect_document_language_from_documents(
        self, documents: list[Document]
    ) -> tuple[str, float]:
        """Detect language from the bounded parser result without blocking the event loop."""
        preview_text = " ".join([doc.page_content for doc in documents[:3]])[:2000]
        if len(preview_text) < 50:
            logger.warning("⚠️ Not enough text for language detection")
            return "EN", 0.5
        detected_lang = self.language_service.detect_language(preview_text)
        confidence = 0.9
        logger.info(
            f"🌍 Preview language detected: {detected_lang} (confidence: {confidence:.2f})"
        )
        return detected_lang.upper(), confidence
