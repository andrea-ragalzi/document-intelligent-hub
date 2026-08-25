# Multi-stage Dockerfile for FastAPI Backend
# Stage 1: Builder - Install dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

ARG PYTORCH_CPU_INDEX_URL=https://download.pytorch.org/whl/cpu
ARG TORCH_VERSION=2.10.0+cpu
ARG TORCHVISION_VERSION=0.25.0+cpu
ARG FIREBASE_ADMIN_VERSION=7.1.0
ARG GOOGLE_CLOUD_FIRESTORE_VERSION=2.21.0
ARG GOOGLE_API_CORE_VERSION=2.28.1

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files and minimal app structure for editable install
COPY pyproject.toml poetry.lock README.md ./
COPY app/__init__.py app/__init__.py
COPY scripts/export_lock_constraints.py scripts/export_lock_constraints.py

# Convert Poetry's lock into pip constraints so the deployment build cannot
# silently resolve different transitive versions from those tested locally.
RUN python scripts/export_lock_constraints.py

# Install the CPU-only PyTorch wheels before the application dependencies.
# The application explicitly runs all-MiniLM-L6-v2 on CPU; using PyPI's Linux
# wheels here would otherwise pull the CUDA runtime into the deployment image.
# Keep Firebase/Firestore aligned with the working Poetry lock. Newer Firestore
# clients encode `(default)` in this project's database resource path.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --only-binary=:all: \
        --constraint /tmp/constraints.txt \
        --extra-index-url "${PYTORCH_CPU_INDEX_URL}" \
        "torch==${TORCH_VERSION}" \
        "torchvision==${TORCHVISION_VERSION}" && \
    pip install --no-cache-dir --only-binary=:all: \
        --constraint /tmp/constraints.txt \
        "firebase-admin==${FIREBASE_ADMIN_VERSION}" \
        "google-api-core==${GOOGLE_API_CORE_VERSION}" \
        "google-cloud-firestore==${GOOGLE_CLOUD_FIRESTORE_VERSION}"

# The application itself is trusted local source and some locked dependencies
# are source-only on PyPI, so a universal binary-only install is not possible.
# Every third-party resolution is nevertheless constrained by poetry.lock.
RUN pip install --no-cache-dir \
        --constraint /tmp/constraints.txt \
        --only-binary=:all: \
        --no-binary=antlr4-python3-runtime,langdetect,pypika \
        -e . && \
    pip check

# Stage 2: Runtime - Create minimal runtime image
FROM python:3.12-slim

WORKDIR /app

# Install only the native libraries used by the current CPU embedding and PDF
# parsing paths (UnstructuredPDFLoader with Poppler/Tesseract/libmagic).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libgomp1 \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create directory for ChromaDB persistence
RUN mkdir -p chroma_db && \
    # Create non-root user for security
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Environment variables (can be overridden by docker-compose or deployment platform)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Health check (uses Railway's injected PORT when present)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os, requests; requests.get(f'http://localhost:{os.getenv(\"PORT\", \"8000\")}/', timeout=2).raise_for_status()"

# Run the application. Shell expansion is required for Railway's dynamic port;
# local containers retain port 8000 when PORT is not supplied.
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port \"${PORT:-8000}\""]
