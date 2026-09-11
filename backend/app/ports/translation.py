"""Application-facing contract for retrieval translation."""

from typing import Protocol


class TranslationPort(Protocol):
    """Translation capabilities required by answer generation."""

    def translate_query_to_language(self, query: str, target_language: str) -> str:
        """Translate a retrieval query to the target language."""

    def translate_answer_back(self, answer: str, target_language: str) -> str:
        """Translate a generated answer while preserving its formatting."""
