from app.schemas.rag import (
    QueryRequest,
    QueryResponse,
    SummarizeRequest,
    SummarizeResponse,
    UploadResponse,
)
from app.services.rag_service import rag_service
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

# Router instance
router = APIRouter(prefix="/rag", tags=["rag"])


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
def query_document(request: QueryRequest):
    """
    Queries the vector store for relevant information based on the user's question,
    filtered by user_id, and generates a response using the LLM.
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
def check_documents(user_id: str):
    """
    Checks if a user has any indexed documents in the vector store.
    Returns the count of documents for the given user_id.
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
def summarize_conversation(request: SummarizeRequest):
    """
    Generates a concise summary of the conversation history.
    Useful for long-term memory storage and context retrieval.
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

