# backend/app/services/translation_service.py

"""
Translation Service Module

Handles query translation for optimal document retrieval matching.
Translates user queries to the document language to improve semantic similarity scores.
"""

from typing import Dict

from app.core.config import settings
from openai import OpenAI
from pydantic import SecretStr


class TranslationService:
    """
    Service for translating user queries to document languages.
    
    This service ensures that queries are translated to match the language
    of the indexed documents, improving embedding similarity and retrieval quality.
    """
    
    # Language code to full name mapping
    LANGUAGE_NAMES: Dict[str, str] = {
        "IT": "Italian",
        "EN": "English", 
        "FR": "French",
        "DE": "German",
        "ES": "Spanish",
        "PT": "Portuguese",
        "NL": "Dutch",
        "PL": "Polish",
        "RU": "Russian",
        "ZH": "Chinese",
        "JA": "Japanese",
        "KO": "Korean",
    }
    
    def __init__(self):
        """Initialize the translation service with OpenAI client."""
        # Extract API key securely
        api_key_value = (
            settings.OPENAI_API_KEY.get_secret_value()
            if isinstance(settings.OPENAI_API_KEY, SecretStr)
            else str(settings.OPENAI_API_KEY)
        )
        self.openai_client = OpenAI(api_key=api_key_value)
        self.model = settings.LLM_MODEL
    
    def translate_query_to_english(self, query: str) -> str:
        """
        Translate a query to English using OpenAI LLM.
        
        This method is used for legacy compatibility and when English
        is specifically required for certain operations.
        
        Args:
            query: The user query in any language
            
        Returns:
            The query translated to English, or original if already in English
        """
        prompt = (
            f"Translate the following user query to a standard, concise English search phrase. "
            f"If the query is already in English, return it unchanged. Query: '{query}'"
        )

        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
            content = response.choices[0].message.content
            return content.strip() if content else query

        except Exception as e:
            print(f"Error translating query to English: {e}. Using original query.")
            return query
    
    def translate_query_to_language(self, query: str, target_language: str) -> str:
        """
        Translate a query to the specified target language.
        
        This improves semantic matching when documents are in a specific language.
        Embeddings work better when query and documents are in the same language.
        Proper nouns (names, places, brands) are preserved in translation.
        
        Args:
            query: The original user query
            target_language: The target language code (e.g., 'IT', 'EN', 'FR')
            
        Returns:
            The query translated to the target language
        """
        target_lang_name = self.LANGUAGE_NAMES.get(target_language.upper(), "English")
        
        prompt = (
            f"Translate the following user query to {target_lang_name}. "
            f"Keep it concise and suitable for document search. "
            f"IMPORTANT: Do NOT translate proper nouns (person names, place names, company names, brands, product names). "
            f"Keep all proper nouns in their original form. "
            f"If the query is already in {target_lang_name}, return it unchanged. "
            f"Query: '{query}'"
        )

        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a professional translator. Preserve all proper nouns (names, places, brands) without translation."
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
            content = response.choices[0].message.content
            translated = content.strip() if content else query
            
            print(f"DEBUG [TranslationService]: Translated query to {target_language}: {translated}")
            return translated

        except Exception as e:
            print(f"ERROR translating query to {target_language}: {e}. Using original query.")
            return query
    
    def get_language_name(self, language_code: str) -> str:
        """
        Get the full language name from a language code.
        
        Args:
            language_code: ISO language code (e.g., 'IT', 'EN')
            
        Returns:
            Full language name (e.g., 'Italian', 'English')
        """
        return self.LANGUAGE_NAMES.get(language_code.upper(), "English")


# Singleton instance
translation_service = TranslationService()
