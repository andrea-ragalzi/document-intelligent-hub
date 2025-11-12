# State Management Architecture

## Overview

L'applicazione utilizza un'architettura moderna di state management che separa **UI state** da **Server state**:

- **Zustand**: Gestisce lo stato dell'interfaccia utente (modals, alerts, flags)
- **TanStack Query**: Gestisce lo stato del server (conversazioni da Firestore)

## Perché questa architettura?

### Problemi risolti:
1. ✅ **Prop drilling eliminato**: I componenti accedono direttamente agli store
2. ✅ **Separazione delle responsabilità**: UI state vs Server state
3. ✅ **Cache automatica**: TanStack Query cache le conversazioni
4. ✅ **Optimistic updates**: Le modifiche appaiono istantaneamente
5. ✅ **Automatic refetch**: Sincronizzazione automatica con Firestore
6. ✅ **DevTools**: Debug eccellente con Redux DevTools e React Query DevTools
7. ✅ **TypeScript-first**: Type safety completa

### Vantaggi rispetto a `useState`:
- **Meno boilerplate**: 1 store vs 10+ useState
- **Migliore performance**: Re-render solo quando necessario
- **Più scalabile**: Facile aggiungere nuove features
- **Più testabile**: Store isolati e facilmente mockabili

---

## 📁 Struttura dei File

```
frontend/
├── stores/
│   └── uiStore.ts                    # Zustand store per UI state
├── hooks/
│   └── queries/
│       └── useConversationsQuery.ts  # TanStack Query hooks per Firestore
├── providers/
│   └── QueryProvider.tsx             # Setup TanStack Query client
└── app/
    ├── layout.tsx                    # Wrap con QueryProvider
    └── page.tsx                      # Usa entrambi gli store
```

---

## 🎨 UI Store (Zustand)

**File**: `stores/uiStore.ts`

Gestisce tutto lo stato dell'interfaccia:

### State:
- `statusAlert`: Alert di stato dell'app
- `uploadAlert`: Alert per upload documenti
- `renameModalOpen`: Stato modal rinomina
- `confirmDeleteOpen`: Stato modal conferma eliminazione
- `conversationToRename`: Dati conversazione da rinominare
- `conversationToDelete`: Dati conversazione da eliminare
- `currentConversationId`: ID conversazione attiva
- `lastSavedMessageCount`: Contatore messaggi salvati
- `isSaving`: Flag salvataggio in corso

### Actions:
- `setStatusAlert()`, `setUploadAlert()`
- `openRenameModal()`, `closeRenameModal()`
- `openDeleteModal()`, `closeDeleteModal()`
- `setCurrentConversation()`, `updateSavedMessageCount()`
- `startSaving()`, `finishSaving()`, `resetConversation()`

### Utilizzo:

```typescript
import { useUIStore } from "@/stores/uiStore";

function MyComponent() {
  // Accedi solo allo stato che ti serve (evita re-render inutili)
  const { statusAlert, setStatusAlert } = useUIStore();
  
  const handleAction = () => {
    setStatusAlert({ message: "Fatto!", type: "success" });
  };
}
```

### DevTools:
Apri **Redux DevTools** nel browser per vedere:
- Tutti gli stati in tempo reale
- History delle azioni
- Time-travel debugging

---

## 🔄 Server State (TanStack Query)

**File**: `hooks/queries/useConversationsQuery.ts`

Gestisce le conversazioni con Firestore usando mutations e queries.

### Query:
```typescript
// Carica tutte le conversazioni dell'utente
const { data: conversations, isLoading } = useConversationsQuery(userId);
```

**Features**:
- Cache automatica (30 secondi stale time)
- Auto-refetch quando necessario
- Loading e error states automatici

### Mutations:

#### 1. Create Conversation
```typescript
const createConversation = useCreateConversation(userId);

await createConversation.mutateAsync({
  name: "Nuova conversazione",
  history: chatHistory
});
```

**Features**:
- Optimistic update: Appare subito nella lista
- Rollback automatico se fallisce
- Refetch dopo successo

#### 2. Update Name
```typescript
const updateName = useUpdateConversationName(userId);

await updateName.mutateAsync({
  id: "conv-123",
  newName: "Nuovo nome"
});
```

#### 3. Update History (Auto-save)
```typescript
const updateHistory = useUpdateConversationHistory(userId);

await updateHistory.mutateAsync({
  id: "conv-123",
  history: updatedChatHistory
});
```

**Ottimizzazione**: Non fa refetch automatico per evitare troppi roundtrip

#### 4. Delete Conversation
```typescript
const deleteConversation = useDeleteConversation(userId);

await deleteConversation.mutateAsync("conv-123");
```

**Features**:
- Rimozione ottimistica dalla UI
- Rollback se fallisce

### Query Keys:
```typescript
conversationKeys.all         // ["conversations"]
conversationKeys.byUser(id)  // ["conversations", userId]
```

Usati per invalidare e refetch cache in modo granulare.

---

## 🏗️ Setup in `layout.tsx`

```typescript
import { QueryProvider } from "@/providers/QueryProvider";

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <QueryProvider>
          <AuthProvider>
            {children}
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
```

**Configurazione QueryClient**:
- `staleTime: 30s` - Dati "fresh" per 30 secondi
- `gcTime: 5min` - Garbage collection dopo 5 minuti
- `retry: 1` - Riprova una volta in caso di errore
- `refetchOnWindowFocus: false` - Evita refetch continui

---

## 📱 Utilizzo in `page.tsx`

### Before (useState):
```typescript
const [statusAlert, setStatusAlert] = useState(null);
const [renameModalOpen, setRenameModalOpen] = useState(false);
const [conversationToRename, setConversationToRename] = useState(null);
// ... altri 7 useState ...

const { savedConversations, saveConversation, ... } = useConversations(...);
```

### After (Zustand + TanStack Query):
```typescript
// UI State
const {
  statusAlert,
  setStatusAlert,
  renameModalOpen,
  openRenameModal,
  closeRenameModal,
  // ... tutto in un posto
} = useUIStore();

// Server State
const { data: savedConversations = [] } = useConversationsQuery(userId);
const createConversation = useCreateConversation(userId);
const updateName = useUpdateConversationName(userId);
```

**Vantaggi**:
- ✅ 1 import invece di 10+ useState
- ✅ Actions con nomi chiari
- ✅ Type safety completo
- ✅ DevTools integrate

---

## 🔥 Auto-save Flow

```typescript
useEffect(() => {
  if (isLoading || !userId || chatHistory.length < 2) return;
  
  const autoSave = async () => {
    if (currentConversationId) {
      // Update esistente
      await updateHistory.mutateAsync({
        id: currentConversationId,
        history: chatHistory
      });
    } else {
      // Crea nuova
      await createConversation.mutateAsync({
        name: generateName(),
        history: chatHistory
      });
    }
  };
  
  const timeoutId = setTimeout(autoSave, 500); // Debounce
  return () => clearTimeout(timeoutId);
}, [chatHistory, isLoading, currentConversationId]);
```

**Features**:
1. Salva solo quando l'assistente finisce (`!isLoading`)
2. Debounce di 500ms per evitare multipli salvataggi
3. Crea nuova conversazione la prima volta
4. Aggiorna conversazione esistente le volte successive
5. Optimistic updates per UX fluida

---

## 🛠️ DevTools

### Zustand DevTools (Redux DevTools):
1. Installa [Redux DevTools Extension](https://github.com/reduxjs/redux-devtools)
2. Apri DevTools nel browser
3. Seleziona tab "Redux"
4. Vedi tutte le azioni e lo stato in tempo reale

### TanStack Query DevTools:
1. Già integrato (solo in development)
2. Clicca sul badge floating in basso a sinistra
3. Vedi:
   - Tutte le query attive
   - Cache status (fresh/stale/inactive)
   - Mutations in corso
   - Network requests

---

## 🚀 Vantaggi per il Futuro

### Scalabilità:
- ✅ Facile aggiungere nuovi store (es. `chatStore`, `settingsStore`)
- ✅ Facile aggiungere nuove mutations (es. `useShareConversation`)
- ✅ Facile aggiungere middleware (logger, persist, etc)

### Performance:
- ✅ Re-render solo componenti necessari (selector granulari)
- ✅ Cache automatica riduce chiamate a Firestore
- ✅ Optimistic updates per UX istantanea

### Developer Experience:
- ✅ DevTools eccellenti per debugging
- ✅ Type safety completa con TypeScript
- ✅ Codice più leggibile e manutenibile

### Testing:
- ✅ Store mockabili facilmente
- ✅ Mutations testabili in isolamento
- ✅ Separazione chiara delle responsabilità

---

## 📚 Best Practices

### 1. Separare UI State da Server State
```typescript
// ❌ NON mescolare
const [conversations, setConversations] = useState([]); // Server state
const [modalOpen, setModalOpen] = useState(false);      // UI state

// ✅ Separare chiaramente
const { data: conversations } = useConversationsQuery(userId); // Server state
const { modalOpen } = useUIStore();                             // UI state
```

### 2. Usare Optimistic Updates
```typescript
// Mutations con optimistic update rendono l'app super reattiva
const mutation = useMutation({
  mutationFn: deleteItem,
  onMutate: async (id) => {
    // Rimuovi subito dalla UI
    queryClient.setQueryData(['items'], old => 
      old.filter(item => item.id !== id)
    );
  }
});
```

### 3. Selector Granulari
```typescript
// ❌ Re-render quando QUALSIASI cosa cambia nello store
const store = useUIStore();

// ✅ Re-render solo quando statusAlert cambia
const statusAlert = useUIStore(state => state.statusAlert);
```

### 4. Query Keys Consistenti
```typescript
// Usa sempre gli stessi query keys per invalidazione corretta
export const conversationKeys = {
  all: ["conversations"],
  byUser: (userId) => ["conversations", userId],
};
```

---

## 🔄 Migration da `useState` a Store

### Step 1: Identifica il tipo di state
- **UI state**: Modal open/close, form values, UI flags → Zustand
- **Server state**: Dati da API/Firestore → TanStack Query

### Step 2: Crea azioni nello store
```typescript
// Prima
const [modalOpen, setModalOpen] = useState(false);

// Dopo
const { modalOpen, openModal, closeModal } = useUIStore();
```

### Step 3: Sostituisci async functions con mutations
```typescript
// Prima
const deleteItem = async (id) => {
  await api.delete(id);
  refetch();
};

// Dopo
const deleteMutation = useDeleteItem();
await deleteMutation.mutateAsync(id); // Auto-refetch
```

---

## 📖 Risorse

- [Zustand Docs](https://zustand-demo.pmnd.rs/)
- [TanStack Query Docs](https://tanstack.com/query/latest)
- [State Management Patterns](https://kentcdodds.com/blog/application-state-management-with-react)
- [When to use TanStack Query](https://tanstack.com/query/latest/docs/framework/react/guides/does-this-replace-client-state)

---

## 🎯 Summary

**Zustand**: UI state locale (modals, alerts, flags)  
**TanStack Query**: Server state remoto (Firestore data)  
**Result**: Codice pulito, performante, scalabile, testabile 🚀
