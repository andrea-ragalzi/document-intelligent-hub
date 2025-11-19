"""
Query Parser Service - Extract File Filters and Optimize Queries

This service uses OpenAI gpt-4o-mini with structured output for:
1. Extracting file references (include/exclude)
2. Cleaning the query by removing file mentions
3. Correcting grammar and spelling errors
4. Removing filler words and redundancy
5. Multilingual support (Italian, English, mixed)

Cost analysis:
- gpt-4o-mini: $0.15/1M input tokens, $0.60/1M output tokens
- Typical query: ~150 input + ~60 output tokens = $0.00007 (~0.07 cents)
- 1000 queries = $0.07 (7 cents)

Examples:
- "Search only in file report.pdf for expenses" → include: [report.pdf], cleaned: "expenses"
- "Exclude tutorial.pdf from search" → exclude: [tutorial.pdf], cleaned: "search"
- "tipo volevo sapere come configurare" → cleaned: "Come configurare?"
- "qual'è" → "Qual è" (grammar fix)
"""

from typing import List

from app.core.config import settings
from app.core.logging import logger
from app.db.chroma_client import get_embedding_function
from app.schemas.rag_schema import FileFilterResponse
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, SecretStr


class FileFilterExtraction(BaseModel):
    """Structured output for file filter extraction."""
    include_files: List[str] = Field(
        default_factory=list,
        description="List of filenames to INCLUDE in search (search ONLY in these files)"
    )
    exclude_files: List[str] = Field(
        default_factory=list,
        description="List of filenames to EXCLUDE from search (do NOT search in these files)"
    )
    cleaned_query: str = Field(
        ...,
        description="The query with all file references removed, grammar corrected, and unnecessary words removed"
    )


class QueryParserService:
    """
    Service for extracting file filters and optimizing queries.
    
    Uses OpenAI gpt-4o-mini with structured output:
    - Multilingual understanding (Italian, English, mixed)
    - Accurate extraction of include/exclude lists
    - Grammar and spelling correction
    - Filler word removal (tipo, praticamente, basically, like)
    - Intelligent query cleaning and optimization
    - Low cost (~$0.00007 per query)
    
    Benefits:
    - Handles complex queries with multiple files
    - Understands context (exclude vs include)
    - Improves query quality for better retrieval
    - Works with any language and synonyms
    - Structured JSON output (no parsing errors)
    """
    
    def __init__(self):
        """Initialize the query parser with OpenAI gpt-4o-mini."""
        # Use gpt-4o-mini for cost-effective file extraction
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=SecretStr(settings.OPENAI_API_KEY)
        )
        
        # Parser for structured output
        self.parser = JsonOutputParser(pydantic_object=FileFilterExtraction)
        
        # Get embedding function for file validation (HuggingFace - free)
        self.embeddings = get_embedding_function()
        
        logger.debug("✅ QueryParserService initialized with gpt-4o-mini (low cost, high accuracy)")
    
    def extract_file_filters(
        self,
        query: str,
        available_files: List[str]
    ) -> FileFilterResponse:
        """
        Extract file filters and optimize query for semantic search.
        
        Uses OpenAI gpt-4o-mini with structured output to:
        1. Identify file references in the query
        2. Classify them as include or exclude based on context
        3. Clean the query by removing file mentions
        4. Correct grammar and spelling errors
        5. Remove filler words and redundancy
        
        Args:
            query: The user's natural language query (any language)
            available_files: List of available document filenames for validation
        
        Returns:
            FileFilterResponse with include_files, exclude_files, and optimized cleaned_query
        
        Example:
            >>> service.extract_file_filters(
            ...     "tipo volevo sapere qual'è il budget escludi i file A.pdf, B.pdf",
            ...     ["A.pdf", "B.pdf", "C.pdf"]
            ... )
            FileFilterResponse(
                include_files=[],
                exclude_files=["A.pdf", "B.pdf"],
                cleaned_query="Qual è il budget?",
                original_query="tipo volevo sapere qual'è il budget escludi i file A.pdf, B.pdf"
            )
        """
        try:
            logger.info(f"🔍 Parsing query for file filters: {query[:100]}...")
            logger.debug(f"   Available files: {available_files}")
            
            # Build prompt for LLM
            prompt = self._build_extraction_prompt(query, available_files)
            
            # Call LLM with structured output
            chain = prompt | self.llm | self.parser
            result = chain.invoke({
                "query": query,
                "available_files": "\n".join([f"- {f}" for f in available_files])
            })
            
            logger.debug(f"   LLM extraction result: {result}")
            
            # Validate filenames against available files
            validated_include = self._validate_filenames(
                result["include_files"], available_files
            )
            validated_exclude = self._validate_filenames(
                result["exclude_files"], available_files
            )
            
            # Use cleaned query from LLM
            cleaned_query = result["cleaned_query"].strip()
            
            # Ensure cleaned query is not empty
            if not cleaned_query or len(cleaned_query) < 3:
                logger.warning("⚠️  Cleaned query too short, using original")
                cleaned_query = query
            
            logger.info("✅ File filters extracted:")
            logger.info(f"   Include: {validated_include}")
            logger.info(f"   Exclude: {validated_exclude}")
            logger.info(f"   Cleaned query: {cleaned_query}")
            
            return FileFilterResponse(
                include_files=validated_include,
                exclude_files=validated_exclude,
                original_query=query,
                cleaned_query=cleaned_query
            )
            
        except Exception as e:
            logger.error(f"❌ File filter extraction failed: {e}")
            logger.info("   Falling back to no filtering")
            
            # Fallback: no filtering, use original query
            return FileFilterResponse(
                include_files=[],
                exclude_files=[],
                original_query=query,
                cleaned_query=query
            )
    
    def _build_extraction_prompt(
        self, 
        query: str, 
        available_files: List[str]
    ) -> ChatPromptTemplate:
        """
        Build the prompt for file filter extraction.
        
        Uses clear instructions with examples to guide the LLM.
        """
        template = """You are a file filter extraction and query optimization expert. Your task is to:
1. Extract files to INCLUDE in search (search ONLY in these files)
2. Extract files to EXCLUDE from search (do NOT search in these files)
3. Clean and optimize the query for semantic search

FILE EXTRACTION RULES:
- Extract exact filenames as they appear in the query
- Understand context: "only in X", "search in X", "mentioned in X", "menzionata nel X" → INCLUDE X
- Understand context: "exclude X", "escludi X", "without X", "not in X", "ignore X" → EXCLUDE X
- If multiple files in a list → extract all of them
- Return EXACT filenames from the query (case-sensitive)

QUERY CLEANING RULES:
- Remove ALL file references (filenames, phrases like "in file", "escludi i file", "menzionata nel", etc.)
- Fix grammar and spelling errors (typos, verb agreement, article usage)
- Remove filler words: "tipo", "praticamente", "diciamo", "comunque", "insomma", "basically", "like", "actually"
- Remove redundant words while preserving meaning
- Keep the query concise and clear for semantic search
- Preserve the original language (Italian stays Italian, English stays English)

AVAILABLE FILES (for reference):
{available_files}

USER QUERY:
{query}

EXAMPLES:

Query: "Search only in report.pdf for expenses"
→ include_files: ["report.pdf"], exclude_files: [], cleaned_query: "expenses"

Query: "Find Python info but exclude tutorial.pdf"
→ include_files: [], exclude_files: ["tutorial.pdf"], cleaned_query: "Python information"

Query: "escludi i file A.pdf, B.pdf e C.pdf"
→ include_files: [], exclude_files: ["A.pdf", "B.pdf", "C.pdf"], cleaned_query: ""

Query: "i velociraptor sanno aprire le porte? escludi i file X.pdf, Y.pdf e Z.pdf"
→ include_files: [], exclude_files: ["X.pdf", "Y.pdf", "Z.pdf"], cleaned_query: "I velociraptor sanno aprire le porte?"

Query: "tipo, praticamente volevo sapere come fare per, diciamo, configurare il server"
→ include_files: [], exclude_files: [], cleaned_query: "Come configurare il server?"

Query: "qual'è il costo totale del progetto menzionato nel Budget.pdf?"
→ include_files: ["Budget.pdf"], exclude_files: [], cleaned_query: "Qual è il costo totale del progetto?"

Now extract from the user query above and apply all rules.

{format_instructions}
"""
        
        prompt = ChatPromptTemplate.from_template(template)
        prompt = prompt.partial(format_instructions=self.parser.get_format_instructions())
        
        return prompt
    
    def _validate_filenames(
        self, 
        extracted_files: List[str], 
        available_files: List[str]
    ) -> List[str]:
        """
        Validate extracted filenames against available files.
        
        Uses case-insensitive exact matching first, then falls back to
        semantic similarity (HuggingFace embeddings) for fuzzy matches.
        
        This ensures LLM-extracted filenames match actual available files.
        """
        if not extracted_files or not available_files:
            return []
        
        validated = []
        available_lower = {f.lower(): f for f in available_files}
        
        for extracted in extracted_files:
            extracted_lower = extracted.lower()
            
            # Try exact match (case-insensitive)
            if extracted_lower in available_lower:
                validated.append(available_lower[extracted_lower])
                logger.debug(f"   ✓ Exact match: {extracted} → {available_lower[extracted_lower]}")
            else:
                # Try fuzzy match using HuggingFace embeddings
                best_match = self._find_best_match(extracted, available_files)
                if best_match:
                    validated.append(best_match)
                    logger.debug(f"   ✓ Fuzzy match: {extracted} → {best_match}")
                else:
                    logger.warning(f"   ✗ No match found for: {extracted}")
        
        return validated
    
    def _find_best_match(
        self, 
        filename: str, 
        available_files: List[str],
        threshold: float = 0.7
    ) -> str | None:
        """
        Find best matching filename using semantic similarity.
        
        Uses HuggingFace embeddings (free, local) to compute cosine similarity.
        Only returns match if similarity > threshold.
        """
        try:
            import numpy as np
            
            # Get embedding for extracted filename
            filename_embedding = self.embeddings.embed_query(filename)
            
            # Get embeddings for all available files
            available_embeddings = self.embeddings.embed_documents(available_files)
            
            # Compute cosine similarities
            similarities = [
                np.dot(filename_embedding, available_emb) 
                for available_emb in available_embeddings
            ]
            
            # Find best match
            max_similarity = max(similarities)
            if max_similarity >= threshold:
                best_idx = similarities.index(max_similarity)
                logger.debug(f"   Similarity: {max_similarity:.2f} for {available_files[best_idx]}")
                return available_files[best_idx]
            
            return None
            
        except Exception as e:
            logger.error(f"   Error computing similarity: {e}")
            return None


# --- Global Service Instance ---

# Singleton instance for dependency injection
query_parser_service = QueryParserService()
