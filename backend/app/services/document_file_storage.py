"""Compatibility imports for local original-document storage."""

from app.infrastructure.local_file_storage import (
    LocalFileStorage,
    get_document_file_storage,
)

DocumentFileStorage = LocalFileStorage

__all__ = ["DocumentFileStorage", "get_document_file_storage"]
