"""Private filesystem storage for original uploaded documents."""

import hashlib
import os
import tempfile
from pathlib import Path

from app.core.config import settings
from app.core.security import sanitize_filename


class DocumentFileStorage:
    """Persist originals below an opaque, per-user directory."""

    def __init__(self, root_path: str | Path) -> None:
        self.root_path = Path(root_path).resolve()

    @staticmethod
    def _digest(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _path_for(self, user_id: str, filename: str) -> Path:
        safe_filename = sanitize_filename(filename)
        user_directory = self.root_path / self._digest(user_id)
        # The generated storage name keeps client filenames out of paths while
        # retaining the PDF extension for a correct media type on download.
        return user_directory / f"{self._digest(safe_filename)}.pdf"

    def store(self, user_id: str, filename: str, content: bytes) -> None:
        """Atomically persist an already-validated original document."""
        destination = self._path_for(user_id, filename)
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        descriptor, temporary_path = tempfile.mkstemp(dir=destination.parent, prefix=".upload-")
        try:
            with os.fdopen(descriptor, "wb") as temporary_file:
                temporary_file.write(content)
            os.replace(temporary_path, destination)
            os.chmod(destination, 0o600)
        except Exception:
            if os.path.exists(temporary_path):
                os.unlink(temporary_path)
            raise

    def get(self, user_id: str, filename: str) -> Path | None:
        """Return an owned original's path when it is available."""
        candidate = self._path_for(user_id, filename)
        return candidate if candidate.is_file() else None

    def delete(self, user_id: str, filename: str) -> bool:
        """Delete one owned original without affecting other users."""
        candidate = self._path_for(user_id, filename)
        if not candidate.is_file():
            return False
        candidate.unlink()
        return True

    def delete_all(self, user_id: str) -> None:
        """Delete every original belonging to one authenticated user."""
        user_directory = self.root_path / self._digest(user_id)
        if not user_directory.is_dir():
            return
        for candidate in user_directory.iterdir():
            if candidate.is_file():
                candidate.unlink()
        user_directory.rmdir()


_document_file_storage: DocumentFileStorage | None = None


def get_document_file_storage() -> DocumentFileStorage:
    """Get the process-local storage service configured for this deployment."""
    global _document_file_storage
    if _document_file_storage is None:
        _document_file_storage = DocumentFileStorage(settings.DOCUMENT_STORAGE_PATH)
    return _document_file_storage
