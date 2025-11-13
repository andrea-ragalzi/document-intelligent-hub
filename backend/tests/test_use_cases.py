"""
Test suite for Use Case optimization with modular prompts.

Tests the 6 common use cases (CU1-CU6) to verify constraint adherence,
output format compliance, and quality of responses.
"""

import pytest
from app.schemas.use_cases import (
    OutputFormat,
    PromptConstraints,
    UseCaseType,
    get_output_format_description,
    get_use_case_definition,
)
from app.services.prompt_template_service import prompt_template_service


class TestUseCaseDefinitions:
    """Test suite for use case definitions and schemas."""
    
    def test_all_use_cases_defined(self):
        """Verify all 6 use cases are properly defined."""
        use_cases = [
            UseCaseType.PROFESSIONAL_CONTENT,
            UseCaseType.CODE_DEVELOPMENT,
            UseCaseType.DATA_ANALYSIS,
            UseCaseType.CREATIVE_BRAINSTORMING,
            UseCaseType.STRUCTURED_PLANNING,
            UseCaseType.BUSINESS_STRATEGY
        ]
        
        for use_case in use_cases:
            definition = get_use_case_definition(use_case)
            assert definition is not None
            assert definition.code == use_case
            assert definition.name
            assert definition.description
            assert definition.role_persona
    
    def test_output_format_descriptions(self):
        """Verify all output formats have descriptions."""
        formats = [
            OutputFormat.MARKDOWN_TEXT,
            OutputFormat.CODE_BLOCK,
            OutputFormat.BULLET_LIST,
            OutputFormat.NUMBERED_LIST,
            OutputFormat.HIERARCHICAL,
            OutputFormat.STRUCTURED_TABLE,
            OutputFormat.JSON_STRUCTURED
        ]
        
        for fmt in formats:
            description = get_output_format_description(fmt)
            assert description
            assert len(description) > 10


class TestPromptTemplateService:
    """Test suite for prompt template generation."""
    
    def test_extract_quantity_from_query_italian(self):
        """Test quantity extraction from Italian queries."""
        queries = [
            ("voglio una lista di 10 persone", 10),
            ("dammi 5 idee creative", 5),
            ("lista di 3 scenari possibili", 3),
            ("genera esattamente 7 titoli", 7),
            ("no quantity here", None)
        ]
        
        for query, expected in queries:
            result = prompt_template_service.extract_quantity_from_query(query)
            assert result == expected, f"Failed for query: {query}"
    
    def test_extract_quantity_from_query_english(self):
        """Test quantity extraction from English queries."""
        queries = [
            ("give me a list of 10 people", 10),
            ("I need 5 creative ideas", 5),
            ("list of 3 possible scenarios", 3),
            ("generate exactly 7 titles", 7),
            ("no quantity here", None)
        ]
        
        for query, expected in queries:
            result = prompt_template_service.extract_quantity_from_query(query)
            assert result == expected, f"Failed for query: {query}"
    
    def test_create_constraints_for_creative_brainstorming(self):
        """Test constraint creation for CU4 (Creative Brainstorming)."""
        constraints = prompt_template_service.create_constraints_for_use_case(
            use_case=UseCaseType.CREATIVE_BRAINSTORMING,
            quantity=5
        )
        
        assert constraints.quantity_constraint
        assert "5" in constraints.quantity_constraint
        assert "EXACTLY" in constraints.quantity_constraint
        assert constraints.data_type_constraint
        assert constraints.format_constraint
    
    def test_create_constraints_for_business_strategy(self):
        """Test constraint creation for CU6 (Business Strategy)."""
        constraints = prompt_template_service.create_constraints_for_use_case(
            use_case=UseCaseType.BUSINESS_STRATEGY,
            quantity=4
        )
        
        assert constraints.quantity_constraint
        assert "4" in constraints.quantity_constraint
        assert constraints.data_type_constraint
        assert "business analysis framework" in constraints.data_type_constraint.lower()
    
    def test_build_modular_prompt_structure(self):
        """Test that modular prompts follow the 4-section structure."""
        constraints = PromptConstraints(
            quantity_constraint="The response MUST contain EXACTLY 5 items.",
            data_type_constraint="Each item MUST be a unique creative idea.",
            format_constraint="Output MUST be a numbered list from 1 to 5."
        )
        
        prompt = prompt_template_service.build_modular_prompt(
            use_case=UseCaseType.CREATIVE_BRAINSTORMING,
            user_request="Generate 5 innovative app ideas for fitness",
            constraints=constraints,
            additional_context="Focus on accessibility and inclusivity"
        )
        
        # Verify 4 sections are present
        assert "**I. PERSONALITY AND OBJECTIVE**" in prompt
        assert "**II. SPECIFIC USER REQUEST**" in prompt
        assert "**III. CONSTRAINTS AND REQUIREMENTS**" in prompt
        assert "**IV. ADDITIONAL CONTEXT**" in prompt
        
        # Verify key elements
        assert "Creative Strategist" in prompt  # Role persona for CU4
        assert "5 innovative app ideas" in prompt  # User request
        assert "EXACTLY 5" in prompt  # Quantity constraint
        assert "accessibility and inclusivity" in prompt  # Additional context
    
    def test_build_modular_prompt_with_retrieved_context(self):
        """Test prompt building with RAG-retrieved context."""
        constraints = PromptConstraints(
            quantity_constraint="The response MUST contain EXACTLY 10 items.",
            data_type_constraint="Each item MUST be a person's name.",
            format_constraint="Output MUST be a numbered list from 1 to 10."
        )
        
        retrieved_context = """
        [DOCUMENT 1]
        Section: Chapter 3
        ---
        The council includes Mayor Solirion Torralyn d'Sivis...
        
        [DOCUMENT 2]
        Section: Chapter 5
        ---
        Commander Bestan ir'Tonn leads the guard...
        """
        
        prompt = prompt_template_service.build_modular_prompt(
            use_case=UseCaseType.DATA_ANALYSIS,
            user_request="Extract the names of 10 important people from the documents",
            constraints=constraints,
            retrieved_context=retrieved_context
        )
        
        # Verify context inclusion
        assert "**RETRIEVED CONTEXT FROM DOCUMENTS:**" in prompt
        assert "Solirion Torralyn d'Sivis" in prompt
        assert "Bestan ir'Tonn" in prompt
        assert "Base your answer EXCLUSIVELY on the retrieved context" in prompt
    
    def test_build_prompt_without_optional_sections(self):
        """Test prompt building without optional sections (history, context)."""
        constraints = prompt_template_service.create_constraints_for_use_case(
            use_case=UseCaseType.CODE_DEVELOPMENT,
            quantity=1
        )
        
        prompt = prompt_template_service.build_modular_prompt(
            use_case=UseCaseType.CODE_DEVELOPMENT,
            user_request="Write a Python function to validate email addresses",
            constraints=constraints
        )
        
        # Should have 3 sections (no IV since no additional context)
        assert "**I. PERSONALITY AND OBJECTIVE**" in prompt
        assert "**II. SPECIFIC USER REQUEST**" in prompt
        assert "**III. CONSTRAINTS AND REQUIREMENTS**" in prompt
        assert "**IV. ADDITIONAL CONTEXT**" not in prompt
    
    def test_all_use_cases_generate_valid_prompts(self):
        """Test that all 6 use cases can generate valid prompts."""
        use_cases = [
            (UseCaseType.PROFESSIONAL_CONTENT, "Write a formal business report on AI adoption"),
            (UseCaseType.CODE_DEVELOPMENT, "Create a React component for user authentication"),
            (UseCaseType.DATA_ANALYSIS, "Analyze the quarterly sales data and extract key trends"),
            (UseCaseType.CREATIVE_BRAINSTORMING, "Generate 5 innovative marketing campaign ideas"),
            (UseCaseType.STRUCTURED_PLANNING, "Create a project roadmap for launching a mobile app"),
            (UseCaseType.BUSINESS_STRATEGY, "Develop a SWOT analysis for entering the European market")
        ]
        
        for use_case, request in use_cases:
            constraints = prompt_template_service.create_constraints_for_use_case(
                use_case=use_case,
                quantity=5 if use_case == UseCaseType.CREATIVE_BRAINSTORMING else None
            )
            
            prompt = prompt_template_service.build_modular_prompt(
                use_case=use_case,
                user_request=request,
                constraints=constraints
            )
            
            # Verify basic structure
            assert len(prompt) > 100, f"Prompt too short for {use_case}"
            assert "**I. PERSONALITY AND OBJECTIVE**" in prompt
            assert "**II. SPECIFIC USER REQUEST**" in prompt
            assert "**III. CONSTRAINTS AND REQUIREMENTS**" in prompt
            assert request in prompt


class TestConstraintEnforcement:
    """Test suite for constraint enforcement in prompts."""
    
    def test_quantity_constraint_emphasis(self):
        """Test that quantity constraints are properly emphasized."""
        constraints = PromptConstraints(
            quantity_constraint="The response MUST contain EXACTLY 10 items.",
            data_type_constraint="Each item MUST be a person's name.",
            format_constraint="Output MUST be a numbered list."
        )
        
        prompt = prompt_template_service.build_modular_prompt(
            use_case=UseCaseType.CREATIVE_BRAINSTORMING,
            user_request="Generate 10 character names",
            constraints=constraints
        )
        
        # Verify emphasis on quantity
        assert "CRITICAL" in prompt
        assert "NON-NEGOTIABLE" in prompt
        assert "Count your output items before responding" in prompt
    
    def test_format_constraint_specification(self):
        """Test that format constraints are clearly specified."""
        constraints = prompt_template_service.create_constraints_for_use_case(
            use_case=UseCaseType.STRUCTURED_PLANNING,
            quantity=None
        )
        
        prompt = prompt_template_service.build_modular_prompt(
            use_case=UseCaseType.STRUCTURED_PLANNING,
            user_request="Create a study plan for learning Python",
            constraints=constraints
        )
        
        # Verify format constraint section
        assert "FORMAT CONSTRAINT" in prompt
        assert "PRIORITY" in prompt
        assert "hierarchical structure" in prompt.lower()
    
    def test_additional_constraints_inclusion(self):
        """Test that additional constraints are properly included."""
        constraints = PromptConstraints(
            quantity_constraint="EXACTLY 3 items",
            data_type_constraint="Each item is a paragraph",
            format_constraint="Markdown text",
            additional_constraints=[
                "Use formal language appropriate for business communication",
                "Include specific metrics and data points where applicable"
            ]
        )
        
        prompt = prompt_template_service.build_modular_prompt(
            use_case=UseCaseType.PROFESSIONAL_CONTENT,
            user_request="Write 3 paragraphs about digital transformation",
            constraints=constraints
        )
        
        # Verify additional constraints are included
        assert "formal language" in prompt.lower()
        assert "metrics and data points" in prompt.lower()
        assert "ADDITIONAL REQUIREMENT" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
