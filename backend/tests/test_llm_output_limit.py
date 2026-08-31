"""Tests that final-answer output is bounded by server-controlled settings."""

from unittest.mock import Mock

from app.core.constants import LLMConstants
from app.schemas.rag_schema import QueryRequest
from app.services.answer_generation_service import AnswerGenerationService


def _service(llm: Mock) -> AnswerGenerationService:
    language_service = Mock()
    language_service.detect_language.return_value = "EN"
    return AnswerGenerationService(
        llm=llm,
        repository=Mock(),
        language_service=language_service,
        translation_service=Mock(),
        query_expansion_service=Mock(),
        reranking_service=Mock(),
    )


def test_final_answer_invocation_has_server_controlled_output_limit() -> None:
    """The final model call always receives the central 1000-token ceiling."""
    llm = Mock()
    llm.invoke.return_value.content = "Grounded answer"

    answer = _service(llm)._invoke_llm_and_translate("prompt", "EN")

    assert answer == "Grounded answer"
    llm.invoke.assert_called_once_with("prompt", max_tokens=LLMConstants.MAX_TOKENS)
    assert LLMConstants.MAX_TOKENS == 1000


def test_client_supplied_output_limit_cannot_override_server_limit() -> None:
    """Unknown request fields do not change the server-side final answer ceiling."""
    request = QueryRequest(query="What is in the document?", max_tokens=999_999)
    llm = Mock()
    llm.invoke.return_value.content = "Grounded answer"

    _service(llm)._invoke_llm_and_translate(request.query, "EN")

    assert "max_tokens" not in request.model_fields_set
    llm.invoke.assert_called_once_with(request.query, max_tokens=LLMConstants.MAX_TOKENS)
