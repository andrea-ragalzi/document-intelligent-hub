"""Chroma dependency construction should reuse the process-local client and collection."""

from unittest.mock import Mock, patch

from app.db import chroma_client


def test_chroma_client_and_collection_are_reused(monkeypatch) -> None:
    """Avoid reconnecting/recreating collection metadata for every query."""
    client = Mock()
    collection = Mock()
    client.get_or_create_collection.return_value = collection
    monkeypatch.setattr(chroma_client, "_chroma_client_singleton", None)
    monkeypatch.setattr(chroma_client, "_chroma_collection_singleton", None)

    with patch("app.db.chroma_client.PersistentClient", return_value=client) as create_client:
        first_client = chroma_client.get_chroma_client()
        second_client = chroma_client.get_chroma_client()
        first_collection = chroma_client.get_chroma_collection(first_client)
        second_collection = chroma_client.get_chroma_collection(second_client)

    assert first_client is second_client is client
    assert first_collection is second_collection is collection
    create_client.assert_called_once()
    client.get_or_create_collection.assert_called_once()
