# Use Case Optimization System - User Guide

## Overview

The Document Intelligence Hub now supports **6 Common Use Cases** with optimized prompt templates that overcome LLM limitations like "Constraint Neglect" (when the model ignores specific requirements like exact quantities or formats).

**NEW:** The system now includes **automatic use case detection** - you don't need to specify the use case manually! The system analyzes your query and automatically applies the appropriate optimization.

## The 6 Use Cases (CU1-CU6)

| Code | Name | Description | Optimal Output |
|------|------|-------------|----------------|
| **CU1** | Professional Content Generation | Creating formal documents (reports, emails, essays) with specific tone and structure | Formatted Markdown with clear structure |
| **CU2** | Code Development and Debugging | Writing, debugging, or refactoring code components | Complete executable code blocks |
| **CU3** | Data Analysis and Document Synthesis | Analyzing documents, extracting key points, summarizing | Bullet lists, tables, or structured JSON |
| **CU4** | Creative Brainstorming and Ideation | Generating ideas, titles, names with quantity limits | Numbered lists with exact quantities |
| **CU5** | Structured Planning and Schemas | Creating project plans, roadmaps, outlines | Hierarchical structures |
| **CU6** | Strategic Business Documents | Generating SWOT, PESTEL, Business Cases | Fixed-section tables/schemas |

## How It Works

### 4-Section Modular Prompt Structure

Each use case generates prompts following this proven structure:

1. **PERSONALITY AND OBJECTIVE** - Sets the expert role and primary task
2. **SPECIFIC USER REQUEST** - Contains your question and retrieved context
3. **CONSTRAINTS AND REQUIREMENTS** - Critical rules the LLM MUST follow
4. **ADDITIONAL CONTEXT** - Optional supplementary information

### Key Features

- ✅ **Automatic Quantity Extraction** - Detects numbers in queries ("10 people", "5 ideas")
- ✅ **Constraint Emphasis** - Repeats critical requirements multiple times
- ✅ **Format Enforcement** - Specifies exact output format expected
- ✅ **Multilingual Support** - Works with Italian, English, and other languages
- ✅ **RAG Integration** - Combines with retrieved document context

## API Usage

### Basic Query (Automatic Detection)

The system now **automatically detects** the appropriate use case from your query!

```json
POST /rag/query/
{
  "query": "Give me a list of 10 important people",
  "user_id": "user123",
  "conversation_history": []
}
```

**What happens:**
1. System detects "list of 10" pattern → Auto-selects CU4
2. Applies constraint enforcement automatically
3. Returns exactly 10 items as requested

### Manual Use Case Specification (Optional)

You can still manually specify a use case if needed:

```json
POST /rag/query/
{
  "query": "Give me a list of 10 most important people in Sharn",
  "user_id": "user123",
  "conversation_history": [],
  "use_case": "CU4"
}
```

### Available Use Case Values

- `"CU1"` - Professional Content
- `"CU2"` - Code Development
- `"CU3"` - Data Analysis
- `"CU4"` - Creative Brainstorming ← **Best for lists and ideation**
- `"CU5"` - Structured Planning
- `"CU6"` - Business Strategy

**Note:** In most cases, you don't need to specify `use_case` - the system will detect it automatically!

## Automatic Use Case Detection

### How It Works

The system analyzes your query using pattern matching and keyword detection to automatically select the best use case.

### Detection Patterns

**CU4 - Creative Brainstorming (Auto-detected for):**
- "list of 10 people"
- "give me 5 ideas"
- "generate 7 titles"
- "brainstorm alternatives"
- Any query with quantity + items pattern

**CU3 - Data Analysis (Auto-detected for):**
- "summarize the main points"
- "what are the key insights"
- "analyze the trends"
- "extract the findings"

**CU2 - Code Development (Auto-detected for):**
- "write a Python function"
- "debug this code"
- "refactor the component"
- "create a script"

**CU6 - Business Strategy (Auto-detected for):**
- "SWOT analysis"
- "PESTEL analysis"
- "business case"
- "competitive analysis"

**CU5 - Structured Planning (Auto-detected for):**
- "create an outline"
- "project plan"
- "roadmap for"
- "steps to achieve"

**CU1 - Professional Content (Auto-detected for):**
- "write a formal report"
- "draft a professional email"
- "business proposal"

### Confidence Levels

The system calculates confidence levels for detection:
- **High:** Strong pattern match, will definitely use optimized prompt
- **Medium:** Good keyword match, optimization applied
- **Low:** Weak match, optimization applied cautiously
- **None:** No clear match, uses standard RAG prompt

### When Auto-Detection Doesn't Match

If your query doesn't clearly match any use case pattern, the system falls back to the standard RAG prompt - which still works well for general questions!

## Example Scenarios

### Scenario 1: Extract List of Names (CU4)

**Problem:** Standard RAG returns generic categories instead of specific names.

**Query:**
```json
{
  "query": "voglio una lista di 10 persone importanti a Sharn",
  "user_id": "user123",
  "use_case": "CU4"
}
```

**What Happens:**
1. System detects quantity: 10
2. Creates strict constraints: "EXACTLY 10 items"
3. Sets role: "Creative Strategist and Innovation Consultant"
4. Emphasizes: "Extract ALL specific names, prioritize names over categories"
5. Format: "Numbered list from 1 to 10"

**Result:** LLM returns exactly 10 specific names, not generic roles.

---

### Scenario 2: Generate SWOT Analysis (CU6)

**Query:**
```json
{
  "query": "Genera una analisi SWOT per il lancio del prodotto X con 4 punti per sezione",
  "user_id": "user123",
  "use_case": "CU6"
}
```

**What Happens:**
1. System detects quantity: 4
2. Creates business analysis constraints
3. Sets role: "Strategic Business Analyst"
4. Format: "Markdown table with fixed sections"
5. Each section gets EXACTLY 4 points

**Result:** Proper SWOT table with 4 items per quadrant.

---

### Scenario 3: Code Refactoring (CU2)

**Query:**
```json
{
  "query": "Refactor this Python function to use async/await",
  "user_id": "user123",
  "use_case": "CU2"
}
```

**What Happens:**
1. Sets role: "Senior Software Engineer"
2. Constraint: "Complete, commented, executable code"
3. Format: "Code block with language specification"

**Result:** Production-ready refactored code.

---

### Scenario 4: Document Summary (CU3)

**Query:**
```json
{
  "query": "Summarize the key points from the quarterly report",
  "user_id": "user123",
  "use_case": "CU3"
}
```

**What Happens:**
1. Sets role: "Data Analyst and Information Synthesis Specialist"
2. Constraint: "Bullet points or structured table"
3. Emphasizes: "Extract specific data points"

**Result:** Clean bullet-point summary with key metrics.

## When to Use Each Use Case

### Use CU1 (Professional Content) When:
- Writing formal reports or business documents
- Need specific tone (formal, professional, academic)
- Require proper document structure

### Use CU2 (Code Development) When:
- Generating code components
- Debugging or refactoring
- Need executable, tested code

### Use CU3 (Data Analysis) When:
- Summarizing documents
- Extracting key insights
- Analyzing trends or patterns

### Use CU4 (Creative Brainstorming) When:
- **Generating lists with specific quantities** ← Most common!
- Need creative ideas or alternatives
- Extracting multiple specific items (names, titles, concepts)

### Use CU5 (Structured Planning) When:
- Creating project roadmaps
- Building course outlines
- Need hierarchical structure

### Use CU6 (Business Strategy) When:
- Generating SWOT, PESTEL, Business Canvas
- Need fixed-format business documents
- Strategic analysis required

## Constraint System

### Quantity Constraints
- Automatically extracted from queries
- Patterns recognized: "10 people", "5 ideas", "list of 3", "need 7"
- Emphasized as **CRITICAL** and **NON-NEGOTIABLE**

### Format Constraints
- Specified based on use case optimal output
- LLM instructed to follow exact format
- Examples: "Numbered list 1-10", "Markdown table", "JSON with keys X,Y,Z"

### Data Type Constraints
- Each use case has specific element types
- CU4: "Each element MUST be a unique, creative idea"
- CU2: "Each code block MUST be complete and executable"
- CU6: "Each section MUST follow business analysis framework"

## Advanced Features

### Automatic Quantity Detection

Supports multiple languages and patterns:

**Italian:**
- "voglio una lista di 10 persone" → 10
- "dammi 5 idee creative" → 5
- "esattamente 7 titoli" → 7

**English:**
- "give me a list of 10 people" → 10
- "I need 5 creative ideas" → 5
- "exactly 7 titles" → 7

### Constraint Repetition

Critical constraints are repeated 3+ times throughout the prompt:
1. In the objective section
2. In the constraints section
3. With emphasis (CRITICAL, NON-NEGOTIABLE)
4. With verification instructions ("Count your output before responding")

### RAG Context Integration

When documents are retrieved, they're formatted as:

```
**RETRIEVED CONTEXT FROM DOCUMENTS:**
[DOCUMENT 1]
Section: Chapter 3
Type: Narrative
---
Content here...

[DOCUMENT 2]
Section: Chapter 5
---
More content...

IMPORTANT: Base your answer EXCLUSIVELY on the retrieved context above.
Extract specific information, names, dates, and details directly from this context.
```

## Performance Tips

1. **Let auto-detection work** - In most cases, just write natural queries:
   - "Give me a list of 10 people" ✅ (auto-detects CU4)
   - "Summarize the key points" ✅ (auto-detects CU3)
   - "Write a function to validate emails" ✅ (auto-detects CU2)

2. **Manual override when needed** - Specify `use_case` only if:
   - Auto-detection picks wrong use case
   - You want to force a specific prompt style
   - Testing different approaches

3. **Be explicit for best results** - Include:
   - The number of items wanted ("10 people", not just "some people")
   - The type of elements (names, ideas, steps)
   - Action keywords (summarize, analyze, create, write)

4. **Trust the fallback** - If no use case matches, standard RAG still works well for general questions

## Troubleshooting

### Problem: Getting categories instead of specific names
**Solution:** 
- Auto-detection should handle this automatically for queries like "list of 10 people"
- If not working, manually specify `use_case: "CU4"`

### Problem: Not getting exact quantity requested
**Solution:** 
- Make sure your query includes the number ("10 people", not "some people")
- Auto-detection will activate CU4 which enforces exact counts
- Check debug logs to see if use case was detected

### Problem: Wrong output format
**Solution:** 
- Be more explicit in your query (use keywords like "summarize", "analyze", "write code")
- Manually specify the appropriate use case if auto-detection fails

### Problem: Auto-detection picks wrong use case
**Solution:** 
- Override with manual `use_case` parameter
- Report the query pattern so we can improve detection

### Problem: Generic answers when documents have details
**Solution:** 
- Use appropriate keywords to trigger auto-detection ("list", "summarize", "extract")
- Be specific about what you want ("10 people" vs "some people")

## Implementation Details

### Backend Files Created

1. `app/schemas/use_cases.py` - Defines all 6 use cases and their characteristics
2. `app/services/prompt_template_service.py` - Generates optimized prompts
3. `app/services/use_case_detection_service.py` - **NEW:** Auto-detects use cases from queries
4. `tests/test_use_cases.py` - 13 tests for prompt generation
5. `tests/test_use_case_detection.py` - **NEW:** 16 tests for auto-detection

### API Changes

- `QueryRequest` schema: Added optional `use_case` field
- `answer_query()` method: Auto-detection when `use_case` is None
- Router: Passes use_case to service layer (auto-detected or manual)

### Detection Algorithm

1. Query is analyzed with regex patterns (weight: 3 points per match)
2. Keywords are checked (weight: 1 point per match)
3. Use case with highest score is selected
4. If score > 0, use case is applied
5. If score = 0, fallback to standard RAG

## Testing

Run all tests (47 total):
```bash
pytest -v
```

Run only use case tests:
```bash
pytest tests/test_use_cases.py -v           # 13 tests - prompt generation
pytest tests/test_use_case_detection.py -v  # 16 tests - auto-detection
```

All tests should pass! ✅

## Future Enhancements

- [x] Auto-detect use case from query intent ✅ **IMPLEMENTED**
- [ ] ML-based use case prediction with learning
- [ ] Custom constraint profiles per user
- [ ] Use case recommendations in API response
- [ ] Performance metrics per use case
- [ ] Frontend UI for use case selection and override

---

**Note:** The use case system is **fully automatic** but also supports manual specification. Most queries will automatically benefit from optimized prompts without any explicit configuration needed!
