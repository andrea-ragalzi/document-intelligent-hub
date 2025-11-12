# Configurazione Firestore Security Rules

## 📋 Panoramica

Questo documento spiega come configurare le regole di sicurezza per Firestore nella Firebase Console.

## 🔐 Regole di Sicurezza

Le regole di sicurezza sono definite nel file `firestore.rules` e devono essere applicate manualmente nella Firebase Console.

## 🚀 Deploy delle Regole

### Opzione 1: Firebase Console (Manuale)

1. Vai alla [Firebase Console](https://console.firebase.google.com/)
2. Seleziona il tuo progetto **intelligent-document-hub-a16c1**
3. Nel menu laterale, vai a **Firestore Database**
4. Clicca sulla tab **Rules** (Regole)
5. Copia e incolla il contenuto del file `firestore.rules`
6. Clicca su **Publish** (Pubblica)

### Opzione 2: Firebase CLI (Automatico)

Se hai installato Firebase CLI:

```bash
# Installa Firebase CLI se non l'hai già fatto
npm install -g firebase-tools

# Login a Firebase
firebase login

# Inizializza Firebase nel progetto (solo la prima volta)
firebase init firestore
# Seleziona il progetto esistente
# Usa il file firestore.rules quando richiesto

# Deploy delle regole
firebase deploy --only firestore:rules
```

## 📝 Spiegazione delle Regole

```javascript
// Conversazioni: solo il proprietario può accedere
match /conversations/{conversationId} {
  // ✅ Lettura: solo se userId nel documento corrisponde all'utente autenticato
  allow read: if request.auth != null 
              && request.auth.uid == resource.data.userId;
  
  // ✅ Modifica/Cancellazione: solo il proprietario
  allow update, delete: if request.auth != null 
                        && request.auth.uid == resource.data.userId;
  
  // ✅ Creazione: solo se l'utente sta creando una conversazione per se stesso
  allow create: if request.auth != null 
                && request.auth.uid == request.resource.data.userId;
}
```

### Cosa Proteggono le Regole

1. **Autenticazione Richiesta**: Solo utenti loggati possono accedere
2. **Isolamento Dati**: Ogni utente vede solo le proprie conversazioni
3. **Prevenzione Manipolazione**: Un utente non può creare conversazioni per altri utenti
4. **Sicurezza Default**: Tutte le altre collezioni sono bloccate

## 🧪 Testare le Regole

### Nella Firebase Console

1. Vai su **Firestore Database > Rules**
2. Clicca su **Rules Playground**
3. Prova query di esempio:

```javascript
// Test: Lettura conversazione propria (dovrebbe ALLOW)
// Location: /conversations/conv123
// Auth: uid = "user123"
// Read: resource.data.userId = "user123"

// Test: Lettura conversazione altrui (dovrebbe DENY)
// Location: /conversations/conv456
// Auth: uid = "user123"
// Read: resource.data.userId = "user789"
```

### Nel Browser

Apri la Console del Browser dopo il login e prova:

```javascript
// Dovrebbe funzionare
const myConversations = await getDocs(
  query(collection(db, 'conversations'), 
  where('userId', '==', currentUser.uid))
);

// Dovrebbe fallire (permission denied)
const allConversations = await getDocs(
  collection(db, 'conversations')
);
```

## ⚠️ IMPORTANTE

**NON DIMENTICARE** di applicare queste regole prima di andare in produzione!

Senza le regole corrette:
- ❌ Tutti potrebbero leggere tutte le conversazioni
- ❌ Chiunque potrebbe modificare o eliminare dati altrui
- ❌ I dati sensibili sarebbero esposti

## 🔍 Verifica Configurazione

Dopo aver applicato le regole, verifica che:

1. ✅ Puoi salvare le tue conversazioni
2. ✅ Puoi vedere solo le tue conversazioni
3. ✅ Non puoi vedere conversazioni di altri utenti
4. ✅ Non puoi modificare conversazioni di altri utenti

## 📚 Risorse

- [Firestore Security Rules Documentation](https://firebase.google.com/docs/firestore/security/get-started)
- [Rules Language Reference](https://firebase.google.com/docs/firestore/security/rules-structure)
- [Testing Rules](https://firebase.google.com/docs/firestore/security/test-rules-emulator)
