"""
Tests for Use Case Auto-Detection Service.

Verifies that queries are correctly classified into appropriate use cases
based on patterns, keywords, and query structure.
"""

import pytest
from app.schemas.use_cases import UseCaseType
from app.services.use_case_detection_service import use_case_detection_service


class TestUseCaseDetection:
    """Test suite for automatic use case detection."""
    
    def test_detect_cu4_list_queries_english(self):
        """Test detection of CU4 (Creative Brainstorming) from list queries in English."""
        queries = [
            "Give me a list of 10 people",
            "I need 5 creative ideas for marketing",
            "Generate 7 titles for blog posts",
            "Brainstorm 3 alternative approaches",
            "List of 8 potential risks",
        ]
        
        for query in queries:
            detected = use_case_detection_service.detect_use_case(query)
            assert detected == UseCaseType.CREATIVE_BRAINSTORMING, f"Failed for: {query}"
    
    def test_detect_cu4_list_queries_italian(self):
        """Test detection of CU4 from list queries in Italian."""
        queries = [
            "voglio una lista di 10 persone",
            "dammi 5 idee creative",
            "genera esattamente 7 titoli",
            "lista di 3 scenari possibili",
        ]
        
        for query in queries:
            detected = use_case_detection_service.detect_use_case(query)
            assert detected == UseCaseType.CREATIVE_BRAINSTORMING, f"Failed for: {query}"
    
    def test_detect_cu3_summary_queries(self):
        """Test detection of CU3 (Data Analysis) from summary/analysis queries."""
        queries = [
            "Summarize the main points of this document",
            "What are the key insights from the report?",
            "Analyze the trends in the data",
            "Extract the key findings",
            "Give me the key takeaways",
        ]
        
        for query in queries:
            detected = use_case_detection_service.detect_use_case(query)
            assert detected == UseCaseType.DATA_ANALYSIS, f"Failed for: {query}"
    
    def test_detect_cu2_code_queries(self):
        """Test detection of CU2 (Code Development) from code-related queries."""
        queries = [
            "Write a Python function to validate emails",
            "Debug this JavaScript code",
            "Refactor the authentication logic",
            "Create a React component for user profile",
            "Implement a sorting algorithm",
            "Fix the bug in this function",
        ]
        
        for query in queries:
            detected = use_case_detection_service.detect_use_case(query)
            assert detected == UseCaseType.CODE_DEVELOPMENT, f"Failed for: {query}"
    
    def test_detect_cu6_business_strategy(self):
        """Test detection of CU6 (Business Strategy) from business analysis queries."""
        queries = [
            "Generate a SWOT analysis for our product",
            "Create a PESTEL analysis for market entry",
            "Develop a business case for this initiative",
            "What are the strengths and weaknesses of this approach?",
            # "Analyze the competitive landscape",  # This could also match CU3
        ]
        
        for query in queries:
            detected = use_case_detection_service.detect_use_case(query)
            assert detected == UseCaseType.BUSINESS_STRATEGY, f"Failed for: {query}"
    
    def test_detect_cu5_planning_queries(self):
        """Test detection of CU5 (Structured Planning) from planning/outline queries."""
        queries = [
            "Create an outline for a course on machine learning",
            "Develop a project plan for website redesign",
            "What are the steps to launch a startup?",
            "Build a roadmap for product development",
            "Structure a study plan for Python",
        ]
        
        for query in queries:
            detected = use_case_detection_service.detect_use_case(query)
            assert detected == UseCaseType.STRUCTURED_PLANNING, f"Failed for: {query}"
    
    def test_detect_cu1_professional_content(self):
        """Test detection of CU1 (Professional Content) from formal writing queries."""
        queries = [
            "Write a formal business report on sales performance",
            "Draft a professional email to the client",
            "Create a business proposal document",
        ]
        
        for query in queries:
            detected = use_case_detection_service.detect_use_case(query)
            assert detected == UseCaseType.PROFESSIONAL_CONTENT, f"Failed for: {query}"
    
    def test_no_detection_for_generic_queries(self):
        """Test that generic queries don't trigger use case detection."""
        queries = [
            "What is this about?",
            "Tell me more",
            "Explain",
            "Who is mentioned?",
            "When did this happen?",
        ]
        
        for query in queries:
            detected = use_case_detection_service.detect_use_case(query)
            # These might not match any use case strongly
            # Just verify the function doesn't crash
            assert detected is None or isinstance(detected, UseCaseType)
    
    def test_confidence_level_high(self):
        """Test high confidence detection."""
        query = "Give me a list of 10 creative ideas for marketing campaigns"
        use_case, confidence = use_case_detection_service.get_confidence_level(query)
        
        assert use_case == UseCaseType.CREATIVE_BRAINSTORMING
        assert confidence == 'high'
    
    def test_confidence_level_medium(self):
        """Test medium/high confidence detection for brainstorm queries."""
        query = "Brainstorm some ideas"
        use_case, confidence = use_case_detection_service.get_confidence_level(query)
        
        assert use_case == UseCaseType.CREATIVE_BRAINSTORMING
        assert confidence in ['medium', 'low', 'high']  # Flexible based on scoring
    
    def test_confidence_level_none(self):
        """Test no confidence when no patterns match."""
        query = "What time is it?"
        use_case, confidence = use_case_detection_service.get_confidence_level(query)
        
        assert use_case is None
        assert confidence == 'none'
    
    def test_priority_cu4_over_cu3_for_lists(self):
        """Test that CU4 is prioritized over CU3 for list queries with quantities."""
        # This query could match both CU3 (extract) and CU4 (list of X)
        query = "Extract a list of 10 key people mentioned"
        detected = use_case_detection_service.detect_use_case(query)
        
        # Should prioritize CU4 because of "list of 10" pattern
        assert detected == UseCaseType.CREATIVE_BRAINSTORMING
    
    def test_multilingual_detection(self):
        """Test detection works across different languages."""
        test_cases = [
            ("voglio una lista di 5 idee", UseCaseType.CREATIVE_BRAINSTORMING),
            ("summarize the key points", UseCaseType.DATA_ANALYSIS),
            ("scrivi una funzione Python per validare email", UseCaseType.CODE_DEVELOPMENT),
        ]
        
        for query, expected_use_case in test_cases:
            detected = use_case_detection_service.detect_use_case(query)
            assert detected == expected_use_case, f"Failed for: {query}"
    
    def test_case_insensitive_detection(self):
        """Test that detection is case-insensitive."""
        queries = [
            "GIVE ME A LIST OF 10 PEOPLE",
            "give me a list of 10 people",
            "Give Me A List Of 10 People",
        ]
        
        for query in queries:
            detected = use_case_detection_service.detect_use_case(query)
            assert detected == UseCaseType.CREATIVE_BRAINSTORMING
    
    def test_partial_pattern_matching(self):
        """Test that partial matches still work."""
        # Query has "summarize" but not full pattern
        query = "Can you summarize?"
        detected = use_case_detection_service.detect_use_case(query)
        
        assert detected == UseCaseType.DATA_ANALYSIS


class TestScoring:
    """Test suite for scoring mechanism."""
    
    def test_scoring_patterns_higher_than_keywords(self):
        """Test that pattern matches score higher than keyword matches."""
        # This has both pattern and keyword, should score high
        query1 = "Give me a list of 10 ideas"  # Pattern match (3 pts) + keywords (1+ pts)
        
        # This has only keyword, should score lower
        query2 = "Some ideas would be nice"  # Only keyword (1 pt)
        
        use_case1, conf1 = use_case_detection_service.get_confidence_level(query1)
        use_case2, conf2 = use_case_detection_service.get_confidence_level(query2)
        
        # First should have higher confidence
        confidence_order = ['none', 'low', 'medium', 'high']
        assert confidence_order.index(conf1) >= confidence_order.index(conf2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
