# backend/app/schemas/rag.py
from typing import List, Literal, Optional

from app.schemas.use_cases import UseCaseType
from pydantic import BaseModel, Field

# --- RAG CATEGORIES ---
# These are the possible categories for the user query, used for specialized retrieval logic.
# The Literal type ensures the LLM output is strictly one of these values.
CATEGORIES = Literal[
    "GENERAL_SEARCH",       # Standard informational query
    "TROUBLESHOOTING",      # Question related to errors, fixes, or problems
    "POLICY_CHECK",         # Query about rules, compliance, or regulations
    "TECHNICAL_SPECIFICATION", # Query about device/system specs, data sheets, or code
]

# --- RAG Schemas ---

class UploadRequest(BaseModel):
    """
    Schema for document upload request.
    Optionally includes the document's language for better multilingual support.
    """
    user_id: str = Field(..., description="The unique ID of the user (tenant).")
    document_language: Optional[str] = Field(
        None,
        description="Optional: Document language code (IT, EN, FR, DE, ES, etc.). If not provided, will be auto-detected."
    )

class UploadResponse(BaseModel):
    """Schema for successful document upload response."""
    message: str = Field(..., description="Success message.")
    status: str = Field(..., description="Status code (success/error).")
    chunks_indexed: int = Field(..., description="Number of document chunks indexed.")
    detected_language: str = Field(..., description="The detected or specified document language code.")

class ConversationMessage(BaseModel):
    """
    Schema for a single message in the conversation history.
    Used to maintain context across multiple exchanges.
    """
    role: Literal["user", "assistant"] = Field(
        ...,
        description="The role of the message sender (user or assistant)."
    )
    content: str = Field(
        ...,
        description="The content of the message."
    )

class QueryClassification(BaseModel):
    """
    Schema for classifying the user query intent.
    Used by the LLM to return a structured JSON response.
    """
    category_tag: CATEGORIES = Field(
        ...,
        description="The classified category tag of the user's query."
    )

class QueryRequest(BaseModel):
    """Schema for the incoming RAG query request."""
    query: str = Field(..., description="The user's natural language question.")
    user_id: str = Field(..., description="The unique ID of the user (tenant).")
    conversation_history: List[ConversationMessage] = Field(
        default=[],
        description="Recent conversation history for context (last 5-7 exchanges). Empty list if no history."
    )
    use_case: Optional[UseCaseType] = Field(
        None,
        description=(
            "Optional: Use case type for optimized prompt generation (CU1-CU6). "
            "CU1=Professional Content, CU2=Code Development, CU3=Data Analysis, "
            "CU4=Creative Brainstorming, CU5=Structured Planning, CU6=Business Strategy"
        )
    )

class QueryResponse(BaseModel):
    """Schema for the outgoing RAG query response."""
    answer: str = Field(..., description="The LLM-generated answer based on the retrieved context.")
    source_documents: List[str] = Field(..., description="List of filenames that provided the context.")

class SummarizeRequest(BaseModel):
    """Schema for requesting a conversation summary."""
    conversation_history: List[ConversationMessage] = Field(
        ...,
        description="The full or recent conversation history to summarize."
    )

class SummarizeResponse(BaseModel):
    """Schema for the conversation summary response."""
    summary: str = Field(..., description="The generated conversation summary.")
