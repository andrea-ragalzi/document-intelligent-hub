"""Capability-aware options shared by the application's OpenAI chat clients."""

from dataclasses import dataclass
from typing import Any, TypedDict

from app.config.security_constants import LLM_MAX_RETRIES, LLM_TIMEOUT_SECONDS

@dataclass(frozen=True)
class ModelCapabilities:
    """Known provider constraints for an individual chat model."""

    supports_explicit_temperature: bool = True


MODEL_CAPABILITIES = {
    "gpt-5.6-luna": ModelCapabilities(supports_explicit_temperature=False),
}


class OpenAIClientOptions(TypedDict):
    """Transport options accepted by the synchronous OpenAI client."""

    timeout: int
    max_retries: int


def _temperature_options(model: str, temperature: float) -> dict[str, float]:
    """Return temperature only when the selected model accepts that parameter."""
    capabilities = MODEL_CAPABILITIES.get(model, ModelCapabilities())
    return {"temperature": temperature} if capabilities.supports_explicit_temperature else {}


def chat_model_options(model: str, api_key: Any, temperature: float) -> dict[str, Any]:
    """Build LangChain chat-model options while preserving normal model defaults."""
    return {
        "model": model,
        "api_key": api_key,
        "timeout": LLM_TIMEOUT_SECONDS,
        "max_retries": LLM_MAX_RETRIES,
        **_temperature_options(model, temperature),
    }


def chat_completion_options(model: str, temperature: float) -> dict[str, Any]:
    """Build OpenAI chat-completion options for the selected model capability."""
    return {"model": model, **_temperature_options(model, temperature)}


def openai_client_options() -> OpenAIClientOptions:
    """Configure one bounded, non-retrying transport attempt for OpenAI clients."""
    return {"timeout": LLM_TIMEOUT_SECONDS, "max_retries": LLM_MAX_RETRIES}
