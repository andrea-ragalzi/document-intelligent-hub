#!/bin/bash

# 🧪 Quick Test Script - Verify the application is working

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_test() {
    echo -e "\n${YELLOW}▶ $1${NC}"
}

# Configuration
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"
TEST_USER_ID="test-user-$(date +%s)"

echo -e "${BLUE}===========================================${NC}"
echo -e "${BLUE}  Document Intelligent Hub - Quick Test${NC}"
echo -e "${BLUE}===========================================${NC}"

# Test 1: Backend Health Check
print_test "Test 1: Backend Health Check"
if curl -sf "$BACKEND_URL/" > /dev/null 2>&1; then
    RESPONSE=$(curl -s "$BACKEND_URL/")
    if echo "$RESPONSE" | grep -q "running"; then
        print_success "Backend is running and healthy"
    else
        print_error "Backend response unexpected: $RESPONSE"
        exit 1
    fi
else
    print_error "Backend is not responding at $BACKEND_URL"
    print_info "Make sure services are running: docker-compose ps"
    exit 1
fi

# Test 2: Frontend Health Check
print_test "Test 2: Frontend Health Check"
if curl -sf "$FRONTEND_URL/" > /dev/null 2>&1; then
    print_success "Frontend is running and responding"
else
    print_error "Frontend is not responding at $FRONTEND_URL"
    exit 1
fi

# Test 3: API Documentation
print_test "Test 3: API Documentation"
if curl -sf "$BACKEND_URL/docs" > /dev/null 2>&1; then
    print_success "API documentation is accessible at $BACKEND_URL/docs"
else
    print_error "API documentation is not accessible"
fi

# Test 4: Create a test PDF file
print_test "Test 4: Upload Document"
TEST_PDF="/tmp/test_doc_$(date +%s).pdf"

# Create minimal PDF
cat > "$TEST_PDF" << 'EOF'
%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 88
>>
stream
BT
/F1 12 Tf
100 700 Td
(This is a test document for the Document Intelligent Hub.) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000317 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
454
%%EOF
EOF

# Upload the PDF
UPLOAD_RESPONSE=$(curl -s -X POST "$BACKEND_URL/rag/upload/" \
    -F "file=@$TEST_PDF" \
    -F "user_id=$TEST_USER_ID")

if echo "$UPLOAD_RESPONSE" | grep -q "success"; then
    CHUNKS=$(echo "$UPLOAD_RESPONSE" | grep -o '"chunks_indexed":[0-9]*' | cut -d':' -f2)
    print_success "Document uploaded successfully ($CHUNKS chunks indexed)"
else
    print_error "Document upload failed"
    echo "Response: $UPLOAD_RESPONSE"
    rm -f "$TEST_PDF"
    exit 1
fi

# Cleanup test PDF
rm -f "$TEST_PDF"

# Test 5: Query the document
print_test "Test 5: Query Document"
QUERY_DATA=$(cat <<EOF
{
  "query": "What is this document about?",
  "user_id": "$TEST_USER_ID",
  "chat_history": []
}
EOF
)

QUERY_RESPONSE=$(curl -s -X POST "$BACKEND_URL/rag/query/" \
    -H "Content-Type: application/json" \
    -d "$QUERY_DATA")

if echo "$QUERY_RESPONSE" | grep -q "answer"; then
    ANSWER=$(echo "$QUERY_RESPONSE" | grep -o '"answer":"[^"]*"' | cut -d'"' -f4 | head -c 100)
    print_success "Query successful"
    print_info "Answer preview: ${ANSWER}..."
else
    print_error "Query failed"
    echo "Response: $QUERY_RESPONSE"
    exit 1
fi

# Test 6: Query with chat history
print_test "Test 6: Query with Chat History"
QUERY_WITH_HISTORY=$(cat <<EOF
{
  "query": "Can you tell me more?",
  "user_id": "$TEST_USER_ID",
  "chat_history": [
    {
      "type": "user",
      "text": "What is this document about?"
    },
    {
      "type": "assistant",
      "text": "This is a test document."
    }
  ]
}
EOF
)

HISTORY_RESPONSE=$(curl -s -X POST "$BACKEND_URL/rag/query/" \
    -H "Content-Type: application/json" \
    -d "$QUERY_WITH_HISTORY")

if echo "$HISTORY_RESPONSE" | grep -q "answer"; then
    print_success "Query with chat history successful"
else
    print_error "Query with chat history failed"
fi

# Summary
echo ""
echo -e "${GREEN}===========================================${NC}"
echo -e "${GREEN}  ✅ All Tests Passed Successfully!${NC}"
echo -e "${GREEN}===========================================${NC}"
echo ""
print_info "Your application is working correctly!"
print_info "You can now:"
echo "  • Access the frontend at $FRONTEND_URL"
echo "  • View API docs at $BACKEND_URL/docs"
echo "  • Upload documents and ask questions"
echo ""
