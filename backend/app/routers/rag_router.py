"""
RAG Router - Transport Layer (Refactored with Dependency Injection)

Handles HTTP endpoints for document RAG operations.
Strictly follows layered architecture:
- NO business logic in this layer
- Only route definition, validation (Pydantic), and service delegation
- Services injected via FastAPI Depends()

Microservices-ready: Easy to extract into separate service
"""

from app.schemas.rag_schema import (
    DocumentDeleteResponse,
    DocumentListResponse,
    QueryRequest,
    QueryResponse,
    SummarizeRequest,
    SummarizeResponse,
    UploadResponse,
)
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


@router.post("/query/", response_model=QueryResponse)
def query_document(
    request: QueryRequest,
    rag_service: RAGService = Depends(get_rag_service),  # Injected by FastAPI
):
    """
    Queries the vector store for relevant information based on the user's question,
    filtered by user_id, and generates a response using the LLM.
    
    Transport Layer: Validates input, delegates to service, returns response.
    Optionally accepts conversation history for context-aware responses.
    Optionally accepts use_case parameter for optimized prompt generation (CU1-CU6).
    """
    try:
        # Call the RAG service to get the answer and source documents
        # Pass conversation history if provided (defaults to empty list in schema)
        # Pass use_case if provided for optimized prompt generation
        answer, sources = rag_service.answer_query(
            request.query, 
            request.user_id,
            request.conversation_history,
            request.use_case
        )

        return QueryResponse(answer=answer, source_documents=sources)
    except Exception as e:
        # Log the error for debugging purposes
        print(f"Query processing error: {e}")
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

