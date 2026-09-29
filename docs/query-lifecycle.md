# Query Lifecycle — Frontend to Grounded Answer

## Overview

The dashboard sends a question through a Next.js chat adapter to the authenticated FastAPI query endpoint. The endpoint may answer a narrow exact-evidence request deterministically. Otherwise it prepares the query and delegates retrieval, context selection, and grounded generation to application services. FastAPI returns a complete JSON answer and citation list; the Next.js adapter progressively emits that completed answer to the chat UI.

```text
User → dashboard chat → useChatAI → authenticated /api/chat request
→ POST /rag/query/ → workspace and quota checks → routing/query preparation
→ retrieval → reranking → context selection → grounded generation
→ evidence validation → QueryResponse → chat adapter → displayed answer and sources
```

## 1. Frontend query submission

The active dashboard is `frontend/app/dashboard/page.tsx`. Its `ChatSection` renders the composer and messages. `createSubmitHandler` in `frontend/components/ChatSection/chatHelpers.ts` accepts a nonblank question of at most 1,000 characters when a user ID is available, no request is in progress, and chat is enabled (documents are available, the server is online, and the displayed limit is not reached). The dashboard's `submitQuery` delegates to `useChatAI.handleSubmit`. Suggested questions fill the input through the same dashboard state.

`frontend/hooks/useChatAI.ts` owns the AI SDK `useChat` messages, input, loading/error state, and submission. `useChat` optimistically adds the user turn and sends its messages to `/api/chat`; the hook also supplies `userId` in the request body. The dashboard derives `chatHistory` from these messages for display and, for registered users, later Firestore autosave.

## 2. Authentication and API request

On each submission, `useChatAI.handleSubmit` calls `getIdToken()` from `AuthContext`, which calls the current Firebase user's `getIdToken()` (allowing Firebase to refresh an expired token). With no token, submission stops. Otherwise `useChat` sends `Authorization: Bearer <token>` to the Next.js `POST /api/chat` route in `frontend/app/api/chat/route.ts`.

That route requires the header and a body `userId`, takes the final user message as `query`, and forwards at most the preceding 14 messages as `conversation_history`. It sends JSON `{ query, user_id, conversation_history }`, plus `output_language` if supplied, to `POST ${NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/rag"}/query/`, forwarding the bearer header. The normal dashboard hook supplies no output language override. `user_id` is adapter compatibility data: the backend's `QueryRequest` has no such field, and authorization uses the verified token instead.

The adapter propagates backend non-2xx status and error detail (including 429). Its catch path returns 500. It does not set a separate fetch timeout; FastAPI bounds its worker wait. The Next.js route sets `maxDuration = 300`.

## 3. Backend HTTP boundary

`backend/main.py` mounts `backend/app/routers/query_router.py`; its `query_document` handles `POST /rag/query/`. Pydantic `QueryRequest` in `backend/app/schemas/rag_schema.py` requires a 3–1,000 character query, validates user/assistant history messages and their size limits, and accepts optional `output_language`.

`get_query_workspace_access` in `backend/app/core/auth.py` verifies the Firebase ID token. A registered user must have verified email and receives a workspace ID equal to their verified UID. A Firebase anonymous principal may query the reserved shared demo workspace. Client-supplied IDs do not select a workspace.

The router acquires process-local global expensive-operation and per-principal query slots, plus a guest concurrency slot for guests; a full limiter returns 429 without waiting. It then runs the potentially billable work in a thread while retaining those leases until the worker actually finishes, including after an HTTP timeout. Before document lookup or model calls, the worker reserves a registered user's tier-based daily query slot through `QueryQuotaService`, or a guest UID/IP/global daily budget through `GuestQueryBudgetService`. Exhausted quotas return 429. These admission, request, timeout, and response-mapping duties belong to the HTTP boundary; application services own query decisions and RAG work.

## 4. Pre-RAG routing and query preparation

After reservation, the router calls `RAGService.get_user_documents(workspace_id)` to obtain accessible filenames and document metadata. It tries `RAGService.try_deterministic_query` on the raw question first. `DeterministicQueryRouter` recognizes only specific exact occurrence, page-location, labeled-value, and document-count shapes, and routes requests with conversation history to RAG. A fully validated deterministic answer with trusted citations returns directly through the common `QueryResponse` mapping. Unsupported, ambiguous, or failed exact-evidence cases continue through RAG.

On the RAG branch, `QueryParserService.extract_file_filters` uses the configured model to clean the question, validate mentioned filenames against the accessible catalog (exact match first, then bounded embedding similarity), and produce include/exclude filters. The cleaned query goes to `RAGService`; the raw question is retained separately. If the parser reports two valid standalone retrieval questions for a compound request, the router passes them as `retrieval_queries`. Invalid or failed parsing falls back to the original query and no filters. Include filters take precedence over exclude filters downstream.

## 5. RAG orchestration

`RAGService.answer_query` in `backend/app/services/rag_orchestrator_service.py` coordinates services; it does not implement HTTP handling or vector persistence. It retains the raw user question for the answer prompt and response-language decision, while using the parser's cleaned question for context detection and possible reformulation.

`LanguageService.resolve_response_language` prefers an explicit output override, then a language request in the current message, then reliable detection of that message, recent user messages, and finally English. `QueryProcessingService.requires_conversation_context` checks for a short or conversational question with history, excluding short questions with an identifiable named subject. Only when history is needed does RAG retain it for reformulation and the answer prompt. Reformulation uses an LLM and returns the cleaned question if the result is invalid or a handled invocation error occurs. Language detection on the resulting retrieval question is separate from the response-language choice.

`QueryProcessingService.classify_query` exists, but semantic query classification is **not called** by the normal `answer_query` path.

## 6. Retrieval pipeline

`AnswerGenerationService.generate_answer` translates a non-English retrieval question to English through the translation adapter, falling back to the original on failure. It then calls `_retrieve_and_rerank`:

1. For a normal query, `QueryExpansionService` asks an LLM for up to five alternative search phrasings and rejects variants that alter protected identifiers. For a validated two-part compound query, it skips LLM expansion and uses those two parts. It builds an ordered pool from the translated question, raw user question, and the applicable variants, removing equivalent query strings. Compound candidate lists use a smaller per-search bound and reciprocal-rank fusion before reranking.
2. `VectorStoreRepository.get_retriever` creates a Chroma retriever with a metadata filter on `source = workspace_id`, plus validated filename inclusion or exclusion. Searches for the distinct queries run concurrently (at most four workers), with a bounded number of dense candidates per search. This gives semantic recall without crossing workspaces.
3. When the raw question or compound parts contain distinctive names or identifiers, `_extract_lexical_terms` supplies at most three terms to `VectorStoreRepository.lexical_candidate_search`. That repository performs bounded, tenant-scoped Chroma content/title lookups and limited surrounding-document expansion, applying the same filename filters. These candidates supplement dense retrieval for exact strings; they are not automatically evidence.
4. Dense and lexical candidates are merged by content-and-metadata identity. `_suppress_retrieval_noise` removes repeated header/footer text across pages and exact duplicate content within one document, while retaining identical text from different documents.
5. `VectorStoreRepository.get_temporary_page_contexts` inspects the retrieved pages in the same workspace and may add bounded page or parser-parent aggregates where fragments need surrounding context. These are temporary candidates, not new persisted chunks. The service reconciles overlapping aggregates before reranking.

## 7. Reranking and final context selection

### Reranking

`RerankingService.rerank_candidates` scores and orders all eligible merged candidates. Its signals include initial retrieval rank, query-term coverage/frequency, filename and metadata relevance, identifier matches, compound-part coverage, and context quality. It suppresses atomic chunks fully represented by an aggregate. The result is an ordered candidate pool with `rerank_score` metadata; it is not yet the final prompt context. Expansion helps recall, but the scoring query is the raw question and, when different, the translated retrieval question.

### Final context selection

`FinalContextSelector.select` applies a relative score gate (at least 70% of the best score), targets at least two chunks when available, and caps context at five. Among similarly scored candidates it favors different documents and pages, and it avoids exact or near-duplicate text. It can fill below the score gate to meet the minimum when possible. This separate step controls prompt size and evidence diversity without modifying reranker scores.

## 8. Grounded generation

`AnswerGenerationService._generate_llm_response` assigns selected context passages IDs `C1`, `C2`, and so on, and formats each with backend-known filename and optional page metadata. `_build_final_prompt` combines the configured RAG system prompt, response language, the **raw current user message**, relevant formatted conversation history, and selected context. It instructs the answer model to answer from that context and return structured `AnswerWithEvidence { answer, evidence_ids }`, using the minimum sufficient passage IDs. A request with no selected documents still reaches generation with empty context.

## 9. Evidence and citations

The model supplies answer text and proposed context IDs, not trusted filenames or page numbers. `_citations_from_evidence_ids` accepts only IDs present in the selected context map, then derives filename and valid one-based page number from chunk metadata. It deduplicates filename/page pairs in context order. Unknown IDs, missing filenames, or empty evidence IDs produce no citation for those entries. A selected chunk without valid page metadata can still yield a filename-only citation.

When the normal answer has **zero valid citations** and reranked atomic candidates exist, `_run_citation_rescue` may run once. It first allowlists only workspace-owned, file-filter-compliant atomic chunks with valid pages; an extraction model proposes exact spans with source IDs and pages. The backend checks each ID, page, uniqueness, and verbatim presence in the trusted chunk. If any spans pass, the answer model generates again from only those verified spans, and its new evidence IDs undergo the same citation mapping. If extraction or rescue generation fails, or nothing verifies, the normal answer and its empty citations are preserved. A rescue answer can also have no citations if its IDs do not validate.

## 10. API response

The router converts service sources into `QueryResponse { answer, source_documents, citations }`. `_normalize_citations` validates citation objects, deduplicates filename/page pairs, and caps the list at five; it also accepts legacy filename strings. `source_documents` is the ordered set of filenames derived from that normalized citation list, not a separate model claim. `SourceCitation` contains `filename` and optional one-based `page_number` (which can be null when unavailable). The same response shape covers deterministic and RAG results.

## 11. Frontend response handling

The Next.js `/api/chat` route parses the complete FastAPI JSON. It uses `answer` or a fallback display string, validates structured citations, and uses `source_documents` for filename-only citations only when `citations` is absent. It strips internal `[DOCUMENT n]` markers. It then emits the finished answer character by character, with a short delay, in AI SDK text-stream format and appends citations as a `sources` annotation. **FastAPI does not stream model tokens to this UI.**

`useChatAI` receives that stream through `useChat`, whose messages and loading state update as the answer arrives. The hook converts assistant annotations into `ChatMessage.sources`; `ChatSection` displays the turns through `ChatMessageDisplay`, which deduplicates and groups citations by filename and renders clickable page links. Opening one fetches the authenticated document content and navigates to the cited page. After completion, `onFinish` refreshes query usage; the dashboard autosaves completed user/assistant pairs and their sources to Firestore for registered users. Loading ends with the SDK request. On error, `useChatAI` removes the optimistic trailing user turn, refreshes usage, and suppresses console noise for 429 responses.

## 12. Failure and fallback paths

- Missing/invalid Firebase authorization returns 401; unverified registered email is denied. The Next.js adapter also rejects a missing bearer header or missing `userId`/latest user message.
- Full concurrency slots and exhausted registered or guest budgets return 429. The backend's worker wait times out with 504; a worker that continues after the HTTP timeout keeps its lease until it actually finishes. Unhandled query failures return 500, retaining an already reserved quota slot.
- An unsupported or unvalidated deterministic route falls through to RAG. Parser failure uses the raw question without file filters; reformulation and retrieval translation each fall back to their input; expansion failure leaves the base query pool.
- Empty retrieval still reaches the answer model with empty context. Answer-model failure returns a fixed error answer with no citations. Invalid or absent model evidence IDs yield no citations; the conditional rescue described above may recover verified evidence.
- Backend errors propagate through `/api/chat`; `useChatAI` clears the incomplete optimistic turn and settles loading through the AI SDK.

## 13. End-to-end sequence diagram

```mermaid
sequenceDiagram
    actor User
    participant UI as ChatSection / Dashboard
    participant Hook as useChatAI / useChat
    participant Auth as Firebase Auth / Admin SDK
    participant Adapter as Next.js /api/chat
    participant Router as FastAPI QueryRouter
    participant Parser as QueryParserService
    participant RAG as RAGService
    participant Processing as QueryProcessingService
    participant Generation as AnswerGenerationService
    participant Ranker as RerankingService
    participant Selector as FinalContextSelector
    participant Repo as VectorStoreRepository
    participant Store as ChromaDB
    participant LLM as Answer LLM

    User->>UI: Submit question
    UI->>Hook: handleSubmit
    Hook->>Auth: getIdToken()
    Auth-->>Hook: ID token
    Hook->>Adapter: POST /api/chat (messages, bearer token)
    Adapter->>Router: POST /rag/query/ (query, history, bearer token)
    Router->>Auth: Verify token / resolve workspace
    Auth-->>Router: Principal and workspace
    Router->>Router: Acquire leases; reserve quota
    Router->>RAG: get_user_documents(workspace)
    RAG->>Repo: List accessible documents
    Repo->>Store: Workspace-scoped lookup
    Store-->>Repo: Document metadata
    Repo-->>RAG: Accessible documents
    RAG-->>Router: Accessible documents
    Router->>RAG: Try deterministic route
    alt Valid deterministic answer
        RAG-->>Router: Answer and trusted citations
    else Normal RAG
        Router->>Parser: extract_file_filters(raw query, accessible files)
        Parser->>LLM: Structured parsing request
        LLM-->>Parser: File filters and cleaned query
        Parser-->>Router: Cleaned query, filters, optional compound parts
        Router->>RAG: answer_query(cleaned, raw, history, filters)
        RAG->>Processing: Context decision; optional reformulation
        Processing-->>RAG: Retrieval question
        RAG->>Generation: generate_answer
        Generation->>Repo: Tenant-filtered dense and lexical searches
        Repo->>Store: Vector and bounded content lookups
        Store-->>Repo: Candidate chunks
        Repo-->>Generation: Candidates and temporary page context
        Generation->>Ranker: Score and order candidates
        Ranker-->>Generation: Reranked candidates
        Generation->>Selector: Select bounded diverse context
        Selector-->>Generation: Final passages
        Generation->>LLM: Structured grounded answer request
        LLM-->>Generation: Answer and evidence IDs
        Generation->>Generation: Validate IDs; map metadata; optional rescue
        Generation-->>RAG: Answer and citations
        RAG-->>Router: Answer and citations
    end
    Router-->>Adapter: Complete QueryResponse JSON
    Adapter-->>Hook: Simulated character stream and source annotation
    Hook-->>UI: Updated messages, loading state, citations
    UI-->>User: Render answer and clickable sources
```

## 14. Responsibility summary

| Layer / component | Main responsibility |
|---|---|
| Frontend UI (`ChatSection`, dashboard, `ChatMessageDisplay`) | Accept eligible questions, display messages and clickable citations, autosave completed registered-user conversations. |
| Frontend query layer (`useChatAI`, `/api/chat`) | Get a valid Firebase token per request, manage AI SDK chat state, adapt messages to backend JSON and completed JSON back to a UI stream. |
| QueryRouter (`query_document`) | Validate the HTTP request and identity, resolve workspace, enforce admission/quota, attempt deterministic routing, parse query filters, and normalize the response. |
| `RAGService` | Coordinate language, conversation context, optional reformulation, deterministic evidence operations, and answer generation. |
| `QueryProcessingService` | Decide whether history is needed and optionally reformulate a contextual question. |
| `AnswerGenerationService` | Assemble retrieval candidates, invoke ranking/selection, construct the grounded prompt, validate evidence, and map citations. |
| `VectorStoreRepository` | Scope Chroma operations to the workspace and filename filters; supply dense/lexical candidates and temporary page/parent context. |
| `RerankingService` | Score and order eligible candidates using retrieval, text, metadata, and compound-query signals. |
| `FinalContextSelector` | Bound the prompt context using a relative score threshold, diversity, and redundancy rules. |
