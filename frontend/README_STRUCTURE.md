# Frontend - Document RAG

Applicazione Next.js 15 con TypeScript per l'interfaccia del sistema RAG (Retrieval-Augmented Generation).

## Struttura del progetto

```
frontend/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Layout principale
│   ├── page.tsx           # Pagina principale (orchestrazione)
│   └── globals.css        # Stili globali
├── components/            # Componenti React riutilizzabili
│   ├── AlertMessage.tsx   # Messaggi di notifica
│   ├── ChatMessageDisplay.tsx  # Visualizzazione messaggi chat
│   ├── ChatSection.tsx    # Sezione chat principale
│   ├── ConversationList.tsx    # Lista conversazioni salvate
│   ├── SaveModal.tsx      # Modale per salvare conversazioni
│   ├── Sidebar.tsx        # Barra laterale (upload + conversazioni)
│   └── UploadSection.tsx  # Sezione per l'upload di documenti
├── hooks/                 # Custom React Hooks
│   ├── useConversations.ts     # Gestione conversazioni (localStorage)
│   ├── useDocumentUpload.ts    # Upload documenti PDF
│   ├── useRAGChat.ts          # Chat con il backend RAG
│   ├── useTheme.ts            # Gestione tema dark/light
│   └── useUserId.ts           # Gestione ID utente locale
├── lib/                   # Utilities e configurazioni
│   ├── constants.ts       # Costanti globali (URL API, chiavi localStorage)
│   └── types.ts           # Tipi TypeScript condivisi
└── public/                # Asset statici

```

## Tecnologie utilizzate

- **Next.js 15** - Framework React con App Router
- **TypeScript** - Tipizzazione statica
- **Tailwind CSS** - Styling utility-first
- **lucide-react** - Libreria di icone
- **localStorage** - Persistenza dati lato client (conversazioni)

## Architettura

### Hooks personalizzati

Ogni hook ha una responsabilità specifica e può essere usato indipendentemente:

- `useTheme`: Gestisce il tema (light/dark) con persistenza in localStorage
- `useUserId`: Genera e mantiene un ID utente univoco per il tenant
- `useConversations`: CRUD per le conversazioni salvate (localStorage)
- `useDocumentUpload`: Gestisce l'upload di file PDF al backend
- `useRAGChat`: Gestisce la chat con il backend RAG (query/risposte)

### Componenti

I componenti sono separati per responsabilità:

- **Presentazionali**: `AlertMessage`, `ChatMessageDisplay`
- **Container**: `Sidebar`, `ChatSection`
- **Modali**: `SaveModal`

### Flusso dati

1. `page.tsx` orchestra tutti gli hooks e componenti
2. Gli hooks gestiscono la logica di business e lo stato
3. I componenti ricevono props e callbacks
4. Le interazioni utente triggano callbacks che aggiornano lo stato negli hooks

## Configurazione

### URL Backend

Modificare in `lib/constants.ts`:

\`\`\`typescript
export const API_BASE_URL = "http://127.0.0.1:8000/rag";
\`\`\`

### Tema

Il tema viene salvato in localStorage con chiave `theme` e supporta:
- `light` (default)
- `dark`
- Auto-detect da sistema operativo al primo caricamento

### Conversazioni

Le conversazioni vengono salvate in localStorage con chiave `rag_conversations`.

## Sviluppo

\`\`\`bash
# Installa dipendenze
npm install

# Avvia il server di sviluppo
npm run dev

# Build per produzione
npm run build

# Avvia in produzione
npm start
\`\`\`

## Note

- **Nessuna dipendenza da Firebase/Firestore**: tutto è gestito localmente
- **Type-safe**: Tutti i tipi sono definiti in `lib/types.ts`
- **Modulare**: Ogni funzionalità può essere modificata indipendentemente
- **Responsive**: Design ottimizzato per mobile e desktop
