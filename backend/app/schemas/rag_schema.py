# backend/app/schemas/rag.py
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, root_validator

# --- RAG CATEGORIES ---
# These are the possible categories for the user query, used for specialized retrieval logic.
# The Literal type ensures the LLM output is strictly one of these values.
CATEGORIES = Literal[
    "GENERAL_SEARCH",       # Standard informational query
    "TROUBLESHOOTING",      # Question related to errors, fixes, or problems
    "POLICY_CHECK",         # Query about rules, compliance, or regulations
    "TECHNICAL_SPECIFICATION", # Query about device/system specs, data sheets, or code
]

# --- ChromaDB Metadata Schemas ---

class ChunkMetadata(BaseModel):
    """
    Pydantic schema for ChromaDB chunk metadata.
    Enforces structure and validation for document chunk metadata.
    """
    # Multi-tenancy (CRITICAL for data isolation)
    source: str = Field(..., description="User ID (tenant identifier) - CRITICAL for multi-tenancy isolation")
    
    # Document identification
    original_filename: str = Field(..., description="Original filename of the uploaded document")
    original_language_code: str = Field(..., description="Document language code (e.g., 'EN', 'IT', 'FR')")
    
    # Chunk positioning
    chunk_index: Optional[int] = Field(None, description="Index of this chunk within the document")
    chapter_title: Optional[str] = Field(None, description="Chapter or section title for hierarchical context")
    element_type: Optional[str] = Field(None, description="Type of document element (e.g., 'NarrativeText', 'Title', 'Header')")
    
    # Temporal tracking
    uploaded_at: Optional[int] = Field(None, description="Upload timestamp in milliseconds (for sorting)")
    
    class Config:
        """Pydantic config for strict validation"""
        extra = "forbid"  # Reject any extra fields not defined in schema

class DocumentMetadata(BaseModel):
    """
    Pydantic schema for document-level metadata (aggregated view).
    Used when listing documents or retrieving document information.
    """
    filename: str = Field(..., description="Document filename")
    chunks_count: int = Field(..., description="Number of chunks in this document")
    language: str = Field(..., description="Document language code")
    uploaded_at: Optional[str] = Field(None, description="Upload timestamp")
    user_id: str = Field(..., description="User ID (owner of the document)")


# --- Bug Report Schema ---

class BugReportRequest(BaseModel):
    """
    Schema for user bug reports.
    Used to collect structured feedback about errors, hallucinations, or system issues.
    """
    user_id: str = Field(..., description="User ID who is reporting the bug")
    conversation_id: Optional[str] = Field(None, description="ID of the conversation where the bug occurred")
    description: str = Field(..., min_length=10, description="Description of the bug (minimum 10 characters)")
    timestamp: str = Field(..., description="ISO timestamp when the bug was reported")
    user_agent: Optional[str] = Field(None, description="Browser user agent for debugging context")
    
    class Config:
        extra = "allow"  # Allow extra fields for flexibility


class FeedbackRequest(BaseModel):
    """
    Schema for user feedback with star rating.
    Collects user satisfaction and optional comments.
    """
    user_id: str = Field(..., description="User ID who is providing feedback")
    conversation_id: Optional[str] = Field(None, description="ID of the conversation being rated")
    rating: int = Field(..., ge=1, le=5, description="Star rating from 1 to 5")
    message: Optional[str] = Field(None, description="Optional feedback message")
    timestamp: str = Field(..., description="ISO timestamp when feedback was submitted")
    user_agent: Optional[str] = Field(None, description="Browser user agent for context")
    
    class Config:
        extra = "allow"


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

    @root_validator(pre=True)
    def ensure_category_alias(cls, values):
        """Accept either 'category_tag' or its common alias 'category'."""
        if "category_tag" not in values and "category" in values:
            values["category_tag"] = values.pop("category")
        return values

class QueryRequest(BaseModel):
    """Schema for the incoming RAG query request."""
    query: str = Field(..., description="The user's natural language question.")
    user_id: str = Field(..., description="The unique ID of the user (tenant).")
    conversation_history: List[ConversationMessage] = Field(
        default=[],
        description="Recent conversation history for context (last 5-7 exchanges). Empty list if no history."
    )
    output_language: Optional[str] = Field(
        None,
        description=(
            "Optional: ISO language code for response (IT, EN, FR, DE, ES, etc.). "
            "If not provided, response will be in the same language as the query."
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

# --- Document Management Schemas ---

class DocumentInfo(BaseModel):
    """Schema for document information."""
    filename: str = Field(..., description="The name of the document file.")
    chunks_count: int = Field(..., description="Number of chunks/pieces this document was split into.")
    language: Optional[str] = Field(None, description="Detected or specified language of the document.")
    uploaded_at: Optional[str] = Field(None, description="Upload timestamp if available.")

class DocumentListResponse(BaseModel):
    """Schema for listing user documents."""
    documents: List[DocumentInfo] = Field(..., description="List of user's indexed documents.")
    total_count: int = Field(..., description="Total number of documents.")
    user_id: str = Field(..., description="The user ID these documents belong to.")

class DocumentDeleteResponse(BaseModel):
    """Schema for document deletion response."""
    message: str = Field(..., description="Success message.")
    filename: str = Field(..., description="Name of the deleted document.")
    chunks_deleted: int = Field(..., description="Number of chunks deleted from the vector store.")

class DetectLanguageResponse(BaseModel):
    """Schema for language detection preview response."""
    detected_language: str = Field(..., description="The detected language code (IT, EN, FR, etc.)")
    confidence: float = Field(..., description="Confidence score (0.0 to 1.0)")
    filename: str = Field(..., description="Name of the analyzed file")

class LanguageInfo(BaseModel):
    """Schema for supported language information."""
    code: str = Field(..., description="ISO 639-1 language code (e.g., 'EN', 'IT', 'ES')")
    english_name: str = Field(..., description="Language name in English (e.g., 'English', 'Italian')")
    native_name: str = Field(..., description="Language name in native script (e.g., 'Italiano', 'Español')")
    flag: str = Field(..., description="Flag emoji representing the language (e.g., '🇬🇧', '🇮🇹')")
    sources_label: str = Field(..., description="Translation of 'Sources' in this language (e.g., 'Fonti', 'Fuentes')")

class LanguagesListResponse(BaseModel):
    """Schema for listing all supported languages."""
    languages: List[LanguageInfo] = Field(..., description="List of all supported languages with metadata")
    total_count: int = Field(..., description="Total number of supported languages")

# --- Query Parser Schemas ---

class FileFilterRequest(BaseModel):
    """Schema for file filter extraction request."""
    query: str = Field(..., description="The user's query potentially containing file references")
    available_files: List[str] = Field(..., description="List of available document filenames for validation")

class FileFilterResponse(BaseModel):
    """Schema for extracted file filters from query."""
    include_files: List[str] = Field(
        default=[],
        description="List of filenames to include in search (empty = include all)"
    )
    exclude_files: List[str] = Field(
        default=[],
        description="List of filenames to exclude from search"
    )
    original_query: str = Field(..., description="The original query before filter extraction")
    cleaned_query: str = Field(..., description="Query with file references removed for better semantic search")
