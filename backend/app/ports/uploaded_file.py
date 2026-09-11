"""Application-facing contract for an uploaded document stream."""

from typing import Protocol


class UploadedFilePort(Protocol):
    """Minimal upload interface required by document ingestion."""

    filename: str | None

    async def read(self) -> bytes:
        """Read the uploaded document bytes."""
