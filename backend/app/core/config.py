# backend/app/core/config.py
import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_prompt_from_file(
    env_var_name: str, fallback_path: str, fallback_text: str
) -> str:
    """
    Load prompt from file path specified in environment variable.
    Falls back to default file path, then to generic text if neither exists.

    Args:
        env_var_name: Name of environment variable containing file path
        fallback_path: Default file path if env var not set
        fallback_text: Generic fallback text if file not found

    Returns:
        Prompt text loaded from file or fallback
    """
    # Try environment variable first
    file_path = os.environ.get(env_var_name)

    # Fall back to default path
    if not file_path:
        file_path = fallback_path

    # Try to load from file
    if file_path:
        path = Path(file_path)
        if path.exists() and path.is_file():
            try:
                return path.read_text(encoding="utf-8").strip()
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"⚠️  [CONFIG] Failed to read {file_path}: {e}")

    # Return fallback if file not found
    return fallback_text


class Settings(BaseSettings):
    # Specifica che le variabili devono essere caricate dal file .env
    # e le rende disponibili nell'ambiente (Docker, Railway)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Document Intelligent Hub Backend"
    PROJECT_VERSION: str = "1.0.0"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # === CRITICAL: API KEYS (MUST BE IN .env) ===
    OPENAI_API_KEY: str = ""  # Required for LLM and embeddings
    APP_NAME: str = "Document Intelligent Hub"

    # === RAG CONFIGURATION ===
    CHROMA_DB_PATH: str = "chroma_db"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    LLM_MODEL: str = "gpt-3.5-turbo"  # Can be overridden via .env

    # === RAG SYSTEM PROMPTS (SECURITY: LOADED FROM FILES) ===
    # ⚠️ SECURITY CRITICAL: These prompts are loaded from external files to:
    # 1. Keep .env clean and readable (no 50-line strings)
    # 2. Allow easy editing without env var escaping issues
    # 3. Maintain security (files are git-ignored)
    # 4. Enable different prompts per environment via RAG_SYSTEM_PROMPT_PATH env var
    #
    # Default paths: backend/config/*.txt (git-ignored)
    # Override via: RAG_SYSTEM_PROMPT_PATH, CLASSIFICATION_PROMPT_PATH, QUERY_REFORMULATION_PROMPT_PATH

    RAG_SYSTEM_PROMPT: str = Field(
        default_factory=lambda: _load_prompt_from_file(
            "RAG_SYSTEM_PROMPT_PATH",
            "./config/rag_system_prompt.txt",
            "You are a helpful AI assistant.",
        ),
        description="Main RAG system prompt (loaded from file)",
    )

    CLASSIFICATION_PROMPT_TEMPLATE: str = Field(
        default_factory=lambda: _load_prompt_from_file(
            "CLASSIFICATION_PROMPT_PATH",
            "./config/classification_prompt.txt",
            "Classify the following query: {query}",
        ),
        description="Query classification prompt (loaded from file)",
    )

    QUERY_REFORMULATION_PROMPT: str = Field(
        default_factory=lambda: _load_prompt_from_file(
            "QUERY_REFORMULATION_PROMPT_PATH",
            "./config/query_reformulation_prompt.txt",
            "Reformulate this query: {query}",
        ),
        description="Query reformulation prompt (loaded from file)",
    )


# Global settings instance accessible from the entire application
settings = Settings()

# Log loaded model for immediate confirmation at startup
print(f"🤖 [CONFIG] Loaded LLM Model: {settings.LLM_MODEL}")

# Security check: Warn if using fallback prompts (not production-ready)
if settings.RAG_SYSTEM_PROMPT == "You are a helpful AI assistant.":
    print(
        "⚠️  [SECURITY WARNING] Using fallback RAG_SYSTEM_PROMPT - SET IN .env FOR PRODUCTION!"
    )
else:
    print(
        f"🔐 [CONFIG] RAG System Prompt: {len(settings.RAG_SYSTEM_PROMPT)} chars (loaded from .env)"
    )
