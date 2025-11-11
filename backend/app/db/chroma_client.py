# backend/app/db/chroma_client.py
from chromadb import PersistentClient
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr
from app.core.config import settings

# Il nome della Collection è l'equivalente di una "tabella" in ChromaDB
COLLECTION_NAME = "document_intelligence_collection"

def get_embedding_function():
    """Restituisce la funzione di embedding di OpenAI."""
    # Riduciamo 'chunk_size' a 500 per assicurare il rispetto del limite massimo di 300k token per richiesta.
    return OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL, 
        api_key=SecretStr(settings.OPENAI_API_KEY),
        chunk_size=500  # RIDOTTO DA 1000 A 500
    )

def get_chroma_client():
    """Inizializza il client ChromaDB."""
    # Crea un client persistente che salverà i dati nella cartella definita in settings
    client = PersistentClient(path=settings.CHROMA_DB_PATH)
    return client

def get_rag_collection():
    """Restituisce la collection per la logica RAG, usando il client."""
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        # La funzione di embedding viene fornita da LangChain/Chroma wrapper, non qui.
    )
    return collection