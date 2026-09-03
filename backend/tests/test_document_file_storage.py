"""Tests for private original-document storage."""

from pathlib import Path

from app.services.document_file_storage import DocumentFileStorage


def test_stores_and_reads_original_only_for_its_owner(tmp_path: Path) -> None:
    """A storage key must not be shared between authenticated users."""
    storage = DocumentFileStorage(tmp_path)
    content = b"%PDF-1.4 private document"

    storage.store("owner-uid", "report.pdf", content)

    stored_file = storage.get("owner-uid", "report.pdf")
    assert stored_file is not None
    assert stored_file.read_bytes() == content
    assert storage.get("other-uid", "report.pdf") is None


def test_deleting_original_removes_only_that_users_file(tmp_path: Path) -> None:
    """Deleting an owned document must not remove a same-named file for another user."""
    storage = DocumentFileStorage(tmp_path)
    storage.store("owner-uid", "shared.pdf", b"owner")
    storage.store("other-uid", "shared.pdf", b"other")

    assert storage.delete("owner-uid", "shared.pdf") is True
    assert storage.get("owner-uid", "shared.pdf") is None
    other_file = storage.get("other-uid", "shared.pdf")
    assert other_file is not None
    assert other_file.read_bytes() == b"other"
