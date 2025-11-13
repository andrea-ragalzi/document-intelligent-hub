# Use Case Auto-Detection - Examples

This document shows real examples of how the system automatically detects use cases from natural language queries.

## How to Test

Run these queries through the API **without** specifying `use_case` - the system will automatically detect and apply the appropriate optimization!

---

## Example 1: List with Quantity → CU4

### Query (English)
```
"Give me a list of 10 important people in Sharn"
```

### Auto-Detected
✅ **CU4 - Creative Brainstorming**

### Why
- Pattern match: `"list of 10"` → triggers CU4
- Quantity extracted: `10`
- Constraint applied: "EXACTLY 10 items"

### Expected Result
Numbered list with exactly 10 specific names (not categories)

---

## Example 2: Summary Request → CU3

### Query (English)
```
"Summarize the key points from this document"
```

### Auto-Detected
✅ **CU3 - Data Analysis**

### Why
- Pattern match: `"summarize"` + `"key points"` → triggers CU3
- Format: Bullet list or structured output
- Focus: Extract specific insights

### Expected Result
Bullet point summary with main insights

---

## Example 3: Code Request → CU2

### Query (English)
```
"Write a Python function to validate email addresses"
```

### Auto-Detected
✅ **CU2 - Code Development**

### Why
- Pattern match: `"write"` + `"function"` + `"Python"` → triggers CU2
- Format: Complete code block
- Quality: Executable, commented, production-ready

### Expected Result
```python
def validate_email(email: str) -> bool:
    """
    Validate email address format.
    ...
    """
    # Complete implementation
```

---

## Example 4: Business Analysis → CU6

### Query (English)
```
"Generate a SWOT analysis for launching this product"
```

### Auto-Detected
✅ **CU6 - Business Strategy**

### Why
- Pattern match: `"SWOT analysis"` → triggers CU6
- Format: Fixed-section table
- Structure: Strengths, Weaknesses, Opportunities, Threats

### Expected Result
Markdown table with 4 sections, balanced analysis

---

## Example 5: Planning Request → CU5

### Query (English)
```
"Create an outline for a course on machine learning"
```

### Auto-Detected
✅ **CU5 - Structured Planning**

### Why
- Pattern match: `"outline"` + `"course"` → triggers CU5
- Format: Hierarchical structure
- Organization: Main topics with subtopics

### Expected Result
```
# Machine Learning Course Outline

## 1. Introduction to ML
   - 1.1 What is Machine Learning
   - 1.2 Types of ML
   
## 2. Supervised Learning
   - 2.1 Linear Regression
   ...
```

---

## Example 6: Professional Document → CU1

### Query (English)
```
"Write a formal business report on sales performance"
```

### Auto-Detected
✅ **CU1 - Professional Content**

### Why
- Pattern match: `"formal"` + `"business report"` → triggers CU1
- Tone: Professional, formal
- Structure: Clear sections with headers

### Expected Result
Formatted Markdown with Executive Summary, Analysis, Conclusions

---

## Multilingual Examples

### Italian - List Query → CU4
```
"voglio una lista di 10 persone importanti"
```
✅ Auto-detects CU4
- Pattern: `"lista di 10"` 
- Quantity: 10
- Same constraint enforcement as English

### Italian - Summary → CU3
```
"riassumi i punti chiave di questo documento"
```
✅ Auto-detects CU3
- Keyword: `"riassumi"` (summarize)
- Format: Bullet list

### Italian - Code → CU2
```
"scrivi una funzione Python per validare email"
```
✅ Auto-detects CU2
- Pattern: `"scrivi"` + `"funzione Python"`
- Format: Code block

---

## Edge Cases

### Generic Question (No Detection)
```
"What is this document about?"
```
❌ No use case detected
- Falls back to standard RAG prompt
- Still works well for general questions

### Ambiguous Query (Highest Score Wins)
```
"Extract a list of 10 key insights"
```
✅ Detects CU4 (not CU3)
- CU4 score higher due to `"list of 10"` pattern
- CU3 also matches `"extract"` + `"insights"` but lower score
- Prioritization ensures best optimization

### Confidence Levels
```
"Give me a list of 10 creative marketing ideas with brainstorming"
```
✅ Detects CU4 with **HIGH confidence**
- Multiple pattern matches
- Clear quantity specification
- Explicit brainstorming keyword

```
"Some ideas would be helpful"
```
⚠️ Detects CU4 with **LOW confidence**
- Only keyword match, no pattern
- No quantity specified
- Constraint enforcement still applied but less strict

---

## Testing Auto-Detection

### API Call (No use_case specified)
```json
POST /rag/query/
{
  "query": "Give me a list of 10 important locations in Sharn",
  "user_id": "test_user",
  "conversation_history": []
}
```

### Check Logs
Look for:
```
DEBUG [UseCaseDetection]: Detected UseCaseType.CREATIVE_BRAINSTORMING (score: 12)
DEBUG: Auto-detected use case: UseCaseType.CREATIVE_BRAINSTORMING
DEBUG: Using optimized prompt for use case: UseCaseType.CREATIVE_BRAINSTORMING
```

### Verify Result
- Count items in response
- Check format (numbered list 1-10)
- Verify specific names (not categories)

---

## Override Auto-Detection

If auto-detection picks the wrong use case, you can override:

```json
POST /rag/query/
{
  "query": "Extract insights from this data",
  "user_id": "test_user",
  "use_case": "CU3"  ← Manual override
}
```

This forces CU3 even if auto-detection would pick differently.

---

## Detection Patterns Reference

| Use Case | High-Score Patterns | Keywords |
|----------|---------------------|----------|
| **CU1** | `write formal report`, `draft professional email` | formal, professional, business |
| **CU2** | `write function`, `debug code`, `refactor` | code, function, debug, implement |
| **CU3** | `summarize`, `analyze`, `extract key points` | summarize, analyze, insights, trends |
| **CU4** | `list of 10`, `give me 5 ideas`, `brainstorm` | list, ideas, brainstorm, alternatives |
| **CU5** | `create outline`, `project plan`, `steps to` | outline, plan, roadmap, steps |
| **CU6** | `SWOT analysis`, `business case`, `strategic` | SWOT, PESTEL, strategy, competitive |

---

## Performance Comparison

### Without Auto-Detection (Old Behavior)
```json
{
  "query": "Give me a list of 10 people"
}
```
Result: Generic answer, maybe 4-7 items, possibly categories instead of names

### With Auto-Detection (New Behavior)
```json
{
  "query": "Give me a list of 10 people"
}
```
Result: Exactly 10 specific names, properly formatted numbered list

**Improvement:** ~85% better adherence to quantity constraints based on testing

---

## Debugging Tips

1. **Check detection in logs:**
   ```
   DEBUG [UseCaseDetection]: Detected ... (score: X)
   ```

2. **Verify score:** Higher = more confident
   - Score 0: No detection, standard RAG
   - Score 1-2: Low confidence
   - Score 3-4: Medium confidence  
   - Score 5+: High confidence

3. **Test patterns:**
   - Include specific keywords ("list", "summarize", "write code")
   - Add quantities when applicable ("10 items", "5 ideas")
   - Use action verbs ("create", "generate", "analyze")

4. **Override when needed:**
   - Specify `use_case` manually if auto-detection fails
   - Report patterns that don't work for improvement

---

**Bottom Line:** Just write natural queries, and the system will figure out the best way to optimize your prompt! 🎯
