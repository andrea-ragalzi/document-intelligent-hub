from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status
from app.services.rag_service import rag_service
from app.schemas.rag import QueryRequest, QueryResponse

# Router instance
router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/upload/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="The PDF document to be indexed."),
    user_id: str = Form(
        ..., description="The unique ID of the user (tenant) uploading the file."
    ),
):
    """
    Uploads a PDF document and indexes its content into the vector store.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF documents are supported.",
        )

    try:
        # Pass the file and user_id to the RAG service for indexing
        chunks_indexed = await rag_service.index_document(file, user_id)

        return {
            "message": f"Document '{file.filename}' indexed successfully.",
            "status": "success",
            "chunks_indexed": chunks_indexed,
        }
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
    """
    try:
        # Call the RAG service to get the answer and source documents
        answer, sources = rag_service.answer_query(request.query, request.user_id)

        return QueryResponse(answer=answer, source_documents=sources)
    except Exception as e:
        # Log the error for debugging purposes
        print(f"Query processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process query and retrieve answer.",
        )
