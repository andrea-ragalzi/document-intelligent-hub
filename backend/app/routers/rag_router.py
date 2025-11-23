"""
RAG Router - Transport Layer (Refactored with Dependency Injection)

Handles HTTP endpoints for document RAG operations.
Strictly follows layered architecture:
- NO business logic in this layer
- Only route definition, validation (Pydantic), and service delegation
- Services injected via FastAPI Depends()

Microservices-ready: Easy to extract into separate service
"""

from app.config.languages import SUPPORTED_LANGUAGES
from app.schemas.rag_schema import (
    DetectLanguageResponse,
    DocumentDeleteResponse,
    DocumentInfo,
    DocumentListResponse,
    FeedbackRequest,
    LanguageInfo,
    LanguagesListResponse,
    QueryRequest,
    QueryResponse,
    SummarizeRequest,
    SummarizeResponse,
    UploadResponse,
)
from app.services.query_parser_service import query_parser_service
from app.services.rag_service import RAGService, get_rag_service
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

# Router instance
router = APIRouter(prefix="/rag", tags=["rag"])


# --- Type alias for cleaner dependency injection ---
# Note: Using explicit Depends() in function signatures for clarity


@router.post("/upload/", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="The PDF document to be indexed."),
    user_id: str = Form(
        ..., description="The unique ID of the user (tenant) uploading the file."
    ),
    document_language: str = Form(
        None, 
        description="Optional: Document language code (IT, EN, FR, DE, ES, etc.). Auto-detected if not provided."
    ),
    rag_service: RAGService = Depends(get_rag_service),  # Injected by FastAPI
):
    """
    Uploads a PDF document and indexes its content into the vector store.
    
    Optionally accepts a language code to specify the document's language.
    This enables better multilingual support when a user has documents in different languages.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF documents are supported.",
        )

    try:
        # Pass the file, user_id, and optional language to the RAG service
        chunks_indexed, detected_language = await rag_service.index_document(
            file, user_id, document_language
        )

        return UploadResponse(
            message=f"Document '{file.filename}' indexed successfully.",
            status="success",
            chunks_indexed=chunks_indexed,
            detected_language=detected_language,
        )
    except Exception as e:
        # Log the error for debugging purposes
        print(f"Indexing error for file {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process and index document.",
        )


@router.post("/detect-language/", response_model=DetectLanguageResponse)
async def detect_language_preview(
    file: UploadFile = File(..., description="The PDF document to analyze."),
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    Detects the language of a PDF document WITHOUT indexing it.
    Used for preview/auto-detection before upload.
    
    This endpoint:
    - Extracts text from the PDF
    - Runs language detection (5-pass voting)
    - Returns detected language code and confidence
    - Does NOT store anything in the vector database
    """
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF documents are supported.",
        )

    try:
        detected_language, confidence = await rag_service.detect_document_language_preview(file)
        
        return DetectLanguageResponse(
            detected_language=detected_language,
            confidence=confidence,
            filename=file.filename or "unknown.pdf"
        )
    except Exception as e:
        from app.core.logging import logger
        logger.error(f"Language detection preview error for {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to detect document language.",
        )


@router.post("/query/", response_model=QueryResponse)
def query_document(
    request: QueryRequest,
    rag_service: RAGService = Depends(get_rag_service),  # Injected by FastAPI
):
    """
    Queries the vector store for relevant information based on the user's question,
    filtered by user_id, and generates a response using the LLM.
    
    NEW: Automatically extracts file filtering instructions from natural language
    (e.g., "only in file X", "exclude file Y") and applies them to the search.
    
    Transport Layer: Validates input, delegates to service, returns response.
    Optionally accepts conversation history for context-aware responses.
    """
    try:
        # Log use case for debugging
        from app.core.logging import logger
        
        # === DETAILED REQUEST LOGGING ===
        logger.info(f"{'='*80}")
        logger.info("📥 [ROUTER] NEW QUERY REQUEST")
        logger.info(f"{'='*80}")
        logger.info(f"👤 User ID: {request.user_id}")
        logger.info(f"❓ Query: {request.query}")
        logger.info(f"📜 Conversation History: {len(request.conversation_history)} messages")
        if request.conversation_history:
            for idx, msg in enumerate(request.conversation_history[-3:], 1):  # Last 3 messages
                logger.debug(f"   [{idx}] {msg.role}: {msg.content[:80]}...")
        
        if request.output_language:
            logger.info(f"🌍 Output Language: {request.output_language}")
        else:
            logger.info("🌍 Output Language: Not specified (will auto-detect from query)")
        
        logger.info(f"{'='*80}")
        
        # === STEP 1: EXTRACT FILE FILTERS AND OPTIMIZE QUERY ===
        # Get user's available documents for validation
        available_documents = rag_service.get_user_documents(request.user_id)
        available_filenames = [doc.filename for doc in available_documents]
        
        logger.info(f"📂 User has {len(available_filenames)} documents available")
        logger.info("🔍 Extracting file filters and optimizing query...")
        
        # Extract file filters using OpenAI gpt-4o-mini
        # This also:
        # - Removes file references from query
        # - Corrects grammar and spelling
        # - Removes filler words (tipo, praticamente, etc.)
        # Cost: ~$0.00007 per query (7 cents per 1000 queries)
        filter_result = query_parser_service.extract_file_filters(
            query=request.query,
            available_files=available_filenames
        )
        
        # Use optimized query for RAG (file references removed, grammar corrected)
        query_for_rag = filter_result.cleaned_query
        include_files = filter_result.include_files if filter_result.include_files else None
        exclude_files = filter_result.exclude_files if filter_result.exclude_files else None
        
        logger.info(f"✅ File filters: include={include_files}, exclude={exclude_files}")
        logger.info(f"🧹 Optimized query: {query_for_rag}")
        
        # === STEP 2: CALL RAG SERVICE WITH FILTERS ===
        # Call the RAG service to get the answer and source documents
        # Pass conversation history if provided (defaults to empty list in schema)
        # Pass output_language if provided for explicit response language control
        # Pass file filters extracted from query
        answer, sources = rag_service.answer_query(
            query_for_rag, 
            request.user_id,
            request.conversation_history,
            request.output_language,
            include_files=include_files,
            exclude_files=exclude_files
        )
        
        # === DETAILED RESPONSE LOGGING ===
        logger.info(f"{'='*80}")
        logger.info("📤 [ROUTER] QUERY RESPONSE")
        logger.info(f"{'='*80}")
        logger.info(f"✅ Answer length: {len(answer)} characters")
        logger.info(f"📚 Sources: {len(sources)} documents")
        if sources:
            logger.info(f"   Files: {', '.join(sources[:5])}")
        logger.info(f"📝 Answer preview: {answer[:200]}...")
        logger.info(f"{'='*80}")

        return QueryResponse(answer=answer, source_documents=sources)
    except Exception as e:
        # Log the error for debugging purposes
        logger.error(f"{'='*80}")
        logger.error("❌ [ROUTER] QUERY PROCESSING ERROR")
        logger.error(f"{'='*80}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        import traceback
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        logger.error(f"{'='*80}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process query and retrieve answer.",
        )


@router.get("/documents/check")
def check_documents(
    user_id: str,
    rag_service: RAGService = Depends(get_rag_service),  # Injected by FastAPI
):
    """
    Checks if a user has any indexed documents in the vector store.
    Returns the count of documents for the given user_id.
    
    Transport Layer: Parameter validation and service delegation only.
    """
    try:
        # Get document count for the user
        doc_count = rag_service.get_user_document_count(user_id)

        return {
            "has_documents": doc_count > 0,
            "document_count": doc_count,
            "user_id": user_id,
        }
    except Exception as e:
        print(f"Error checking document status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check document status.",
        )


@router.post("/summarize/", response_model=SummarizeResponse)
def summarize_conversation(
    request: SummarizeRequest,
    rag_service: RAGService = Depends(get_rag_service),  # Injected by FastAPI
):
    """
    Generates a concise summary of the conversation history.
    Useful for long-term memory storage and context retrieval.
    
    Transport Layer: Schema validation and service delegation.
    """
    try:
        summary = rag_service.generate_conversation_summary(request.conversation_history)
        return SummarizeResponse(summary=summary)
    except Exception as e:
        print(f"Summarization error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate conversation summary.",
        )


@router.get("/documents/list", response_model=DocumentListResponse)
def list_user_documents(
    user_id: str,
    rag_service: RAGService = Depends(get_rag_service),  # Injected by FastAPI
):
    """
    Lists all documents indexed for a specific user with metadata.
    Returns document names, chunk counts, and language information.
    
    Transport Layer: Query parameter validation and service delegation.
    """
    try:
        documents = rag_service.get_user_documents(user_id)
        return DocumentListResponse(
            documents=documents,
            total_count=len(documents),
            user_id=user_id,
        )
    except Exception as e:
        print(f"Error listing documents for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document list.",
        )


@router.delete("/documents/delete", response_model=DocumentDeleteResponse)
def delete_document(
    user_id: str,
    filename: str,
    rag_service: RAGService = Depends(get_rag_service),  # Injected by FastAPI
):
    """
    Deletes a specific document and all its chunks from the vector store.
    Requires both user_id and filename to ensure proper authorization.
    
    Transport Layer: Parameter validation, service delegation, HTTP status handling.
    """
    try:
        chunks_deleted = rag_service.delete_user_document(user_id, filename)
        
        if chunks_deleted == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{filename}' not found for user {user_id}.",
            )
        
        return DocumentDeleteResponse(
            message=f"Document '{filename}' deleted successfully.",
            filename=filename,
            chunks_deleted=chunks_deleted,
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting document {filename} for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document.",
        )


@router.delete("/documents/delete-all")
def delete_all_documents(
    user_id: str,
    rag_service: RAGService = Depends(get_rag_service),  # Injected by FastAPI
):
    """
    Deletes ALL documents for a specific user.
    Use with caution - this is irreversible!
    
    Transport Layer: Parameter validation and service delegation.
    """
    try:
        chunks_deleted = rag_service.delete_all_user_documents(user_id)
        
        return {
            "message": f"All documents deleted successfully for user {user_id}.",
            "chunks_deleted": chunks_deleted,
        }
    except Exception as e:
        print(f"Error deleting all documents for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete all documents.",
        )


@router.get("/languages/", response_model=LanguagesListResponse, status_code=status.HTTP_200_OK)
def get_supported_languages():
    """
    Returns the complete list of supported languages with metadata.
    
    This endpoint serves as the single source of truth for language configuration
    across the application. No authentication required (public data).
    
    Response includes:
    - Language code (ISO 639-1)
    - English name
    - Native name
    - Flag emoji
    - Translated "Sources" label
    
    Cache-friendly: Languages rarely change, safe to cache client-side.
    """
    languages = [
        LanguageInfo(
            code=lang["code"],
            english_name=lang["english_name"],
            native_name=lang["native_name"],
            flag=lang["flag"],
            sources_label=lang["sources_label"],
        )
        for lang in SUPPORTED_LANGUAGES
    ]
    
    return LanguagesListResponse(
        languages=languages,
        total_count=len(languages)
    )


@router.post("/report-bug/", status_code=status.HTTP_201_CREATED)
async def report_bug(
    user_id: str = Form(..., description="User ID who is reporting the bug"),
    description: str = Form(..., min_length=10, description="Bug description (min 10 chars)"),
    conversation_id: str = Form(None, description="Optional conversation ID"),
    timestamp: str = Form(..., description="ISO timestamp when bug was reported"),
    user_agent: str = Form(None, description="Optional browser user agent"),
    attachment: UploadFile = File(None, description="Optional file: image, video, PDF, or archive (ZIP, RAR, 7z, TAR.GZ) - max 10MB"),
):
    """
    📝 Bug Report Endpoint
    
    Collects structured user feedback about errors, hallucinations, or system issues.
    Sends email notification via SendGrid with optional attachment and logs to file.
    Critical for MVP to identify and fix RAG accuracy problems and backend errors.
    
    Args:
        user_id: User ID who is reporting the bug
        description: Bug description (minimum 10 characters)
        conversation_id: Optional conversation ID for context
        timestamp: ISO timestamp when bug was reported
        user_agent: Optional browser user agent string
        attachment: Optional file attachment (image/video/PDF/archive, max 10MB)
    
    Returns:
        Success message with report ID and email status
    
    Features:
        - Sends formatted email to support team via SendGrid
        - Supports file attachments (images, videos, PDFs, archives) up to 10MB
        - Logs to logs/bug_reports.log with structured JSON
        - Includes conversation context for debugging
    
    Setup:
        - Requires SENDGRID_API_KEY in .env
        - Configure SENDGRID_FROM_EMAIL and SUPPORT_EMAIL
    """
    import json
    from datetime import datetime
    from pathlib import Path

    from app.core.logging import logger
    from app.services.email_service import get_email_service
    
    # Validate attachment size (max 10MB)
    if attachment and attachment.size:
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if attachment.size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Attachment too large. Maximum size is 10MB, got {attachment.size / 1024 / 1024:.2f}MB"
            )
    
    # Read attachment content if provided
    attachment_data = None
    attachment_filename = None
    attachment_type = None
    
    if attachment and attachment.filename:
        attachment_content = await attachment.read()
        attachment_data = attachment_content
        attachment_filename = attachment.filename
        attachment_type = attachment.content_type
        logger.info(f"📎 Attachment received | Name: {attachment_filename} | Type: {attachment_type} | Size: {len(attachment_content)} bytes")
    
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Structured log entry
    log_entry = {
        "timestamp": timestamp,
        "user_id": user_id,
        "conversation_id": conversation_id,
        "description": description,
        "user_agent": user_agent,
        "attachment_filename": attachment_filename,
        "attachment_size": len(attachment_data) if attachment_data else 0,
        "server_timestamp": datetime.utcnow().isoformat(),
    }
    
    # Write to dedicated bug reports log
    bug_log_path = logs_dir / "bug_reports.log"
    with open(bug_log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    # Send email notification via SendGrid
    email_service = get_email_service()
    email_sent = email_service.send_bug_report(
        user_id=user_id,
        description=description,
        conversation_id=conversation_id,
        timestamp=timestamp,
        user_agent=user_agent,
        attachment_data=attachment_data,
        attachment_filename=attachment_filename,
        attachment_type=attachment_type,
    )
    
    # Log to main logs with emoji for visibility
    attachment_info = f" | 📎 {attachment_filename}" if attachment_filename else ""
    logger.bind(BUG_REPORT=True).warning(
        f"🐞 Bug Report from {user_id} | Conv: {conversation_id or 'N/A'} | Email: {'✅' if email_sent else '❌'}{attachment_info} | {description[:100]}"
    )
    
    return {
        "message": "Bug report received successfully",
        "report_id": f"{user_id}_{datetime.utcnow().timestamp()}",
        "status": "logged",
        "email_sent": email_sent,
        "attachment_included": attachment_filename is not None,
    }


@router.post("/feedback/", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback: FeedbackRequest,
):
    """
    ⭐ User Feedback Endpoint
    
    Collects user feedback with star rating (0.5-5.0) and optional message.
    Sends email notification to support team and logs to file.
    Helps track user satisfaction and identify areas for improvement.
    
    Args:
        feedback: Feedback data with rating, optional message, and context
    
    Returns:
        Success message with feedback ID and email status
    
    Features:
        - Star rating from 0.5 to 5.0 (half-star increments)
        - Optional feedback message
        - Sends formatted email with star visualization
        - Logs to logs/feedback.log with structured JSON
        - Includes conversation context for targeted improvements
    
    Setup:
        - Requires SENDGRID_API_KEY in .env
        - Configure SENDGRID_FROM_EMAIL and SUPPORT_EMAIL
    """
    import json
    from datetime import datetime
    from pathlib import Path

    from app.core.logging import logger
    from app.services.email_service import get_email_service
    
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Structured log entry
    log_entry = {
        "timestamp": feedback.timestamp,
        "user_id": feedback.user_id,
        "conversation_id": feedback.conversation_id,
        "rating": feedback.rating,
        "message": feedback.message,
        "user_agent": feedback.user_agent,
        "server_timestamp": datetime.utcnow().isoformat(),
    }
    
    # Write to dedicated feedback log
    feedback_log_path = logs_dir / "feedback.log"
    with open(feedback_log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    # Send email notification via SendGrid
    email_service = get_email_service()
    email_sent = email_service.send_feedback(
        user_id=feedback.user_id,
        rating=feedback.rating,
        message=feedback.message,
        conversation_id=feedback.conversation_id,
        timestamp=feedback.timestamp,
        user_agent=feedback.user_agent,
    )
    
    # Determine sentiment emoji for logging
    if feedback.rating >= 4.0:
        sentiment_emoji = "😊"
    elif feedback.rating >= 3.0:
        sentiment_emoji = "😐"
    else:
        sentiment_emoji = "😞"
    
    # Log to main logs with emoji for visibility
    logger.bind(FEEDBACK=True).info(
        f"{sentiment_emoji} Feedback from {feedback.user_id} | Rating: {feedback.rating}/5.0 | Conv: {feedback.conversation_id or 'N/A'} | Email: {'✅' if email_sent else '❌'} | {feedback.message[:100] if feedback.message else 'No message'}"
    )
    
    return {
        "message": "Feedback received successfully",
        "feedback_id": f"{feedback.user_id}_{datetime.utcnow().timestamp()}",
        "status": "logged",
        "email_sent": email_sent,
    }




