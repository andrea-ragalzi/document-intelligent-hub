"""
Application-wide constants.

All magic numbers and configuration values should be defined here
for easy maintenance and documentation.
"""


class ConversationConstants:
    """Conversation memory management constants."""

    BUFFER_SIZE = 7  # Number of message pairs to keep in memory
    SUMMARY_THRESHOLD = 20  # Messages before triggering summary
    MAX_HISTORY_LENGTH = 14  # Total messages (7 pairs * 2)


class ChunkingConstants:
    """Document chunking configuration."""

    # Fixed-size chunking (fallback)
    DEFAULT_CHUNK_SIZE = 1000  # Characters per chunk
    DEFAULT_CHUNK_OVERLAP = 200  # Overlap between chunks

    # Structural chunking
    MIN_CHUNK_SIZE = 50  # Minimum characters for a valid chunk
    MAX_CHUNK_SIZE = 2000  # Maximum characters per chunk
    COMBINE_SMALL_CHUNKS_THRESHOLD = 200  # Combine chunks smaller than this


class QueryConstants:
    """Query processing constants."""

    PARSER_MODEL = "gpt-4o-mini"
    PARSER_COST_PER_1K_QUERIES = 0.07  # USD
    MAX_QUERY_LENGTH = 1000  # Characters
    MIN_QUERY_LENGTH = 3  # Characters
    MIN_QUERY_LENGTH_FOR_REFORMULATION = (
        30  # Characters - triggers reformulation if shorter
    )

    # Query expansion
    BASE_RETRIEVAL_K = 30  # Documents to retrieve before reranking
    FINAL_RETRIEVAL_K = 15  # Documents after reranking

    # Conversational patterns for reformulation detection
    CONVERSATIONAL_PATTERNS = [
        "i mean",
        "what about",
        "how about",
        "what if",
        "invece",
        "intendo",
        "voglio dire",
        "piuttosto",
        "je veux dire",
        "plutôt",
        "en fait",
        "ich meine",
        "stattdessen",
        "eigentlich",
    ]


class LanguageConstants:
    """Language detection and translation constants."""

    DETECTION_SAMPLE_SIZE = 50  # Documents to analyze for user preference
    MIN_TEXT_LENGTH_FOR_DETECTION = 5  # Characters
    DEFAULT_LANGUAGE = "EN"
    DEFAULT_CONFIDENCE = 0.9  # Confidence score for language detection

    SUPPORTED_LANGUAGES = [
        "EN",
        "IT",
        "FR",
        "DE",
        "ES",
        "PT",
        "NL",
        "PL",
        "RU",
        "ZH",
        "JA",
        "KO",
        "AR",
        "HI",
        "TR",
        "SV",
        "DA",
        "FI",
        "NO",
        "CS",
        "HU",
        "RO",
    ]

    # Translation for "Sources" label
    SOURCES_TRANSLATIONS = {
        "EN": "Sources",
        "IT": "Fonti",
        "FR": "Sources",
        "DE": "Quellen",
        "ES": "Fuentes",
        "PT": "Fontes",
    }


class TierConstants:
    """User tier and quota constants."""

    UNLIMITED_QUOTA = 9999  # Effectively unlimited
    FREE_QUOTA = 10
    PRO_QUOTA = 100
    PREMIUM_QUOTA = 500


class MobileUXConstants:
    """Mobile user experience constants (frontend reference)."""

    LONG_PRESS_DURATION_MS = 500  # Milliseconds for long-press
    DRAG_DISMISS_THRESHOLD_PX = 100  # Pixels to trigger dismiss


class CacheConstants:
    """Caching configuration."""

    TRANSLATION_CACHE_SIZE = 1000  # LRU cache max size
    QUERY_EXPANSION_CACHE_SIZE = 500


class APIConstants:
    """API rate limiting and timeouts."""

    REQUEST_TIMEOUT_SECONDS = 30
    MAX_FILE_SIZE_MB = 10
    MAX_REQUESTS_PER_MINUTE = 60

    # Bug report constraints
    MIN_BUG_DESCRIPTION_LENGTH = 10  # Characters
    MAX_BUG_DESCRIPTION_LENGTH = 5000  # Characters


class EmbeddingConstants:
    """Embedding model configuration."""

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION = 384  # Vector dimensions
    BATCH_SIZE = 100  # Documents to embed at once


class DocumentConstants:
    """Document management constants."""

    SAMPLE_SIZE = 100000  # Chunks to sample for document discovery
    MAX_FILENAME_LENGTH = 255  # Characters
    SUPPORTED_FORMATS = ["pdf"]  # Currently only PDF


class LLMConstants:
    """LLM model configuration."""

    DEFAULT_MODEL = "gpt-3.5-turbo"
    QUERY_GEN_MODEL = (
        "gpt-4o-mini"  # For cheap operations (classification, reformulation)
    )
    DEFAULT_TEMPERATURE = 0.2  # Lower = more deterministic
    MAX_TOKENS = 1000  # Maximum tokens in response
