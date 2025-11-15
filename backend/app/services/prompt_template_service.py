"""
Prompt Template Service for Optimized LLM Interactions.

This service generates structured, modular prompts following best practices
to overcome issues like "Constraint Neglect" and ensure adherence to
quantity, format, and quality requirements.

The 4-section prompt structure:
    I. PERSONALITY AND OBJECTIVE - Sets role and primary task
    II. SPECIFIC USER REQUEST - Dynamic content from user
    III. CONSTRAINTS AND REQUIREMENTS - Critical rules to enforce
    IV. ADDITIONAL CONTEXT - Optional supplementary information
"""

from app.schemas.use_cases import (
    PromptConstraints,
    UseCaseDefinition,
    UseCaseType,
    get_output_format_description,
    get_use_case_definition,
)


class PromptTemplateService:
    """
    Service for generating optimized, constraint-aware prompts for different use cases.

    This service implements the modular prompt strategy with hierarchical structure
    and critical constraint repetition to ensure LLM adherence to requirements.
    """

    def __init__(self):
        """Initialize the prompt template service."""
        pass

    def build_modular_prompt(
        self,
        use_case: UseCaseType,
        user_request: str,
        constraints: PromptConstraints,
        additional_context: str | None = None,
        retrieved_context: str | None = None,
    ) -> str:
        """
        Build a complete modular prompt following the 4-section structure.

        Args:
            use_case: The type of use case (CU1-CU6)
            user_request: The specific user request/question
            constraints: Prompt constraints (quantity, format, data type)
            additional_context: Optional additional context or instructions
            retrieved_context: Optional RAG-retrieved context from documents

        Returns:
            Complete structured prompt ready for LLM consumption
        """
        use_case_def = get_use_case_definition(use_case)

        # Section I: Personality and Objective
        section_i = self._build_personality_section(use_case_def)

        # Section II: Specific User Request
        section_ii = self._build_request_section(user_request, retrieved_context)

        # Section III: Constraints and Requirements
        section_iii = self._build_constraints_section(constraints, use_case_def)

        # Section IV: Additional Context (if provided)
        section_iv = (
            self._build_context_section(additional_context)
            if additional_context
            else ""
        )

        # Combine all sections
        prompt_parts = [section_i, section_ii, section_iii]
        if section_iv:
            prompt_parts.append(section_iv)

        return "\n\n".join(prompt_parts)

    def _build_personality_section(self, use_case_def: UseCaseDefinition) -> str:
        """
        Build Section I: Personality and Objective.

        Args:
            use_case_def: The use case definition

        Returns:
            Formatted personality section
        """
        return f"""**I. PERSONALITY AND OBJECTIVE**

Act as a {use_case_def.role_persona}, meticulous and professional.

Your PRIMARY task is to execute the user's request while *RIGOROUSLY* respecting ALL constraints regarding format and quantity.

CRITICAL RULE: Do NOT deviate from the exact number of elements requested. Do NOT provide approximate or generic categories when specific items are requested."""

    def _build_request_section(
        self, user_request: str, retrieved_context: str | None = None
    ) -> str:
        """
        Build Section II: Specific User Request.

        Args:
            user_request: The user's specific question or request
            retrieved_context: Optional context retrieved from RAG

        Returns:
            Formatted request section
        """
        section = f"""**II. SPECIFIC USER REQUEST**

{user_request}"""

        if retrieved_context:
            section += f"""

**RETRIEVED CONTEXT FROM DOCUMENTS:**
{retrieved_context}

IMPORTANT: Base your answer EXCLUSIVELY on the retrieved context above. Extract specific information, names, dates, and details directly from this context."""

        return section

    def _build_constraints_section(
        self, constraints: PromptConstraints, use_case_def: UseCaseDefinition
    ) -> str:
        """
        Build Section III: Constraints and Requirements.

        Args:
            constraints: The prompt constraints to enforce
            use_case_def: The use case definition

        Returns:
            Formatted constraints section with critical rules
        """
        output_format_desc = get_output_format_description(use_case_def.optimal_output)

        section = """**III. CONSTRAINTS AND REQUIREMENTS**

THESE CONSTRAINTS MUST BE RESPECTED BEFORE EVERYTHING ELSE.
"""

        constraint_number = 1

        # Quantity constraint (if specified)
        if constraints.quantity_constraint:
            section += f"""
{constraint_number}. **QUANTITY CONSTRAINT (CRITICAL):** {constraints.quantity_constraint}
   - This is NON-NEGOTIABLE. Count your output items before responding.
   - If you cannot provide the exact quantity, explain why instead of approximating."""
            constraint_number += 1

        # Data type constraint (if specified)
        if constraints.data_type_constraint:
            section += f"""
{constraint_number}. **DATA TYPE CONSTRAINT:** {constraints.data_type_constraint}
   - Each item must match this specification exactly."""
            constraint_number += 1

        # Format constraint (always required)
        section += f"""
{constraint_number}. **FORMAT CONSTRAINT (PRIORITY):** {constraints.format_constraint}
   - Expected format: {output_format_desc}
   - Follow this format structure precisely."""
        constraint_number += 1

        # Additional constraints
        if constraints.additional_constraints:
            for i, additional in enumerate(
                constraints.additional_constraints, start=constraint_number
            ):
                section += f"""
{i}. **ADDITIONAL REQUIREMENT:** {additional}"""

        return section

    def _build_context_section(self, additional_context: str) -> str:
        """
        Build Section IV: Additional Context (optional).

        Args:
            additional_context: Additional context or instructions

        Returns:
            Formatted context section
        """
        return f"""**IV. ADDITIONAL CONTEXT**

{additional_context}"""

    def create_constraints_for_use_case(
        self,
        use_case: UseCaseType,
        quantity: int | None = None,
        custom_format: str | None = None,
        additional: list[str] | None = None,
    ) -> PromptConstraints:
        """
        Create appropriate constraints for a specific use case.

        Args:
            use_case: The use case type
            quantity: Optional exact quantity requirement
            custom_format: Optional custom format override
            additional: Optional additional constraints

        Returns:
            PromptConstraints object configured for the use case
        """
        use_case_def = get_use_case_definition(use_case)
        output_format_desc = get_output_format_description(use_case_def.optimal_output)

        # Build quantity constraint if specified
        quantity_constraint = None
        if quantity is not None:
            quantity_constraint = (
                f"The response MUST contain EXACTLY {quantity} items/elements."
            )

        # Build data type constraint based on use case
        data_type_constraints = {
            UseCaseType.PROFESSIONAL_CONTENT: "Each section MUST be a complete paragraph with proper structure.",
            UseCaseType.CODE_DEVELOPMENT: "Each code block MUST be complete, commented, and executable.",
            UseCaseType.DATA_ANALYSIS: "Each point MUST be a specific insight or data extraction.",
            UseCaseType.CREATIVE_BRAINSTORMING: "Each element MUST be a unique, creative idea.",
            UseCaseType.STRUCTURED_PLANNING: "Each section MUST be a clear step or hierarchical component.",
            UseCaseType.BUSINESS_STRATEGY: "Each section MUST follow the required business analysis framework.",
        }

        data_type_constraint = data_type_constraints.get(use_case)

        # Format constraint
        format_constraint = (
            custom_format or f"Output MUST be formatted as: {output_format_desc}"
        )

        return PromptConstraints(
            quantity_constraint=quantity_constraint,
            data_type_constraint=data_type_constraint,
            format_constraint=format_constraint,
            additional_constraints=additional or [],
        )

    def extract_quantity_from_query(self, query: str) -> int | None:
        """
        Extract quantity requirements from a user query.

        Looks for patterns like "10 people", "5 ideas", "list of 3", etc.

        Args:
            query: The user query

        Returns:
            Extracted quantity or None if not found
        """
        import re

        # Patterns to match quantity requests
        patterns = [
            r"(\d+)\s+(?:items|elements|people|persons|persone|ideas?|idee|points|punti|steps|passaggi|titles?|titoli|creative|scenarios?|scenari)",
            r"(?:list|lista)\s+(?:of|di)\s+(\d+)",
            r"(?:give|dammi|voglio|need)\s+(?:me|una)?\s+(?:lista|list)?\s*(?:of|di)?\s*(\d+)",
            r"(?:need|voglio)\s+(\d+)",
            r"exactly\s+(\d+)",
            r"esattamente\s+(\d+)",
        ]

        query_lower = query.lower()
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue

        return None


# Singleton instance
prompt_template_service = PromptTemplateService()
