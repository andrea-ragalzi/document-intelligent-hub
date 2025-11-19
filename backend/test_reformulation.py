"""
Quick test for query reformulation functionality.
Run with: poetry run python test_reformulation.py
"""

from app.services.rag_service import RAGService
from app.schemas.rag_schema import ConversationMessage
from app.repositories.dependencies import get_vector_store_repository

# Initialize service
repository_dependency = get_vector_store_repository()
repository = next(repository_dependency)
rag_service = RAGService(repository=repository)

# Test cases
test_cases = [
    {
        "query": "intendo la guerra delle 5 nazioni",
        "history": [
            ConversationMessage(role="user", content="chi ha combattuto la guerra?"),
            ConversationMessage(
                role="assistant", content="Non ho informazioni sufficienti."
            ),
        ],
        "expected": "Complete question about the War of 5 Nations",
    },
    {
        "query": "what about Napoleon?",
        "history": [
            ConversationMessage(role="user", content="Who was the French emperor?"),
            ConversationMessage(role="assistant", content="Napoleon Bonaparte was..."),
        ],
        "expected": "Complete question about Napoleon",
    },
    {
        "query": "Chi ha vinto la battaglia di Waterloo?",
        "history": [],
        "expected": "Should remain unchanged (already complete)",
    },
]

print("=" * 80)
print("QUERY REFORMULATION TEST")
print("=" * 80)

for idx, test in enumerate(test_cases, 1):
    print(f"\nTest {idx}:")
    print(f"  Original: {test['query']}")
    print(f"  History: {len(test['history'])} messages")

    reformulated = rag_service._reformulate_query(test["query"], test["history"])

    print(f"  Reformulated: {reformulated}")
    print(f"  Expected: {test['expected']}")
    print(f"  Changed: {'Yes' if reformulated != test['query'] else 'No'}")
print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)

try:
    repository_dependency.close()
except StopIteration:
    pass
print("=" * 80)
