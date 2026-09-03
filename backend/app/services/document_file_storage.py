"""Private filesystem storage for original uploaded documents."""

import hashlib
import json
import os
import tempfile
import uuid
from pathlib import Path

from app.core.config import settings
from app.core.security import sanitize_filename


class DocumentFileStorage:
    """Persist originals below an opaque, per-user directory."""

    _MANIFEST_FILENAME = ".document-originals.json"

    def __init__(self, root_path: str | Path) -> None:
        self.root_path = Path(root_path).resolve()

    @staticmethod
    def _digest(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _user_directory(self, user_id: str) -> Path:
        """Build a trusted, opaque directory for an authenticated user."""
        user_directory = (self.root_path / self._digest(user_id)).resolve()
        if user_directory.parent != self.root_path:
            raise ValueError("Invalid document storage directory")
        return user_directory

    @staticmethod
    def _document_key(filename: str) -> str:
        """Use the sanitized display name only as a private manifest key."""
        return sanitize_filename(filename)

    @staticmethod
    def _is_storage_name(storage_name: object) -> bool:
        """Accept only server-generated UUIDv4 PDF names from a manifest."""
        if not isinstance(storage_name, str) or not storage_name.endswith(".pdf"):
            return False
        try:
            return uuid.UUID(storage_name.removesuffix(".pdf")).version == 4
        except ValueError:
            return False

    def _storage_path(self, user_directory: Path, storage_name: object) -> Path | None:
        """Resolve a server-generated filename and enforce directory containment."""
        if not self._is_storage_name(storage_name):
            return None
        trusted_directory = os.path.realpath(user_directory)
        candidate = os.path.realpath(os.path.join(trusted_directory, str(storage_name)))
        trusted_prefix = f"{trusted_directory}{os.sep}"
        if not candidate.startswith(trusted_prefix):
            return None
        return Path(candidate)

    def _manifest_path(self, user_directory: Path) -> Path:
        return user_directory / self._MANIFEST_FILENAME

    def _read_manifest(self, user_directory: Path) -> dict[str, str]:
        """Read only valid server-generated references from a private manifest."""
        manifest_path = self._manifest_path(user_directory)
        if not manifest_path.is_file():
            return {}
        try:
            raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(raw_manifest, dict):
            return {}
        return {
            document_key: storage_name
            for document_key, storage_name in raw_manifest.items()
            if isinstance(document_key, str) and self._is_storage_name(storage_name)
        }

    @staticmethod
    def _write_bytes(destination: Path, content: bytes) -> None:
        """Atomically write a private file within an already-trusted directory."""
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

    def _write_manifest(self, user_directory: Path, manifest: dict[str, str]) -> None:
        serialized_manifest = json.dumps(manifest, separators=(",", ":"), sort_keys=True)
        self._write_bytes(
            self._manifest_path(user_directory), serialized_manifest.encode("utf-8")
        )

    def store(self, user_id: str, filename: str, content: bytes) -> None:
        """Atomically persist an already-validated original document."""
        user_directory = self._user_directory(user_id)
        user_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        document_key = self._document_key(filename)
        storage_name = f"{uuid.uuid4()}.pdf"
        destination = self._storage_path(user_directory, storage_name)
        if destination is None:
            raise ValueError("Unable to create document storage path")

        try:
            self._write_bytes(destination, content)
            manifest = self._read_manifest(user_directory)
            previous_file = self._storage_path(
                user_directory, manifest.get(document_key)
            )
            manifest[document_key] = storage_name
            self._write_manifest(user_directory, manifest)
        except Exception:
            if destination.exists():
                destination.unlink()
            raise

        if previous_file is not None and previous_file.is_file():
            previous_file.unlink()

    def get(self, user_id: str, filename: str) -> Path | None:
        """Return an owned original's path when it is available."""
        user_directory = self._user_directory(user_id)
        storage_name = self._read_manifest(user_directory).get(
            self._document_key(filename)
        )
        candidate = self._storage_path(user_directory, storage_name)
        if candidate is None:
            return None
        return candidate if candidate.is_file() else None

    def delete(self, user_id: str, filename: str) -> bool:
        """Delete one owned original without affecting other users."""
        user_directory = self._user_directory(user_id)
        document_key = self._document_key(filename)
        manifest = self._read_manifest(user_directory)
        candidate = self._storage_path(user_directory, manifest.get(document_key))
        if candidate is None or not candidate.is_file():
            return False
        candidate.unlink()
        del manifest[document_key]
        self._write_manifest(user_directory, manifest)
        return True

    def delete_all(self, user_id: str) -> None:
        """Delete every original belonging to one authenticated user."""
        user_directory = self._user_directory(user_id)
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
