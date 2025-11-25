# 🔒 Invitation Code Security

## Panoramica

Sistema di registrazione sicuro con codici d'invito obbligatori. Gli utenti non possono accedere al sistema senza un codice valido, **eccetto** per le email presenti nella lista unlimited.

---

## 🚀 Flow di Registrazione

### 1. **Utente Standard** (non nella lista unlimited)

```
Login → InvitationCodeModal → Inserire Codice → Backend Valida → Tier Assegnato
```

**Comportamento:**
- ✅ Modale si apre automaticamente al primo login
- ✅ Campo codice è **obbligatorio** (bottone disabilitato se vuoto)
- ✅ Backend verifica validità del codice:
  - Codice esiste?
  - È già stato usato?
  - È scaduto?
- ✅ Se **tutti i controlli passano** → Tier assegnato (FREE/PRO/UNLIMITED)
- ❌ Se **un controllo fallisce** → Errore mostrato all'utente

**Possibili Errori:**
- `"Invalid invitation code"` - Codice non trovato nel database
- `"Invitation code has already been used"` - Codice già utilizzato
- `"Invitation code has expired"` - Codice scaduto
- `"Invitation code is required for registration"` - Nessun codice fornito

### 2. **Utente Unlimited** (email nella whitelist)

```
Login → Backend Riconosce Email → UNLIMITED Tier Assegnato Automaticamente
```

**Email Unlimited Configurate:**
- `andrea.ragalzi.social@gmail.com` ✅
- `andrea.ragalzi.code@gmail.com` ✅

**Comportamento:**
- ✅ Backend controlla l'email **prima** di richiedere il codice
- ✅ Se email trovata in `app_config/settings.unlimited_emails` → **bypassa validazione codice**
- ✅ Assegna automaticamente tier **UNLIMITED**
- ✅ Modale si chiude con successo

---

## 🔐 Sicurezza Backend

### Endpoint: `POST /auth/register`

**Validazione Multi-Step:**

```python
# Step 1: Verifica Firebase ID Token
decoded_token = auth.verify_id_token(id_token)
user_id = decoded_token["uid"]
user_email = decoded_token.get("email")

# Step 2: Controlla Lista Unlimited
unlimited_emails = await get_unlimited_emails()
if user_email in unlimited_emails:
    # Bypass validazione codice
    assigned_tier = "UNLIMITED"
    auth.set_custom_user_claims(user_id, {"tier": assigned_tier})
    return RegistrationResponse(...)

# Step 3: Richiedi Codice (OBBLIGATORIO se non unlimited)
if not invitation_code:
    raise HTTPException(400, "Invitation code is required for registration")

# Step 4-7: Valida Codice
# - Esiste nel database?
# - Non è stato usato?
# - Non è scaduto?
# - Assegna tier e marca come usato
```

**Firestore Security:**
- ✅ Codici d'invito in `invitation_codes` collection
- ✅ Lista unlimited in `app_config/settings.unlimited_emails`
- ✅ Cache della lista unlimited (riduce letture Firestore)

---

## 🎨 Sicurezza Frontend

### InvitationCodeModal (Modifiche Applicate)

**❌ Rimosso:**
- Bottone "Skip" (permetteva bypass non autorizzato)
- Prop `allowSkip` (non più necessario)

**✅ Implementato:**
- Campo codice **obbligatorio** (bottone disabilitato se vuoto)
- Validazione client-side (trim, uppercase)
- Gestione errori robusta (legge `detail` o `message` dal backend)
- Modale non può essere chiusa senza completare la registrazione

### Codice Chiave:

```tsx
// Bottone disabilitato se codice vuoto
<button
  type="submit"
  disabled={isRegistering || !code.trim()}
  className="..."
>
  Activate Account
</button>

// Nessun bottone "Skip"
// ✅ Tutti gli utenti devono inserire un codice
// ✅ Backend decide se accettarlo o bypassarlo (unlimited emails)
```

---

## 📊 Tipi di Tier e Limiti

| Tier | Documenti | Conversazioni | Metodo di Accesso |
|------|-----------|---------------|-------------------|
| **FREE** | 5 | 10 | Codice: `FREE2024` |
| **PRO** | 50 | 100 | Codice: `PRO2024` |
| **UNLIMITED** | ∞ | ∞ | Email whitelist o codice: `UNLIMITED2024` |

---

## 🧪 Testing

### Test Case 1: Utente Standard senza Codice
```
✅ Modale si apre
✅ Campo codice vuoto
✅ Bottone "Activate Account" disabilitato
✅ Utente NON può procedere
```

### Test Case 2: Utente Standard con Codice Invalido
```
✅ Modale si apre
✅ Inserisce "INVALID123"
✅ Clicca "Activate Account"
❌ Backend restituisce: "Invalid invitation code"
✅ Errore mostrato nella modale (box rosso)
```

### Test Case 3: Utente Standard con Codice Valido
```
✅ Modale si apre
✅ Inserisce "PRO2024"
✅ Clicca "Activate Account"
✅ Backend valida codice → Assegna tier PRO
✅ Modale si chiude
✅ TierBadge mostra "PRO" ⚡
```

### Test Case 4: Utente Unlimited (andrea.ragalzi.social@gmail.com)
```
✅ Modale si apre
✅ Backend riconosce email automaticamente
✅ Assegna tier UNLIMITED (senza validare codice)
✅ Modale si chiude
✅ TierBadge mostra "UNLIMITED" 👑
```

### Test Case 5: Codice Già Usato
```
✅ Inserisce "PRO2024" (già usato da altro utente)
❌ Backend: "Invitation code has already been used"
✅ Errore mostrato nella modale
```

### Test Case 6: Codice Scaduto
```
✅ Inserisce "EXPIRED2023"
❌ Backend: "Invitation code has expired"
✅ Errore mostrato nella modale
```

---

## 🔧 Configurazione

### Aggiungere Email alla Lista Unlimited

1. **Via Firebase Console:**
   ```
   Firestore → app_config → settings → unlimited_emails (array)
   ```

2. **Via Python Script:**
   ```python
   from firebase_admin import firestore
   
   db = firestore.client()
   settings_ref = db.collection("app_config").document("settings")
   settings_ref.update({
       "unlimited_emails": firestore.ArrayUnion(["new-email@example.com"])
   })
   ```

3. **Cache Invalidation:**
   - Backend usa cache globale `_unlimited_emails_cache`
   - Per forzare refresh: **riavvia backend** (cache viene ripopolata)

### Creare Nuovo Codice d'Invito

```python
from firebase_admin import firestore
from datetime import datetime, timedelta

db = firestore.client()
codes_ref = db.collection("invitation_codes")

codes_ref.document("NEWCODE2024").set({
    "tier": "PRO",  # FREE, PRO, o UNLIMITED
    "is_used": False,
    "expires_at": datetime.now() + timedelta(days=90),
    "created_at": firestore.SERVER_TIMESTAMP
})
```

---

## 🛡️ Best Practices

1. ✅ **Mai esporre codici d'invito pubblicamente**
2. ✅ **Limitare durata dei codici** (30-365 giorni)
3. ✅ **Monitorare uso dei codici** (campo `used_by_user_id`)
4. ✅ **Creare codici single-use** (`is_used: false`)
5. ✅ **Email unlimited solo per admin/staff**
6. ✅ **Logging completo di tutte le registrazioni**
7. ✅ **Firestore Security Rules** per proteggere `invitation_codes` collection:

```javascript
// firestore.rules
match /invitation_codes/{codeId} {
  // Nessuno può leggere/scrivere direttamente
  // Solo backend può accedere (via Admin SDK)
  allow read, write: if false;
}

match /app_config/settings {
  // Solo backend può leggere/scrivere
  allow read, write: if false;
}
```

---

## 📝 Note Importanti

- **Backend Lazy Initialization:** Firestore client inizializzato solo quando necessario (evita errori import-time)
- **Frontend Error Handling:** Gestisce sia `detail` (FastAPI) che `message` (fallback)
- **Token Refresh:** Dopo registrazione, frontend forza refresh con `getIdToken(true)` per ottenere nuovi Custom Claims
- **UI/UX:** Modale non può essere chiusa finché registrazione non è completata (previene stato inconsistente)

---

## 🚨 Troubleshooting

### "Invitation code is required for registration"
- **Causa:** Utente non nella lista unlimited + nessun codice fornito
- **Soluzione:** Inserire codice valido o aggiungere email a unlimited_emails

### "Invalid invitation code"
- **Causa:** Codice non esiste in Firestore
- **Soluzione:** Verificare ortografia o contattare support

### "Invitation code has already been used"
- **Causa:** Codice single-use già utilizzato da altro utente
- **Soluzione:** Richiedere nuovo codice a support

### "Invitation code has expired"
- **Causa:** Data di scadenza superata
- **Soluzione:** Richiedere nuovo codice a support

### Backend non riconosce email unlimited
- **Causa:** Cache non aggiornata o typo in email
- **Soluzione:** 
  1. Verificare email in `app_config/settings.unlimited_emails`
  2. Riavviare backend per invalidare cache
  3. Controllare logs: `"✅ Loaded N unlimited emails from Firestore"`

---

## 📧 Supporto

Per problemi o richieste di codici d'invito:
- **Email:** andrea.ragalzi.code@gmail.com
- **Logs Backend:** `backend/logs/app.log`
- **Firebase Console:** `console.firebase.google.com`
