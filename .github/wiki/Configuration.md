# Configuration Guide

Complete configuration reference for Document Intelligent Hub.

## Environment Variables

### Backend Configuration

Create `backend/.env`:

```bash
# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# LLM Provider
LLM_PROVIDER=openai  # openai, anthropic, ollama
LLM_API_KEY=your_api_key_here
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# Embeddings
EMBEDDING_MODEL=text-embedding-ada-002
EMBEDDING_PROVIDER=openai

# ChromaDB
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION_NAME=documents

# CORS
FRONTEND_URL=http://localhost:3000
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001

# RAG Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RESULTS=5

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### Frontend Configuration

Create `frontend/.env.local`:

```bash
# Firebase Authentication
NEXT_PUBLIC_FIREBASE_API_KEY=your_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789
NEXT_PUBLIC_FIREBASE_APP_ID=1:123456789:web:abc123

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# App Configuration
NEXT_PUBLIC_APP_NAME=Document Intelligent Hub
NEXT_PUBLIC_APP_VERSION=1.0.0
```

## Detailed Configuration

### LLM Provider Setup

#### OpenAI

```bash
LLM_PROVIDER=openai
LLM_API_KEY=sk-proj-...
LLM_MODEL=gpt-4  # or gpt-3.5-turbo, gpt-4-turbo
```

**Models:**

- `gpt-4`: Best quality, slower
- `gpt-4-turbo`: Fast GPT-4
- `gpt-3.5-turbo`: Fastest, cheaper

#### Anthropic Claude

```bash
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-...
LLM_MODEL=claude-3-opus-20240229
```

**Models:**

- `claude-3-opus`: Highest capability
- `claude-3-sonnet`: Balanced
- `claude-3-haiku`: Fastest

#### Local with Ollama

```bash
LLM_PROVIDER=ollama
LLM_API_KEY=  # not needed
LLM_MODEL=llama2
OLLAMA_BASE_URL=http://localhost:11434
```

### Embedding Configuration

#### OpenAI Embeddings

```bash
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-ada-002
```

#### Local Embeddings

```bash
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### ChromaDB Configuration

```bash
# Persistence directory
CHROMA_PERSIST_DIR=./chroma_db

# Collection name
CHROMA_COLLECTION_NAME=documents

# Distance metric: l2, cosine, or ip
CHROMA_DISTANCE_METRIC=cosine
```

### RAG Parameters

```bash
# Text chunking
CHUNK_SIZE=1000           # Characters per chunk
CHUNK_OVERLAP=200         # Overlap between chunks

# Retrieval
TOP_K_RESULTS=5          # Number of chunks to retrieve
SIMILARITY_THRESHOLD=0.7  # Minimum similarity score

# Context window
MAX_CONTEXT_LENGTH=4000   # Max characters in context
```

### CORS Configuration

```bash
# Single origin
FRONTEND_URL=http://localhost:3000

# Multiple origins (comma-separated)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,https://yourdomain.com
```

### Firebase Configuration

Get configuration from [Firebase Console](https://console.firebase.google.com/):

1. Go to Project Settings
2. Scroll to "Your apps" → Web app
3. Copy configuration values

**Security Rules** (Firestore):

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Conversations collection
    match /conversations/{conversationId} {
      allow read: if request.auth != null &&
                     request.auth.uid == resource.data.userId;
      allow create: if request.auth != null &&
                       request.auth.uid == request.resource.data.userId;
      allow update, delete: if request.auth != null &&
                               request.auth.uid == resource.data.userId;
    }
  }
}
```

## Advanced Configuration

### Custom Python Configuration

Edit `backend/app/core/config.py`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # LLM
    llm_provider: str = "openai"
    llm_api_key: str
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.7

    # Custom settings
    max_upload_size: int = 50_000_000  # 50MB
    allowed_file_types: list[str] = [".pdf", ".txt"]

    class Config:
        env_file = ".env"

settings = Settings()
```

### Custom Next.js Configuration

Edit `frontend/next.config.ts`:

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // React strict mode
  reactStrictMode: true,

  // Image optimization
  images: {
    domains: ["yourdomain.com"],
  },

  // Environment variables
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },

  // Redirects
  async redirects() {
    return [
      {
        source: "/old-path",
        destination: "/new-path",
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
```

### TanStack Query Configuration

Edit `frontend/providers/QueryProvider.tsx`:

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000, // 30 seconds
      gcTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
  },
});
```

**Options:**

- `staleTime`: How long data is considered fresh
- `gcTime`: How long inactive data stays in cache
- `retry`: Number of retry attempts on failure
- `refetchOnWindowFocus`: Refetch when window regains focus

### Zustand DevTools Configuration

Edit `frontend/stores/uiStore.ts`:

```typescript
export const useUIStore = create<UIStore>()(
  devtools(
    set => ({
      // ... store implementation
    }),
    {
      name: "UI Store",
      enabled: process.env.NODE_ENV === "development",
    }
  )
);
```

## Performance Tuning

### Backend Performance

```bash
# Increase workers for production
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000

# With gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### Frontend Performance

```bash
# Production build
npm run build
npm start

# Analyze bundle size
npm run build -- --analyze
```

### Database Performance

```bash
# ChromaDB memory settings
CHROMA_CACHE_SIZE=1000  # Number of embeddings to cache
```

## Docker Configuration

### Docker Compose

Edit `docker-compose.yml`:

```yaml
version: "3.8"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - LLM_API_KEY=${LLM_API_KEY}
      - CHROMA_PERSIST_DIR=/data
    volumes:
      - ./backend/chroma_db:/data

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
      - NEXT_PUBLIC_FIREBASE_API_KEY=${FIREBASE_API_KEY}
    depends_on:
      - backend
```

### Environment Variables for Docker

Create `.env` in root:

```bash
# LLM
LLM_API_KEY=your_key_here

# Firebase
FIREBASE_API_KEY=your_key_here
FIREBASE_PROJECT_ID=your_project_id
```

## Security Configuration

### API Key Protection

```bash
# Never commit .env files
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
```

### HTTPS Configuration

For production, use HTTPS:

```bash
# Backend with SSL
uvicorn main:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

### Rate Limiting

Add to `backend/main.py`:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/query")
@limiter.limit("10/minute")
async def query_endpoint():
    pass
```

## Logging Configuration

### Backend Logging

Edit `backend/app/core/config.py`:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### Frontend Logging

Use `console` methods:

```typescript
if (process.env.NODE_ENV === "development") {
  console.log("Debug info");
}
```

## Testing Configuration

### Backend Testing

Edit `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --cov=app
    --cov-report=html
    --cov-report=term
```

### Frontend Testing

Edit `vitest.config.ts`:

```typescript
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
    },
  },
});
```

## Next Steps

- [Development Workflow](Development-Workflow) - Development guide
- [Docker Deployment](Docker-Deployment) - Deploy with Docker
- [Production Deployment](Production-Deployment) - Production setup
- [Performance Optimization](Performance-Optimization) - Tune performance

## Troubleshooting

See [Common Issues](Common-Issues) for configuration problems.
