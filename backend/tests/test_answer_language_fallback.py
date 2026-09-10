"""Regression tests for resolved response language in RAG fallbacks."""

from unittest.mock import Mock

import pytest

from app.repositories.vector_store_repository import VectorStoreRepository
from app.schemas.rag_schema import AnswerWithEvidence
from app.services.answer_generation_service import AnswerGenerationService


def _service() -> tuple[AnswerGenerationService, Mock]:
    repository = Mock(spec=VectorStoreRepository)
    repository.get_retriever.return_value.invoke.return_value = []
    repository.lexical_candidate_search.return_value = []
    language_service = Mock()
    service_llm = Mock()
    service_llm.with_structured_output.return_value.invoke.side_effect = [
        AnswerWithEvidence(answer="English fallback", evidence_ids=[]),
        AnswerWithEvidence(answer="Spanish fallback", evidence_ids=[]),
        AnswerWithEvidence(answer="Italian fallback", evidence_ids=[]),
    ]
    reranking_service = Mock()
    reranking_service.rerank_documents.return_value = []
    return (
        AnswerGenerationService(
            llm=service_llm,
            repository=repository,
            language_service=language_service,
            translation_service=Mock(translate_query_to_language=lambda query, _target: query),
            query_expansion_service=Mock(),
            reranking_service=reranking_service,
        ),
        language_service,
    )


def test_no_document_fallback_uses_current_message_language_rules() -> None:
    service, language_service = _service()
    service.query_expansion_service.generate_alternative_queries.return_value = []

    english_answer, _ = service.generate_answer(
        query="What is the capital of Australia?", user_id="user", query_language="en"
    )
    spanish_answer, _ = service.generate_answer(
        query="Esta muerto?", user_id="user", query_language="es"
    )
    italian_answer, _ = service.generate_answer(
        query="Chi è Alice?", user_id="user", query_language="it"
    )

    assert english_answer == "English fallback"
    assert spanish_answer == "Spanish fallback"
    assert italian_answer == "Italian fallback"
    prompts = [call.args[0] for call in service.llm.with_structured_output.return_value.invoke.call_args_list]
    assert all("LANG:" in prompt for prompt in prompts)
    assert all("Q:" in prompt for prompt in prompts)
    assert all("C:" in prompt for prompt in prompts)
    assert all("insufficient" in prompt.lower() for prompt in prompts)
    language_service.translate_answer_back.assert_not_called()


@pytest.mark.parametrize(
    ("current_message", "history", "output_language"),
    [
        ("Chi è Alice?", [], None),
        ("Who is Ellie Sattler?", ["Rispondi in italiano."], None),
        ("¿Quién es Ellie Sattler?", ["Rispondi in italiano."], None),
        ("Chi è Ellie Sattler?", ["Responde en español."], None),
        ("Chi è Alice? Rispondi in spagnolo.", [], None),
        ("And him?", ["¿Quién es Dennis Nedry?"], None),
        ("Who is Ellie Sattler?", [], None),
        ("¿Quién es Ellie Sattler?", [], None),
        ("Chi è Ellie Sattler?", [], None),
        ("¿Quién es Alice?", ["Italian source document"], None),
    ],
)
def test_answer_prompt_uses_resolved_language_over_history_or_context(
    current_message: str, history: list[str], output_language: str | None
) -> None:
    service = AnswerGenerationService.__new__(AnswerGenerationService)
    history_text = "\n".join(f"U|{message}" for message in history)

    prompt = service._build_final_prompt(
        "English source document", history_text, current_message, output_language or "en"
    )

    assert f"Q:\n{current_message}" in prompt
    if history:
        assert "H:" in prompt
        assert history[0] in prompt
    else:
        assert "\n\nH:" not in prompt
    assert f"LANG:{output_language or 'en'}" in prompt
    assert "LANG is authoritative" in prompt
    assert "H and C must never override LANG" in prompt
    assert "insufficient-information responses" in prompt
