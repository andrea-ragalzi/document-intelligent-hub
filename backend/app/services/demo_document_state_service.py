"""Persist the user's explicit choice to remove the starter document."""

from firebase_admin import firestore


class DemoDocumentStateService:
    """Store starter-document dismissal alongside the user's existing usage state."""

    def _state(self, user_id: str) -> dict[str, object]:
        snapshot = firestore.client().collection("user_usage").document(user_id).get()
        return snapshot.to_dict() or {} if snapshot.exists else {}

    def is_deleted(self, user_id: str) -> bool:
        return bool(self._state(user_id).get("demo_document_deleted"))

    def mark_deleted(self, user_id: str) -> None:
        firestore.client().collection("user_usage").document(user_id).set(
            {"demo_document_deleted": True}, merge=True
        )
