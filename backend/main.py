"""FastAPI main application entry point with lifespan management, middleware, and routing."""

import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Load explicit DEV-only routing/persistence first, then fill remaining local
# secrets from the legacy/base file. Real process variables (tests, Docker and
# Railway) stay authoritative because neither file overwrites them.
dev_env_path = Path(__file__).parent / ".env.development.local"
load_dotenv(dotenv_path=dev_env_path, override=False)
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=False)

# Now, import other modules (after load_dotenv to load env vars first)
# pylint: disable=wrong-import-position
from app.core.config import settings  # noqa: E402
from app.core.firebase import initialize_firebase  # noqa: E402
from app.core.logging import logger  # noqa: E402
from app.db.chroma_client import get_chroma_client, get_embedding_function  # noqa: E402
from app.routers import (  # noqa: E402
    auth_router,
    documents_router,
    query_router,
    support_router,
)

# pylint: enable=wrong-import-position


# --- Lifespan Context Manager (Modern FastAPI Pattern) ---
@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> Any:  # pylint: disable=unused-argument,redefined-outer-name
    """Application lifespan manager - handles startup and shutdown."""
    # STARTUP
    logger.info(f"🚀 Starting {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}")
    logger.info(f"🤖 LLM Model: {settings.LLM_MODEL}")
    logger.info(f"🧠 Embedding Model: {settings.EMBEDDING_MODEL_NAME}")

    # Initialize Firebase (optional — app starts without it, auth endpoints won't register)
    try:
        initialize_firebase()
    except ValueError as e:
        logger.warning(f"⚠️ Firebase not initialized: {e}")
        logger.warning("⚠️ Authentication endpoints will be unavailable")

    # Verify ChromaDB connection and preload models
    try:
        if not os.path.exists(settings.CHROMA_DB_PATH):
            os.makedirs(settings.CHROMA_DB_PATH)
            logger.info(f"📁 Created persistent DB folder: {settings.CHROMA_DB_PATH}")

        client = get_chroma_client()
        logger.info(f"✅ ChromaDB client connected (Version: {client.get_version()})")

        embedding_fn = get_embedding_function()
        embedding_fn.embed_query("test")  # Preload model
        logger.info("✅ Embedding model preloaded successfully.")

    except Exception as e:
        logger.error(f"❌ Critical startup failure: {e}")
        raise

    yield  # Application runs here

    # SHUTDOWN
    logger.info("🔄 Shutting down application...")
    logger.info("✅ Shutdown complete!")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Document Intelligent Hub API",
    lifespan=lifespan,
)

# --- CORS Configuration ---
if os.getenv("ENVIRONMENT") == "production":
    origins = settings.ALLOWED_ORIGINS.split(",")
    logger.info(f"🔒 Production CORS enabled for: {origins}")
else:
    origins = ["*"]
    logger.warning("🔓 Development CORS enabled for all origins ('*')")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Logging Middleware ---
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable[[Request], Any]) -> Any:
    """Log all HTTP requests with timing information."""
    start_time = time.time()
    request_id = request.headers.get("X-Request-ID") or uuid4().hex
    request.state.request_id = request_id
    client_host = request.client.host if request.client else "unknown"
    logger.bind(ACCESS=True).info(
        f"➡️  [{request_id}] {request.method} {request.url.path} - Client: {client_host}"
    )

    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000  # in milliseconds
        status_emoji = "✅" if response.status_code < 400 else "❌"
        logger.bind(ACCESS=True).info(
            f"{status_emoji} [{request_id}] {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Time: {process_time:.2f}ms"
        )
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(
            f"❌ [{request_id}] {request.method} {request.url.path} - Error: {str(e)} - Time: {process_time:.2f}ms"
        )
        # Re-raise the exception to be handled by FastAPI's error handling
        raise


# --- Router Registration ---
app.include_router(documents_router.router)
app.include_router(query_router.router)
app.include_router(support_router.router)

# Conditionally register auth router if Firebase is available
try:
    import firebase_admin

    # Check if Firebase is initialized using public API
    try:
        firebase_admin.get_app()
        app.include_router(auth_router.router)
        logger.info("✅ Authentication endpoints registered.")
    except ValueError:
        logger.warning(
            "⚠️ Authentication endpoints NOT registered - Firebase not initialized."
        )
except (ImportError, AttributeError):
    logger.warning(
        "⚠️ Authentication endpoints NOT registered - 'firebase_admin' not found."
    )


# --- Root Endpoint (Health Check) ---
@app.get("/", tags=["Root"])
def read_root() -> dict[str, str]:
    """Health check endpoint to verify the API is running."""
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME} API!",
        "version": settings.PROJECT_VERSION,
        "status": "healthy",
    }
