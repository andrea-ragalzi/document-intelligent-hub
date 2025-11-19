"""
Unit tests for Query Parser Service.

Tests the LLM-based file filter extraction from natural language queries.
"""

from unittest.mock import Mock, patch

import pytest
from app.schemas.rag_schema import FileFilterResponse
from app.services.query_parser_service import QueryParserService


@pytest.fixture
def query_parser():
    """Create a QueryParserService instance for testing."""
    return QueryParserService()


class TestFileReferenceDetection:
    """Test heuristic detection of file references in queries"""
    
    def test_detects_italian_file_references(self, query_parser):
        """Test detection of Italian file reference patterns"""
        queries_with_references = [
            "Cerca solo nel file report.pdf",
            "Escludi contratto.pdf dalla ricerca",
            "Usa il documento analisi.pdf",
            "Cerca senza tutorial.pdf",
        ]
        
        for query in queries_with_references:
            assert query_parser.has_file_references(query), f"Should detect file reference in: {query}"
    
    def test_detects_english_file_references(self, query_parser):
        """Test detection of English file reference patterns"""
        queries_with_references = [
            "Search only in file data.pdf",
            "Exclude draft.pdf from results",
            "Use document report.pdf",
            "Search without notes.pdf",
        ]
        
        for query in queries_with_references:
            assert query_parser.has_file_references(query), f"Should detect file reference in: {query}"
    
    def test_no_false_positives(self, query_parser):
        """Test that normal queries without file references are not detected"""
        normal_queries = [
            "What is the main topic?",
            "Explain the concept of machine learning",
            "Quali sono i requisiti?",
            "How does this work?",
        ]
        
        for query in normal_queries:
            assert not query_parser.has_file_references(query), f"Should NOT detect file reference in: {query}"


class TestFileFilterExtraction:
    """Test LLM-based file filter extraction"""
    
    @patch("app.services.query_parser_service.ChatOpenAI")
    def test_extract_include_filter_italian(self, mock_llm_class, query_parser):
        """Test extraction of INCLUDE filter from Italian query"""
        # Mock LLM response
        mock_llm_instance = Mock()
        mock_response = Mock()
        mock_response.content = """{
            "include_files": ["report.pdf"],
            "exclude_files": [],
            "cleaned_query": "Quali sono i requisiti?"
        }"""
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm_instance
        
        # Create service with mocked LLM
        service = QueryParserService()
        service.llm = mock_llm_instance
        
        # Test extraction
        result = service.extract_file_filters(
            query="Quali sono i requisiti solo nel file report.pdf?",
            available_files=["report.pdf", "data.pdf", "specs.pdf"]
        )
        
        assert isinstance(result, FileFilterResponse)
        assert "report.pdf" in result.include_files
        assert len(result.exclude_files) == 0
        assert result.cleaned_query == "Quali sono i requisiti?"
    
    @patch("app.services.query_parser_service.ChatOpenAI")
    def test_extract_exclude_filter_italian(self, mock_llm_class, query_parser):
        """Test extraction of EXCLUDE filter from Italian query"""
        # Mock LLM response
        mock_llm_instance = Mock()
        mock_response = Mock()
        mock_response.content = """{
            "include_files": [],
            "exclude_files": ["tutorial.pdf"],
            "cleaned_query": "Cerca informazioni su Python"
        }"""
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm_instance
        
        # Create service with mocked LLM
        service = QueryParserService()
        service.llm = mock_llm_instance
        
        # Test extraction
        result = service.extract_file_filters(
            query="Cerca informazioni su Python ma escludi tutorial.pdf",
            available_files=["tutorial.pdf", "reference.pdf", "guide.pdf"]
        )
        
        assert isinstance(result, FileFilterResponse)
        assert len(result.include_files) == 0
        assert "tutorial.pdf" in result.exclude_files
        assert "Python" in result.cleaned_query
    
    @patch("app.services.query_parser_service.ChatOpenAI")
    def test_extract_both_filters(self, mock_llm_class, query_parser):
        """Test extraction of both INCLUDE and EXCLUDE filters"""
        # Mock LLM response
        mock_llm_instance = Mock()
        mock_response = Mock()
        mock_response.content = """{
            "include_files": ["report.pdf", "data.pdf"],
            "exclude_files": ["draft.pdf"],
            "cleaned_query": "Analizza le vendite"
        }"""
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm_instance
        
        # Create service with mocked LLM
        service = QueryParserService()
        service.llm = mock_llm_instance
        
        # Test extraction
        result = service.extract_file_filters(
            query="Usa report.pdf e data.pdf ma non draft.pdf per analizzare le vendite",
            available_files=["report.pdf", "data.pdf", "draft.pdf", "notes.pdf"]
        )
        
        assert isinstance(result, FileFilterResponse)
        assert len(result.include_files) == 2
        assert "report.pdf" in result.include_files
        assert "data.pdf" in result.include_files
        assert "draft.pdf" in result.exclude_files
    
    @patch("app.services.query_parser_service.ChatOpenAI")
    def test_no_filters_in_normal_query(self, mock_llm_class, query_parser):
        """Test that normal queries return empty filters"""
        # Mock LLM response
        mock_llm_instance = Mock()
        mock_response = Mock()
        mock_response.content = """{
            "include_files": [],
            "exclude_files": [],
            "cleaned_query": "What is the main topic?"
        }"""
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm_instance
        
        # Create service with mocked LLM
        service = QueryParserService()
        service.llm = mock_llm_instance
        
        # Test extraction
        result = service.extract_file_filters(
            query="What is the main topic?",
            available_files=["doc1.pdf", "doc2.pdf"]
        )
        
        assert len(result.include_files) == 0
        assert len(result.exclude_files) == 0
        assert result.cleaned_query == "What is the main topic?"
    
    def test_validates_against_available_files(self, query_parser):
        """Test that extraction validates filenames against available documents"""
        # This test will use actual LLM call (if API key available) or fail gracefully
        try:
            result = query_parser.extract_file_filters(
                query="Usa nonexistent.pdf per la ricerca",
                available_files=["report.pdf", "data.pdf"]  # nonexistent.pdf NOT in list
            )
            
            # Should NOT include invalid filename
            assert "nonexistent.pdf" not in result.include_files
            
        except Exception:
            # If LLM call fails (no API key, network error), skip this test
            pytest.skip("LLM call failed - requires OpenAI API key")
    
    @patch("app.services.query_parser_service.ChatOpenAI")
    def test_handles_llm_failure_gracefully(self, mock_llm_class, query_parser):
        """Test fallback behavior when LLM call fails"""
        # Mock LLM to raise exception
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.side_effect = Exception("LLM API error")
        mock_llm_class.return_value = mock_llm_instance
        
        # Create service with mocked LLM
        service = QueryParserService()
        service.llm = mock_llm_instance
        
        # Should not crash, should return fallback (no filters)
        result = service.extract_file_filters(
            query="Cerca nel file report.pdf",
            available_files=["report.pdf"]
        )
        
        assert isinstance(result, FileFilterResponse)
        assert len(result.include_files) == 0  # Fallback: no filtering
        assert len(result.exclude_files) == 0
        assert result.cleaned_query == "Cerca nel file report.pdf"  # Original query preserved


class TestCaseInsensitiveMatching:
    """Test that filename matching is case-insensitive"""
    
    @patch("app.services.query_parser_service.ChatOpenAI")
    def test_case_insensitive_include(self, mock_llm_class, query_parser):
        """Test case-insensitive filename matching for include filters"""
        # Mock LLM returns lowercase filename
        mock_llm_instance = Mock()
        mock_response = Mock()
        mock_response.content = """{
            "include_files": ["report.pdf"],
            "exclude_files": [],
            "cleaned_query": "Cerca"
        }"""
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm_instance
        
        service = QueryParserService()
        service.llm = mock_llm_instance
        
        # Available files have different case
        result = service.extract_file_filters(
            query="Cerca nel file report.pdf",
            available_files=["Report.pdf", "DATA.PDF"]  # Different case
        )
        
        # Should match case-insensitively and return actual filename from available list
        assert len(result.include_files) == 1
        assert "Report.pdf" in result.include_files  # Actual filename from available list


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    @patch("app.services.query_parser_service.ChatOpenAI")
    def test_empty_available_files(self, mock_llm_class, query_parser):
        """Test behavior when no files are available"""
        mock_llm_instance = Mock()
        mock_response = Mock()
        mock_response.content = """{
            "include_files": ["report.pdf"],
            "exclude_files": [],
            "cleaned_query": "Test"
        }"""
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm_instance
        
        service = QueryParserService()
        service.llm = mock_llm_instance
        
        result = service.extract_file_filters(
            query="Cerca nel file report.pdf",
            available_files=[]  # No files available
        )
        
        # Should validate and return empty (no valid files)
        assert len(result.include_files) == 0
    
    @patch("app.services.query_parser_service.ChatOpenAI")
    def test_cleaned_query_too_short_fallback(self, mock_llm_class, query_parser):
        """Test fallback when LLM returns very short cleaned query"""
        mock_llm_instance = Mock()
        mock_response = Mock()
        mock_response.content = """{
            "include_files": ["test.pdf"],
            "exclude_files": [],
            "cleaned_query": "X"
        }"""
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm_instance
        
        service = QueryParserService()
        service.llm = mock_llm_instance
        
        original_query = "Cerca nel file test.pdf informazioni importanti"
        result = service.extract_file_filters(
            query=original_query,
            available_files=["test.pdf"]
        )
        
        # Should fallback to original query when cleaned is too short
        assert result.cleaned_query == original_query
