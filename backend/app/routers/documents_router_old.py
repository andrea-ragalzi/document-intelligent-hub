"""
Documents Router - Document Management Endpoints

Handles document operations:
- Upload PDF documents
- Detect document language
- List user documents
- Delete documents (single/all)
- Check document status
"""

from app.config.security_constants import MAX_DOCUMENT_UPLOAD_SIZE, FILE_READ_CHUNK_SIZE
from app.core.auth import verify_firebase_token
from app.core.logging import logger
from app.core.security import sanitize_filename, get_safe_file_size_mb
from app.schemas.rag_schema import (
    DetectLanguageResponse,
    DocumentDeleteResponse,
    DocumentListResponse,
    UploadResponse,
)
from app.services.rag_orchestrator_service import RAGService, get_rag_service
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from io import BytesIO

router = APIRouter(prefix="/rag", tags=["documents"])


@router.post("/upload/", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="The PDF document to be indexed."),
    user_id: str = Form(
        ..., description="User ID (required for multi-tenancy isolation)"
    ),
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    **Upload and index a PDF document.**

    - Validates file type (PDF only)
    - Extracts text and metadata
    - Detects document language
    - Chunks content intelligently
    - Generates embeddings (local HuggingFace model)
    - Stores in ChromaDB with user_id isolation

    **Multi-tenancy:** Each document is tagged with `user_id` for data isolation.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )

    # Index document via service layer
    try:
        # Reset file pointer for service to read
        await file.seek(0)
        chunks_indexed, detected_language = await rag_service.index_document(
            file=file, user_id=user_id, document_language=None
        )
        return UploadResponse(
            message=f"Document '{file.filename}' indexed successfully",
            status="success",
            chunks_indexed=chunks_indexed,
            detected_language=detected_language or "Unknown",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Indexing error for file {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {str(e)}",
        )


@router.post("/detect-language/", response_model=DetectLanguageResponse)
async def detect_document_language(
    file: UploadFile = File(..., description="The PDF document to analyze."),
    user_id: str = Form(
        ..., description="User ID (for potential future tracking)"
    ),
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    **Detect the language of a PDF document (preview before upload).**

    - Reads PDF content
    - Detects language using `langdetect`
    - Returns language code and confidence

    **Use case:** Frontend can show detected language before user uploads.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )

    # Detect language via service
    try:
        # Reset file pointer for service to read
        await file.seek(0)
        language_code, confidence = await rag_service.detect_document_language_preview(
            file=file
        )
        
        return DetectLanguageResponse(
            detected_language=language_code,
            confidence=confidence,
            filename=file.filename,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Language detection failed: {str(e)}",
        )


@router.get("/documents/check")
async def check_documents(
    user_id: str,
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    **Check if user has any documents uploaded.**

    Returns `has_documents` boolean and document count.
    """
    try:
        count = rag_service.get_user_document_count(user_id)
        return {"has_documents": count > 0, "document_count": count}
    except Exception as e:
        logger.error(f"❌ Error checking document status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check document status: {str(e)}",
        )


@router.get("/documents/list", response_model=DocumentListResponse)
async def list_documents(
    user_id: str,
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    **List all documents uploaded by a user.**

    - Returns filename, language, chunk count, upload timestamp
    - Filtered by `user_id` for multi-tenancy
    """
    try:
        documents = rag_service.get_user_documents(user_id)
        return DocumentListResponse(
            documents=documents,
            total_count=len(documents),
            user_id=user_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}",
        )


@router.delete("/documents/delete", response_model=DocumentDeleteResponse)
async def delete_document(
    user_id: str,
    filename: str,
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    **Delete a specific document by filename.**

    - Removes all chunks associated with the document
    - Filtered by `user_id` to prevent cross-tenant deletion
    """
    try:
        deleted_count = rag_service.delete_user_document(
            user_id=user_id, filename=filename
        )
        if deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{filename}' not found for user {user_id}",
            )
        return DocumentDeleteResponse(
            message=f"Document '{filename}' deleted successfully",
            filename=filename,
            chunks_deleted=deleted_count,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}",
        )


@router.delete("/documents/delete-all")
async def delete_all_documents(
    user_id: str,
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    **Delete ALL documents for a user.**

    - Removes all chunks for the user
    - ⚠️ **DANGEROUS:** No undo!
    """
    try:
        deleted_count = rag_service.delete_all_user_documents(user_id)
        if deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No documents found for user {user_id}",
            )
        return {
            "message": f"All documents deleted successfully for user {user_id}",
            "chunks_deleted": deleted_count,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete documents: {str(e)}",
        )
