# backend/app/services/language_detection_service.py

"""
Language Detection Service Module

Detects the predominant language of a user's document collection.
Used to optimize query translation for better semantic matching.
"""

from typing import Dict

from app.db.chroma_client import COLLECTION_NAME, get_chroma_client


class LanguageDetectionService:
    """
    Service for detecting document languages from ChromaDB metadata.
    
    This service analyzes the 'original_language_code' metadata field
    to determine which language is most common in a user's documents.
    """
    
    def __init__(self):
        """Initialize the language detection service with ChromaDB client."""
        self.chroma_client = get_chroma_client()
    
    def get_user_document_language(self, user_id: str, sample_size: int = 50) -> str:
        """
        Detect the predominant language in a user's document collection.
        
        This method samples documents from the user's collection and analyzes
        the 'original_language_code' metadata field to find the most common language.
        
        Args:
            user_id: The user identifier for multi-tenancy filtering
            sample_size: Number of documents to sample (default: 50)
            
        Returns:
            The most common language code (e.g., 'IT', 'EN', 'FR')
            Defaults to 'EN' if no documents or no language metadata found
        """
        try:
            collection = self.chroma_client.get_collection(name=COLLECTION_NAME)
            
            # Retrieve a sample of user's documents
            results = collection.get(
                where={"source": user_id},
                limit=sample_size,
                include=["metadatas"]
            )
            
            metadatas = results.get("metadatas") if results else None
            if not metadatas:
                print(f"DEBUG [LanguageDetection]: No documents found for user {user_id}, defaulting to EN")
                return "EN"
            
            # Count language occurrences
            language_counts: Dict[str, int] = {}
            for metadata in metadatas:
                if metadata and "original_language_code" in metadata:
                    lang = metadata["original_language_code"]
                    # Ensure it's a string before counting
                    if isinstance(lang, str):
                        language_counts[lang] = language_counts.get(lang, 0) + 1
            
            if not language_counts:
                print(f"DEBUG [LanguageDetection]: No language metadata found for user {user_id}, defaulting to EN")
                return "EN"
            
            # Find the most common language
            predominant_language = max(language_counts, key=lambda k: language_counts[k])
            
            print(f"DEBUG [LanguageDetection]: User {user_id} languages: {language_counts}")
            print(f"DEBUG [LanguageDetection]: Predominant language: {predominant_language}")
            
            return predominant_language
            
        except Exception as e:
            print(f"Error detecting document language for user {user_id}: {e}. Defaulting to EN")
            return "EN"
    
    def get_language_distribution(self, user_id: str, sample_size: int = 100) -> Dict[str, int]:
        """
        Get the distribution of languages in a user's document collection.
        
        Useful for analytics and understanding multilingual document sets.
        
        Args:
            user_id: The user identifier
            sample_size: Number of documents to sample
            
        Returns:
            Dictionary mapping language codes to document counts
        """
        try:
            collection = self.chroma_client.get_collection(name=COLLECTION_NAME)
            
            results = collection.get(
                where={"source": user_id},
                limit=sample_size,
                include=["metadatas"]
            )
            
            metadatas = results.get("metadatas") if results else None
            if not metadatas:
                return {}
            
            language_counts: Dict[str, int] = {}
            for metadata in metadatas:
                if metadata and "original_language_code" in metadata:
                    lang = metadata["original_language_code"]
                    if isinstance(lang, str):
                        language_counts[lang] = language_counts.get(lang, 0) + 1
            
            return language_counts
            
        except Exception as e:
            print(f"Error getting language distribution for user {user_id}: {e}")
            return {}


# Singleton instance
language_detection_service = LanguageDetectionService()
