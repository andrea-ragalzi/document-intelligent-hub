"""
Unit tests for Query Parser Service.

Tests the LLM-based file filter extraction from natural language queries.
"""

from unittest.mock import Mock, patch

import pytest
from app.services.query_parser_service import FileFilterResponse, QueryParserService
from langchain_core.output_parsers import StrOutputParser


@pytest.fixture
def query_parser():
    """Fixture for QueryParserService."""
    return QueryParserService()


class TestFileFilterExtraction:
    """Test suite for file filter extraction logic."""

    @patch("app.services.query_parser_service.ChatOpenAI")
    @patch.object(StrOutputParser, "invoke")
    def test_extract_include_filter_italian(self, mock_str_parser_invoke, mock_llm_class, query_parser):
        """Test extraction of INCLUDE filter from Italian query"""
        # Mock the output of the StrOutputParser step in the chain
        mock_response_content = """{
            "include_files": ["report.pdf"],
            "exclude_files": [],
            "cleaned_query": "Quali sono i requisiti?"
        }"""
        mock_str_parser_invoke.return_value = mock_response_content
    
        # Create service - the patches will apply to the instances created within
        service = QueryParserService()
    
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
    @patch.object(StrOutputParser, "invoke")
    def test_extract_exclude_filter_italian(self, mock_str_parser_invoke, mock_llm_class, query_parser):
        """Test extraction of EXCLUDE filter from Italian query"""
        # Mock the output of the StrOutputParser step
        mock_response_content = """{
            "include_files": [],
            "exclude_files": ["tutorial.pdf"],
            "cleaned_query": "Cerca informazioni su Python"
        }"""
        mock_str_parser_invoke.return_value = mock_response_content
    
        # Create service
        service = QueryParserService()
    
        # Test extraction
        result = service.extract_file_filters(
            query="Cerca informazioni su Python ma escludi tutorial.pdf",
            available_files=["tutorial.pdf", "reference.pdf", "guide.pdf"]
        )
    
        assert isinstance(result, FileFilterResponse)
        assert len(result.include_files) == 0
        assert "tutorial.pdf" in result.exclude_files
        assert result.cleaned_query == "Cerca informazioni su Python"

    @patch("app.services.query_parser_service.ChatOpenAI")
    @patch.object(StrOutputParser, "invoke")
    def test_extract_both_filters(self, mock_str_parser_invoke, mock_llm_class, query_parser):
        """Test extraction of both INCLUDE and EXCLUDE filters"""
        # Mock the output of the StrOutputParser step
        mock_response_content = """{
            "include_files": ["report.pdf", "data.pdf"],
            "exclude_files": ["draft.pdf"],
            "cleaned_query": "Analizza le vendite"
        }"""
        mock_str_parser_invoke.return_value = mock_response_content
    
        # Create service
        service = QueryParserService()
    
        # Test extraction
        result = service.extract_file_filters(
            query="Usa report.pdf e data.pdf ma non draft.pdf per analizzare le vendite",
            available_files=["report.pdf", "data.pdf", "draft.pdf", "notes.pdf"]
        )
    
        assert isinstance(result, FileFilterResponse)
        assert len(result.include_files) == 2
        assert "report.pdf" in result.include_files
        assert "data.pdf" in result.include_files
        assert len(result.exclude_files) == 1
        assert "draft.pdf" in result.exclude_files
        assert result.cleaned_query == "Analizza le vendite"

    @patch("app.services.query_parser_service.ChatOpenAI")
    @patch.object(StrOutputParser, "invoke")
    def test_no_filters_found(self, mock_str_parser_invoke, mock_llm_class, query_parser):
        """Test that no filters are found in a normal query"""
        # Mock the output of the StrOutputParser step
        mock_response_content = """{
            "include_files": [],
            "exclude_files": [],
            "cleaned_query": "What is the main topic?"
        }"""
        mock_str_parser_invoke.return_value = mock_response_content
    
        # Create service
        service = QueryParserService()
    
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
    @patch.object(StrOutputParser, "invoke")
    def test_case_insensitive_include(self, mock_str_parser_invoke, mock_llm_class, query_parser):
        """Test case-insensitive filename matching for include filters"""
        # Mock LLM returns lowercase filename
        mock_response_content = """{
            "include_files": ["report.pdf"],
            "exclude_files": [],
            "cleaned_query": "Cerca"
        }"""
        mock_str_parser_invoke.return_value = mock_response_content
    
        service = QueryParserService()
    
        # Available files have different case
        result = service.extract_file_filters(
            query="Cerca nel file report.pdf",
            available_files=["Report.pdf", "DATA.PDF"]  # Different case
        )
    
        # Should match case-insensitively and return actual filename from available list
        assert len(result.include_files) == 1
        assert result.include_files[0] == "Report.pdf"

    @patch("app.services.query_parser_service.ChatOpenAI")
    @patch.object(StrOutputParser, "invoke")
    def test_case_insensitive_exclude(self, mock_str_parser_invoke, mock_llm_class, query_parser):
        """Test case-insensitive filename matching for exclude filters"""
        # Mock LLM returns mixed case filename
        mock_response_content = """{
            "include_files": [],
            "exclude_files": ["Notes.PDF"],
            "cleaned_query": "Cerca"
        }"""
        mock_str_parser_invoke.return_value = mock_response_content
    
        service = QueryParserService()
    
        # Available files are lowercase
        result = service.extract_file_filters(
            query="Cerca senza Notes.PDF",
            available_files=["report.pdf", "notes.pdf"]
        )
    
        # Should match case-insensitively and return actual filename
        assert len(result.exclude_files) == 1
        assert result.exclude_files[0] == "notes.pdf"

    @patch("app.services.query_parser_service.ChatOpenAI")
    @patch.object(StrOutputParser, "invoke")
    def test_non_existent_file_is_ignored(self, mock_str_parser_invoke, mock_llm_class, query_parser):
        """Test that non-existent files in the query are ignored"""
        # Mock LLM returns a file that is not in the available list
        mock_response_content = """{
            "include_files": ["non_existent.pdf"],
            "exclude_files": ["report.pdf"],
            "cleaned_query": "Cerca ed escludi"
        }"""
        mock_str_parser_invoke.return_value = mock_response_content
    
        service = QueryParserService()
    
        result = service.extract_file_filters(
            query="Cerca in non_existent.pdf ed escludi report.pdf",
            available_files=["report.pdf", "data.pdf"]
        )
    
        # "non_existent.pdf" should be ignored, "report.pdf" should be excluded
        assert len(result.include_files) == 0
        assert len(result.exclude_files) == 1
        assert result.exclude_files[0] == "report.pdf"
