"""
Prompt Template Service for Optimized LLM Interactions.

This service generates structured, modular prompts following best practices
to overcome issues like "Constraint Neglect" and ensure adherence to
quantity, format, and quality requirements.

The prompt structure enforces RAG context usage and includes:
    - System-level RAG enforcement rules (loaded from environment)
    - User request
    - Retrieved context block
    - Final question
"""

from app.core.config import settings
from app.schemas.use_cases import PromptConstraints, UseCaseType


class PromptTemplateService:
    """
    Service for generating optimized, constraint-aware prompts.

    This service implements structured prompts with RAG context enforcement
    to ensure LLM adherence to document-based information.
    """

    def __init__(self):
        """Initialize the prompt template service."""
        pass

    def build_modular_prompt(
        self,
        user_request: str,
        constraints: PromptConstraints | None = None,
        additional_context: str | None = None,
        retrieved_context: str | None = None,
    ) -> str:
        """
        Build a complete modular prompt with RAG context enforcement.

        Args:
            user_request: The specific user request/question
            constraints: Optional prompt constraints (quantity, format, data type)
            additional_context: Optional additional context or instructions
            retrieved_context: Optional RAG-retrieved context from documents

        Returns:
            Complete structured prompt ready for LLM consumption
        """
        # System-level enforcement header
        system_header = self._build_context_enforcement_header()

        # Build constraints section if provided
        constraints_section = ""
        if constraints:
            constraints_section = self._build_constraints_section(constraints)

        # Additional context section (if provided)
        context_section = ""
        if additional_context:
            context_section = self._build_context_section(additional_context)

        # RAG context block
        rag_context_block = self._build_rag_context_block(retrieved_context)
        
        # Final question block
        final_question_block = self._build_new_question_block(user_request)

        # Combine all sections
        prompt_parts = [system_header]
        
        if constraints_section:
            prompt_parts.append(constraints_section)
            
        if context_section:
            prompt_parts.append(context_section)
            
        prompt_parts.append(rag_context_block)
        prompt_parts.append(final_question_block)

        return "\n\n".join(prompt_parts)

    def create_constraints_for_use_case(self, use_case: UseCaseType, quantity: int | None = None) -> PromptConstraints:
        """
        Create prompt constraints based on a specific use case.
        """
        from app.schemas.use_cases import (
            get_output_format_description,
            get_use_case_definition,
        )

        definition = get_use_case_definition(use_case)
        
        # The definition provides the *type* of format, we need the description
        format_description = get_output_format_description(definition.optimal_output)

        # For business strategy, we add a specific instruction
        if use_case == UseCaseType.BUSINESS_STRATEGY:
            format_description += " using a business analysis framework (e.g., SWOT, PESTEL)."

        # No specific data type constraints are defined for the base use cases yet
        data_type = None

        return self.create_constraints(
            quantity=quantity,
            data_type=data_type,
            custom_format=format_description,
            additional=[],
        )

    def get_query_rewriter_prompt(self, query: str) -> str:
        """Return the ultra-concise (TOON) prompt for the query rewriter agent."""
        return (
            "TOON|QUERY-REWRITER v6\n"
            "TASK: emit EXACTLY 4 recall-max search clauses.\n"
            "FORMAT: JSON array of four strings. Nothing else.\n"
            "PLAYBOOK:\n"
            "1. Split intents; one focus per clause.\n"
            "2. Expand nouns into Entità Operative Chiave, synonyms, protocol IDs, telemetry tags.\n"
            "3. Compress tokens: drop filler, keep domain nouns/verbs, prefer hyphenated n-grams.\n"
            "4. Mirror query language; if multilingual, pair key terms in both tongues.\n"
            "5. Ban duplicates, commentary, numbering, markdown.\n"
            f"USER QUERY: {query}\n"
            "RETURN:"
        )

    def _build_context_enforcement_header(self) -> str:
        """
        Build the mandatory system header enforcing RAG context usage.
        
        Now loads from environment variable (settings.RAG_SYSTEM_PROMPT)
        instead of hardcoded text for security and flexibility.
        """
        # Use environment-configured prompt instead of hardcoded
        # This allows different prompts for dev/staging/prod without code changes
        return f"""**SYSTEM RAG CONTEXT ENFORCEMENT HEADER**

{settings.RAG_SYSTEM_PROMPT}"""

    def _build_rag_context_block(self, retrieved_context: str | None) -> str:
        """Create the dedicated [RAG Context] block placed before the question."""
        context_content = (
            retrieved_context.strip()
            if retrieved_context and retrieved_context.strip()
            else "NESSUNA INFORMAZIONE DISPONIBILE NEL CONTESTO RECUPERATO."
        )
        return f"""[RAG Context]
{context_content}"""

    def _build_new_question_block(self, user_request: str) -> str:
        """Attach the final user question immediately after the context block."""
        return f"""[New Question]
{user_request}"""

    def _build_constraints_section(self, constraints: PromptConstraints) -> str:
        """
        Build constraints and requirements section.

        Args:
            constraints: The prompt constraints to enforce

        Returns:
            Formatted constraints section with critical rules
        """
        section = """**CONSTRAINTS AND REQUIREMENTS**

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

        # Format constraint (if specified)
        if constraints.format_constraint:
            section += f"""
{constraint_number}. **FORMAT CONSTRAINT (PRIORITY):** {constraints.format_constraint}
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
        Build additional context section.

        Args:
            additional_context: Additional context or instructions

        Returns:
            Formatted context section
        """
        return f"""**ADDITIONAL CONTEXT**

{additional_context}"""

    def create_constraints(
        self,
        quantity: int | None = None,
        data_type: str | None = None,
        custom_format: str | None = None,
        additional: list[str] | None = None,
    ) -> PromptConstraints:
        """
        Create prompt constraints.

        Args:
            quantity: Optional exact quantity requirement
            data_type: Optional data type description
            custom_format: Optional custom format specification
            additional: Optional additional constraints

        Returns:
            PromptConstraints object
        """
        # Build quantity constraint if specified
        quantity_constraint = None
        if quantity is not None:
            quantity_constraint = (
                f"The response MUST contain EXACTLY {quantity} items/elements."
            )

        # Format constraint - default if not provided
        if custom_format is None:
            custom_format = "Provide a clear and well-structured response."

        return PromptConstraints(
            quantity_constraint=quantity_constraint,
            data_type_constraint=data_type,
            format_constraint=custom_format,
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
