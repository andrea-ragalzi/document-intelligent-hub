"""
Security Constants - File Upload and Rate Limiting Configuration

Centralized security-related constants to avoid magic numbers.
"""

# === FILE UPLOAD LIMITS ===

# Maximum size for PDF document uploads (50MB)
# Used in: documents_router.py (upload_document)
MAX_DOCUMENT_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB in bytes

# Maximum size for bug report attachments (10MB)
# Used in: support_router.py (report_bug)
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10MB in bytes

# Chunk size for streaming file validation (8KB)
FILE_READ_CHUNK_SIZE = 8192  # 8KB

# === FILE TYPE RESTRICTIONS ===

# Allowed document file extensions
ALLOWED_DOCUMENT_EXTENSIONS = [".pdf"]

# Allowed attachment file types for bug reports
ALLOWED_ATTACHMENT_MIME_TYPES = [
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
    "video/mp4",
    "video/webm",
    "application/pdf",
    "application/zip",
    "application/x-zip-compressed",
]

# === QUERY LIMITS ===

# Maximum queries per day for UNLIMITED tier
# Used to prevent abuse even on unlimited plans
UNLIMITED_TIER_MAX_QUERIES = 9999

# === DELETION CONFIRMATION ===

# Required confirmation string for bulk delete operations
DELETE_ALL_CONFIRMATION = "DELETE ALL"

# === LOGGING ===

# Maximum log file size before rotation (100MB)
MAX_LOG_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Number of log files to keep
LOG_FILE_BACKUP_COUNT = 5

# === RATE LIMITING (for future implementation) ===

# Maximum bug reports per hour per IP
BUG_REPORT_RATE_LIMIT = "5/hour"

# Maximum feedback submissions per hour per IP
FEEDBACK_RATE_LIMIT = "10/hour"

# Maximum document uploads per hour per user
UPLOAD_RATE_LIMIT = "20/hour"

# === FILENAME CONSTRAINTS ===

# Maximum filename length (filesystem limit)
MAX_FILENAME_LENGTH = 255

# === TIMEOUT SETTINGS ===

# Maximum time to wait for LLM response (seconds)
LLM_TIMEOUT_SECONDS = 60

# Maximum time to wait for PDF parsing (seconds)
PDF_PARSING_TIMEOUT_SECONDS = 30
