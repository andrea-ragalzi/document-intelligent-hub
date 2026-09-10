"""Deterministic regression tests for retrieval candidate selection."""

from unittest.mock import Mock

from langchain_core.documents import Document

from app.services.answer_generation_service import AnswerGenerationService
from app.services.query_expansion_service import QueryExpansionService
from app.services.reranking_service import RerankingService


def _document(content: str, filename: str, page: int = 1) -> Document:
    return Document(
        page_content=content,
        metadata={"original_filename": filename, "page_number": page},
    )


def _answer_service() -> AnswerGenerationService:
    return AnswerGenerationService(
        llm=Mock(),
        repository=Mock(),
        language_service=Mock(),
        translation_service=Mock(),
        query_expansion_service=Mock(),
        reranking_service=Mock(),
    )


def test_simple_query_keeps_single_query_expansion_path() -> None:
    service = _answer_service()
    service.query_expansion_service.generate_alternative_queries.return_value = []
    service.repository.lexical_candidate_search.return_value = []
    service.repository.get_retriever.return_value.invoke.return_value = [
        _document("Alice follows the Cat.", "Alice.pdf")
    ]
    service.reranking_service.rerank_documents.return_value = []

    service._retrieve_and_rerank(
        "What happens when the Cat disappears?",
        "What happens when the Cat disappears?",
        "user",
        include_files=None,
        exclude_files=None,
    )

    service.query_expansion_service.generate_alternative_queries.assert_called_once()
    service.repository.get_retriever.assert_called_once()
    assert service.repository.get_retriever.call_args.kwargs["k"] == 12


def test_compound_query_uses_bounded_queries_and_deduplicates_candidates() -> None:
    service = _answer_service()
    duplicate_a = _document("Alice follows the Cat.", "Alice.pdf")
    duplicate_b = _document("Alice follows the Cat.", "Alice.pdf")
    second = _document("The Cat disappears.", "Alice.pdf", page=2)
    service.repository.get_retriever.return_value.invoke.side_effect = [
        [duplicate_a, second],
        [duplicate_b],
        [second],
    ]
    service.repository.lexical_candidate_search.return_value = []
    service.reranking_service.rerank_documents.return_value = []

    service._retrieve_and_rerank(
        "Who is Alice and what happens when the Cat disappears?",
        "Who is Alice and what happens when the Cat disappears?",
        "user",
        include_files=None,
        exclude_files=None,
        retrieval_queries=["Who is Alice?", "What happens when the Cat disappears?"],
    )

    service.query_expansion_service.generate_alternative_queries.assert_not_called()
    assert service.repository.get_retriever.call_args.kwargs["k"] == 6
    rerank_kwargs = service.reranking_service.rerank_documents.call_args.kwargs
    assert len(rerank_kwargs["documents"]) == 2
    assert rerank_kwargs["required_query_groups"] == [
        "Who is Alice?",
        "What happens when the Cat disappears?",
    ]


def test_invalid_compound_output_falls_back_to_simple_retrieval() -> None:
    service = _answer_service()

    assert service._validated_compound_queries(None) == []
    assert service._validated_compound_queries(["only one"]) == []
    assert service._validated_compound_queries(["a", "b", "c"]) == []
    assert service._validated_compound_queries(["a", 1]) == []


def test_inspection_result_outranks_related_vehicle_material() -> None:
    query = "Quale veicolo T-CAR ha superato il test di override manuale e quali invece lo hanno fallito?"
    documents = [
        _document(
            "T-CAR V.3 usa un codice di override manuale programmato ogni dodici ore.",
            "Specifiche Veicoli Tour.pdf",
        ),
        _document(
            "Il malfunzionamento dell'override ha causato un rischio operativo per i veicoli.",
            "Memorandum Anomalie.pdf",
        ),
        _document(
            "Test override manuale: T-CAR 1 superato; T-CAR 2, 3 e 4 fallito.",
            "Rapporto Ispezione Veicoli Tour.pdf",
        ),
    ]

    ranked = RerankingService().rerank_documents(documents, query, [], top_n=3)

    assert ranked[0].metadata["original_filename"] == "Rapporto Ispezione Veicoli Tour.pdf"


def test_exact_identifier_outranks_generic_emergency_chunk() -> None:
    documents = [
        _document(
            "La procedura di emergenza Lockout sospende alcuni sistemi del parco.",
            "Piano di Contingenza.pdf",
        ),
        _document(
            "SRI_LOCKOUT_F1 avvia la fase 1, blocca i veicoli e reindirizza l'energia.",
            "Manuale Sistema V4.1.pdf",
        ),
    ]

    ranked = RerankingService().rerank_documents(
        documents, "Che cosa fa esattamente il comando SRI_LOCKOUT_F1?", [], top_n=2
    )

    assert ranked[0].metadata["original_filename"] == "Manuale Sistema V4.1.pdf"


def test_compound_brachiosaurus_question_keeps_evidence_for_both_facts() -> None:
    query = "Qual è il consumo giornaliero del Brachiosauro e quale caratteristica genetica unica presenta?"
    documents = [
        _document("Il Brachiosauro è una specie erbivora.", "Report Generale.pdf"),
        _document(
            "Dieta: consumo giornaliero stimato di 200 kg di vegetazione.",
            "Rapporto Genetico BRAC (Brachiosauro).pdf",
        ),
        _document(
            "Unicità genetica: la colorazione cutanea cambia con la temperatura corporea.",
            "Rapporto Genetico BRAC (Brachiosauro).pdf",
        ),
        _document("Il DNA del parco è proprietà di InGen.", "Contratto Legale.pdf"),
    ]

    ranked = RerankingService().rerank_documents(
        documents,
        query,
        _answer_service()._split_compound_retrieval_queries(query),
        top_n=2,
        required_query_groups=_answer_service()._split_compound_retrieval_queries(query),
    )

    selected_text = " ".join(document.page_content for document in ranked).lower()
    assert "200 kg" in selected_text
    assert "colorazione" in selected_text


def test_duplicate_chunks_do_not_consume_multiple_final_evidence_positions() -> None:
    duplicate = _document(
        "SRI_LOCKOUT_F1 blocca i veicoli e reindirizza l'energia.",
        "Manuale Sistema V4.1.pdf",
    )
    documents = [
        duplicate,
        _document(
            "SRI_LOCKOUT_F1 blocca i veicoli e reindirizza l'energia.",
            "Manuale Sistema V4.1.pdf",
        ),
        _document(
            "La fase uno richiede una doppia conferma dal centro di controllo.",
            "Piano di Contingenza.pdf",
        ),
    ]

    ranked = RerankingService().rerank_documents(
        documents, "Che cosa fa il comando SRI_LOCKOUT_F1?", [], top_n=3
    )

    assert [document.page_content for document in ranked].count(duplicate.page_content) == 1


def test_complete_page_context_replaces_its_preserved_atomic_chunks() -> None:
    page_context = _document(
        "Test override manuale: T-CAR 02 successo; T-CAR 01, 03 e 04 fallito.",
        "Rapporto Ispezione Veicoli Tour.pdf",
    )
    page_context.metadata["context_aggregation"] = True
    documents = [
        page_context,
        _document("Test Override Manuale", "Rapporto Ispezione Veicoli Tour.pdf"),
        _document("T-CAR 02", "Rapporto Ispezione Veicoli Tour.pdf"),
        _document("SUCCESSO", "Rapporto Ispezione Veicoli Tour.pdf"),
    ]

    ranked = RerankingService().rerank_documents(
        documents,
        "Quale veicolo T-CAR ha superato il test di override manuale?",
        [],
        top_n=4,
    )

    assert ranked == [page_context]


def test_atomic_sri_evidence_is_not_removed_by_incomplete_page_context() -> None:
    atomic = _document(
        "SRI_LOCKOUT_F1 avvia la Fase 1 Lockout, blocca i veicoli e reindirizza "
        "l'energia al Recinto 6 e T-REX.",
        "Manuale d'Uso del Sistema V4.1.pdf",
    )
    incomplete_page = _document(
        "InGen - Manuale Tecnico\nSezione 2: Sistema di Rete Intera (SRI)",
        "Manuale d'Uso del Sistema V4.1.pdf",
    )
    incomplete_page.metadata["context_aggregation"] = True

    ranked = RerankingService().rerank_documents(
        [incomplete_page, atomic, _document("Emergency systems", "ADHD.pdf")],
        "Che cosa fa esattamente il comando SRI_LOCKOUT_F1?",
        [],
        top_n=3,
    )

    assert atomic in ranked
    assert ranked[0] == atomic


def test_atomic_jophery_authorization_survives_incomplete_page_context() -> None:
    atomic = _document(
        "Jophery Brown è l'unica persona autorizzata ad accedere al magazzino "
        "di riserva del Cloruro di Potassio e degli integratori L-LIMIT.",
        "Profilo di Jophery Brown (Logistica Cibo).pdf",
    )
    incomplete_page = _document(
        "Profilo del personale: Jophery Brown\nGestione delle forniture.",
        "Profilo di Jophery Brown (Logistica Cibo).pdf",
    )
    incomplete_page.metadata["context_aggregation"] = True

    ranked = RerankingService().rerank_documents(
        [incomplete_page, atomic, _document("Riserva alimentare", "Inventario.pdf")],
        "Chi è autorizzato ad accedere al magazzino di riserva del Cloruro di Potassio e degli integratori L-LIMIT?",
        [],
        top_n=3,
    )

    assert atomic in ranked
    assert ranked[0] == atomic


def test_jophery_direct_answer_outranks_query_expansion_vocabulary() -> None:
    query = (
        "Chi è autorizzato ad accedere al magazzino di riserva del Cloruro di "
        "Potassio e degli integratori L-LIMIT?"
    )
    direct = _document(
        "Jophery Brown è l'unica persona autorizzata ad accedere al magazzino "
        "di riserva del Cloruro di Potassio e degli integratori L-LIMIT.",
        "Profilo di Jophery Brown (Logistica Cibo).pdf",
    )
    expansion_match = _document(
        "Authorized supply access times, East Dock delivery schedule, warehouse "
        "procedures and potassium chloride supplement logistics.",
        "Piano Logistico Rotazione.pdf",
    )

    ranked = RerankingService().rerank_documents(
        [expansion_match, direct],
        query,
        [
            "authorized supply access times East Dock delivery schedule",
            "warehouse procedures and potassium chloride supplement logistics",
        ],
        top_n=2,
    )

    assert ranked[0] == direct


def test_compound_selection_tracks_support_for_each_subquestion() -> None:
    query = (
        "Qual è il consumo giornaliero del Brachiosauro e quale caratteristica "
        "genetica unica presenta?"
    )
    groups = _answer_service()._split_compound_retrieval_queries(query)
    diet = _document(
        "Brachiosauro: consumo giornaliero di 200 kg di vegetazione.",
        "Rapporto BRAC.pdf",
    )
    genetics = _document(
        "Brachiosauro: caratteristica genetica unica, colorazione cutanea termica.",
        "Rapporto BRAC.pdf",
    )

    ranked = RerankingService().rerank_documents(
        [diet, genetics, _document("Brachiosauro erbivoro", "Generale.pdf")],
        query,
        groups,
        top_n=3,
        required_query_groups=groups,
    )

    assert diet in ranked
    assert genetics in ranked
    assert groups[0] in diet.metadata["supported_query_groups"]
    assert groups[1] in genetics.metadata["supported_query_groups"]


def test_compound_group_is_not_satisfied_by_entity_anchor_alone() -> None:
    query = (
        "Come differiscono il Gruppo Tattico e il Gruppo di Dominanza dei VELO-B "
        "e quali conseguenze hanno avuto i loro scontri territoriali?"
    )
    groups = _answer_service()._split_compound_retrieval_queries(query)
    generic = _document(
        "Classificazione generale della popolazione VELO-B.",
        "Rapporto VELO.pdf",
        page=1,
    )
    factions = _document(
        "Gruppo Tattico: piccolo e coeso. Gruppo di Dominanza: grande e instabile.",
        "Rapporto VELO.pdf",
        page=2,
    )
    consequences = _document(
        "Gli scontri territoriali hanno causato mortalità e distruzione dei nidi.",
        "Rapporto VELO.pdf",
        page=2,
    )

    ranked = RerankingService().rerank_documents(
        [generic, factions, consequences],
        query,
        groups,
        top_n=3,
        required_query_groups=groups,
    )

    assert groups[0] not in generic.metadata.get("supported_query_groups", [])
    assert groups[1] not in generic.metadata.get("supported_query_groups", [])
    assert factions in ranked
    assert consequences in ranked


def test_pinpoint_query_does_not_force_three_evidence_items() -> None:
    direct = _document(
        "SRI_LOCKOUT_F1 avvia la Fase 1 Lockout, blocca i veicoli e reindirizza l'energia.",
        "Manuale Sistema V4.1.pdf",
    )
    ranked = RerankingService().rerank_documents(
        [
            direct,
            _document("Procedure generiche di emergenza.", "Piano.pdf"),
            _document("Manutenzione ordinaria dei veicoli.", "Specifiche.pdf"),
        ],
        "Che cosa fa esattamente il comando SRI_LOCKOUT_F1?",
        [],
        top_n=3,
    )

    assert ranked == [direct]


def test_query_expansion_rejects_velo_vehicle_entity_drift() -> None:
    service = QueryExpansionService.__new__(QueryExpansionService)
    service.llm = Mock()
    service.llm.invoke.return_value.content = (
        "vehicle containment failures during blackout\n"
        "VELO vehicle override failures\n"
        "VELO escape risk known before containment failure"
    )

    alternatives = service.generate_alternative_queries(
        "Why was the VELO risk known before containment failure?"
    )

    assert alternatives == ["VELO escape risk known before containment failure"]


def test_query_expansion_preserves_exact_identifier() -> None:
    service = QueryExpansionService.__new__(QueryExpansionService)
    service.llm = Mock()
    service.llm.invoke.return_value.content = (
        "What does sri_lockout_f1 do?\n"
        "SRI_LOCKOUT_F1 Phase 1 Lockout behavior"
    )

    alternatives = service.generate_alternative_queries(
        "What does SRI_LOCKOUT_F1 do?"
    )

    assert alternatives == ["SRI_LOCKOUT_F1 Phase 1 Lockout behavior"]
