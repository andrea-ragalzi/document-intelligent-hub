"""Capability-aware options shared by the application's OpenAI chat clients."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModelCapabilities:
    """Known provider constraints for an individual chat model."""

    supports_explicit_temperature: bool = True


MODEL_CAPABILITIES = {
    "gpt-5.6-luna": ModelCapabilities(supports_explicit_temperature=False),
}


def _temperature_options(model: str, temperature: float) -> dict[str, float]:
    """Return temperature only when the selected model accepts that parameter."""
    capabilities = MODEL_CAPABILITIES.get(model, ModelCapabilities())
    return {"temperature": temperature} if capabilities.supports_explicit_temperature else {}


def chat_model_options(model: str, api_key: Any, temperature: float) -> dict[str, Any]:
    """Build LangChain chat-model options while preserving normal model defaults."""
    return {"model": model, "api_key": api_key, **_temperature_options(model, temperature)}


def chat_completion_options(model: str, temperature: float) -> dict[str, Any]:
    """Build OpenAI chat-completion options for the selected model capability."""
    return {"model": model, **_temperature_options(model, temperature)}
