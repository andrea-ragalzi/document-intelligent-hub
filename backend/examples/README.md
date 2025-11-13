# Examples - Use Case Optimization System

This directory contains example scripts demonstrating how to use the Use Case Optimization feature.

## Prerequisites

1. Backend running on `http://localhost:8000`
2. At least one document uploaded (e.g., `sharn_city_of_tower.pdf`)
3. Python `requests` library installed

## Running the Examples

### Install requests (if not already installed)

```bash
pip install requests
```

### Run the test suite

```bash
python test_use_cases_api.py
```

## What the Tests Demonstrate

### Test 1: Basic Query (No Use Case)
Standard RAG behavior without use case optimization.

### Test 2: Creative Brainstorming (CU4)
Shows how CU4 enforces exact quantity constraints for lists.

### Test 3: Italian Query with CU4
Demonstrates multilingual support with constraint enforcement.

### Test 4: Data Analysis (CU3)
Document summarization with bullet point format.

### Test 5: Business Strategy (CU6)
SWOT analysis generation with structured output.

### Test 6: Structured Planning (CU5)
Hierarchical outline creation.

### Comparison Test
Direct comparison of same query with and without use case optimization.

## Expected Results

When run successfully, you should see:
- ✅ All queries return status 200
- ✅ CU4 queries return EXACTLY the number of items requested
- ✅ Outputs follow the format specified by each use case
- ✅ Italian queries work as well as English queries
- ✅ Comparison shows clear difference in adherence to constraints

## Troubleshooting

**Connection Error:**
- Make sure backend is running: `cd backend && poetry run uvicorn main:app --reload`

**No documents found:**
- Upload a PDF first using the `/rag/upload/` endpoint

**Wrong results:**
- Check that you're using the correct `user_id` that matches your uploaded documents

## Use Case Reference

| Code | When to Use |
|------|-------------|
| `CU1` | Professional documents with specific tone |
| `CU2` | Code generation, debugging, refactoring |
| `CU3` | Document analysis, summarization, insights |
| `CU4` | **Lists with exact quantities**, entity extraction |
| `CU5` | Project plans, outlines, hierarchical structures |
| `CU6` | Business strategy documents (SWOT, PESTEL, etc.) |

## Custom Examples

You can create your own tests by following this pattern:

```python
response = requests.post(
    f"{BASE_URL}/rag/query/",
    json={
        "query": "Your question here",
        "user_id": "your_user_id",
        "conversation_history": [],
        "use_case": "CU4"  # Choose appropriate use case
    }
)

result = response.json()
print(result['answer'])
```

## More Information

See [USE_CASE_GUIDE.md](../../USE_CASE_GUIDE.md) for complete documentation.
