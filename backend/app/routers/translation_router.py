"""
Translation Router

REST API endpoints for translation operations.
Provides HTTP interface for text translation services.

Architecture: Router → Service (no repository needed for translation)
"""

from app.schemas.translation_schema import TranslationRequest, TranslationResponse
from app.services.language_service import language_service
from app.services.translation_service import translation_service
from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix="/translation",
    tags=["Translation"],
)


@router.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """
    Translate text to the specified target language.
    
    Args:
        request: Translation request with text and target language
    
    Returns:
        Translation response with original and translated text
    
    Raises:
        HTTPException: If translation fails
    """
    try:
        # Detect source language
        source_language = language_service.detect_language(request.text)
        
        # Translate to target language
        translated_text = translation_service.translate_query_to_language(
            query=request.text,
            target_language=request.target_language
        )
        
        return TranslationResponse(
            original_text=request.text,
            translated_text=translated_text,
            source_language=source_language,
            target_language=request.target_language
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Translation failed: {str(e)}"
        )
