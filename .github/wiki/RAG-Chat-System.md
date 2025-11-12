# RAG Chat System

Understanding the Retrieval-Augmented Generation (RAG) architecture.

## Overview

The RAG system combines document retrieval with large language models to provide accurate, context-aware responses based on your uploaded documents.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Query                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│               Language Detection                             │
│            (Italian / English)                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│               Query Embedding                                │
│         (Convert text to vector)                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│             ChromaDB Search                                  │
│        (Find similar document chunks)                        │
│              Top K = 5 results                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│            Context Construction                              │
│      (Combine retrieved chunks)                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              LLM Generation                                  │
│      (GPT-4 generates response)                              │
│         with streaming output                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│            Response to User                                  │
│      (With source citations)                                 │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Document Processing Pipeline

**Location**: `backend/app/services/rag_service.py`

#### Upload Flow

```python
1. Receive PDF file
2. Extract text with PyPDF2
3. Split into chunks (1000 chars, 200 overlap)
4. Generate embeddings for each chunk
5. Store in ChromaDB with metadata
6. Return success response
```

#### Chunking Strategy

```python
CHUNK_SIZE = 1000          # Characters per chunk
CHUNK_OVERLAP = 200        # Overlap between chunks
```

**Why overlap?**
- Preserves context across chunk boundaries
- Ensures no information loss
- Better retrieval accuracy

**Example:**

```
Document: "The quick brown fox jumps over the lazy dog. The dog was sleeping."

Chunk 1: "The quick brown fox jumps over the lazy dog."
Chunk 2: "lazy dog. The dog was sleeping."
         ^^^^^^^^^ (overlap)
```

### 2. Embedding Generation

**Provider**: OpenAI `text-embedding-ada-002`

**Process:**
```python
text = "What is machine learning?"
embedding = openai.Embedding.create(
    input=text,
    model="text-embedding-ada-002"
)
vector = embedding['data'][0]['embedding']  # 1536 dimensions
```

**Properties:**
- **Dimensions**: 1536
- **Max input**: 8191 tokens
- **Output**: Normalized vector
- **Cost**: $0.0001 / 1K tokens

### 3. Vector Database (ChromaDB)

**Location**: `backend/chroma_db/`

#### Collection Structure

```python
{
  "ids": ["doc1_chunk1", "doc1_chunk2", ...],
  "embeddings": [[0.1, 0.2, ...], [0.3, 0.4, ...], ...],
  "metadatas": [
    {
      "source": "document.pdf",
      "page": 1,
      "chunk_index": 0
    },
    ...
  ],
  "documents": ["text of chunk 1", "text of chunk 2", ...]
}
```

#### Similarity Search

```python
# Query embedding
query_vector = embed("What is AI?")

# Search ChromaDB
results = collection.query(
    query_embeddings=[query_vector],
    n_results=5,  # Top 5 most similar
    include=["documents", "metadatas", "distances"]
)
```

**Distance Metrics:**
- **Cosine**: Default, measures angle between vectors
- **L2**: Euclidean distance
- **IP**: Inner product

### 4. Context Construction

**Strategy**: Combine top-k retrieved chunks into context

```python
def build_context(query_results):
    chunks = []
    for doc, metadata in zip(query_results['documents'][0], 
                             query_results['metadatas'][0]):
        chunks.append({
            'text': doc,
            'source': metadata['source'],
            'page': metadata.get('page', 'N/A')
        })
    
    # Format context
    context = "\n\n---\n\n".join([
        f"Source: {chunk['source']} (Page {chunk['page']})\n{chunk['text']}"
        for chunk in chunks
    ])
    
    return context, chunks
```

### 5. LLM Generation

**Provider**: OpenAI GPT-4

#### Prompt Template

```python
system_prompt = """You are a helpful AI assistant that answers questions based on provided document context.

Instructions:
1. Answer based ONLY on the provided context
2. If the answer is not in the context, say "I cannot find this information in the provided documents"
3. Cite sources when possible
4. Be concise and accurate
5. Maintain conversation context
"""

user_prompt = f"""Context from documents:
{context}

User question: {query}

Please provide a detailed answer based on the context above."""
```

#### Streaming Response

```python
async def stream_response(messages):
    async for chunk in openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=messages,
        temperature=0.7,
        max_tokens=2000,
        stream=True
    ):
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

## Multi-Language Support

**Location**: `backend/app/services/language_service.py`

### Language Detection

```python
from langdetect import detect

def detect_language(text: str) -> str:
    try:
        lang = detect(text)
        return 'it' if lang == 'it' else 'en'
    except:
        return 'en'  # default to English
```

### Language-Specific Prompts

**Italian:**
```python
system_prompt_it = """Sei un assistente AI utile che risponde a domande basandosi sul contesto fornito dai documenti.

Istruzioni:
1. Rispondi SOLO in base al contesto fornito
2. Se la risposta non è nel contesto, di' "Non riesco a trovare queste informazioni nei documenti forniti"
3. Cita le fonti quando possibile
4. Sii conciso e preciso
5. Mantieni il contesto della conversazione
"""
```

**English:**
```python
system_prompt_en = """You are a helpful AI assistant that answers questions based on provided document context.

Instructions:
1. Answer based ONLY on the provided context
2. If the answer is not in the context, say "I cannot find this information in the provided documents"
3. Cite sources when possible
4. Be concise and accurate
5. Maintain conversation context
"""
```

## API Integration

### Backend Endpoint

**POST** `/api/query`

```python
@router.post("/query")
async def query_documents(request: QueryRequest):
    # 1. Detect language
    language = detect_language(request.query)
    
    # 2. Retrieve context from ChromaDB
    context, sources = retrieve_context(request.query)
    
    # 3. Build prompt
    messages = build_messages(request.query, context, language)
    
    # 4. Stream response
    return StreamingResponse(
        stream_llm_response(messages),
        media_type="text/event-stream"
    )
```

### Frontend Integration

**Location**: `frontend/app/api/chat/route.ts`

```typescript
export async function POST(req: Request) {
  const { messages, userId } = await req.json();
  
  // Call backend RAG endpoint
  const response = await fetch(`${API_URL}/api/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: messages[messages.length - 1].content,
      user_id: userId
    })
  });
  
  // Stream response to frontend
  return new Response(response.body, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    }
  });
}
```

## Streaming Implementation

### Why Streaming?

- ✅ **Better UX**: Users see response as it's generated
- ✅ **Perceived Speed**: Feels faster than waiting for complete response
- ✅ **Real-time Feedback**: Users can stop if answer is wrong
- ✅ **Lower Memory**: No need to buffer entire response

### Vercel AI SDK Integration

**Location**: `frontend/hooks/useChatAI.ts`

```typescript
import { useChat } from 'ai/react';

export function useChatAI({ userId }: { userId: string }) {
  const {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    setMessages
  } = useChat({
    api: '/api/chat',
    body: { userId },
    onResponse: (response) => {
      console.log('Stream started');
    },
    onFinish: (message) => {
      console.log('Stream completed');
    },
    onError: (error) => {
      console.error('Stream error:', error);
    }
  });
  
  return {
    chatHistory: messages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    setMessages
  };
}
```

## Performance Optimization

### Caching Strategy

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_embedding(text: str) -> List[float]:
    """Cache embeddings to avoid duplicate API calls"""
    return openai.Embedding.create(
        input=text,
        model="text-embedding-ada-002"
    )['data'][0]['embedding']
```

### Batch Processing

```python
def embed_batch(texts: List[str]) -> List[List[float]]:
    """Process multiple texts at once"""
    response = openai.Embedding.create(
        input=texts,
        model="text-embedding-ada-002"
    )
    return [item['embedding'] for item in response['data']]
```

### Query Optimization

```python
# Pre-filter by metadata before similarity search
results = collection.query(
    query_embeddings=[query_vector],
    n_results=10,
    where={"source": "specific_document.pdf"}  # Filter
)
```

## Quality Improvements

### Re-ranking

After initial retrieval, re-rank results:

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def rerank_results(query: str, documents: List[str]) -> List[int]:
    pairs = [[query, doc] for doc in documents]
    scores = reranker.predict(pairs)
    return sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
```

### Hybrid Search

Combine vector similarity with keyword matching:

```python
def hybrid_search(query: str):
    # Vector search
    vector_results = chroma_collection.query(
        query_embeddings=[embed(query)],
        n_results=10
    )
    
    # Keyword search (BM25)
    keyword_results = bm25_search(query, top_k=10)
    
    # Combine and deduplicate
    combined = merge_results(vector_results, keyword_results)
    return combined
```

## Monitoring & Debugging

### Logging Query Pipeline

```python
import logging

logger = logging.getLogger(__name__)

async def process_query(query: str):
    logger.info(f"Query received: {query}")
    
    # Embedding
    start = time.time()
    embedding = await get_embedding(query)
    logger.info(f"Embedding generated in {time.time() - start:.2f}s")
    
    # Retrieval
    start = time.time()
    results = search_chromadb(embedding)
    logger.info(f"Retrieved {len(results)} chunks in {time.time() - start:.2f}s")
    
    # Generation
    start = time.time()
    response = await generate_response(query, results)
    logger.info(f"Response generated in {time.time() - start:.2f}s")
    
    return response
```

### Response Quality Metrics

Track metrics:
- Query latency
- Number of retrieved chunks
- Token usage
- User feedback (implicit/explicit)

## Advanced Features

### Conversation History

Maintain context across multiple turns:

```python
conversation_history = [
    {"role": "user", "content": "What is AI?"},
    {"role": "assistant", "content": "AI is..."},
    {"role": "user", "content": "How does it work?"}  # "it" refers to AI
]
```

### Citation Tracking

Track which sources were used:

```python
{
  "answer": "Machine learning is a subset of AI...",
  "sources": [
    {"document": "ai_basics.pdf", "page": 5, "relevance": 0.95},
    {"document": "ml_intro.pdf", "page": 2, "relevance": 0.87}
  ]
}
```

## Next Steps

- [Document Upload](Document-Upload) - Upload implementation
- [Multi-language Support](Multi-language-Support) - Language handling
- [API Endpoints](API-Endpoints) - Complete API reference
- [Performance Optimization](Performance-Optimization) - Tune RAG system

## Further Reading

- [LangChain RAG Tutorial](https://python.langchain.com/docs/use_cases/question_answering/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [RAG Best Practices](https://www.pinecone.io/learn/retrieval-augmented-generation/)
