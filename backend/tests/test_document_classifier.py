import pytest
from unittest.mock import MagicMock, patch
from app.services.document_classifier_service import DocumentClassifierService, DocumentCategory

@pytest.fixture
def classifier_service():
    return DocumentClassifierService()

def test_classify_structural_document(classifier_service):
    filename = "Protocollo_Sicurezza_2024.pdf"
    content = "Questo protocollo definisce le procedure di sicurezza..."
    category = classifier_service.classify_document(filename, content)
    assert category == DocumentCategory.AUTORITA_STRUTTURALE

def test_classify_unstructured_document(classifier_service):
    filename = "Meeting_Notes.pdf"
    content = "Appunti della riunione del venerdì..."
    category = classifier_service.classify_document(filename, content)
    assert category == DocumentCategory.INFORMATIVO_NON_STRUTTURATO

def test_classify_by_keyword_in_content(classifier_service):
    filename = "Documento_Generico.pdf"
    content = "Vedi allegato A per i dettagli..."
    category = classifier_service.classify_document(filename, content)
    assert category == DocumentCategory.AUTORITA_STRUTTURALE

def test_classify_by_keyword_in_filename(classifier_service):
    filename = "Manuale_Utente.pdf"
    content = "Istruzioni per l'uso..."
    category = classifier_service.classify_document(filename, content)
    assert category == DocumentCategory.AUTORITA_STRUTTURALE
