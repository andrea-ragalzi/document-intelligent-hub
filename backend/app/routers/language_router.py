"""
Language Detection Router

REST API endpoints for language detection operations.
Provides HTTP interface for language identification services.

Architecture: Router → Service (no repository needed for language detection)
"""

from app.schemas.language_schema import (
    LanguageDetectionRequest,
    LanguageDetectionResponse,
)
from app.services.language_service import language_service
from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix="/language",
    tags=["Language Detection"],
)


@router.post("/detect", response_model=LanguageDetectionResponse)
async def detect_language(request: LanguageDetectionRequest):
    """
    Detect the language of the provided text content.
    
    Args:
        request: Language detection request with text content
    
    Returns:
        Language detection response with language code and name
    
    Raises:
        HTTPException: If language detection fails
    """
    try:
        # Detect language using the language service
        language_code = language_service.detect_language(request.content)
        
        # Get full language name
        language_name = language_service.get_language_name(language_code)
        
        return LanguageDetectionResponse(
            language_code=language_code,
            language_name=language_name,
            confidence=1.0  # langdetect doesn't provide confidence scores
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Language detection failed: {str(e)}"
        )
