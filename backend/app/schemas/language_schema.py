"""
Language Detection Schema Module

Pydantic schemas for language detection operations.
Used for API request/response validation and internal data structures.
"""

from typing import Literal

from pydantic import BaseModel, Field

# Supported language codes
LanguageCode = Literal[
    "EN", "IT", "FR", "DE", "ES", "PT", "NL", "PL", "RU", "ZH", "JA", "KO"
]


class LanguageDetectionRequest(BaseModel):
    """Schema for language detection request."""

    content: str = Field(
        ..., description="Text content to detect language from", min_length=1
    )


class LanguageDetectionResponse(BaseModel):
    """Schema for language detection response."""

    language_code: str = Field(
        ..., description="Detected language code (e.g., 'EN', 'IT', 'FR')"
    )
    language_name: str = Field(
        ..., description="Full language name (e.g., 'English', 'Italian')"
    )
    confidence: float = Field(
        default=1.0,
        description="Detection confidence score (0.0 to 1.0)",
        ge=0.0,
        le=1.0,
    )
