# Backend — Document Intelligent Hub

AI-powered RAG (Retrieval-Augmented Generation) API built with **FastAPI** and **LangChain**.

## Overview

This backend service exposes a REST API for uploading documents, indexing them into a vector store (ChromaDB), and answering questions using LLM-based retrieval pipelines.

## Tech Stack

- **Python 3.12**
- **FastAPI** — async REST API framework
- **LangChain** — LLM orchestration and RAG pipelines
- **ChromaDB** — vector store for document embeddings
- **OpenAI** — language model and embedding provider
- **Cohere** — reranking support
- **Firebase Admin** — authentication and Firestore integration
- **Poetry** — dependency management

## Getting Started

### Prerequisites

- Python 3.12+
- [Poetry](https://python-poetry.org/docs/#installation)

### Installation

```sh
poetry install
```

### Running the server

```sh
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Running with Docker

```sh
docker compose up --build
```

## Environment Variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key for embeddings and completions |
| `COHERE_API_KEY` | Cohere API key for reranking |
| `PORT` | Server port (default: `8000`) |

## Testing

```sh
poetry run pytest --cov=app
```

## License

MIT