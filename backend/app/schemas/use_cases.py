"""
Use Case Definitions for Document Intelligence Hub.

This module defines the 6 common use cases for content and application hubs,
with their characteristics, optimal output formats, and prompt constraints.
"""

from enum import Enum
from typing import Dict

from pydantic import BaseModel, Field


class UseCaseType(str, Enum):
    """
    Enumeration of the 6 common use cases for the hub.
    """

    GENERIC = "GENERIC"             # Generic use case for fallback
    PROFESSIONAL_CONTENT = "CU1"  # Professional content generation
    CODE_DEVELOPMENT = "CU2"       # Code development and debugging
    DATA_ANALYSIS = "CU3"          # Data analysis and document synthesis
    CREATIVE_BRAINSTORMING = "CU4" # Creative brainstorming and ideation
    STRUCTURED_PLANNING = "CU5"    # Plans and structured schemas
    BUSINESS_STRATEGY = "CU6"      # Strategic business documents


class OutputFormat(str, Enum):
    """
    Standard output formats for different use cases.
    """
    MARKDOWN_TEXT = "markdown_text"           # Formatted text with structure
    CODE_BLOCK = "code_block"                 # Complete executable code
    BULLET_LIST = "bullet_list"               # Bullet points or table
    NUMBERED_LIST = "numbered_list"           # Numbered list with constraints
    HIERARCHICAL = "hierarchical"             # Hierarchical structure
    STRUCTURED_TABLE = "structured_table"     # Fixed-section table/schema
    JSON_STRUCTURED = "json_structured"       # JSON with specific keys


class UseCaseDefinition(BaseModel):
    """
    Complete definition of a use case with its characteristics.
    """
    code: UseCaseType
    name: str
    description: str
    typical_activity: str
    optimal_output: OutputFormat
    role_persona: str  # The expert role to assume
    constraint_priority: str  # Type of constraint (quantity, format, etc.)
    
    
# Dictionary mapping use case types to their full definitions
USE_CASE_DEFINITIONS: Dict[UseCaseType, UseCaseDefinition] = {
    UseCaseType.GENERIC: UseCaseDefinition(
        code=UseCaseType.GENERIC,
        name="Generic Query",
        description="General question-answer interaction without specific use case requirements",
        typical_activity="Answering general questions based on document context",
        optimal_output=OutputFormat.MARKDOWN_TEXT,
        role_persona="Knowledgeable Assistant and Information Provider",
        constraint_priority="CLARITY: Clear, accurate response based on provided context"
    ),
    
    UseCaseType.PROFESSIONAL_CONTENT: UseCaseDefinition(
        code=UseCaseType.PROFESSIONAL_CONTENT,
        name="Professional Content Generation",
        description="User needs an initial draft of a formal document (report, complex email, academic essay) with specific tone and length",
        typical_activity="Creating professional documents with specific tone and structure requirements",
        optimal_output=OutputFormat.MARKDOWN_TEXT,
        role_persona="Professional Writer and Communication Expert",
        constraint_priority="FORMAT: Clear structure with titles and paragraphs"
    ),
    
    UseCaseType.CODE_DEVELOPMENT: UseCaseDefinition(
        code=UseCaseType.CODE_DEVELOPMENT,
        name="Code Development and Debugging",
        description="User requests a software component, error correction, or refactoring of an existing function in a specific language",
        typical_activity="Writing, debugging, or refactoring code components",
        optimal_output=OutputFormat.CODE_BLOCK,
        role_persona="Senior Software Engineer and Code Architect",
        constraint_priority="COMPLETENESS: Fully executable, commented, production-ready code"
    ),
    
    UseCaseType.DATA_ANALYSIS: UseCaseDefinition(
        code=UseCaseType.DATA_ANALYSIS,
        name="Data Analysis and Document Synthesis",
        description="User uploads or provides text/document/data and requests a summary, key point extraction, or trend analysis",
        typical_activity="Analyzing documents and extracting structured insights",
        optimal_output=OutputFormat.BULLET_LIST,
        role_persona="Data Analyst and Information Synthesis Specialist",
        constraint_priority="STRUCTURE: Bullet points or structured table/JSON"
    ),
    
    UseCaseType.CREATIVE_BRAINSTORMING: UseCaseDefinition(
        code=UseCaseType.CREATIVE_BRAINSTORMING,
        name="Creative Brainstorming and Ideation",
        description="User seeks ideas, titles, project names, or short stories, often with quantity limits (e.g., '5 catchy titles', '3 possible scenarios')",
        typical_activity="Generating creative ideas with specific quantity constraints",
        optimal_output=OutputFormat.NUMBERED_LIST,
        role_persona="Creative Strategist and Innovation Consultant",
        constraint_priority="QUANTITY: EXACT number of items as requested"
    ),
    
    UseCaseType.STRUCTURED_PLANNING: UseCaseDefinition(
        code=UseCaseType.STRUCTURED_PLANNING,
        name="Structured Plans and Schemas",
        description="User wants to define the structure for a project, study plan, roadmap, or index (e.g., 'Course outline for X', 'Steps to launch product Y')",
        typical_activity="Creating hierarchical plans and structured outlines",
        optimal_output=OutputFormat.HIERARCHICAL,
        role_persona="Project Manager and Strategic Planner",
        constraint_priority="HIERARCHY: Clear hierarchical structure with sections and subsections"
    ),
    
    UseCaseType.BUSINESS_STRATEGY: UseCaseDefinition(
        code=UseCaseType.BUSINESS_STRATEGY,
        name="Strategic Business Documents",
        description="User requests key business documents (SWOT, PESTEL, Business Case, Value Proposition) following a fixed model",
        typical_activity="Generating strategic business analysis documents",
        optimal_output=OutputFormat.STRUCTURED_TABLE,
        role_persona="Strategic Business Analyst and Consultant",
        constraint_priority="FIXED STRUCTURE: Table or schema with fixed sections"
    )
}


class PromptConstraints(BaseModel):
    """
    Constraints to be applied to a prompt for a specific use case.
    """
    quantity_constraint: str | None = Field(
        None, 
        description="Exact quantity requirement (e.g., 'EXACTLY 5 items', 'MUST contain 10 elements')"
    )
    data_type_constraint: str | None = Field(
        None,
        description="Type of data elements required (e.g., 'Each element MUST be a single idea')"
    )
    format_constraint: str = Field(
        ...,
        description="Output format requirement (e.g., 'MUST be formatted as Markdown numbered list')"
    )
    additional_constraints: list[str] = Field(
        default_factory=list,
        description="Additional constraints specific to the use case"
    )
    
    
def get_use_case_definition(use_case: UseCaseType) -> UseCaseDefinition:
    """
    Retrieve the full definition for a specific use case.
    
    Args:
        use_case: The use case type to retrieve
        
    Returns:
        Complete use case definition with all characteristics
    """
    return USE_CASE_DEFINITIONS[use_case]


def get_output_format_description(output_format: OutputFormat) -> str:
    """
    Get a detailed description of an output format for prompt construction.
    
    Args:
        output_format: The output format to describe
        
    Returns:
        Human-readable description suitable for inclusion in prompts
    """
    format_descriptions = {
        OutputFormat.MARKDOWN_TEXT: "Formatted Markdown text with clear structure (titles, paragraphs, emphasis)",
        OutputFormat.CODE_BLOCK: "Complete code block with language specification, comments, and proper formatting",
        OutputFormat.BULLET_LIST: "Bullet point list or Markdown table with clear organization",
        OutputFormat.NUMBERED_LIST: "Numbered list from 1 to N, where N is the EXACT quantity requested",
        OutputFormat.HIERARCHICAL: "Hierarchical structure with main titles and nested subtitles (using Markdown headers)",
        OutputFormat.STRUCTURED_TABLE: "Markdown table with fixed columns and required number of rows per section",
        OutputFormat.JSON_STRUCTURED: "Valid JSON with specified keys and structure"
    }
    return format_descriptions.get(output_format, "Structured output")
