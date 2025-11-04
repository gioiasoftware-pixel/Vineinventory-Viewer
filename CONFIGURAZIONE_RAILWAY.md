# 🔧 Configurazione Variabili Ambiente Railway

**IMPORTANTE:** Configurare queste variabili ambiente **PRIMA** di fare commit e push!

## 📋 Variabili da Configurare

### 1. **Processor** (`gioia-processor`)

#### Dashboard Railway:
👉 https://railway.app/project/[PROJECT_ID]/service/[PROCESSOR_SERVICE_ID]/variables

#### Variabile da aggiungere:
```
JWT_SECRET_KEY = <genera-una-chiave-segreta-sicura>
```

**Esempio di chiave sicura:**
```
openssl rand -hex 32
```
Oppure usa un generatore online di chiavi segrete (minimo 32 caratteri).

**NOTA:** La stessa chiave deve essere configurata anche nel bot!

---

### 2. **Bot Telegram** (`telegram-ai-bot`)

#### Dashboard Railway:
👉 https://railway.app/project/[PROJECT_ID]/service/[BOT_SERVICE_ID]/variables

#### Variabili da aggiungere:

**a) JWT Secret Key (stessa del processor):**
```
JWT_SECRET_KEY = <stessa-chiave-del-processor>
```

**b) Viewer URL (URL del viewer su Railway):**
```
VIEWER_URL = https://vineinventory-viewer.railway.app
```

**NOTA:** 
- `JWT_SECRET_KEY` deve essere **IDENTICA** a quella del processor
- `VIEWER_URL` sarà disponibile dopo il deploy del viewer. Puoi usare un placeholder temporaneo e aggiornarlo dopo.

---

### 3. **Viewer** (`Vineinventory Viewer`)

#### Dashboard Railway:
👉 https://railway.app/project/[PROJECT_ID]/service/[VIEWER_SERVICE_ID]/variables

#### Variabili da aggiungere (opzionali):

Il viewer è statico, quindi non necessita di variabili ambiente specifiche. Railway imposterà automaticamente:
- `PORT` (automatico)

**Se viewer e processor sono su domini diversi**, configura in `app.js`:
```javascript
const CONFIG = {
    apiBase: "https://gioia-processor.railway.app",  // URL processor
    endpointSnapshot: "/api/inventory/snapshot",
    endpointCsv: "/api/inventory/export.csv",
    pageSize: 50
};
```

---

## 🔐 Generazione Chiave Segreta JWT

### Opzione 1: Terminale (Linux/Mac)
```bash
openssl rand -hex 32
```

### Opzione 2: Python
```python
import secrets
print(secrets.token_hex(32))
```

### Opzione 3: Online Generator
Usa un generatore online di chiavi segrete (es. https://randomkeygen.com/)

**Esempio di chiave generata:**
```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
```

---

## ✅ Checklist Pre-Commit

- [ ] ✅ Generata chiave segreta JWT (`JWT_SECRET_KEY`)
- [ ] ✅ Configurata `JWT_SECRET_KEY` nel **Processor** su Railway
- [ ] ✅ Configurata `JWT_SECRET_KEY` nel **Bot** su Railway (stessa chiave!)
- [ ] ✅ Configurata `VIEWER_URL` nel **Bot** su Railway
- [ ] ✅ Verificato che `VIEWER_URL` sia corretto (dopo deploy viewer)
- [ ] ✅ Testato endpoint `/api/inventory/snapshot` con token valido
- [ ] ✅ Testato comando `/view` nel bot

---

## 🧪 Test Post-Deploy

### 1. Test Processor Endpoint
```bash
# Genera token temporaneo (usa Python o script)
curl "https://gioia-processor.railway.app/api/inventory/snapshot?token=YOUR_JWT_TOKEN"
```

### 2. Test Bot Comando
Nel bot Telegram:
```
/view
```

Dovrebbe restituire un link con token JWT valido.

### 3. Test Viewer
Apri il link generato dal bot nel browser. Dovrebbe:
- ✅ Caricare l'inventario
- ✅ Mostrare filtri funzionanti
- ✅ Permettere download CSV

---

## 🚨 Troubleshooting

### "Token scaduto o non valido"
- Verifica che `JWT_SECRET_KEY` sia **identica** in processor e bot
- Verifica che il token non sia scaduto (validità 1 ora)

### "Utente non trovato"
- Verifica che l'utente abbia completato onboarding
- Verifica che `telegram_id` nel token corrisponda all'utente nel database

### "CORS error" nel viewer
- Verifica che il processor abbia CORS configurato correttamente
- Verifica che `apiBase` in `app.js` sia corretto

---

## 📝 Note Finali

- **JWT_SECRET_KEY**: Chiave critica per sicurezza. Mai committare nel codice!
- **VIEWER_URL**: Può essere aggiornato dopo il deploy del viewer
- **Token expiry**: 1 ora (configurabile in `viewer_utils.py`)

---

**Data:** 2025-11-04  
**Versione:** 1.0

