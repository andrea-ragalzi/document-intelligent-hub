# backend/main.py

import os
import time
import warnings
from pathlib import Path

# Load .env file before any other imports
from dotenv import load_dotenv

# Load .env from backend directory
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

from app.core.config import settings
from app.core.logging import logger
from app.db.chroma_client import (  # Import database initialization
    get_chroma_client,
    get_embedding_function,
)
from app.routers import language_router, rag_router, translation_router
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Suppress ONNX Runtime GPU device discovery warnings
os.environ["ORT_LOG_SEVERITY_LEVEL"] = "3"  # Only show errors
warnings.filterwarnings("ignore", category=UserWarning, module="onnxruntime")

# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for Document Intelligent Hub - Multi-Tenant RAG System."
)

logger.info(f"🚀 Starting {settings.PROJECT_NAME} v{settings.VERSION}")


# --- Startup Event Handler (Dependency Injection Setup) ---
@app.on_event("startup")
async def startup_event():
    """
    Application startup handler.
    
    Initializes database connections and verifies system readiness.
    This is where you would initialize connection pools, load models, etc.
    
    Architecture Note:
        - Database clients are initialized via dependency injection at request time
        - This handler only verifies that the system can connect successfully
        - Actual per-request connections managed by FastAPI's Depends()
    """
    logger.info("🔧 Running startup checks...")
    
    # Ensure ChromaDB persistence folder exists
    if not os.path.exists(settings.CHROMA_DB_PATH):
        os.makedirs(settings.CHROMA_DB_PATH)
        logger.info(f"📁 Created persistent database folder: {settings.CHROMA_DB_PATH}")
    else:
        logger.info(f"📁 Using existing database folder: {settings.CHROMA_DB_PATH}")
    
    # Verify ChromaDB connection
    try:
        client = get_chroma_client()
        logger.info("✅ ChromaDB client initialized successfully")
        logger.info(f"📊 ChromaDB version: {client.get_version()}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize ChromaDB client: {e}")
        raise
    
    # Preload embedding model to avoid "meta tensor" errors on first request
    try:
        embedding_fn = get_embedding_function()
        # Test embedding generation to ensure model is fully loaded
        test_embedding = embedding_fn.embed_query("test")
        logger.info(f"✅ Embedding model preloaded successfully ({len(test_embedding)} dimensions)")
    except Exception as e:
        logger.error(f"❌ Failed to preload embedding model: {e}")
        raise
    
    logger.info("✅ Application startup complete!")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown handler.
    
    Cleanup resources, close connections, and gracefully shutdown services.
    
    Architecture Note:
        - ChromaDB client doesn't require explicit cleanup (handled by OS)
        - Add here any custom cleanup logic (e.g., save state, close connections)
    """
    logger.info("🔄 Shutting down application...")
    logger.info("✅ Shutdown complete!")


# --- Logging Middleware ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing information."""
    start_time = time.time()
    
    # Log request
    client_host = request.client.host if request.client else "unknown"
    logger.bind(ACCESS=True).info(
        f"➡️  {request.method} {request.url.path} - Client: {client_host}"
    )
    
    # Process request
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        status_emoji = "✅" if response.status_code < 400 else "❌"
        logger.bind(ACCESS=True).info(
            f"{status_emoji} {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s"
        )
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"❌ {request.method} {request.url.path} - Error: {str(e)} - Time: {process_time:.3f}s")
        raise

# --- CORS Configuration ---
# CORS is required to allow the React frontend (running on a different port/origin) 
# to communicate with this FastAPI backend.
# Note: When using allow_credentials=True, you cannot use "*" for origins
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Mobile access via local network IP (all ports)
    "http://192.168.0.206:3000",
    "http://192.168.0.206:3001",
    "http://192.168.0.206:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (GET, POST, etc.)
    allow_headers=["*"], # Allow all headers
)

# --- Router Registration ---
# Register all feature API endpoints
app.include_router(rag_router.router)
app.include_router(language_router.router)
app.include_router(translation_router.router)

# --- Root Endpoint (Health Check) ---
@app.get("/")
def read_root():
    """Health check endpoint - verifies API is running."""
    return {
        "message": f"{settings.PROJECT_NAME} API is running!",
        "version": settings.VERSION,
        "status": "healthy"
    }
