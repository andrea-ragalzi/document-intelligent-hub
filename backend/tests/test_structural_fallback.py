from app.services.document_classifier_service import document_classifier_service

def test_structural_density_check():
    """Test the heuristic structural density check."""
    
    # Case 1: High density (numbered list) - 1.1, 1.2, etc.
    # "1.1 Section\n" is ~12 chars. 100 times = 1200 chars. 100 matches.
    # Density = (100 / 1200) * 1000 = 83 > 5. Should be True.
    high_density_text = "1.1 Section\n1.2 Section\n1.3 Section\n" * 40
    assert document_classifier_service.has_structural_density(high_density_text) is True

    # Case 2: High density (headers) - ## Header
    # "## Header 1\n" is ~12 chars.
    header_text = "## Header 1\n### Header 2\n## Header 3\n" * 40
    assert document_classifier_service.has_structural_density(header_text) is True

    # Case 3: Low density (plain text)
    plain_text = "This is a plain text document without much structure. It just goes on and on. " * 50
    assert document_classifier_service.has_structural_density(plain_text) is False

    # Case 4: Mixed but low density
    mixed_text = "1.1 Start\n" + ("Plain text filling the space between headers. " * 20) + "\n1.2 End"
    # 2 matches in ~1000 chars. Density ~ 2. Should be False.
    assert document_classifier_service.has_structural_density(mixed_text) is False
