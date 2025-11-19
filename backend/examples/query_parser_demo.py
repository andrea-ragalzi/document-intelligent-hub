"""
Demo script for Query Parser Service - File Filtering for RAG

This script demonstrates the new LLM-based file filtering capability
that allows users to naturally specify which files to include or exclude
from their RAG search queries.

EXAMPLES:
---------

1. INCLUDE filter (Italian):
   Query: "Quali sono i requisiti solo nel file report.pdf?"
   → Searches ONLY in report.pdf
   
2. EXCLUDE filter (English):
   Query: "Search for Python info but exclude tutorial.pdf"
   → Searches all files EXCEPT tutorial.pdf
   
3. BOTH filters:
   Query: "Usa data.pdf e report.pdf ma escludi draft.pdf"
   → Searches ONLY in data.pdf and report.pdf (draft.pdf excluded)

USAGE:
------
# From router (automatic):
The router automatically extracts file filters and passes them to the RAG service.

# Direct service usage:
from app.services.query_parser_service import query_parser_service

result = query_parser_service.extract_file_filters(
    query="Cerca solo nel file report.pdf",
    available_files=["report.pdf", "data.pdf", "specs.pdf"]
)

print(f"Include: {result.include_files}")  # ["report.pdf"]
print(f"Exclude: {result.exclude_files}")  # []
print(f"Cleaned: {result.cleaned_query}")  # "Cerca"

ARCHITECTURE:
-------------
1. Router receives query from user
2. Router gets user's available documents
3. Query Parser Service extracts file references using LLM (gpt-4o-mini)
4. Cleaned query + filters passed to RAG Service
5. Repository applies metadata filters to ChromaDB query
6. Results returned only from specified files

BENEFITS:
---------
- Natural language interface (no special syntax)
- Multilingual support (IT, EN, FR, DE, ES, etc.)
- Case-insensitive filename matching
- Automatic validation against available documents
- Graceful fallback if extraction fails
"""

# Example 1: Basic include filter
example_1_query = "Quali sono i requisiti solo nel file requirements.pdf?"
example_1_available = ["requirements.pdf", "specs.pdf", "guide.pdf"]

print("="*80)
print("EXAMPLE 1: INCLUDE FILTER (Italian)")
print("="*80)
print(f"Query: {example_1_query}")
print(f"Available files: {example_1_available}")
print()
print("Expected extraction:")
print("  - include_files: ['requirements.pdf']")
print("  - exclude_files: []")
print("  - cleaned_query: 'Quali sono i requisiti?'")
print()
print("RAG will search ONLY in requirements.pdf")
print()

# Example 2: Exclude filter
example_2_query = "Find information about Python but exclude tutorial.pdf"
example_2_available = ["tutorial.pdf", "reference.pdf", "guide.pdf", "cookbook.pdf"]

print("="*80)
print("EXAMPLE 2: EXCLUDE FILTER (English)")
print("="*80)
print(f"Query: {example_2_query}")
print(f"Available files: {example_2_available}")
print()
print("Expected extraction:")
print("  - include_files: []")
print("  - exclude_files: ['tutorial.pdf']")
print("  - cleaned_query: 'Find information about Python'")
print()
print("RAG will search in reference.pdf, guide.pdf, cookbook.pdf (NOT tutorial.pdf)")
print()

# Example 3: Both filters
example_3_query = "Usa report.pdf e data.pdf ma non draft.pdf per l'analisi"
example_3_available = ["report.pdf", "data.pdf", "draft.pdf", "notes.pdf"]

print("="*80)
print("EXAMPLE 3: BOTH FILTERS (Italian)")
print("="*80)
print(f"Query: {example_3_query}")
print(f"Available files: {example_3_available}")
print()
print("Expected extraction:")
print("  - include_files: ['report.pdf', 'data.pdf']")
print("  - exclude_files: ['draft.pdf']")
print("  - cleaned_query: 'L'analisi'")
print()
print("RAG will search ONLY in report.pdf and data.pdf")
print("(Include takes precedence, so exclude is ignored)")
print()

# Example 4: No filters (normal query)
example_4_query = "What is the main topic discussed in the documents?"
example_4_available = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]

print("="*80)
print("EXAMPLE 4: NO FILTERS (Normal Query)")
print("="*80)
print(f"Query: {example_4_query}")
print(f"Available files: {example_4_available}")
print()
print("Expected extraction:")
print("  - include_files: []")
print("  - exclude_files: []")
print("  - cleaned_query: 'What is the main topic discussed in the documents?'")
print()
print("RAG will search in ALL available documents (no filtering)")
print()

# Example 5: Case-insensitive matching
example_5_query = "Search in REPORT.PDF only"
example_5_available = ["report.pdf", "Data.PDF", "specs.pdf"]

print("="*80)
print("EXAMPLE 5: CASE-INSENSITIVE MATCHING")
print("="*80)
print(f"Query: {example_5_query}")
print(f"Available files: {example_5_available}")
print()
print("Expected extraction:")
print("  - include_files: ['report.pdf']  # Matched case-insensitively")
print("  - exclude_files: []")
print("  - cleaned_query: 'Search only'")
print()
print("RAG will search ONLY in report.pdf (matched 'REPORT.PDF' → 'report.pdf')")
print()

print("="*80)
print("API ENDPOINT INTEGRATION")
print("="*80)
print("""
POST /rag/query/
{
  "query": "Cerca solo nel file report.pdf informazioni su Python",
  "user_id": "user-123",
  "conversation_history": [],
  "output_language": "IT"
}

INTERNAL FLOW:
1. Router extracts user's documents: ["report.pdf", "data.pdf", "guide.pdf"]
2. Query Parser detects file reference and extracts:
   - include_files: ["report.pdf"]
   - cleaned_query: "Informazioni su Python"
3. RAG Service receives:
   - query: "Informazioni su Python"
   - include_files: ["report.pdf"]
4. Repository creates filtered retriever:
   - filter: {source: "user-123", original_filename: {$in: ["report.pdf"]}}
5. Vector search returns chunks ONLY from report.pdf
6. LLM generates answer based on filtered context
7. Response returned to user with source: ["report.pdf"]
""")

print("="*80)
print("SUPPORTED PATTERNS (Multi-language)")
print("="*80)
print("""
INCLUDE patterns:
  - "only in file X" / "solo nel file X"
  - "search in X" / "cerca in X"
  - "use document X" / "usa documento X"
  - "nel documento X" / "in the document X"

EXCLUDE patterns:
  - "exclude file Y" / "escludi Y"
  - "without Y" / "senza Y"
  - "ignore Y" / "ignora Y"
  - "don't search in Y" / "non cercare in Y"

SUPPORTED LANGUAGES:
  - Italian (IT)
  - English (EN)
  - French (FR)
  - German (DE)
  - Spanish (ES)
  - And more...
""")

print("="*80)
print("PERFORMANCE OPTIMIZATION")
print("="*80)
print("""
The router includes a fast heuristic check BEFORE calling the LLM:

if query_parser_service.has_file_references(query):
    # Only call LLM if file references detected
    filters = query_parser_service.extract_file_filters(...)
else:
    # Skip LLM call for normal queries (saves time & cost)
    filters = None

This heuristic checks for keywords like:
  - "file", "documento", "document"
  - "solo", "only", "escludi", "exclude"
  - File extensions (.pdf, .docx, etc.)
  - "senza", "without", "ignora", "ignore"

Result: LLM called ONLY when needed, reducing latency and API costs.
""")

print("="*80)
print("ERROR HANDLING")
print("="*80)
print("""
If LLM extraction fails (network error, API limit, etc.):
  → Fallback: No filtering applied, search all documents
  → User query proceeds normally
  → Error logged for debugging
  → No crash or user-facing error

If user mentions non-existent file:
  → Validation against available_files
  → Invalid filenames filtered out
  → Only valid files included in filter
  → User gets results from valid files only
""")

print()
print("Implementation complete! 🎉")
print()
print("Test the feature:")
print("  1. Start backend: cd backend && poetry run uvicorn main:app --reload")
print("  2. Use API: POST /rag/query/ with file filter queries")
print("  3. Check logs for filter extraction details")
