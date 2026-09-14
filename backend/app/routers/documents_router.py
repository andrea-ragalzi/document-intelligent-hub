"""
Documents Router - Document Management Endpoints (Security Hardened)

Handles document operations with security enhancements:
- Firebase Auth token verification on all endpoints
- File size validation (50MB limit)
- Filename sanitization (path traversal protection)
- Audit logging for deletions
- Input validation

All endpoints require valid Firebase Auth token in Authorization header.
"""

import asyncio
import os
from io import BytesIO
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from firebase_admin import firestore

from app.config.security_constants import FILE_READ_CHUNK_SIZE
from app.core.auth import require_verified_email, verify_firebase_token
from app.core.logging import logger
from app.core.security import (
    get_safe_file_size_mb,
    sanitize_filename,
)
from app.dependencies import get_document_file_storage, get_rag_service
from app.ports.file_storage import FileStoragePort
from app.schemas.rag_schema import (
    DetectLanguageResponse,
    DemoDocumentSeedResponse,
    DocumentDeleteResponse,
    DocumentListResponse,
    UploadResponse,
)
from app.services.demo_document_service import (
    DEMO_DOCUMENT_FILENAME,
    DEMO_SUGGESTED_QUESTIONS,
    DemoDocumentService,
)
from app.services.rag_orchestrator_service import RAGService
from app.services.query_concurrency_limiter import QueryConcurrencyLimiter, global_expensive_operation_limiter
from app.services.tier_limit_service import (
    check_file_count_limit,
    get_max_upload_size_bytes,
    get_user_tier_limits,
)
router = APIRouter(prefix="/rag", tags=["documents"])

# One costly PDF operation at a time per authenticated UID.  This is an
# intentional in-process guard for the current single-replica public demo.
upload_concurrency_limiter = QueryConcurrencyLimiter()
language_preview_concurrency_limiter = QueryConcurrencyLimiter()
MAX_RENAMED_FILENAME_ATTEMPTS = 1_000


def _delete_user_firestore_data(user_id: str, db: Any) -> int:
    """Delete Firestore records owned by a user and return conversation count.

    Batches are deliberately kept below Firestore's batch-operation ceiling. A
    rerun is safe after a partial failure because deleting an already-deleted
    document is a no-op.
    """
    conversation_count = 0
    batch = db.batch()
    batch_size = 0

    conversations = db.collection("conversations").where("userId", "==", user_id)
    for conversation in conversations.stream():
        batch.delete(conversation.reference)
        conversation_count += 1
        batch_size += 1
        if batch_size == 400:
            batch.commit()
            batch = db.batch()
            batch_size = 0

    batch.delete(db.collection("user_usage").document(user_id))
    batch.commit()
    return conversation_count


def _log_document_failure(operation: str, error: Exception) -> None:
    """Record operational diagnostics without retaining user or SDK details."""
    logger.error("Document {} failed | Type: {}", operation, type(error).__name__)


def _validate_and_sanitize_filename(filename: str | None) -> str:
    """
    Validate and sanitize uploaded filename.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename

    Raises:
        HTTPException: If filename is missing or not a PDF
    """
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required.",
        )

    safe_filename = sanitize_filename(filename)

    if not safe_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )

    return safe_filename


def _get_next_available_filename(
    user_id: str, filename: str, rag_service: RAGService
) -> str:
    """Return a server-chosen PDF name that does not collide for this user."""
    stem, extension = os.path.splitext(filename)
    for suffix in range(1, MAX_RENAMED_FILENAME_ATTEMPTS + 1):
        candidate = f"{stem} ({suffix}){extension}"
        if not rag_service.user_document_exists(user_id, candidate):
            return candidate
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Unable to create a unique filename. Please rename the file and try again.",
    )


def _resolve_duplicate_filename(
    user_id: str,
    filename: str,
    duplicate_action: Literal["reject", "replace", "rename"],
    rag_service: RAGService,
) -> tuple[str, bool]:
    """Resolve a duplicate according to the explicit server-validated action."""
    document_exists = rag_service.user_document_exists(user_id, filename)
    if not document_exists:
        return filename, False
    if duplicate_action == "reject":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A document with this name already exists. Choose replace, rename, or skip it.",
        )
    if duplicate_action == "rename":
        return _get_next_available_filename(user_id, filename, rag_service), False
    return filename, True


async def _get_upload_size_limits(
    user_id: str, rag_service: RAGService, is_replacing: bool
) -> tuple[int, float]:
    """Keep a replacement within its size limit without charging another file slot."""
    if is_replacing:
        max_size_bytes = get_max_upload_size_bytes(user_id)
        return max_size_bytes, get_safe_file_size_mb(max_size_bytes)
    return await asyncio.to_thread(_check_file_limits, user_id, rag_service)


def _delete_replaced_document(
    user_id: str, filename: str, rag_service: RAGService, is_replacing: bool
) -> None:
    """Remove the owned chunks only after a replacement was explicitly requested."""
    if not is_replacing:
        return
    deleted_count = rag_service.delete_user_document(user_id, filename)
    if deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The document changed before it could be replaced. Refresh and try again.",
        )


def _cleanup_failed_document(
    user_id: str,
    filename: str,
    rag_service: RAGService,
    document_storage: FileStoragePort,
) -> None:
    """Best-effort compensating cleanup for a failed index operation."""
    try:
        rag_service.delete_user_document(user_id, filename)
    except Exception as exc:  # pragma: no cover - preserves the original failure
        _log_document_failure("failed-index vector cleanup", exc)
    try:
        document_storage.delete(user_id, filename)
    except Exception as exc:  # pragma: no cover - preserves the original failure
        _log_document_failure("failed-index original cleanup", exc)


def _read_existing_original(
    user_id: str, filename: str, document_storage: FileStoragePort
) -> bytes | None:
    """Read an existing original before replacement makes destructive changes."""
    existing_original = document_storage.get(user_id, filename)
    if existing_original is None:
        return None

    storage_root = os.path.realpath(document_storage.root_path)
    safe_existing_path = os.path.realpath(existing_original)
    if not safe_existing_path.startswith(f"{storage_root}{os.sep}"):
        raise ValueError("Invalid document storage path")

    with open(safe_existing_path, "rb") as original_file:  # noqa: PTH123
        return original_file.read()


async def _restore_replaced_document(
    user_id: str,
    filename: str,
    original_content: bytes | None,
    rag_service: RAGService,
    document_storage: FileStoragePort,
) -> None:
    """Restore the prior replace target after a new version fails to index."""
    _cleanup_failed_document(user_id, filename, rag_service, document_storage)
    if original_content is None:
        return
    document_storage.store(user_id, filename, original_content)
    previous_file = UploadFile(file=BytesIO(original_content), filename=filename)
    try:
        await rag_service.index_document(
            file=previous_file, user_id=user_id, document_language=None
        )
    except Exception:
        _cleanup_failed_document(user_id, filename, rag_service, document_storage)
        raise


def _check_file_limits(user_id: str, rag_service: RAGService) -> tuple[int, float]:
    """
    Check if user has reached file count limit.

    Args:
        user_id: Firebase user ID
        rag_service: RAG service instance

    Returns:
        Tuple of (max_upload_size_bytes, max_upload_size_mb)

    Raises:
        HTTPException: If file count limit is reached
    """
    # The bundled starter PDF is private per user but does not consume the
    # user's personal-upload allowance.
    current_file_count = rag_service.get_user_document_count(
        user_id, include_demo=False
    )
    can_upload, max_files = check_file_count_limit(user_id, current_file_count)

    if not can_upload:
        logger.warning("File limit reached | Files: {}/{}", current_file_count, max_files)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Maximum file limit reached ({current_file_count}/{max_files}). "
                f"Please delete some documents or upgrade your plan."
            ),
        )

    max_upload_size_bytes = get_max_upload_size_bytes(user_id)
    max_upload_size_mb = get_safe_file_size_mb(max_upload_size_bytes)

    return max_upload_size_bytes, max_upload_size_mb


async def _read_and_validate_file_size(
    file: UploadFile, max_size_bytes: int, max_size_mb: float, user_id: str
) -> bytes:
    """
    Read file in chunks and validate size limit.

    Args:
        file: Uploaded file
        max_size_bytes: Maximum file size in bytes
        max_size_mb: Maximum file size in MB (for error message)
        user_id: Firebase user ID

    Returns:
        Complete file content as bytes

    Raises:
        HTTPException: If file size exceeds limit or read error
    """
    file_size = 0
    file_chunks = []

    try:
        while chunk := await file.read(FILE_READ_CHUNK_SIZE):
            file_size += len(chunk)

            if file_size > max_size_bytes:
                size_mb = get_safe_file_size_mb(file_size)
                logger.warning(
                    "Document upload exceeded size limit | Size: {}MB | Limit: {}MB",
                    size_mb,
                    max_size_mb,
                )
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail=(
                        f"File too large. Your plan allows maximum {max_size_mb}MB, "
                        f"got {size_mb}MB"
                    ),
                )

            file_chunks.append(chunk)

        return b"".join(file_chunks)

    except HTTPException:
        raise
    except Exception as exc:
        _log_document_failure("file read", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to read the uploaded file. Please try again.",
        ) from exc


@router.post("/documents/seed-demo", response_model=DemoDocumentSeedResponse)
async def seed_demo_document(
    user_id: str = Depends(require_verified_email),
    rag_service: RAGService = Depends(get_rag_service),
    document_storage: FileStoragePort = Depends(get_document_file_storage),
) -> DemoDocumentSeedResponse:
    """Index the bundled Alice excerpt privately for the verified Firebase UID."""
    global_admitted = await global_expensive_operation_limiter.acquire()
    if not global_admitted:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="The public demo is currently at capacity. Please try again in a few minutes.",
            headers={"Retry-After": "120"},
        )
    try:
        result = await DemoDocumentService(
            rag_service, document_storage
        ).seed_for_user(user_id)
        return DemoDocumentSeedResponse(
            status=result.status,
            message=(
                "Demo document ready."
                if result.status == "ready"
                else "Demo document indexed successfully."
            ),
            filename=DEMO_DOCUMENT_FILENAME,
            chunks_indexed=result.chunks_indexed,
            suggested_questions=DEMO_SUGGESTED_QUESTIONS,
        )
    except Exception as exc:
        _log_document_failure("demo seeding", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Demo document could not be prepared. You can still upload your own PDF.",
        ) from exc
    finally:
        await global_expensive_operation_limiter.release()


@router.post(
    "/upload/", response_model=UploadResponse, status_code=status.HTTP_201_CREATED
)
async def upload_document(
    _request: Request,
    file: UploadFile = File(..., description="The PDF document to be indexed."),
    user_id: str = Depends(require_verified_email),
    rag_service: RAGService = Depends(get_rag_service),
    document_storage: FileStoragePort = Depends(get_document_file_storage),
    duplicate_action: Annotated[
        Literal["reject", "replace", "rename"], Form()
    ] = "reject",
) -> UploadResponse:
    """
    **Upload and index a PDF document.**

    **🔒 Security Features:**
    - Requires valid Firebase Auth token
    - Tier-based file size limit
    - Tier-based file count limit
    - Filename sanitization (prevents path traversal)
    - PDF-only validation

    **Multi-tenancy:** Each document is tagged with verified `user_id` from Auth token.
    **Tier Limits:** Automatically enforced based on user's Firebase custom claims.
    """
    tier, _ = await asyncio.to_thread(get_user_tier_limits, user_id)
    global_admitted = tier == "UNLIMITED"
    if not global_admitted:
        # Indexing can take long enough that an immediate rejection is needlessly
        # frustrating when another costly operation is just about to finish.
        global_admitted = await global_expensive_operation_limiter.acquire_with_timeout(30)
        if not global_admitted:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="The indexing service is busy. Please try again in 30 seconds.",
                headers={"Retry-After": "30"},
            )
    admitted = await upload_concurrency_limiter.acquire(user_id)
    if not admitted:
        if tier != "UNLIMITED":
            await global_expensive_operation_limiter.release()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="A document upload is already running for this account. Please wait for it to finish.",
            headers={"Retry-After": "5"},
        )
    try:
        # Keep the admission lock through count check and indexing.  This makes
        # the existing document-count rule race-free for a single UID.
        safe_filename = _validate_and_sanitize_filename(file.filename)
        safe_filename, is_replacing = _resolve_duplicate_filename(
            user_id, safe_filename, duplicate_action, rag_service
        )
        max_size_bytes, max_size_mb = await _get_upload_size_limits(
            user_id, rag_service, is_replacing
        )

        file_content = await _read_and_validate_file_size(
            file, max_size_bytes, max_size_mb, user_id
        )

        previous_original = (
            _read_existing_original(user_id, safe_filename, document_storage)
            if is_replacing
            else None
        )
        _delete_replaced_document(user_id, safe_filename, rag_service, is_replacing)
        try:
            document_storage.store(user_id, safe_filename, file_content)
            safe_file = UploadFile(
                file=BytesIO(file_content), filename=safe_filename
            )
            chunks_indexed, detected_language = await rag_service.index_document(
                file=safe_file, user_id=user_id, document_language=None
            )
        except Exception:
            if is_replacing:
                await _restore_replaced_document(
                    user_id,
                    safe_filename,
                    previous_original,
                    rag_service,
                    document_storage,
                )
            else:
                _cleanup_failed_document(
                    user_id, safe_filename, rag_service, document_storage
                )
            raise

        logger.info("Document indexed | Chunks: {}", chunks_indexed)

        return UploadResponse(
            message=f"Document '{safe_filename}' indexed successfully",
            filename=safe_filename,
            status="success",
            chunks_indexed=chunks_indexed,
            detected_language=detected_language or "Unknown",
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document upload."
        ) from exc
    except Exception as exc:
        _log_document_failure("indexing", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to index the document. Please try again.",
        ) from exc
    finally:
        await upload_concurrency_limiter.release(user_id)
        if tier != "UNLIMITED":
            await global_expensive_operation_limiter.release()


@router.post("/detect-language/", response_model=DetectLanguageResponse)
async def detect_document_language(
    file: UploadFile = File(..., description="The PDF document to analyze."),
    user_id: str = Depends(require_verified_email),
    rag_service: RAGService = Depends(get_rag_service),
) -> DetectLanguageResponse:
    """
    **Detect the language of a PDF document (preview before upload).**

    **🔒 Security:** Requires valid Firebase Auth token
    """
    global_admitted = await global_expensive_operation_limiter.acquire()
    if not global_admitted:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="The public demo is currently at capacity. Please try again in a few minutes.",
            headers={"Retry-After": "120"},
        )
    admitted = await language_preview_concurrency_limiter.acquire(user_id)
    if not admitted:
        await global_expensive_operation_limiter.release()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="A document preview is already running for this account. Please wait for it to finish.",
            headers={"Retry-After": "5"},
        )
    try:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required.",
            )

        safe_filename = sanitize_filename(file.filename)
        if not safe_filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported.",
            )

        max_size_bytes = await asyncio.to_thread(get_max_upload_size_bytes, user_id)
        max_size_mb = get_safe_file_size_mb(max_size_bytes)
        file_content = await _read_and_validate_file_size(
            file, max_size_bytes, max_size_mb, user_id
        )
        preview_file = UploadFile(file=BytesIO(file_content), filename=safe_filename)
        language_code, confidence = await rag_service.detect_document_language_preview(
            file=preview_file
        )

        return DetectLanguageResponse(
            detected_language=language_code,
            confidence=confidence,
            filename=safe_filename,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _log_document_failure("language preview", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to detect the document language. Please try again.",
        ) from exc
    finally:
        await language_preview_concurrency_limiter.release(user_id)
        await global_expensive_operation_limiter.release()


@router.get("/documents/check")
async def check_documents(
    user_id: str = Depends(verify_firebase_token),
    rag_service: RAGService = Depends(get_rag_service),
) -> dict[str, Any]:
    """
    **Check if user has any documents uploaded.**

    **🔒 Security:** Requires valid Firebase Auth token
    """
    try:
        count = rag_service.get_user_document_count(user_id)
        return {"has_documents": count > 0, "document_count": count}
    except Exception as exc:
        _log_document_failure("status check", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to check document status. Please try again.",
        ) from exc


@router.get("/documents/list", response_model=DocumentListResponse)
async def list_documents(
    user_id: str = Depends(verify_firebase_token),
    rag_service: RAGService = Depends(get_rag_service),
    document_storage: FileStoragePort = Depends(get_document_file_storage),
) -> DocumentListResponse:
    """
    **List all documents uploaded by a user.**

    **🔒 Security:** Requires valid Firebase Auth token. Multi-tenancy enforced.
    """
    try:
        documents = [
            document.model_copy(
                update={
                    "original_available": document_storage.get(user_id, document.filename)
                    is not None
                }
            )
            for document in rag_service.get_user_documents(user_id)
        ]
        return DocumentListResponse(
            documents=documents, total_count=len(documents), user_id=user_id
        )
    except Exception as exc:
        _log_document_failure("listing", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve documents. Please try again.",
        ) from exc


@router.delete("/documents/delete", response_model=DocumentDeleteResponse)
async def delete_document(
    filename: str,
    user_id: str = Depends(verify_firebase_token),
    rag_service: RAGService = Depends(get_rag_service),
    document_storage: FileStoragePort = Depends(get_document_file_storage),
) -> DocumentDeleteResponse:
    """
    **Delete a specific document by filename.**

    **🔒 Security:**
    - Requires valid Firebase Auth token
    - Multi-tenancy: Can only delete own documents
    - Audit logging for forensics
    """
    logger.bind(AUDIT=True).warning("Document deletion requested")

    try:
        # Delete the original first.  If that operation fails, indexed chunks
        # remain available for a safe retry instead of leaving an orphan file.
        original_deleted = document_storage.delete(user_id, filename)
        deleted_count = rag_service.delete_user_document(
            user_id=user_id, filename=filename
        )
        if not original_deleted and deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )

        # Audit log AFTER successful deletion
        logger.bind(AUDIT=True).warning("Document deleted | Chunks: {}", deleted_count)

        return DocumentDeleteResponse(
            message=f"Document '{filename}' deleted successfully",
            filename=filename,
            chunks_deleted=deleted_count,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _log_document_failure("deletion", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete the document. Please try again.",
        ) from exc


@router.get("/documents/content")
async def get_document_content(
    filename: str,
    download: bool = False,
    user_id: str = Depends(verify_firebase_token),
    rag_service: RAGService = Depends(get_rag_service),
    document_storage: FileStoragePort = Depends(get_document_file_storage),
) -> FileResponse:
    """Return an authenticated user's original PDF for preview or download."""
    owned_document = next(
        (
            document
            for document in rag_service.get_user_documents(user_id)
            if document.filename == filename
        ),
        None,
    )
    if owned_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    original_file = document_storage.get(user_id, owned_document.filename)
    if original_file is None:
        # Documents indexed before original-file storage was introduced remain
        # usable for RAG but cannot be reconstructed from ChromaDB chunks.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The original file is unavailable for this document.",
        )

    storage_root = os.path.realpath(document_storage.root_path)
    safe_file_path = os.path.realpath(original_file)
    if not safe_file_path.startswith(f"{storage_root}{os.sep}"):
        logger.warning("Blocked original document outside storage root")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return FileResponse(
        path=safe_file_path,
        media_type="application/pdf",
        filename=owned_document.filename,
        content_disposition_type="attachment" if download else "inline",
    )


@router.delete("/documents/delete-all")
async def delete_all_documents(
    user_id: str = Depends(verify_firebase_token),
    rag_service: RAGService = Depends(get_rag_service),
    document_storage: FileStoragePort = Depends(get_document_file_storage),
) -> dict[str, Any]:
    """
    **Delete ALL documents for a user.**

    **⚠️ DANGEROUS:** No undo!
    **🔒 Security:**
    - Requires valid Firebase Auth token
    - Audit logging for forensics
    """
    logger.bind(AUDIT=True).warning("Bulk document deletion requested")

    try:
        # Both resources may already be absent, or one may have been created
        # by an older version.  The operation is intentionally idempotent.
        document_storage.delete_all(user_id)
        deleted_count = rag_service.delete_all_user_documents(user_id)

        # Audit log AFTER successful deletion
        logger.bind(AUDIT=True).warning(
            "Bulk document deletion completed | Chunks: {}", deleted_count
        )

        return {
            "message": "All documents deleted successfully.",
            "chunks_deleted": deleted_count,
        }
    except HTTPException:
        raise
    except Exception as exc:
        _log_document_failure("bulk deletion", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete documents. Please try again.",
        ) from exc


@router.delete("/account/data")
async def delete_account_data(
    user_id: str = Depends(require_verified_email),
    rag_service: RAGService = Depends(get_rag_service),
    document_storage: FileStoragePort = Depends(get_document_file_storage),
) -> dict[str, int | str]:
    """Delete all server-side data owned by the authenticated account.

    This operation intentionally does not delete the Firebase Auth account.
    The browser performs that final irreversible action only after this
    endpoint has completed. Each deletion is idempotent so a retry after a
    partial infrastructure failure can finish cleanup safely.
    """
    logger.bind(AUDIT=True).warning("Account data deletion requested")
    try:
        chunks_deleted = rag_service.delete_all_user_documents(user_id)
        document_storage.delete_all(user_id)
        conversations_deleted = _delete_user_firestore_data(user_id, firestore.client())
        logger.bind(AUDIT=True).warning(
            "Account data deletion completed | Chunks: {} | Conversations: {}",
            chunks_deleted,
            conversations_deleted,
        )
        return {
            "message": "Account data deleted successfully.",
            "chunks_deleted": chunks_deleted,
            "conversations_deleted": conversations_deleted,
        }
    except Exception as exc:  # pylint: disable=broad-exception-caught
        _log_document_failure("account data deletion", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete account data. Please try again.",
        ) from exc
