# 🧠 Document Intelligent Hub

Full-Stack AI-powered RAG (Retrieval-Augmented Generation) application providing secure, semantic Q&A over proprietary documents. Built with FastAPI, LangChain, ChromaDB, and Next.js with Multi-Tenancy support.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.121-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16.0-000000?style=flat&logo=next.js)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?style=flat&logo=typescript)](https://www.typescriptlang.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker)](https://www.docker.com/)

---

## 🚀 Quick Start

### Docker (Recommended)

```bash
# Clone and setup
git clone https://github.com/andrea-ragalzi/document-intelligent-hub.git
cd document-intelligent-hub

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start services
docker-compose up -d --build
```

**Access:**

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Local Development

```bash
# Install pre-commit hooks (first time only)
pip install pre-commit
pre-commit install

# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -e .
uvicorn main:app --reload

# Frontend (new terminal)
cd frontend
npm install && npm run dev
```

> **Note:** Pre-commit hooks will automatically check for secrets and code quality issues before each commit.

---

## ✨ Key Features

- 🔐 **Multi-Tenant Architecture** - Secure data isolation per user with Firebase authentication
- 📄 **PDF Processing** - Upload and index PDF documents with hierarchical structure awareness
- 🤖 **AI-Powered Q&A** - GPT-based intelligent answers from your documents
- 🧠 **Conversation Memory** - Hybrid short-term + long-term memory for context-aware dialogues
- 💬 **Smart Chat History** - Last 7 exchanges automatically included for coherent conversations
- 📝 **Auto-Summarization** - LLM-generated summaries every 20 messages for long-term context
- 🎨 **Modern UI** - Responsive Next.js with dark mode and beautiful landing page
- 🚀 **Real-time Responses** - Streaming AI responses with Vercel AI SDK
- 🔍 **Semantic Search** - ChromaDB vector store with multi-query retrieval
- 🌍 **Multi-Language Support** - Automatic translation for queries and responses
- 🐳 **Docker Ready** - One-command deployment with docker-compose

---

## 📚 Documentation

**📖 [View Complete Documentation on Wiki](https://github.com/andrea-ragalzi/document-intelligent-hub/wiki)**

### Quick Links

- **Getting Started**

  - [Installation Guide](https://github.com/andrea-ragalzi/document-intelligent-hub/wiki/Installation-Guide)
  - [Quick Start Tutorial](https://github.com/andrea-ragalzi/document-intelligent-hub/wiki/Quick-Start)
  - [Configuration Guide](https://github.com/andrea-ragalzi/document-intelligent-hub/wiki/Configuration)

- **Architecture**

  - [Project Structure](https://github.com/andrea-ragalzi/document-intelligent-hub/wiki/Project-Structure)
  - [Backend Architecture](https://github.com/andrea-ragalzi/document-intelligent-hub/wiki/Backend-Architecture)
  - [Frontend Architecture](https://github.com/andrea-ragalzi/document-intelligent-hub/wiki/Frontend-Architecture)
  - [State Management](https://github.com/andrea-ragalzi/document-intelligent-hub/wiki/State-Management)

- **Features**

  - [RAG Chat System](https://github.com/andrea-ragalzi/document-intelligent-hub/wiki/RAG-Chat-System)
  - [Document Upload](https://github.com/andrea-ragalzi/document-intelligent-hub/wiki/Document-Upload)
  - [Conversation Management](https://github.com/andrea-ragalzi/document-intelligent-hub/wiki/Conversation-Management)

- **Development**

  - [Development Workflow](https://github.com/andrea-ragalzi/document-intelligent-hub/wiki/Development-Workflow)
  - [Testing Guide](https://github.com/andrea-ragalzi/document-intelligent-hub/wiki/Testing-Guide)
  - [Contributing Guidelines](https://github.com/andrea-ragalzi/document-intelligent-hub/wiki/Contributing-Guidelines)

- **Deployment**

  - [Docker Deployment](https://github.com/andrea-ragalzi/document-intelligent-hub/wiki/Docker-Deployment)
  - [Production Deployment](https://github.com/andrea-ragalzi/document-intelligent-hub/wiki/Production-Deployment)

- **Reference**
  - [API Endpoints](https://github.com/andrea-ragalzi/document-intelligent-hub/wiki/API-Endpoints)
  - [Environment Variables](https://github.com/andrea-ragalzi/document-intelligent-hub/wiki/Environment-Variables)
  - [Common Issues](https://github.com/andrea-ragalzi/document-intelligent-hub/wiki/Common-Issues)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Frontend (Next.js 16)                      │
│  • React 19 + TypeScript                                    │
│  • Zustand + TanStack Query (State Management)              │
│  • Tailwind CSS + Dark Mode                                 │
│  • Vercel AI SDK for Streaming                              │
│  • Firebase (Auth + Firestore)                              │
└────────────────┬────────────────────────────────────────────┘
                 │ REST API
┌────────────────▼────────────────────────────────────────────┐
│                  Backend (FastAPI + Python)                  │
│  • LangChain + OpenAI GPT                                    │
│  • Multi-tenant RAG Pipeline                                 │
│  • PDF Processing                                            │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                ChromaDB (Vector Database)                    │
│  • Persistent storage                                        │
│  • Metadata filtering per user                               │
│  • Embedding-based semantic search                           │
└──────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

### Backend

- **FastAPI** - Modern Python web framework
- **LangChain** - LLM orchestration
- **OpenAI** - GPT models for generation
- **ChromaDB** - Vector database
- **PyPDF** - PDF text extraction

### Frontend

- **Next.js 16** - React framework with App Router & Turbopack
- **TypeScript** - Type-safe JavaScript
- **Zustand** - Lightweight state management
- **TanStack Query** - Server state management with caching
- **Tailwind CSS** - Utility-first styling
- **Vercel AI SDK** - Streaming chat responses
- **Firebase** - Authentication & Firestore database

### DevOps

- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **pytest** - Python testing
- **Vitest** - Frontend testing

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest --cov=app --cov-report=html

# Frontend tests
cd frontend
npm run test

# Run all tests with coverage
./run-coverage.sh
```

---

## 📖 API Documentation

Interactive API documentation available when running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoints

**Upload Document**

```bash
POST /rag/upload/
Content-Type: multipart/form-data
Body: { file: PDF, user_id: string }
```

**Query Document**

```bash
POST /rag/query/
Content-Type: application/json
Body: { query: string, user_id: string, chat_history: array }
```

---

## 🤝 Contributing

Contributions are welcome! Please see our [Contributing Guidelines](https://github.com/andrea-ragalzi/document-intelligent-hub/wiki/Contributing-Guidelines) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Andrea Ragalzi**

- Email: andrea.ragalzi.code@gmail.com
- GitHub: [@andrea-ragalzi](https://github.com/andrea-ragalzi)

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Next.js](https://nextjs.org/) - The React Framework
- [LangChain](https://www.langchain.com/) - LLM application framework
- [ChromaDB](https://www.trychroma.com/) - Open-source embedding database
- [OpenAI](https://openai.com/) - GPT models and embeddings
- [Vercel AI SDK](https://sdk.vercel.ai/) - AI streaming toolkit
- [TanStack Query](https://tanstack.com/query) - Powerful data synchronization
- [Zustand](https://github.com/pmndrs/zustand) - Lightweight state management
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS framework
- [Firebase](https://firebase.google.com/) - Authentication and Firestore
- [TypeScript](https://www.typescriptlang.org/) - JavaScript with syntax for types
- [Docker](https://www.docker.com/) - Containerization platform

---

**⭐ Star this repository if you find it helpful!**
