"""
Document Classifier Service

This service classifies documents into predefined categories to determine the
optimal chunking strategy for indexing.
"""

from enum import Enum

class DocumentCategory(str, Enum):
    """Enum for document categories."""
    AUTORITA_STRUTTURALE = "AUTORITA_STRUTTURALE"
    INFORMATIVO_NON_STRUTTURATO = "INFORMATIVO_NON_STRUTTURATO"

class DocumentClassifierService:
    """
    A service to classify documents based on filename and content.
    """

    def __init__(self):
        """Initializes the classifier service."""
        self.structural_keywords = [
            "protocollo", "manuale", "governance", "clausola", 
            "articolo", "allegato", "specifiche"
        ]

    def classify_document(self, filename: str, content_preview: str) -> DocumentCategory:
        """
        Classifies the document into a category.

        Args:
            filename: The name of the file.
            content_preview: The first 1000 characters of the document content.

        Returns:
            The detected DocumentCategory.
        """
        text_to_check = (filename + " " + content_preview).lower()

        for keyword in self.structural_keywords:
            if keyword in text_to_check:
                return DocumentCategory.AUTORITA_STRUTTURALE
        
        return DocumentCategory.INFORMATIVO_NON_STRUTTURATO

    def has_structural_density(self, content: str) -> bool:
        """
        Checks if the document has high structural density (headers, numbered lists).
        Used as a fallback for documents initially classified as unstructured.
        
        Args:
            content: Text content to analyze (recommended: first 5000 chars).
            
        Returns:
            True if structural density exceeds threshold, False otherwise.
        """
        import re
        
        # Patterns for headers and numbered lists
        # 1. Numbered sections (e.g., "1.1 ", "1.2.3 ")
        # 2. Lettered sections (e.g., "A. ", "B. ")
        # 3. Markdown headers (e.g., "## ", "### ")
        patterns = [
            r'^\s*\d+(\.\d+)+\s+',  # 1.1, 1.2.3
            r'^\s*[A-Z]\.\s+',      # A., B.
            r'^\s*#+\s+'            # ## Header
        ]
        
        combined_pattern = "|".join(patterns)
        matches = len(re.findall(combined_pattern, content, flags=re.MULTILINE))
        
        # Calculate density (occurrences per 1000 chars)
        content_length = len(content)
        if content_length == 0:
            return False
            
        density = (matches / content_length) * 1000
        
        # Threshold: > 5 occurrences per 1000 chars
        return density > 5

document_classifier_service = DocumentClassifierService()
