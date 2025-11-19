# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Specifica che le variabili devono essere caricate dal file .env 
    # e le rende disponibili nell'ambiente (Docker, Railway)
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    
    PROJECT_NAME: str = "Document Intelligent Hub Backend"
    VERSION: str = "1.0.0"

    # Impostazioni Critiche
    OPENAI_API_KEY: str = '' # Sarà usata per gli embeddings e i test
    APP_NAME: str = "Document Intelligent Hub"

    # Impostazioni RAG (valori di default che possono essere sovrascritti)
    CHROMA_DB_PATH: str = "chroma_db"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    LLM_MODEL: str = "gpt-3.5-turbo"  # Can be overridden via .env

# Istanza globale dei settings accessibile da tutta l'applicazione
settings = Settings() # type: ignore

# Log del modello caricato per conferma immediata all'avvio
print(f"🤖 [CONFIG] Loaded LLM Model: {settings.LLM_MODEL}")