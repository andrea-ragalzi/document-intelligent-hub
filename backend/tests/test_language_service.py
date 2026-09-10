"""Unit tests for the local language detection boundary."""

from app.services.language_service import LanguageService


def test_detect_language_returns_iso639_1_code() -> None:
    service = LanguageService()

    assert service.detect_language(
        "Questo testo contiene abbastanza parole italiane per essere riconosciuto."
    ) == "it"


def test_detect_language_falls_back_for_empty_text() -> None:
    service = LanguageService()

    assert service.detect_language("") == "en"


def test_detect_language_handles_short_ambiguous_queries() -> None:
    service = LanguageService()

    assert service.detect_language("Chi è Alice?") == "it"
    assert service.detect_language("Quien eres Dennis Nedry?") == "es"
    assert service.detect_language("?Quien eres Alice?") == "es"
    assert service.detect_language("¿Quién eres Alice?") == "es"
    assert service.detect_language("Who is Alice?") == "en"
    assert service.detect_language("devi rispondere in italiano") == "it"
    assert service.detect_language("Chi e Alice?") == "it"


def test_explicit_response_language_overrides_message_language() -> None:
    service = LanguageService()

    assert service.resolve_response_language("In spagnolo rispondi") == "es"
    assert service.resolve_response_language("devi rispondere in italiano") == "it"


def test_ambiguous_short_query_can_use_a_reliable_recent_language() -> None:
    service = LanguageService()

    recent_language = service.detect_language_reliably("devi rispondere in italiano")

    assert recent_language == "it"
    assert service.resolve_response_language(
        "And him?", recent_user_messages=["Who is Dennis Nedry?"]
    ) == "en"
    assert service.detect_language("Who is Alice?", fallback_language="it") == "en"
