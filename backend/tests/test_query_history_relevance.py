"""Regression coverage for contextual history use in RAG queries."""

from unittest.mock import Mock

from app.schemas.rag_schema import ConversationMessage
from app.services.query_processing_service import QueryProcessingService
from app.services.rag_orchestrator_service import RAGService


def _service() -> QueryProcessingService:
    return QueryProcessingService(llm=Mock(), query_gen_llm=Mock())


def test_self_contained_named_question_does_not_use_unrelated_history() -> None:
    history = [
        ConversationMessage(role="user", content="Quali regole non devi mai infrangere?"),
        ConversationMessage(role="assistant", content="Previous rules answer"),
    ]

    assert not _service().requires_conversation_context("Chi e Alice?", history)


def test_short_pronoun_follow_up_keeps_conversation_context() -> None:
    history = [
        ConversationMessage(role="user", content="Quien eres Dennis Nedry?"),
        ConversationMessage(role="assistant", content="Dennis Nedry is a character."),
    ]

    assert _service().requires_conversation_context("Esta muerto?", history)


def test_orchestrator_passes_history_only_for_contextual_turns() -> None:
    history = [
        ConversationMessage(role="user", content="Quali regole non devi mai infrangere?"),
        ConversationMessage(role="assistant", content="Previous rules answer"),
    ]
    service = RAGService.__new__(RAGService)
    service.language_service = Mock()
    service.language_service.resolve_response_language.return_value = "it"
    service.query_processing_service = Mock()
    service.query_processing_service.requires_conversation_context.return_value = False
    service.query_processing_service.reformulate_query.return_value = "Chi e Alice?"
    service.query_processing_service.classify_query.return_value = "GENERAL_SEARCH"
    service.answer_generation_service = Mock()
    service.answer_generation_service.generate_answer.return_value = ("Alice answer", [])

    service.answer_query("Chi e Alice?", "user", history)

    assert service.query_processing_service.reformulate_query.call_args.args[1] == []
    assert service.answer_generation_service.generate_answer.call_args.kwargs[
        "conversation_history"
    ] == []
    assert service.answer_generation_service.generate_answer.call_args.kwargs[
        "current_user_message"
    ] == "Chi e Alice?"
