"""FastAPI main application entry point with lifespan management, middleware, and routing."""

import os
import time
from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

# Load one ignored local configuration file. Real process variables (tests,
# Docker, and Railway) remain authoritative because local values never
# overwrite them.
env_path = Path(__file__).parent / ".env.local"
load_dotenv(dotenv_path=env_path, override=False)

# Now, import other modules (after load_dotenv to load env vars first)
# pylint: disable=wrong-import-position
from app.core.config import settings  # noqa: E402
from app.core.firebase import initialize_firebase  # noqa: E402
from app.core.logging import logger  # noqa: E402
from app.config.security_constants import (  # noqa: E402
    MAX_BUG_REPORT_REQUEST_SIZE,
    MAX_FEEDBACK_REQUEST_SIZE,
)
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
    except ValueError:
        logger.warning("Firebase not initialized")
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

    except Exception as exc:
        logger.error("Critical startup failure | Type: {}", type(exc).__name__)
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


class UploadBodyLimitMiddleware:
    """Bound multipart upload bodies before FastAPI starts parsing them."""

    _limits = {
        "/rag/report-bug/": MAX_BUG_REPORT_REQUEST_SIZE,
    }

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        limit = self._limits.get(scope["path"])
        if limit is None:
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        content_length = headers.get(b"content-length")
        if content_length is not None:
            try:
                declared_size = int(content_length)
            except ValueError:
                await self._send_error(scope, receive, send, 400, "Invalid upload payload.")
                return
            if declared_size < 0:
                await self._send_error(scope, receive, send, 400, "Invalid upload payload.")
                return
            if declared_size > limit:
                await self._send_error(scope, receive, send, 413, "Upload payload is too large.")
                return

        buffered_chunks: list[bytes] = []
        total_size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                break
            if message["type"] != "http.request":
                continue

            body = message.get("body", b"")
            total_size += len(body)
            if total_size > limit:
                await self._send_error(scope, receive, send, 413, "Upload payload is too large.")
                return
            buffered_chunks.append(body)
            if not message.get("more_body", False):
                break

        next_chunk = 0

        async def replay_receive() -> dict[str, Any]:
            nonlocal next_chunk
            if next_chunk >= len(buffered_chunks):
                return {"type": "http.disconnect"}
            body = buffered_chunks[next_chunk]
            next_chunk += 1
            return {
                "type": "http.request",
                "body": body,
                "more_body": next_chunk < len(buffered_chunks),
            }

        await self.app(scope, replay_receive, send)

    @staticmethod
    async def _send_error(
        scope: dict[str, Any], receive: Any, send: Any, status_code: int, detail: str
    ) -> None:
        response = JSONResponse(status_code=status_code, content={"detail": detail})
        await response(scope, receive, send)

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

# Accept forwarded client addresses only from explicitly trusted deployment
# proxies. The invitation limiter relies on request.client.host after this.
app.add_middleware(
    ProxyHeadersMiddleware,
    trusted_hosts=[host.strip() for host in settings.TRUSTED_PROXY_IPS.split(",") if host.strip()],
)
app.add_middleware(UploadBodyLimitMiddleware)


@app.middleware("http")
async def reject_oversized_support_payloads(request: Request, call_next: Callable[[Request], Any]) -> Any:
    """Reject known oversized support bodies before multipart parsing or endpoint work."""
    limits = {
        "/rag/report-bug/": MAX_BUG_REPORT_REQUEST_SIZE,
        "/rag/feedback/": MAX_FEEDBACK_REQUEST_SIZE,
    }
    limit = limits.get(request.url.path)
    content_length = request.headers.get("content-length")
    if limit is not None and content_length is not None:
        try:
            if int(content_length) > limit:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "Submission payload is too large."},
                )
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid submission payload."},
            )
    return await call_next(request)


# --- Logging Middleware ---
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable[[Request], Any]) -> Any:
    """Log all HTTP requests with timing information."""
    start_time = time.time()
    request_id = request.headers.get("X-Request-ID") or uuid4().hex
    request.state.request_id = request_id
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000  # in milliseconds
        logger.bind(ACCESS=True).info(
            "Request completed | ID: {} | Method: {} | Path: {} | Status: {} | Duration: {:.2f}ms",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            process_time,
        )
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as exc:
        process_time = (time.time() - start_time) * 1000
        logger.error(
            "Request failed | ID: {} | Method: {} | Path: {} | Type: {} | Duration: {:.2f}ms",
            request_id,
            request.method,
            request.url.path,
            type(exc).__name__,
            process_time,
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
