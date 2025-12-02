"""
Translation Schema Module

Pydantic schemas for translation operations.
Used for API request/response validation and internal data structures.
"""

from typing import Literal

from pydantic import BaseModel, Field

# Supported language codes for translation
TargetLanguage = Literal[
    "EN", "IT", "FR", "DE", "ES", "PT", "NL", "PL", "RU", "ZH", "JA", "KO"
]


class TranslationRequest(BaseModel):
    """Schema for translation request."""

    text: str = Field(..., description="Text to translate", min_length=1)
    target_language: TargetLanguage = Field(
        ..., description="Target language code (e.g., 'EN', 'IT', 'FR')"
    )
    preserve_proper_nouns: bool = Field(
        default=True,
        description="Whether to preserve proper nouns (names, places, brands) during translation",
    )


class TranslationResponse(BaseModel):
    """Schema for translation response."""

    original_text: str = Field(..., description="Original text before translation")
    translated_text: str = Field(..., description="Translated text")
    source_language: str = Field(
        ..., description="Detected or specified source language code"
    )
    target_language: str = Field(..., description="Target language code")
