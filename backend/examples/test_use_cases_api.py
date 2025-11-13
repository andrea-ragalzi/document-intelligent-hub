"""
Example script demonstrating the Use Case Optimization System.

This script shows how to use the new use case features with the RAG API.
"""

import requests

# API endpoint (adjust if different)
BASE_URL = "http://localhost:8000"

def test_basic_query():
    """Test without use case optimization (standard RAG)."""
    print("\n" + "="*80)
    print("TEST 1: Basic Query (No Use Case)")
    print("="*80)
    
    response = requests.post(
        f"{BASE_URL}/rag/query/",
        json={
            "query": "Give me a list of 10 important people in Sharn",
            "user_id": "test_user",
            "conversation_history": []
        }
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Answer:\n{result['answer']}")
    print(f"\nSources: {result['source_documents']}")


def test_creative_brainstorming():
    """Test CU4 - Creative Brainstorming with quantity constraint."""
    print("\n" + "="*80)
    print("TEST 2: Creative Brainstorming (CU4) - 10 People")
    print("="*80)
    
    response = requests.post(
        f"{BASE_URL}/rag/query/",
        json={
            "query": "Give me a list of 10 important people in Sharn",
            "user_id": "test_user",
            "conversation_history": [],
            "use_case": "CU4"  # Enables constraint enforcement
        }
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Answer:\n{result['answer']}")
    print(f"\nSources: {result['source_documents']}")
    
    # Count items in response
    lines = result['answer'].split('\n')
    numbered_items = [line for line in lines if line.strip() and line.strip()[0].isdigit()]
    print(f"\n✓ Items returned: {len(numbered_items)}")


def test_italian_query_cu4():
    """Test CU4 with Italian query."""
    print("\n" + "="*80)
    print("TEST 3: Italian Query with CU4")
    print("="*80)
    
    response = requests.post(
        f"{BASE_URL}/rag/query/",
        json={
            "query": "voglio una lista di 10 persone importanti a Sharn",
            "user_id": "test_user",
            "conversation_history": [],
            "use_case": "CU4"
        }
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Answer:\n{result['answer']}")
    print(f"\nSources: {result['source_documents']}")


def test_data_analysis():
    """Test CU3 - Data Analysis for document summary."""
    print("\n" + "="*80)
    print("TEST 4: Data Analysis (CU3) - Document Summary")
    print("="*80)
    
    response = requests.post(
        f"{BASE_URL}/rag/query/",
        json={
            "query": "Summarize the key features of Sharn in bullet points",
            "user_id": "test_user",
            "conversation_history": [],
            "use_case": "CU3"
        }
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Answer:\n{result['answer']}")
    print(f"\nSources: {result['source_documents']}")


def test_business_strategy():
    """Test CU6 - Business Strategy for SWOT analysis."""
    print("\n" + "="*80)
    print("TEST 5: Business Strategy (CU6) - SWOT Analysis")
    print("="*80)
    
    response = requests.post(
        f"{BASE_URL}/rag/query/",
        json={
            "query": "Generate a SWOT analysis for Sharn as a city with 4 points per section",
            "user_id": "test_user",
            "conversation_history": [],
            "use_case": "CU6"
        }
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Answer:\n{result['answer']}")
    print(f"\nSources: {result['source_documents']}")


def test_structured_planning():
    """Test CU5 - Structured Planning for hierarchical outline."""
    print("\n" + "="*80)
    print("TEST 6: Structured Planning (CU5) - Travel Guide Outline")
    print("="*80)
    
    response = requests.post(
        f"{BASE_URL}/rag/query/",
        json={
            "query": "Create an outline for a travel guide to Sharn with main sections and subsections",
            "user_id": "test_user",
            "conversation_history": [],
            "use_case": "CU5"
        }
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Answer:\n{result['answer']}")
    print(f"\nSources: {result['source_documents']}")


def compare_with_without_use_case():
    """Compare same query with and without use case."""
    print("\n" + "="*80)
    print("COMPARISON: Same Query With/Without Use Case")
    print("="*80)
    
    query = "Give me exactly 5 interesting locations in Sharn"
    
    # Without use case
    print("\n--- WITHOUT Use Case ---")
    response1 = requests.post(
        f"{BASE_URL}/rag/query/",
        json={
            "query": query,
            "user_id": "test_user",
            "conversation_history": []
        }
    )
    result1 = response1.json()
    print(result1['answer'])
    
    # With CU4
    print("\n--- WITH Use Case CU4 ---")
    response2 = requests.post(
        f"{BASE_URL}/rag/query/",
        json={
            "query": query,
            "user_id": "test_user",
            "conversation_history": [],
            "use_case": "CU4"
        }
    )
    result2 = response2.json()
    print(result2['answer'])


if __name__ == "__main__":
    print("="*80)
    print("USE CASE OPTIMIZATION SYSTEM - TEST SUITE")
    print("="*80)
    print("\nMake sure the backend is running on http://localhost:8000")
    print("and you have uploaded the Sharn PDF document first!")
    
    input("\nPress Enter to start tests...")
    
    try:
        # Run all tests
        test_basic_query()
        test_creative_brainstorming()
        test_italian_query_cu4()
        test_data_analysis()
        test_business_strategy()
        test_structured_planning()
        compare_with_without_use_case()
        
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED")
        print("="*80)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to backend at", BASE_URL)
        print("Make sure the backend is running: poetry run uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
