"""Compatibility import for the OpenAI translation adapter."""

from app.infrastructure.openai_translation_adapter import OpenAITranslationAdapter

TranslationService = OpenAITranslationAdapter

__all__ = ["TranslationService"]
