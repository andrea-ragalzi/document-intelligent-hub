# backend/app/schemas/rag.py
from pydantic import BaseModel, Field
from typing import Literal, List

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

class QueryResponse(BaseModel):
    """Schema for the outgoing RAG query response."""
    answer: str = Field(..., description="The LLM-generated answer based on the retrieved context.")
    source_documents: List[str] = Field(..., description="List of filenames that provided the context.")