"""Application-facing contract for original document storage."""

from pathlib import Path
from typing import Protocol


class FileStoragePort(Protocol):
    """Operations required to retain private original documents."""

    root_path: Path

    def store(self, user_id: str, filename: str, content: bytes) -> None:
        """Persist an original document for its owner."""

    def get(self, user_id: str, filename: str) -> Path | None:
        """Return the owned document path when available."""

    def delete(self, user_id: str, filename: str) -> bool:
        """Delete one owned original document."""

    def delete_all(self, user_id: str) -> None:
        """Delete all original documents owned by a user."""
