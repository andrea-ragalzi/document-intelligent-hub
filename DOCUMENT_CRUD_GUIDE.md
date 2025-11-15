# 📄 Gestione Documenti - Guida CRUD

## Panoramica
È stato implementato un sistema completo di gestione documenti (CRUD) che permette di:
- ✅ **Caricare** documenti PDF
- 📋 **Visualizzare** la lista dei documenti indicizzati
- 🗑️ **Eliminare** documenti singoli o tutti insieme
- 🔄 **Aggiornare** automaticamente la lista dopo modifiche

---

## 🎯 Funzionalità Implementate

### Backend API

#### 1. **GET** `/rag/documents/list`
Restituisce la lista di tutti i documenti indicizzati per un utente.

**Query Parameters:**
- `user_id` (string, required): ID dell'utente

**Response:**
```json
{
  "documents": [
    {
      "filename": "document.pdf",
      "chunks_count": 45,
      "language": "IT",
      "uploaded_at": "2025-11-13T10:30:00"
    }
  ],
  "total_count": 1,
  "user_id": "user123"
}
```

---

#### 2. **DELETE** `/rag/documents/delete`
Elimina un documento specifico e tutti i suoi chunks dal vector store.

**Query Parameters:**
- `user_id` (string, required): ID dell'utente
- `filename` (string, required): Nome del file da eliminare

**Response:**
```json
{
  "message": "Document 'document.pdf' deleted successfully.",
  "filename": "document.pdf",
  "chunks_deleted": 45
}
```

**Errori:**
- `404 Not Found`: Documento non trovato
- `500 Internal Server Error`: Errore durante l'eliminazione

---

#### 3. **DELETE** `/rag/documents/delete-all`
Elimina TUTTI i documenti di un utente (⚠️ operazione irreversibile!).

**Query Parameters:**
- `user_id` (string, required): ID dell'utente

**Response:**
```json
{
  "message": "All documents deleted successfully for user user123.",
  "chunks_deleted": 150
}
```

---

### Frontend Components

#### 1. **DocumentList Component**
`frontend/components/DocumentList.tsx`

Componente che visualizza la lista documenti con:
- 📄 Nome del file
- 🔢 Numero di chunks indicizzati
- 🌐 Lingua del documento
- 🗑️ Pulsante elimina (appare al hover)
- ⚠️ Conferma eliminazione con overlay

**Props:**
```typescript
interface DocumentListProps {
  documents: Document[];
  isLoading: boolean;
  onDeleteDocument: (filename: string) => void;
  onRefresh: () => void;
}
```

**Features:**
- Empty state quando non ci sono documenti
- Loading state con spinner
- Hover effects per UX migliore
- Conferma eliminazione inline
- Scroll automatico per liste lunghe

---

#### 2. **useDocuments Hook**
`frontend/hooks/useDocuments.ts`

Hook personalizzato per gestire lo stato dei documenti.

**API:**
```typescript
const {
  documents,          // Array dei documenti
  isLoading,          // Loading state
  error,              // Errore se presente
  refreshDocuments,   // Funzione per ricaricare
  deleteDocument,     // Elimina documento singolo
  deleteAllDocuments, // Elimina tutti i documenti
} = useDocuments(userId);
```

**Features:**
- Caricamento automatico all'avvio
- Refresh automatico dopo upload
- Gestione errori
- Eventi personalizzati per sincronizzazione
- Type-safe con TypeScript

---

### Integrazione nella Sidebar

La sezione di gestione documenti è stata aggiunta nella sidebar sinistra tra:
1. Document Indexing (upload)
2. **Manage Documents** (nuovo!)
3. Saved Conversations

**Layout:**
```tsx
<Sidebar>
  <UploadSection />       {/* 1. Upload PDF */}
  <DocumentList />         {/* 2. Gestione Documenti */}
  <ConversationList />    {/* 3. Conversazioni Salvate */}
</Sidebar>
```

---

## 🔄 Flusso di Sincronizzazione

### Eventi Personalizzati

1. **documentUploaded**: Emesso dopo upload riuscito
   - Trigger: `useDocumentUpload` hook
   - Listener: `useDocuments` hook
   - Azione: Ricarica lista documenti

2. **refreshDocumentStatus**: Emesso dopo modifica documenti
   - Trigger: `deleteDocument`, `deleteAllDocuments`
   - Listener: `useDocumentStatus` hook
   - Azione: Aggiorna contatore documenti

### Diagramma Flusso

```
User Upload PDF
    ↓
useDocumentUpload → API /upload/
    ↓
Emit "documentUploaded"
    ↓
useDocuments → API /documents/list
    ↓
DocumentList aggiornata
    ↓
Emit "refreshDocumentStatus"
    ↓
useDocumentStatus → Aggiorna contatore
```

---

## 🎨 UI/UX Features

### Stati Visivi

1. **Loading State**
   ```
   [Spinner] Loading documents...
   ```

2. **Empty State**
   ```
   [Icon] No documents uploaded yet
   Upload a PDF to get started
   ```

3. **Document Card**
   ```
   [PDF Icon] document.pdf
              45 chunks • IT
              [Delete on hover]
   ```

4. **Delete Confirmation**
   ```
   [Warning Icon] Delete this document?
   [Delete] [Cancel]
   ```

### Interazioni

- **Hover su documento**: Mostra pulsante elimina
- **Click su elimina**: Mostra conferma inline
- **ESC o click fuori**: Annulla conferma
- **Conferma delete**: Elimina con feedback visivo
- **Loading durante delete**: Pulsante disabilitato con spinner

---

## 🧪 Come Testare

### 1. Test Upload e Lista
```bash
# 1. Avvia backend e frontend
make dev-backend
make dev-frontend

# 2. Fai login
# 3. Carica un documento PDF
# 4. Verifica che appaia nella sezione "Manage Documents"
```

### 2. Test Eliminazione
```bash
# 1. Hover su un documento
# 2. Click sul pulsante trash icon
# 3. Conferma eliminazione
# 4. Verifica che il documento scompaia
# 5. Verifica che il contatore si aggiorni
```

### 3. Test API Diretta
```bash
# Lista documenti
curl "http://localhost:8000/rag/documents/list?user_id=test123"

# Elimina documento
curl -X DELETE "http://localhost:8000/rag/documents/delete?user_id=test123&filename=doc.pdf"

# Elimina tutti
curl -X DELETE "http://localhost:8000/rag/documents/delete-all?user_id=test123"
```

---

## 🔐 Sicurezza

- ✅ **User Isolation**: Ogni operazione richiede `user_id`
- ✅ **Authorization Check**: Backend verifica che documento appartenga all'utente
- ✅ **Type Safety**: TypeScript per prevenire errori
- ✅ **Error Handling**: Gestione completa errori client e server
- ⚠️ **Nota**: In produzione aggiungere autenticazione JWT/OAuth

---

## 🚀 Future Enhancements

Possibili miglioramenti futuri:

1. **📊 Document Preview**
   - Visualizza anteprima contenuto documento
   - Mostra primi paragrafi o pagine

2. **✏️ Rename Document**
   - Permetti di rinominare documenti
   - Aggiorna metadata

3. **📥 Download Document**
   - Permetti di scaricare PDF originale
   - Store file in object storage (S3, MinIO)

4. **🔍 Search Documents**
   - Cerca documenti per nome
   - Filtri per lingua, data, dimensione

5. **📦 Bulk Operations**
   - Seleziona multipli documenti
   - Elimina/scarica in blocco

6. **📈 Document Analytics**
   - Mostra quante query per documento
   - Statistiche di utilizzo

7. **🏷️ Tags/Categories**
   - Aggiungi tags ai documenti
   - Organizza per categorie

8. **⏰ Auto-Expire**
   - Documenti temporanei con TTL
   - Cleanup automatico

---

## 📚 Riferimenti Codice

### Backend
- `backend/app/routers/rag_router.py`: Endpoint API
- `backend/app/services/rag_service.py`: Logica business
- `backend/app/schemas/rag.py`: Schemi Pydantic

### Frontend
- `frontend/components/DocumentList.tsx`: UI lista documenti
- `frontend/components/Sidebar.tsx`: Integrazione sidebar
- `frontend/hooks/useDocuments.ts`: Hook gestione stato
- `frontend/hooks/useDocumentUpload.ts`: Hook upload (modificato)
- `frontend/lib/constants.ts`: Configurazione API

---

## 🐛 Troubleshooting

### Problema: Lista documenti vuota dopo upload
**Soluzione:**
- Verifica che l'evento `documentUploaded` venga emesso
- Controlla console per errori API
- Verifica che `user_id` sia consistente

### Problema: Errore "404 Not Found" durante delete
**Soluzione:**
- Verifica che `filename` sia corretto (encoding URL)
- Controlla che documento appartenga all'utente
- Verifica console backend per logs

### Problema: Lista non si aggiorna dopo delete
**Soluzione:**
- Verifica che `refreshDocuments()` venga chiamato
- Controlla che evento `refreshDocumentStatus` venga emesso
- Forza refresh con F5 come test

---

## ✅ Checklist Implementazione

- [x] Backend: Schema Pydantic per documenti
- [x] Backend: Endpoint GET /documents/list
- [x] Backend: Endpoint DELETE /documents/delete
- [x] Backend: Endpoint DELETE /documents/delete-all
- [x] Backend: Metodi service layer
- [x] Frontend: DocumentList component
- [x] Frontend: useDocuments hook
- [x] Frontend: Integrazione in Sidebar
- [x] Frontend: Event system per sync
- [x] Frontend: UI states (loading, empty, error)
- [x] Frontend: Delete confirmation UX
- [x] Testing: API endpoints
- [x] Testing: UI components
- [x] Documentation: Questa guida!

---

## 🎉 Conclusione

Il sistema di gestione documenti è completamente funzionale e integrato nell'applicazione. Gli utenti possono ora:
- Vedere tutti i loro documenti in un colpo d'occhio
- Eliminare documenti non più necessari
- Gestire lo spazio nel vector store
- Avere feedback visivo immediato

Il sistema è **type-safe**, **responsive** e **user-friendly**! 🚀
