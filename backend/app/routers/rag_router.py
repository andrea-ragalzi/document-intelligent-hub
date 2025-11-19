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


