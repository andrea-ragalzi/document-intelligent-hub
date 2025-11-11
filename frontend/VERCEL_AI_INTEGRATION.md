# Integrazione Vercel AI SDK

## Modifiche Implementate

### 1. Installazione del Package
```bash
npm install ai@^4
```

### 2. Nuovo Hook: `useChatAI`
File: `hooks/useChatAI.ts`

Questo hook sostituisce `useRAGChat` e utilizza l'hook `useChat` di Vercel AI SDK per gestire lo streaming delle risposte.

**Caratteristiche:**
- Gestione automatica dello streaming delle risposte
- Integrazione con l'API route `/api/chat`
- Conversione automatica dei messaggi dal formato Vercel AI al formato ChatMessage dell'app
- Gestione errori integrata

### 3. API Route Proxy
File: `app/api/chat/route.ts`

Questo endpoint Next.js funziona come proxy tra il frontend e il backend FastAPI.

**Funzionalità:**
- Runtime: Edge (per performance ottimali)
- Riceve i messaggi dal frontend (`useChat`)
- Estrae l'ultima query dell'utente
- Formatta la cronologia chat per il backend
- Chiama il backend FastAPI su `http://127.0.0.1:8000/rag/query/`
- Restituisce la risposta in streaming character-by-character

**Formato richiesta al backend:**
```json
{
  "query": "ultima domanda dell'utente",
  "user_id": "uuid-utente",
  "chat_history": [
    { "type": "user", "text": "..." },
    { "type": "assistant", "text": "..." }
  ]
}
```

### 4. Aggiornamento Componenti

#### `page.tsx`
- Rimosso import di `useRAGChat`
- Aggiunto import di `useChatAI`
- Adattato per usare `input`, `handleInputChange`, `handleSubmit` e `isLoading` dal nuovo hook
- Creato wrapper `handleQueryChange` per compatibilità con `ChatSection`
- Disabilitato temporaneamente il caricamento delle conversazioni salvate (richiede refactoring)

#### `ChatSection.tsx`
Nessuna modifica richiesta - rimane compatibile grazie al wrapper.

## Come Funziona

### Flusso dello Streaming

1. **Utente digita una domanda** → `input` gestito da `useChat`
2. **Submit del form** → `handleSubmit` invia una POST a `/api/chat`
3. **API Route** → estrae i dati e chiama il backend FastAPI
4. **Backend FastAPI** → restituisce la risposta JSON
5. **API Route** → crea uno stream e invia i caratteri uno per volta
6. **useChat Hook** → riceve lo stream e aggiorna automaticamente `messages`
7. **UI** → l'ultimo messaggio viene aggiornato in tempo reale mentre arrivano i caratteri

### Formato Messaggi

**Frontend (Vercel AI SDK):**
```typescript
{
  id: string;
  role: 'user' | 'assistant' | 'data' | 'system';
  content: string;
}
```

**Backend (FastAPI):**
```typescript
{
  type: 'user' | 'assistant';
  text: string;
  sources?: string[];
}
```

## Limitazioni Correnti

### 1. Streaming Simulato
L'API route attualmente simula lo streaming inviando la risposta character-by-character.

**TODO Futuro:** Modificare il backend FastAPI per supportare Server-Sent Events (SSE) nativi.

### 2. Gestione delle Fonti
Le fonti dei documenti (`source_documents`) vengono aggiunte alla fine della risposta come testo.

**TODO Futuro:** Implementare un sistema di metadata per separare le fonti dal contenuto.

### 3. Caricamento Conversazioni
Il caricamento delle conversazioni salvate è temporaneamente disabilitato.

**Motivo:** `useChat` gestisce internamente lo stato dei messaggi e non permette di sostituirlo facilmente con conversazioni caricate da localStorage.

**TODO Futuro:** 
- Implementare un sistema di `initialMessages` per `useChat`
- O creare un custom hook che sincronizzi `useChat` con localStorage

## Vantaggi dell'Integrazione

✅ **Streaming Automatico:** `useChat` gestisce automaticamente l'aggiornamento incrementale dell'UI  
✅ **Code Splitting:** Edge Runtime riduce le dimensioni del bundle  
✅ **Type Safety:** TypeScript completo con tipi del SDK  
✅ **Error Handling:** Gestione errori integrata nell'hook  
✅ **Scalabilità:** Pronto per integrare provider LLM (OpenAI, Anthropic, etc.) in futuro  

## Prossimi Passi

1. **Implementare SSE nel Backend FastAPI**
   - Usare `StreamingResponse` di FastAPI
   - Inviare eventi SSE con formato `data: {...}\n\n`
   
2. **Gestire Metadata delle Fonti**
   - Separare le fonti dalla risposta testuale
   - Aggiungere un campo `metadata` ai messaggi
   
3. **Ripristinare Caricamento Conversazioni**
   - Usare `initialMessages` di `useChat`
   - Sincronizzare lo stato con localStorage

4. **Testing End-to-End**
   - Testare lo streaming con diversi tipi di query
   - Verificare la gestione degli errori
   - Testare con documenti di diverse dimensioni

## Testing

Per testare l'integrazione:

```bash
# 1. Avvia il backend FastAPI (se non è già in esecuzione)
cd backend
uvicorn main:app --reload

# 2. Avvia il frontend Next.js
cd frontend
npm run dev

# 3. Apri http://localhost:3000
# 4. Carica un documento PDF
# 5. Fai una domanda e osserva lo streaming della risposta
```

## Configurazione Ambiente

Assicurati che `.env.local` contenga:
```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/rag
```
