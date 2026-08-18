"""Critical deterministic coverage for the RAG happy-path orchestration."""

from unittest.mock import Mock, call, patch

from langchain_core.documents import Document

from app.core.constants import QueryConstants
from app.repositories.vector_store_repository import VectorStoreRepository
from app.services.answer_generation_service import AnswerGenerationService
from app.services.language_service import LanguageService
from app.services.query_expansion_service import QueryExpansionService
from app.services.rag_orchestrator_service import RAGService
from app.services.reranking_service import RerankingService
from app.services.translation_service import TranslationService


def test_authenticated_rag_happy_path_is_scoped_and_returns_sources() -> None:
    """Protect the flow from reformulation through grounded answer attribution."""
    query_processing = Mock()
    query_processing.reformulate_query.return_value = (
        "What changed in the retention policy?"
    )
    query_processing.classify_query.return_value = "POLICY_CHECK"

    repository = Mock(spec=VectorStoreRepository)
    retriever = Mock()
    retrieved_documents = [
        Document(
            page_content="Records are retained for seven years.",
            metadata={
                "source": "verified-user",
                "original_filename": "retention-policy.pdf",
                "chapter_title": "Retention",
            },
        ),
        Document(
            page_content="The updated policy applies from January.",
            metadata={
                "source": "verified-user",
                "original_filename": "policy-update.pdf",
                "chapter_title": "Effective date",
            },
        ),
    ]
    retriever.invoke.return_value = retrieved_documents
    repository.get_retriever.return_value = retriever

    query_expansion = Mock(spec=QueryExpansionService)
    query_expansion.generate_alternative_queries.return_value = [
        "retention policy changes"
    ]
    reranker = Mock(spec=RerankingService)
    reranker.rerank_documents.side_effect = lambda **kwargs: kwargs["documents"]

    llm = Mock()
    llm_response = Mock()
    llm_response.content = "Records are retained for seven years."
    llm.invoke.return_value = llm_response

    language_service = Mock(spec=LanguageService)
    language_service.detect_language.return_value = "EN"
    translation_service = Mock(spec=TranslationService)

    answer_generation = AnswerGenerationService(
        llm=llm,
        repository=repository,
        language_service=language_service,
        translation_service=translation_service,
        query_expansion_service=query_expansion,
        reranking_service=reranker,
    )
    rag_service = RAGService.__new__(RAGService)
    rag_service.query_processing_service = query_processing
    rag_service.answer_generation_service = answer_generation

    with patch("socket.socket.connect") as network_connect:
        answer, sources = rag_service.answer_query(
            query="What changed?",
            user_id="verified-user",
            include_files=["retention-policy.pdf", "policy-update.pdf"],
            exclude_files=["draft.pdf"],
        )

    network_connect.assert_not_called()

    assert answer == (
        "Records are retained for seven years.\n\n"
        "📚 Sources:\n- policy-update.pdf\n- retention-policy.pdf"
    )
    assert sources == ["policy-update.pdf", "retention-policy.pdf"]

    query_processing.reformulate_query.assert_called_once_with("What changed?", [])
    query_processing.classify_query.assert_called_once_with(
        "What changed in the retention policy?"
    )
    query_expansion.generate_alternative_queries.assert_called_once_with(
        "What changed in the retention policy?"
    )
    repository.get_retriever.assert_called_once_with(
        user_id="verified-user",
        k=QueryConstants.BASE_RETRIEVAL_K,
        include_files=["retention-policy.pdf", "policy-update.pdf"],
        exclude_files=["draft.pdf"],
    )
    assert retriever.invoke.call_args_list == [
        call("What changed in the retention policy?"),
        call("retention policy changes"),
    ]

    rerank_call = reranker.rerank_documents.call_args.kwargs
    assert rerank_call["documents"] == retrieved_documents
    assert rerank_call["original_query"] == "What changed in the retention policy?"
    assert rerank_call["alternative_queries"] == ["retention policy changes"]
    assert rerank_call["top_n"] == QueryConstants.FINAL_RETRIEVAL_K

    llm.invoke.assert_called_once()
    prompt = llm.invoke.call_args.args[0]
    assert "Records are retained for seven years." in prompt
    assert "The updated policy applies from January." in prompt
    assert "retention-policy.pdf" in prompt
    assert "policy-update.pdf" in prompt
    assert "What changed in the retention policy?" in prompt
    translation_service.translate_query_to_language.assert_not_called()
    translation_service.translate_answer_back.assert_not_called()
