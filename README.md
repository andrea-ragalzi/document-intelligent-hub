# 🧠 Document Intelligent Hub

Full-Stack AI-powered RAG (Retrieval-Augmented Generation) application providing secure, semantic Q&A over proprietary documents. Built with FastAPI, LangChain, ChromaDB, and Next.js with Multi-Tenancy support.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.121-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16.0-000000?style=flat&logo=next.js)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?style=flat&logo=typescript)](https://www.typescriptlang.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker)](https://www.docker.com/)

## ✨ Features

- 🔐 **Multi-Tenant Architecture**: Secure data isolation per user
- 📄 **PDF Document Processing**: Upload and index PDF documents
- 🤖 **AI-Powered Q&A**: Get intelligent answers from your documents using GPT
- 💬 **Chat History**: Contextual conversations with memory
- 🎨 **Modern UI**: Responsive Next.js frontend with dark mode
- 🚀 **Streaming Responses**: Real-time AI response streaming with Vercel AI SDK
- 🔍 **Semantic Search**: ChromaDB vector store for accurate retrieval
- 🧪 **Fully Tested**: Comprehensive test suite with pytest
- 🐳 **Docker Ready**: One-command deployment

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
│  • React 19 + TypeScript                                    │
│  • Tailwind CSS + Dark Mode                                 │
│  • Vercel AI SDK for Streaming                              │
└────────────────┬────────────────────────────────────────────┘
                 │ REST API
┌────────────────▼────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  • Python 3.12                                               │
│  • LangChain + OpenAI                                        │
│  • Multi-tenant RAG Pipeline                                 │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                    ChromaDB (Vector Store)                   │
│  • Persistent storage                                        │
│  • Metadata filtering per user                               │
│  • Embedding-based retrieval                                 │
└──────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# 1. Clone repository
git clone <repo-url>
cd document-intelligent-hub

# 2. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Start services
docker-compose up -d --build

# 4. Access the application
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**📖 Full Docker guide**: See [DOCKER_DEPLOY.md](DOCKER_DEPLOY.md)

### Option 2: Local Development

#### Backend Setup

```bash
cd backend

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Create .env file
cp .env.example .env
# Add your OPENAI_API_KEY

# Run server
uvicorn main:app --reload

# API available at http://127.0.0.1:8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local
echo "NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/rag" > .env.local

# Run development server
npm run dev

# App available at http://localhost:3000
```

## 📚 API Endpoints

### Upload Document
```bash
POST /rag/upload/
Content-Type: multipart/form-data

# Parameters:
- file: PDF document (required)
- user_id: Unique user identifier (required)

# Response:
{
  "message": "Document 'example.pdf' indexed successfully.",
  "status": "success",
  "chunks_indexed": 42
}
```

### Query Document
```bash
POST /rag/query/
Content-Type: application/json

# Body:
{
  "query": "What is machine learning?",
  "user_id": "user-123",
  "chat_history": [
    {"type": "user", "text": "Previous question"},
    {"type": "assistant", "text": "Previous answer"}
  ]
}

# Response:
{
  "answer": "Machine learning is...",
  "source_documents": ["chunk_id_1", "chunk_id_2"]
}
```

### Interactive API Docs
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_rag_endpoints.py -v

# Run in Docker
docker-compose exec backend pytest
```

**Test Coverage:**
- ✅ Health check endpoint
- ✅ Document upload (valid/invalid files)
- ✅ Query with/without chat history
- ✅ Multi-tenant isolation
- ✅ Error handling
- ✅ End-to-end workflows

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **LangChain**: LLM orchestration framework
- **OpenAI**: GPT models for generation
- **ChromaDB**: Vector database for embeddings
- **PyPDF**: PDF text extraction
- **Pydantic**: Data validation

### Frontend
- **Next.js 16**: React framework with App Router
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first styling
- **Vercel AI SDK**: Streaming chat responses
- **Lucide React**: Icon library
- **localStorage**: Client-side persistence

### DevOps
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **pytest**: Python testing framework
- **GitHub Actions**: CI/CD (optional)

## 📁 Project Structure

```
document-intelligent-hub/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   └── config.py          # Configuration settings
│   │   ├── db/
│   │   │   └── chroma_client.py   # ChromaDB client
│   │   ├── routers/
│   │   │   └── rag_router.py      # API endpoints
│   │   ├── schemas/
│   │   │   └── rag.py             # Pydantic models
│   │   └── services/
│   │       ├── rag_service.py     # RAG business logic
│   │       └── language_service.py # Translation/detection
│   ├── tests/
│   │   ├── conftest.py            # Test fixtures
│   │   └── test_rag_endpoints.py  # Endpoint tests
│   ├── main.py                     # FastAPI app
│   ├── pyproject.toml              # Python dependencies
│   ├── Dockerfile                  # Backend container
│   └── .dockerignore
├── frontend/
│   ├── app/
│   │   ├── api/
│   │   │   └── chat/
│   │   │       └── route.ts       # API route proxy
│   │   ├── layout.tsx             # Root layout
│   │   └── page.tsx               # Main page
│   ├── components/
│   │   ├── ChatSection.tsx
│   │   ├── Sidebar.tsx
│   │   └── ...                    # UI components
│   ├── hooks/
│   │   ├── useChatAI.ts           # Vercel AI SDK hook
│   │   ├── useTheme.ts
│   │   └── ...                    # Custom hooks
│   ├── lib/
│   │   ├── types.ts               # TypeScript types
│   │   └── constants.ts
│   ├── Dockerfile                  # Frontend container
│   ├── package.json
│   └── next.config.ts
├── docker-compose.yml              # Container orchestration
├── .env.example                    # Environment template
├── DOCKER_DEPLOY.md                # Deployment guide
└── README.md                       # This file
```

## 🔧 Configuration

### Environment Variables

#### Required
```env
OPENAI_API_KEY=sk-your-key-here
```

#### Optional (with defaults)
```env
# Backend
CHROMA_DB_PATH=chroma_db
EMBEDDING_MODEL=text-embedding-ada-002
LLM_MODEL=gpt-3.5-turbo
APP_NAME=Document Intelligent Hub

# Frontend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/rag
```

## 🔒 Security Features

- ✅ Multi-tenant data isolation via metadata filtering
- ✅ CORS configuration for frontend/backend communication
- ✅ Non-root user in Docker containers
- ✅ Input validation with Pydantic
- ✅ File type validation (PDF only)
- ✅ Environment variable management
- ✅ Health checks for containers

## 🚧 Roadmap

- [ ] Implement true SSE streaming from FastAPI
- [ ] Add user authentication (JWT)
- [ ] Support multiple file formats (DOCX, TXT, etc.)
- [ ] Implement conversation persistence with database
- [ ] Add document management UI
- [ ] Deploy to cloud platforms (Railway, Vercel, AWS)
- [ ] Add rate limiting
- [ ] Implement caching layer
- [ ] Add monitoring and logging (Sentry, LogRocket)
- [ ] Create admin dashboard

## 📖 Documentation

- [Docker Deployment Guide](DOCKER_DEPLOY.md)
- [Vercel AI SDK Integration](frontend/VERCEL_AI_INTEGRATION.md)
- [API Documentation](http://localhost:8000/docs) (when running)

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Andrea Ragalzi**
- Email: andrea.ragalzi.code@gmail.com
- GitHub: [@andrea-ragalzi](https://github.com/andrea-ragalzi)

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the amazing Python framework
- [LangChain](https://www.langchain.com/) for LLM orchestration
- [Vercel](https://vercel.com/) for Next.js and AI SDK
- [ChromaDB](https://www.trychroma.com/) for vector storage
- [OpenAI](https://openai.com/) for GPT models

---

**⭐ Star this repository if you find it helpful!**
