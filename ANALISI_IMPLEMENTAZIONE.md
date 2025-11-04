# 🍷 Analisi Implementazione Vineinventory Viewer

**Data analisi:** 2025-11-03  
**Status:** Da implementare

---

## 📋 Obiettivo del Progetto

Frontend web **solo lettura** per visualizzare l'inventario vini dell'utente attraverso un link con token temporaneo generato dal bot Telegram.

### Funzionalità Principali
- ✅ Link con token JWT temporaneo generato dal bot
- ✅ Viewer web con tabella inventario completa
- ✅ Barra di ricerca (client-side)
- ✅ Sidebar filtri (Tipologia, Annata, Cantina)
- ✅ Tabella: Nome, Annata, Quantità, Prezzo
- ✅ Paginazione (50 righe/pagina)
- ✅ Download CSV dell'inventario
- ✅ Design pulito: palette granaccia/bianco/nero, no decorazioni

---

## 🏗️ Componenti da Implementare

### 1. **Backend Processor** (`gioia-processor`) - **NUOVO**

#### Endpoint `/api/inventory/snapshot?token=JWT`
- **Funzione:** Restituisce snapshot inventario + facets per filtri
- **Validazione:** Token JWT obbligatorio
- **Response 200:**
  ```json
  {
    "rows": [
      {
        "name": "Brunello di Montalcino",
        "winery": "Biondi Santi",
        "vintage": 2017,
        "qty": 1,
        "price": 49.00,
        "type": "Rosso"
      }
    ],
    "facets": {
      "type": {"Rosso": 150, "Bianco": 84},
      "vintage": {"2017": 23, "2020": 32},
      "winery": {"Biondi Santi": 5, "Gaja": 3}
    },
    "meta": {
      "total_rows": 234,
      "last_update": "2025-11-03T15:32:00Z"
    }
  }
  ```
- **Response 401/410:** Token scaduto/non valido

#### Endpoint `/api/inventory/export.csv?token=JWT`
- **Funzione:** Export CSV inventario
- **Validazione:** Token JWT obbligatorio
- **Response:** `Content-Type: text/csv`
- **Response 401/410:** Token scaduto/non valido

#### Implementazione Tecnica
- Query inventario con aggregazioni per facets (COUNT per tipo, annata, cantina)
- Validazione JWT con `pyjwt`
- Estrazione `telegram_id` e `business_name` dal token payload
- Query database con filtri basati su token

---

### 2. **Bot Telegram** (`telegram-ai-bot`) - **NUOVO**

#### Comando "Vedi tutto" (o `/view`)
- **Trigger:** Messaggio "Vedi tutto" o comando `/view`
- **Funzione:**
  1. Genera token JWT temporaneo con scadenza (es. 24h)
  2. Payload: `{"telegram_id": 123, "business_name": "Nome Locale", "exp": timestamp}`
  3. Risponde con link: `https://viewer.gioia.app/?token=...`

#### Implementazione Tecnica
- Installare `pyjwt` se non presente
- Generare token con secret key condiviso con processor
- Validare che utente abbia onboarding completato e inventario

---

### 3. **Frontend Viewer** - **NUOVO PROGETTO**

#### Struttura File
```
Vineinventory Viewer/
├── index.html          # Markup mockup pulito
├── styles.css          # Tema granaccia/bianco/nero
├── app.js              # Fetch snapshot, filtri, ricerca, CSV, paginazione
├── assets/
│   └── logo.png        # Logo fornito (granaccia)
└── README.md           # Documentazione

```

#### Configurazione (`app.js`)
```javascript
const CONFIG = {
  apiBase: "",                         // se vuoto usa lo stesso dominio del viewer
  endpointSnapshot: "/api/inventory/snapshot",
  endpointCsv: "/api/inventory/export.csv",
  pageSize: 50
};
```

#### Funzionalità Frontend
- Legge token da `?token=...` nella querystring
- Fetch snapshot dal processor
- Popola meta ("234 records • Last updated 5 hours ago")
- Sidebar filtri con facets (Tipologia, Annata, Cantina)
- Tabella con colonne: Nome, Annata, Quantità, Prezzo (€)
- Ricerca istantanea client-side su Nome/Annata/Cantina
- Paginazione 50 righe/pagina
- Pulsante Download CSV → punta a `/api/inventory/export.csv?token=...`
- Gestione errori: se fetch fallisce con 401/410 → banner "Link scaduto o non valido"

#### Design
- Palette: granaccia / bianco / nero
- Typography: Inter (o sistema)
- Logo a sinistra, titolo "Vineinventory"
- Barra ricerca a destra, pulsante Download CSV
- Sidebar "Filters" con sezioni: Tipologia, Annata, Cantina
- Tabella pulita con colonne ordinate
- Nessun elemento decorativo (NO pennellate/NO pallini)
- Responsive: ≤ 980px stack verticale (sidebar sopra, tabella sotto)

---

### 4. **Sistema Token JWT**

#### Generazione (Bot)
- **Libreria:** `pyjwt`
- **Payload:**
  ```python
  {
    "telegram_id": 123456789,
    "business_name": "Nome Locale",
    "iat": int(time.time()),
    "exp": int(time.time()) + 86400  # 24h
  }
  ```
- **Secret:** Variabile ambiente condivisa tra bot e processor
- **Algorithm:** `HS256`

#### Validazione (Processor)
- Verifica signature
- Verifica scadenza (`exp`)
- Estrae `telegram_id` e `business_name`
- Query database basata su questi dati

#### Sicurezza
- Token obbligatorio (`?token=...`)
- Nessun accesso diretto al DB dal frontend: sempre via Processor
- Se chiamata fallisce con 401/410 → non mostrare dati
- (Opzionale) Token single-use con `jti` (JWT ID) per uso una tantum

---

## ✅ Compatibilità con Architettura Attuale

### ✅ **Compatibile**
- Processor è FastAPI → possiamo aggiungere nuovi endpoint facilmente
- Bot ha già accesso a database → può generare token
- Viewer può essere progetto statico separato → deploy indipendente

### 🔧 **Modifiche Necessarie**
- Aggiungere dipendenza `pyjwt` al processor (se non presente)
- Aggiungere dipendenza `pyjwt` al bot (se non presente)
- Configurare CORS nel processor per dominio viewer (se diverso)

---

## 📦 Dipendenze Richieste

### Processor (`gioia-processor`)
- `pyjwt>=2.8.0` - Per validazione token JWT

### Bot (`telegram-ai-bot`)
- `pyjwt>=2.8.0` - Per generazione token JWT

### Viewer (Frontend)
- Nessuna dipendenza esterna (vanilla JS)
- Opzionale: `jwt-decode` per debugging token (non necessario in produzione)

---

## 🔐 Considerazioni Sicurezza

### ✅ **Misure da Implementare**
1. **Token temporanei:** Scadenza configurata (24h suggerito)
2. **Validazione server-side:** Sempre nel processor, mai nel frontend
3. **Nessun accesso diretto DB:** Frontend chiama solo API processor
4. **CORS configurato:** Solo dominio viewer autorizzato (se diverso)
5. **Secret key sicura:** Variabile ambiente, mai hardcoded

### 💡 **Opzionale (Future)**
- Token single-use con `jti` (JWT ID) e tracking nel database
- Rate limiting per endpoint snapshot (es. max 100 richieste/ora per token)
- Logging accessi per audit

---

## 🚀 Deploy

### Processor
- ✅ Endpoint aggiunti all'esistente deploy su Railway/simil
- CORS da configurare se viewer su dominio diverso

### Viewer
- **Opzione 1:** Static hosting (Vercel/Netlify) - **Consigliato**
  - Deploy automatico da git
  - HTTPS incluso
  - CDN globale
- **Opzione 2:** Railway static
  - Stesso provider del processor
- **Opzione 3:** S3 + CloudFront (AWS)

### Bot
- ✅ Nessun cambio deploy necessario
- Solo aggiunta comando handler

---

## ⚠️ Domande Aperte da Risolvere

### 1. **URL Viewer**
- Quale dominio/subdomain usare?
- Esempi: `viewer.gioia.app`, `view.gioia.app`, `inventory.gioia.app`
- **Decisione necessaria prima del deploy**

### 2. **Durata Token**
- Quanto deve restare valido?
- Suggerito: **24 ore** (86400 secondi)
- Alternative: 1h, 12h, 7 giorni
- **Decisione necessaria per implementazione**

### 3. **Logo**
- File `/assets/logo.png` disponibile?
- Formato/risoluzione preferita?
- **Necessario per completare UI**

### 4. **Secret Key JWT**
- Creare nuova variabile ambiente `JWT_SECRET_KEY`?
- Usare secret esistente (se presente)?
- **Necessario per bot e processor**

### 5. **CORS**
- Viewer e processor stesso dominio? (CORS non necessario)
- Domini diversi? (CORS da configurare)
- **Decisione necessaria per configurazione**

### 6. **Mockup Visivo**
- Immagine mockup disponibile per riferimento UI?
- Design specifico sidebar/filtri/tabella?
- **Utile per implementazione precisa**

---

## 📊 Criteri di Accettazione

### UI
- ✅ UI identica al mockup: logo a sinistra, titolo Vineinventory
- ✅ Meta ("234 records • Last updated ...")
- ✅ Barra ricerca a destra, pulsante Download CSV
- ✅ Sidebar "Filters" con sezioni: Tipologia, Annata, Cantina
- ✅ Tabella con colonne: Nome, Annata, Quantità, Prezzo (€)
- ✅ Nessun elemento decorativo (NO pennellate/NO pallini)

### Funzionalità
- ✅ Ricerca istantanea (client-side) su Nome/Annata/Cantina
- ✅ Paginazione (50 righe/pagina)
- ✅ CSV scaricabile quando token valido
- ✅ Errore chiaro se token scaduto (401/410)

### Responsive
- ✅ ≤ 980px: stack verticale (sidebar sopra, tabella sotto)

---

## 🎯 Vantaggi Implementazione

1. **Condivisione Inventario**
   - Utente può condividere link temporaneo con altri (fornitori, clienti)
   - Nessun login necessario
   - Accesso controllato tramite scadenza token

2. **Interfaccia Web Migliore**
   - Visualizzazione tabellare più comoda rispetto a chat bot
   - Filtri e ricerca istantanea
   - Export CSV diretto

3. **Scalabilità**
   - Viewer statico → deploy CDN → alta performance
   - Processor gestisce solo API calls → carico controllato

4. **Esperienza Utente**
   - Link facile da condividere
   - Interfaccia professionale
   - Funzionalità complete (filtri, ricerca, export)

---

## 📝 Prossimi Passi Implementazione

### Fase 1: Backend (Processor)
1. ✅ Installare `pyjwt` in `requirements.txt`
2. ✅ Aggiungere endpoint `/api/inventory/snapshot?token=JWT`
3. ✅ Aggiungere endpoint `/api/inventory/export.csv?token=JWT`
4. ✅ Implementare validazione JWT token
5. ✅ Query inventario con aggregazioni facets
6. ✅ Export CSV

### Fase 2: Bot
1. ✅ Installare `pyjwt` in `requirements.txt`
2. ✅ Aggiungere handler comando "Vedi tutto" o `/view`
3. ✅ Implementare generazione token JWT
4. ✅ Rispondere con link viewer

### Fase 3: Frontend Viewer
1. ✅ Creare struttura progetto (`index.html`, `styles.css`, `app.js`)
2. ✅ Implementare UI seguendo mockup
3. ✅ Integrare fetch API snapshot
4. ✅ Implementare filtri/ricerca/paginazione
5. ✅ Aggiungere download CSV
6. ✅ Gestione errori token scaduto

### Fase 4: Testing & Deploy
1. ✅ Test locale con token fittizio
2. ✅ Test integrazione bot → processor → viewer
3. ✅ Deploy viewer su hosting statico
4. ✅ Configurare CORS se necessario
5. ✅ Test end-to-end

---

## 💡 Note Tecniche

### Mapping Campi Database → API Response
- `name` → `name`
- `producer` → `winery`
- `vintage` → `vintage`
- `quantity` → `qty`
- `selling_price` → `price`
- `wine_type` → `type`

### Facets Aggregazioni
- `type`: COUNT per ogni `wine_type`
- `vintage`: COUNT per ogni `vintage`
- `winery`: COUNT per ogni `producer`

### Query Ottimizzazione
- Usare `SELECT COUNT(*)` per facets (non caricare tutte le righe)
- Paginazione lato server opzionale (per dataset molto grandi)
- Index su colonne usate per filtri (`wine_type`, `vintage`, `producer`)

---

## ✅ Raccomandazione Finale

**Implementabile e molto utile** per l'ecosistema Gio.ia!

Il progetto è:
- ✅ Tecnicamente fattibile
- ✅ Compatibile con architettura esistente
- ✅ Aggiunge valore significativo (condivisione inventario)
- ✅ Design pulito e professionale
- ✅ Sicuro (token temporanei, validazione server)

**Prossimo step:** Risolvere domande aperte (dominio viewer, durata token, logo, secret key) e iniziare implementazione Fase 1.

---

**Versione:** 1.0  
**Data:** 2025-11-03  
**Status:** Pronto per implementazione (pending decisioni domande aperte)

