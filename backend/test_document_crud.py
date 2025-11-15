#!/usr/bin/env python3
"""
Test script per verificare il CRUD dei documenti
"""

import json
import sys

import requests

# Configurazione
BASE_URL = "http://localhost:8000/rag"
TEST_USER_ID = "test_user_crud_123"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_check_documents():
    """Test 1: Verifica stato documenti iniziale"""
    print_section("TEST 1: Check Documents Status")
    
    response = requests.get(f"{BASE_URL}/documents/check", params={"user_id": TEST_USER_ID})
    print(f"Status Code: {response.status_code}")
    
    if response.ok:
        data = response.json()
        print(f"✅ Response: {json.dumps(data, indent=2)}")
        print(f"Has Documents: {data.get('has_documents')}")
        print(f"Document Count: {data.get('document_count')}")
        return data
    else:
        print(f"❌ Error: {response.text}")
        return None

def test_list_documents():
    """Test 2: Lista documenti"""
    print_section("TEST 2: List Documents")
    
    response = requests.get(f"{BASE_URL}/documents/list", params={"user_id": TEST_USER_ID})
    print(f"Status Code: {response.status_code}")
    
    if response.ok:
        data = response.json()
        print(f"✅ Response: {json.dumps(data, indent=2)}")
        print(f"\nTotal Documents: {data.get('total_count')}")
        
        for doc in data.get('documents', []):
            print(f"\n  📄 {doc['filename']}")
            print(f"     Chunks: {doc['chunks_count']}")
            print(f"     Language: {doc.get('language', 'unknown')}")
            
        return data.get('documents', [])
    else:
        print(f"❌ Error: {response.text}")
        return []

def test_upload_document(pdf_path):
    """Test 3: Upload documento"""
    print_section(f"TEST 3: Upload Document - {pdf_path}")
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path, f, 'application/pdf')}
            data = {'user_id': TEST_USER_ID}
            
            response = requests.post(f"{BASE_URL}/upload/", files=files, data=data)
            print(f"Status Code: {response.status_code}")
            
            if response.ok:
                result = response.json()
                print(f"✅ Response: {json.dumps(result, indent=2)}")
                print(f"\nChunks Indexed: {result.get('chunks_indexed')}")
                print(f"Language Detected: {result.get('detected_language')}")
                return True
            else:
                print(f"❌ Error: {response.text}")
                return False
    except FileNotFoundError:
        print(f"❌ File not found: {pdf_path}")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_delete_document(filename):
    """Test 4: Elimina documento"""
    print_section(f"TEST 4: Delete Document - {filename}")
    
    response = requests.delete(
        f"{BASE_URL}/documents/delete",
        params={"user_id": TEST_USER_ID, "filename": filename}
    )
    print(f"Status Code: {response.status_code}")
    
    if response.ok:
        data = response.json()
        print(f"✅ Response: {json.dumps(data, indent=2)}")
        print(f"\nChunks Deleted: {data.get('chunks_deleted')}")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False

def test_delete_all_documents():
    """Test 5: Elimina tutti i documenti"""
    print_section("TEST 5: Delete All Documents")
    
    response = requests.delete(
        f"{BASE_URL}/documents/delete-all",
        params={"user_id": TEST_USER_ID}
    )
    print(f"Status Code: {response.status_code}")
    
    if response.ok:
        data = response.json()
        print(f"✅ Response: {json.dumps(data, indent=2)}")
        print(f"\nTotal Chunks Deleted: {data.get('chunks_deleted')}")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False

def main():
    print("\n" + "🧪 " * 30)
    print("DOCUMENT CRUD - TEST SUITE")
    print("🧪 " * 30)
    
    # Test 1: Check initial state
    test_check_documents()
    
    # Test 2: List documents
    documents = test_list_documents()
    
    # Test 3: Upload (se fornito un file)
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"\n📤 Uploading test file: {pdf_path}")
        if test_upload_document(pdf_path):
            print("\n✅ Upload successful! Checking updated list...")
            test_list_documents()
            test_check_documents()
    else:
        print("\n💡 Tip: Pass a PDF file path as argument to test upload")
        print("   Example: python test_document_crud.py /path/to/file.pdf")
    
    # Test 4: Delete specific document (se ci sono documenti)
    if documents and len(documents) > 0:
        filename = documents[0]['filename']
        print(f"\n🗑️  Testing delete for: {filename}")
        
        if test_delete_document(filename):
            print("\n✅ Delete successful! Checking updated list...")
            test_list_documents()
            test_check_documents()
    
    # Test 5: Delete all (opzionale, commentato per sicurezza)
    # print("\n⚠️  Testing delete all documents...")
    # test_delete_all_documents()
    # test_list_documents()
    # test_check_documents()
    
    print("\n" + "✅ " * 30)
    print("TEST SUITE COMPLETED")
    print("✅ " * 30 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
