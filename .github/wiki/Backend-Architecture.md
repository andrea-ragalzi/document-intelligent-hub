# Backend Architecture

The backend is built with FastAPI and provides a robust RAG (Retrieval-Augmented Generation) API for document processing and intelligent Q&A.

## 📁 Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py          # Configuration and settings
│   ├── db/
│   │   ├── __init__.py
│   │   └── chroma_client.py   # ChromaDB vector store client
│   ├── routers/
│   │   ├── __init__.py
│   │   └── rag_router.py      # API endpoints
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── rag.py             # Pydantic models for validation
│   └── services/
│       ├── __init__.py
│       ├── rag_service.py     # RAG business logic
│       └── language_service.py # Language detection/translation
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Pytest fixtures
│   └── test_rag_endpoints.py  # API endpoint tests
├── chroma_db/                  # ChromaDB persistent storage
├── main.py                     # FastAPI application entry point
├── pyproject.toml              # Python dependencies (Poetry)
├── pytest.ini                  # Pytest configuration
├── Dockerfile                  # Docker container definition
└── README.md
```

## 🏗️ Architecture Layers

### 1. **API Layer** (`routers/`)

**File**: `rag_router.py`

Handles HTTP requests and responses. Defines all API endpoints.

**Endpoints**:
- `GET /` - Health check
- `POST /upload/` - Upload and index PDF documents
- `POST /query/` - Query indexed documents with RAG

**Key Features**:
- FastAPI automatic validation via Pydantic schemas
- CORS middleware for frontend communication
- Error handling with HTTP exceptions
- Multi-part file upload support

### 2. **Service Layer** (`services/`)

Contains business logic separated from API concerns.

#### **RAG Service** (`rag_service.py`)

Core RAG pipeline implementation.

**Key Functions**:
- `index_pdf_document()` - Process and store PDF in vector DB
  - Extract text from PDF
  - Split into chunks with overlap
  - Generate embeddings
  - Store in ChromaDB with metadata
  
- `query_documents()` - Retrieve and generate answers
  - Detect query language
  - Retrieve relevant chunks via semantic search
  - Build context-aware prompt with chat history
  - Generate response using LLM
  - Return answer with sources

**Components Used**:
- **LangChain** - Orchestration framework
- **RecursiveCharacterTextSplitter** - Chunk documents intelligently
- **OpenAIEmbeddings** - Generate vector embeddings
- **ChatOpenAI** - LLM for answer generation

#### **Language Service** (`language_service.py`)

Handles multi-language support.

**Functions**:
- `detect_language()` - Detect language of query
- `translate_to_english()` - Translate non-English queries
- `translate_to_language()` - Translate responses back to original language

### 3. **Data Layer** (`db/`)

#### **ChromaDB Client** (`chroma_client.py`)

Vector database management.

**Features**:
- Persistent storage with disk-based database
- Per-user collections for multi-tenancy
- Metadata filtering for data isolation
- Automatic collection creation

**Key Methods**:
- `get_or_create_collection(user_id)` - Get user-specific collection
- Semantic similarity search
- Document storage with metadata

### 4. **Data Models** (`schemas/`)

**File**: `rag.py`

Pydantic models for request/response validation.

**Models**:

```python
class UploadRequest(BaseModel):
    """File upload request"""
    file: UploadFile
    user_id: str

class UploadResponse(BaseModel):
    """Upload success response"""
    message: str
    status: str
    chunks_indexed: int

class ChatHistoryItem(BaseModel):
    """Single chat history message"""
    type: Literal["user", "assistant"]
    text: str

class QueryRequest(BaseModel):
    """Query request with history"""
    query: str
    user_id: str
    chat_history: List[ChatHistoryItem] = []

class QueryResponse(BaseModel):
    """Query response with sources"""
    answer: str
    source_documents: List[str]
```

### 5. **Configuration** (`core/`)

**File**: `config.py`

Centralized configuration using Pydantic Settings.

**Settings**:
- OpenAI API key
- Model names (embeddings, LLM)
- ChromaDB path
- CORS origins
- Chunk size and overlap

**Example**:
```python
class Settings(BaseSettings):
    openai_api_key: str
    embedding_model: str = "text-embedding-ada-002"
    llm_model: str = "gpt-3.5-turbo"
    chroma_db_path: str = "chroma_db"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## 🔄 RAG Pipeline Flow

### Document Upload Flow

```
1. User uploads PDF
   ↓
2. FastAPI receives file + user_id
   ↓
3. RAG Service extracts text from PDF
   ↓
4. Text split into chunks (1000 chars, 200 overlap)
   ↓
5. Generate embeddings for each chunk
   ↓
6. Store in ChromaDB with metadata:
   - user_id (for filtering)
   - chunk_id
   - source document name
   ↓
7. Return success response
```

### Query Flow

```
1. User sends query + user_id + chat_history
   ↓
2. Detect query language
   ↓
3. Translate to English if needed
   ↓
4. Retrieve relevant chunks from ChromaDB:
   - Semantic similarity search
   - Filter by user_id (multi-tenant)
   - Top 4 most relevant chunks
   ↓
5. Build context:
   - System prompt
   - Chat history
   - Retrieved chunks
   - Current query
   ↓
6. Send to GPT for answer generation
   ↓
7. Translate response to original language
   ↓
8. Return answer + source chunk IDs
```

## 🔐 Multi-Tenancy

**Data Isolation Strategy**:

Each user has a separate ChromaDB collection:
- Collection name: `rag_docs_{user_id}`
- No cross-user data leakage
- Metadata filtering ensures user-specific queries

**Security Features**:
- User ID required for all operations
- Collections isolated at DB level
- No shared embeddings between users

## 🧪 Testing

**Framework**: pytest with fixtures

**Test Coverage**:
- ✅ Health check endpoint
- ✅ PDF upload (valid files)
- ✅ Invalid file type rejection
- ✅ Query without chat history
- ✅ Query with chat history
- ✅ Multi-tenant isolation
- ✅ Error handling (missing user_id, invalid data)

**Run Tests**:
```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test
pytest tests/test_rag_endpoints.py::test_upload_pdf -v
```

## 📦 Dependencies

**Core**:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `langchain` - LLM orchestration
- `openai` - OpenAI API client
- `chromadb` - Vector database
- `pypdf` - PDF text extraction
- `pydantic` - Data validation

**Dev**:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `httpx` - HTTP client for testing

## 🚀 Deployment

### Local Development
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -e .
uvicorn main:app --reload
```

### Docker
```bash
docker build -t rag-backend .
docker run -p 8000:8000 --env-file .env rag-backend
```

### Production Considerations
- Use Gunicorn with Uvicorn workers
- Set up reverse proxy (Nginx)
- Configure proper CORS origins
- Use environment variables for secrets
- Set up logging and monitoring
- Enable rate limiting
- Use connection pooling for ChromaDB

## 📊 Performance Optimization

**Current Optimizations**:
- Persistent ChromaDB (disk-based)
- Efficient text chunking with overlap
- Limited context window (top 4 chunks)
- Async FastAPI handlers

**Future Improvements**:
- [ ] Caching layer for frequent queries
- [ ] Batch embedding generation
- [ ] Connection pooling
- [ ] Response streaming (SSE)
- [ ] Query result caching
- [ ] Background job processing for large uploads

## 🔍 Monitoring & Debugging

**Logging**:
- Console logging enabled
- Log requests/responses in development
- Error tracing with stack traces

**Debug Endpoints**:
- `GET /` - Health check with timestamp
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc documentation

**Useful Commands**:
```bash
# Check logs
docker-compose logs -f backend

# Enter container
docker-compose exec backend bash

# Test endpoint
curl -X POST http://localhost:8000/rag/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "user_id": "user1"}'
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/)
