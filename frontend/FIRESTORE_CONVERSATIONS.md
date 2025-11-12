# Salvataggio Conversazioni con Firebase Firestore

## 📋 Panoramica

Le conversazioni sono ora salvate in modo persistente su **Firebase Firestore**, permettendo agli utenti di accedere alle proprie conversazioni da qualsiasi dispositivo dopo aver effettuato il login.

## 🔧 Implementazione

### Struttura Dati

Ogni conversazione salvata contiene:

```typescript
interface SavedConversation {
    id: string;              // ID documento Firestore
    userId?: string;         // UID utente Firebase
    name: string;            // Nome assegnato alla conversazione
    timestamp: string;       // Data/ora creazione
    history: ChatMessage[];  // Cronologia messaggi
}
```

### Servizi Implementati

#### `lib/conversationsService.ts`

Fornisce funzioni per interagire con Firestore:

- **`saveConversationToFirestore(userId, name, history)`**: Salva una nuova conversazione
- **`loadConversationsFromFirestore(userId)`**: Carica tutte le conversazioni dell'utente
- **`deleteConversationFromFirestore(conversationId)`**: Elimina una conversazione
- **`migrateLocalStorageToFirestore(userId, localConversations)`**: Migra conversazioni da localStorage

### Hook Aggiornato

#### `hooks/useConversations.ts`

Ora richiede sia `currentChatHistory` che `userId`:

```typescript
const { savedConversations, saveConversation, deleteConversation } =
  useConversations({ currentChatHistory: chatHistory, userId });
```

**Funzionalità:**
- ✅ Caricamento automatico da Firestore al login
- ✅ Migrazione automatica da localStorage (solo la prima volta)
- ✅ Fallback a localStorage se Firestore non è disponibile
- ✅ Sincronizzazione bidirezionale

### Autenticazione

#### `hooks/useUserId.ts`

Aggiornato per usare l'UID di Firebase Auth invece di un ID random:

```typescript
const { userId, isAuthReady } = useUserId();
// userId è ora user.uid da Firebase Auth
```

## 🔒 Sicurezza

### Firestore Security Rules (da configurare)

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Conversazioni: solo il proprietario può leggere/scrivere
    match /conversations/{conversationId} {
      allow read, write: if request.auth != null 
                         && request.auth.uid == resource.data.userId;
      allow create: if request.auth != null 
                    && request.auth.uid == request.resource.data.userId;
    }
  }
}
```

**IMPORTANTE:** Devi configurare queste regole nella Firebase Console per proteggere i dati.

## 🚀 Utilizzo

### Salvare una Conversazione

1. L'utente clicca sul pulsante "Salva Chat"
2. Inserisce un nome per la conversazione
3. La conversazione viene salvata su Firestore (e localStorage come backup)

### Caricare le Conversazioni

- Al login, tutte le conversazioni dell'utente vengono caricate automaticamente da Firestore
- Se l'utente aveva conversazioni in localStorage, vengono migrate automaticamente a Firestore

### Eliminare una Conversazione

- L'eliminazione rimuove la conversazione da Firestore e localStorage

## 📦 Collezione Firestore

**Nome collezione:** `conversations`

**Struttura documento:**
```json
{
  "userId": "firebase_user_uid",
  "name": "Nome Conversazione",
  "history": [
    {
      "type": "user",
      "text": "Domanda utente",
      "sources": []
    },
    {
      "type": "assistant",
      "text": "Risposta assistente",
      "sources": ["doc1.pdf", "doc2.pdf"]
    }
  ],
  "createdAt": Timestamp,
  "updatedAt": Timestamp
}
```

## 🔄 Migrazione da localStorage

Al primo login dopo l'aggiornamento:

1. Il sistema controlla se ci sono conversazioni in localStorage
2. Se presenti e Firestore è vuoto, le migra automaticamente
3. Dopo la migrazione, localStorage viene pulito
4. Le conversazioni sono ora accessibili da qualsiasi dispositivo

## ⚡ Fallback Offline

Se Firestore non è disponibile (problemi di rete, configurazione, ecc.):

- Le operazioni vengono eseguite su localStorage
- I dati rimangono locali al dispositivo
- Quando Firestore torna disponibile, i dati possono essere sincronizzati manualmente

## 🧪 Testing

Per testare localmente:

1. Assicurati che `.env.local` contenga le credenziali Firebase corrette
2. Effettua il login nell'app
3. Crea e salva alcune conversazioni
4. Verifica nella Firebase Console > Firestore Database che i documenti siano stati creati
5. Effettua logout e login da un altro browser/dispositivo per verificare la sincronizzazione

## 🐛 Troubleshooting

### "Firebase configuration is missing"
- Verifica che `.env.local` contenga tutte le variabili Firebase necessarie
- Controlla che non ci siano errori nel file `lib/env.config.ts`

### "Failed to save conversation"
- Controlla le Firestore Security Rules
- Verifica che l'utente sia autenticato
- Controlla la console del browser per errori dettagliati

### Le conversazioni non si sincronizzano
- Verifica la connessione internet
- Controlla che Firestore sia abilitato nel progetto Firebase
- Verifica le Security Rules in Firebase Console

## 📚 Risorse

- [Firebase Firestore Documentation](https://firebase.google.com/docs/firestore)
- [Firestore Security Rules](https://firebase.google.com/docs/firestore/security/get-started)
- [Firebase Auth](https://firebase.google.com/docs/auth)
