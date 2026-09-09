"""Tests for provider-model capability aware LLM request construction."""

from app.core.llm_configuration import chat_completion_options, chat_model_options


def test_luna_omits_explicit_temperature_for_chat_clients() -> None:
    options = chat_model_options("gpt-5.6-luna", "secret", temperature=0.0)

    assert options == {"model": "gpt-5.6-luna", "api_key": "secret"}
    assert chat_completion_options("gpt-5.6-luna", temperature=0.8) == {
        "model": "gpt-5.6-luna"
    }


def test_default_development_model_preserves_explicit_temperature() -> None:
    options = chat_model_options("gpt-4o-mini", "secret", temperature=0.8)

    assert options["temperature"] == 0.8
    assert chat_completion_options("gpt-4o-mini", temperature=0.0)["temperature"] == 0.0
