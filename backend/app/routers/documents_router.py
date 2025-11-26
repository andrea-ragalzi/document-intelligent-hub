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

from io import BytesIO

from app.config.security_constants import FILE_READ_CHUNK_SIZE
from app.core.auth import verify_firebase_token
from app.core.logging import logger
from app.core.security import get_safe_file_size_mb, sanitize_filename
from app.schemas.rag_schema import (
    DetectLanguageResponse,
    DocumentDeleteResponse,
    DocumentListResponse,
    UploadResponse,
)
from app.services.rag_orchestrator_service import RAGService, get_rag_service
from app.services.tier_limit_service import (
    check_file_count_limit,
    get_max_upload_size_bytes,
)
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

router = APIRouter(prefix="/rag", tags=["documents"])


@router.post("/upload/", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: UploadFile = File(..., description="The PDF document to be indexed."),
    user_id: str = Depends(verify_firebase_token),
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    **Upload and index a PDF document.**

    **🔒 Security Features:**
    - Requires valid Firebase Auth token
    - Tier-based file size limit (FREE: 10MB, PRO: 50MB, UNLIMITED: 9999MB)
    - Tier-based file count limit
    - Filename sanitization (prevents path traversal)
    - PDF-only validation

    **Multi-tenancy:** Each document is tagged with verified `user_id` from Auth token.
    **Tier Limits:** Automatically enforced based on user's Firebase custom claims.
    """
    # Get user's tier-based limits
    max_upload_size_bytes = await get_max_upload_size_bytes(user_id)
    max_upload_size_mb = get_safe_file_size_mb(max_upload_size_bytes)
    
    # Check file count limit
    current_file_count = rag_service.get_user_document_count(user_id)
    can_upload, max_files = await check_file_count_limit(user_id, current_file_count)
    
    if not can_upload:
        logger.warning(f"⚠️ File limit reached | User: {user_id} | Files: {current_file_count}/{max_files}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Maximum file limit reached ({current_file_count}/{max_files}). Please delete some documents or upgrade your plan."
        )
    
    # Sanitize filename for security (prevent path traversal)
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required.",
        )
    
    safe_filename = sanitize_filename(file.filename)
    
    # Validate file type
    if not safe_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )
    
    # Validate file size (streaming to avoid loading entire file in memory)
    file_size = 0
    file_chunks = []
    
    try:
        while chunk := await file.read(FILE_READ_CHUNK_SIZE):
            file_size += len(chunk)
            
            # Check size limit (tier-based)
            if file_size > max_upload_size_bytes:
                size_mb = get_safe_file_size_mb(file_size)
                logger.warning(f"⚠️ File too large | User: {user_id} | Size: {size_mb}MB | Limit: {max_upload_size_mb}MB")
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large. Your plan allows maximum {max_upload_size_mb}MB, got {size_mb}MB"
                )
            
            file_chunks.append(chunk)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error reading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read file: {str(e)}",
        )
    
    # Reconstruct file from chunks
    file_content = b"".join(file_chunks)
    reconstructed_file = BytesIO(file_content)
    
    # Create new UploadFile with sanitized filename
    safe_file = UploadFile(
        file=reconstructed_file,
        filename=safe_filename,
    )

    # Index document via service layer
    try:
        chunks_indexed, detected_language = await rag_service.index_document(
            file=safe_file, user_id=user_id, document_language=None
        )
        
        logger.info(f"✅ Document indexed | User: {user_id} | File: {safe_filename} | Chunks: {chunks_indexed}")
        
        return UploadResponse(
            message=f"Document '{safe_filename}' indexed successfully",
            status="success",
            chunks_indexed=chunks_indexed,
            detected_language=detected_language or "Unknown",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Indexing error for file {safe_filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {str(e)}",
        )


@router.post("/detect-language/", response_model=DetectLanguageResponse)
async def detect_document_language(
    file: UploadFile = File(..., description="The PDF document to analyze."),
    user_id: str = Depends(verify_firebase_token),
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    **Detect the language of a PDF document (preview before upload).**

    **🔒 Security:** Requires valid Firebase Auth token
    """
    # Sanitize filename
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required.",
        )
    
    safe_filename = sanitize_filename(file.filename)
    
    # Validate file type
    if not safe_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )

    # Detect language via service
    try:
        await file.seek(0)
        language_code, confidence = await rag_service.detect_document_language_preview(
            file=file
        )
        
        return DetectLanguageResponse(
            detected_language=language_code,
            confidence=confidence,
            filename=safe_filename,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Language detection failed: {str(e)}",
        )


@router.get("/documents/check")
async def check_documents(
    user_id: str = Depends(verify_firebase_token),
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    **Check if user has any documents uploaded.**

    **🔒 Security:** Requires valid Firebase Auth token
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
    user_id: str = Depends(verify_firebase_token),
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    **List all documents uploaded by a user.**

    **🔒 Security:** Requires valid Firebase Auth token. Multi-tenancy enforced.
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
    request: Request,
    filename: str,
    user_id: str = Depends(verify_firebase_token),
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    **Delete a specific document by filename.**

    **🔒 Security:** 
    - Requires valid Firebase Auth token
    - Multi-tenancy: Can only delete own documents
    - Audit logging for forensics
    """
    # Audit log BEFORE deletion
    client_ip = request.client.host if request.client else "unknown"
    logger.bind(AUDIT=True).warning(
        f"🗑️ DELETE REQUEST | User: {user_id} | File: {filename} | IP: {client_ip}"
    )
    
    try:
        deleted_count = rag_service.delete_user_document(
            user_id=user_id, filename=filename
        )
        
        if deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{filename}' not found for user {user_id}",
            )
        
        # Audit log AFTER successful deletion
        logger.bind(AUDIT=True).warning(
            f"✅ DELETED | User: {user_id} | File: {filename} | Chunks: {deleted_count}"
        )
        
        return DocumentDeleteResponse(
            message=f"Document '{filename}' deleted successfully",
            filename=filename,
            chunks_deleted=deleted_count,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete failed | User: {user_id} | File: {filename} | Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}",
        )


@router.delete("/documents/delete-all")
async def delete_all_documents(
    request: Request,
    user_id: str = Depends(verify_firebase_token),
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    **Delete ALL documents for a user.**

    **⚠️ DANGEROUS:** No undo! 
    **🔒 Security:** 
    - Requires valid Firebase Auth token
    - Audit logging for forensics
    """
    # Audit log BEFORE deletion
    client_ip = request.client.host if request.client else "unknown"
    logger.bind(AUDIT=True).error(
        f"🚨 BULK DELETE REQUEST | User: {user_id} | IP: {client_ip}"
    )
    
    try:
        deleted_count = rag_service.delete_all_user_documents(user_id)
        
        if deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No documents found for user {user_id}",
            )
        
        # Audit log AFTER successful deletion
        logger.bind(AUDIT=True).error(
            f"✅ BULK DELETED | User: {user_id} | Chunks: {deleted_count}"
        )
        
        return {
            "message": f"All documents deleted successfully for user {user_id}",
            "chunks_deleted": deleted_count,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Bulk delete failed | User: {user_id} | Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete documents: {str(e)}",
        )
