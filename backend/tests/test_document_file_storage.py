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


def test_reupload_replaces_an_original_with_a_new_random_storage_name(tmp_path: Path) -> None:
    """Client filenames must never become stable filesystem paths."""
    storage = DocumentFileStorage(tmp_path)

    storage.store("owner-uid", "report.pdf", b"first version")
    first_file = storage.get("owner-uid", "report.pdf")

    storage.store("owner-uid", "report.pdf", b"second version")
    second_file = storage.get("owner-uid", "report.pdf")

    assert first_file is not None
    assert second_file is not None
    assert second_file != first_file
    

def test_delete_all_removes_only_the_selected_users_originals(tmp_path: Path) -> None:
    """Bulk deletion must preserve originals owned by other users."""
    storage = DocumentFileStorage(tmp_path)
    storage.store("owner-uid", "first.pdf", b"first owner file")
    storage.store("owner-uid", "second.pdf", b"second owner file")
    storage.store("other-uid", "first.pdf", b"other owner's file")

    storage.delete_all("owner-uid")

    assert storage.get("owner-uid", "first.pdf") is None
    assert storage.get("owner-uid", "second.pdf") is None
    other_file = storage.get("other-uid", "first.pdf")
    assert other_file is not None
    assert other_file.read_bytes() == b"other owner's file"
