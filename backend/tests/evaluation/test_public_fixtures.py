from pypdf import PdfReader

from evaluation.run_public_eval import CASES_PATH, DOCUMENTS_DIR, load_cases


def test_every_referenced_public_fixture_exists_and_pages_are_valid() -> None:
    page_counts: dict[str, int] = {}

    for case in load_cases(CASES_PATH):
        for evidence in case.expected_evidence:
            document_path = DOCUMENTS_DIR / evidence.document
            assert document_path.is_file(), document_path
            page_count = page_counts.setdefault(
                evidence.document, len(PdfReader(document_path).pages)
            )
            assert all(1 <= page <= page_count for page in evidence.pages), case.id


def test_public_corpus_contains_exactly_the_declared_logical_documents() -> None:
    referenced = {
        evidence.document
        for case in load_cases(CASES_PATH)
        for evidence in case.expected_evidence
    }

    assert referenced == {
        "03_Velociraptor_Behavior_and_Containment_Dossier.pdf",
        "09_Rapporto_Spegnimento_Ripristino_Energia_e_Controllo_Porte_IT.pdf",
        "10_Recovery_Operations_and_Privileged_Access_Appendix.pdf",
        "Northbyte_Systems_Payslip_August_2026.pdf",
        "alices-adventures-in-wonderland.pdf",
    }
