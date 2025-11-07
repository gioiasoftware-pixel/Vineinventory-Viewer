# 📊 Studio Completo: Vineinventory Viewer

## 🎯 Obiettivo

Il viewer è un frontend web **solo lettura** per visualizzare l'inventario vini dell'utente attraverso un link con token temporaneo generato dal bot Telegram. Permette di:
- Visualizzare inventario completo in tabella
- Filtrare per Tipologia, Annata, Cantina
- Cercare vini per nome/annata/cantina
- Scaricare CSV dell'inventario
- Vedere scorte critiche

## 🏗️ Architettura Attuale

### Componenti

1. **Frontend (Vineinventory Viewer)**
   - `index.html` - Markup HTML
   - `styles.css` - Stili CSS (palette granaccia/bianco/nero)
   - `app.js` - Logica JavaScript (fetch, filtri, ricerca, CSV)
   - `server.py` - Server HTTP semplice per servire file statici
   - `api_generate.py` - Generazione HTML con dati embedded

2. **Backend Processor (gioia-processor)**
   - `api/routers/snapshot.py` - Endpoint API per snapshot inventario
   - `viewer_generator.py` - Generatore HTML con dati embedded
   - `jwt_utils.py` - Validazione token JWT

3. **Bot Telegram (telegram-ai-bot)**
   - `viewer_utils.py` - Generazione token JWT
   - `bot.py` - Comando `/view` per generare link

## 🔄 Flow Completo Attuale

### Flow 1: Utente Richiede Viewer (Comando `/view`)

```
1. Utente → Bot: "/view"
   ↓
2. Bot verifica utente e inventario
   ↓
3. Bot genera token JWT (valido 1 ora)
   ↓
4. Bot avvia 2 job asincroni:
   a. Job 1: Processor → POST /api/viewer/prepare-data
      - Estrae dati inventario dal DB
      - Salva in cache in-memory
   b. Job 2: Viewer → POST /api/generate
      - Genera HTML con dati embedded
      - Salva in cache in-memory
      - Genera view_id
      - Chiama callback bot: POST /api/viewer/link-ready
   ↓
5. Bot attende callback (timeout 60s)
   ↓
6. Bot riceve viewer_url e invia all'utente
   ↓
7. Utente clicca link → Viewer carica dati
```

### Flow 2: Viewer Carica Dati (Token JWT)

```
1. Utente apre: https://viewer.railway.app/?token=JWT_TOKEN
   ↓
2. Viewer (app.js) legge token da URL
   ↓
3. Viewer chiama: GET /api/inventory/snapshot?token=JWT_TOKEN
   ↓
4. Processor valida token JWT
   ↓
5. Processor estrae dati inventario dal DB
   ↓
6. Processor restituisce JSON:
   {
     "rows": [...],
     "facets": {...},
     "meta": {...}
   }
   ↓
7. Viewer renderizza tabella, filtri, ricerca
   ↓
8. Utente può:
   - Filtrare per Tipologia/Annata/Cantina
   - Cercare vini
   - Scaricare CSV
```

### Flow 3: Download CSV

```
1. Utente clicca "Download CSV"
   ↓
2. Viewer chiama: GET /api/inventory/export.csv?token=JWT_TOKEN
   ↓
3. Processor valida token JWT
   ↓
4. Processor estrae dati inventario dal DB
   ↓
5. Processor genera CSV e lo restituisce
   ↓
6. Browser scarica file CSV
```

## 📁 File e Responsabilità

### Frontend (Vineinventory Viewer/)

| File | Responsabilità | Status |
|------|---------------|--------|
| `index.html` | Markup HTML base | ✅ Completo |
| `styles.css` | Stili CSS (palette granaccia) | ✅ Completo |
| `app.js` | Logica JavaScript (fetch, filtri, ricerca, CSV) | ✅ Completo |
| `server.py` | Server HTTP per file statici + endpoint `/api/generate` | ✅ Completo |
| `api_generate.py` | Generazione HTML con dati embedded | ✅ Completo |
| `README.md` | Documentazione | ✅ Completo |

### Backend Processor (gioia-processor/)

| File | Responsabilità | Status |
|------|---------------|--------|
| `api/routers/snapshot.py` | Endpoint `/api/inventory/snapshot` e `/api/inventory/export.csv` | ✅ Completo |
| `viewer_generator.py` | Generatore HTML con dati embedded, cache in-memory | ✅ Completo |
| `jwt_utils.py` | Validazione token JWT | ✅ Completo |

### Bot Telegram (telegram-ai-bot/)

| File | Responsabilità | Status |
|------|---------------|--------|
| `viewer_utils.py` | Generazione token JWT, URL viewer | ✅ Completo |
| `bot.py` | Comando `/view`, gestione callback viewer | ✅ Completo |

## 🔌 API Endpoints

### Processor (gioia-processor)

#### 1. `GET /api/inventory/snapshot?token=JWT`
- **Scopo**: Snapshot inventario con facets per filtri
- **Auth**: Token JWT in query parameter
- **Response**:
  ```json
  {
    "rows": [
      {
        "name": "Brunello di Montalcino",
        "winery": "Biondi Santi",
        "vintage": 2017,
        "qty": 1,
        "price": 49.00,
        "type": "Rosso",
        "critical": true
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
- **Status**: ✅ Implementato

#### 2. `GET /api/inventory/export.csv?token=JWT`
- **Scopo**: Export CSV inventario
- **Auth**: Token JWT in query parameter
- **Response**: File CSV (`Content-Type: text/csv`)
- **Status**: ✅ Implementato

#### 3. `POST /api/viewer/prepare-data`
- **Scopo**: Prepara dati inventario per viewer (salva in cache)
- **Input**: `telegram_id`, `business_name`, `correlation_id`
- **Response**: `{status: "completed", ...}`
- **Status**: ✅ Implementato (ma non usato nel flow attuale)

#### 4. `GET /api/viewer/data?telegram_id=...`
- **Scopo**: Recupera dati inventario dalla cache
- **Response**: Stesso formato di `/api/inventory/snapshot`
- **Status**: ✅ Implementato (ma non usato nel flow attuale)

#### 5. `GET /api/viewer/{view_id}`
- **Scopo**: Serve HTML viewer generato dalla cache
- **Response**: HTML completo con dati embedded
- **Status**: ✅ Implementato (ma non usato nel flow attuale)

### Viewer (Vineinventory Viewer)

#### 1. `POST /api/generate`
- **Scopo**: Genera HTML viewer con dati embedded
- **Input**: `telegram_id`, `business_name`, `correlation_id`
- **Response**: `{view_id: "...", viewer_url: "..."}`
- **Status**: ✅ Implementato (ma non usato nel flow attuale)

### Bot Telegram

#### 1. `POST /api/viewer/link-ready`
- **Scopo**: Callback per notificare bot che link è pronto
- **Input**: `telegram_id`, `viewer_url`, `correlation_id`
- **Response**: `{status: "ok"}`
- **Status**: ✅ Implementato

## ⚙️ Configurazione

### Variabili Ambiente

#### Processor (gioia-processor)
- `JWT_SECRET_KEY` - Secret key per JWT (condivisa con bot)
- `DATABASE_URL` - URL database PostgreSQL

#### Bot (telegram-ai-bot)
- `JWT_SECRET_KEY` - Secret key per JWT (condivisa con processor)
- `VIEWER_URL` - URL viewer (default: `https://vineinventory-viewer-production.up.railway.app`)
- `PROCESSOR_URL` - URL processor (default: `https://gioia-processor-production.up.railway.app`)

#### Viewer (Vineinventory Viewer)
- `API_BASE` - URL processor per chiamate API (default: `https://gioia-processor-production.up.railway.app`)
- `PORT` - Porta server HTTP (default: `8080`)

## 🔍 Stato Attuale

### ✅ Funzionalità Implementate

1. **Frontend Completo**
   - ✅ HTML/CSS/JS completo
   - ✅ Filtri sidebar (Tipologia, Annata, Cantina)
   - ✅ Ricerca istantanea (debounced 300ms)
   - ✅ Paginazione (50 righe/pagina)
   - ✅ Download CSV
   - ✅ Responsive design
   - ✅ Gestione errori (token scaduto/non valido)

2. **Backend Processor**
   - ✅ Endpoint `/api/inventory/snapshot` con token JWT
   - ✅ Endpoint `/api/inventory/export.csv` con token JWT
   - ✅ Validazione token JWT
   - ✅ Estrazione dati inventario dal DB
   - ✅ Calcolo facets per filtri
   - ✅ Generazione CSV

3. **Bot Telegram**
   - ✅ Comando `/view` per generare link
   - ✅ Generazione token JWT
   - ✅ Gestione callback viewer

### ⚠️ Problemi / Limitazioni Attuali

1. **Flow Complesso e Non Utilizzato**
   - Il flow con `POST /api/viewer/prepare-data` e `POST /api/generate` **non è utilizzato**
   - Il bot usa direttamente token JWT invece di view_id
   - La cache in-memory non è utilizzata

2. **Mancanza Debug CSV Post-Processor**
   - **NON c'è modo di vedere CSV post-processor** (dati salvati nel DB)
   - **NON c'è modo di confrontare CSV originale vs post-processor**
   - Il viewer mostra solo dati dal DB, non il CSV originale

3. **Mancanza Confronto Dati**
   - Non c'è modo di vedere:
     - CSV originale caricato
     - CSV post-processor (dati salvati nel DB)
     - Differenze tra i due

4. **Cache In-Memory Non Persistente**
   - Cache in-memory si perde al riavvio
   - Non c'è persistenza tra riavvii

5. **Token JWT Scadenza Fissa**
   - Token valido solo 1 ora
   - Non configurabile

## 🎯 Proposta: Aggiungere Debug CSV Post-Processor

### Obiettivo

Permettere all'utente di:
1. **Vedere CSV post-processor** (dati salvati nel DB) direttamente nel viewer
2. **Confrontare CSV originale vs post-processor** per debug
3. **Scaricare CSV post-processor** per analisi

### Soluzione Proposta

#### Opzione 1: Aggiungere Tab "CSV Post-Processor" nel Viewer

**Modifiche**:
1. Aggiungere tab nel viewer:
   - Tab 1: "Inventario" (attuale)
   - Tab 2: "CSV Post-Processor" (nuovo)
   - Tab 3: "Confronto" (nuovo, opzionale)

2. Endpoint nuovo: `GET /api/inventory/post-processor-csv?token=JWT`
   - Estrae dati dal DB (stesso di snapshot)
   - Genera CSV con tutti i campi
   - Restituisce CSV

3. Endpoint nuovo: `GET /api/inventory/original-csv?token=JWT&job_id=...`
   - Recupera CSV originale dal job
   - Restituisce CSV originale

**Vantaggi**:
- ✅ Permette confronto diretto
- ✅ Non richiede modifiche al flow esistente
- ✅ Facile da implementare

**Svantaggi**:
- ⚠️ Richiede storage CSV originale (attualmente non salvato)

#### Opzione 2: Aggiungere Sezione "Debug" nel Viewer

**Modifiche**:
1. Aggiungere sezione "Debug" nel viewer (solo per admin o con flag)
2. Mostrare:
   - CSV post-processor (dati DB)
   - CSV originale (se disponibile)
   - Statistiche confronto

**Vantaggi**:
- ✅ Non modifica UI principale
- ✅ Accessibile solo quando necessario

**Svantaggi**:
- ⚠️ Richiede storage CSV originale

#### Opzione 3: Endpoint Dedicato per Debug

**Modifiche**:
1. Nuovo endpoint: `GET /api/debug/csv-comparison?token=JWT&job_id=...`
2. Restituisce:
   - CSV originale
   - CSV post-processor
   - Differenze (JSON)

**Vantaggi**:
- ✅ Separato dal viewer principale
- ✅ Può essere chiamato da tool esterni

**Svantaggi**:
- ⚠️ Richiede storage CSV originale

### Raccomandazione

**Opzione 1 + Storage CSV Originale**

1. **Salvare CSV originale** quando viene caricato:
   - Salvare in tabella `processing_jobs` (campo `original_file_content` o tabella separata)
   - O salvare in storage esterno (S3, etc.)

2. **Aggiungere tab "CSV Post-Processor"** nel viewer:
   - Mostra CSV generato dai dati DB
   - Permette download

3. **Aggiungere tab "Confronto"** (opzionale):
   - Mostra CSV originale vs post-processor
   - Evidenzia differenze

## 📋 Checklist Implementazione

### Fase 1: Storage CSV Originale
- [ ] Aggiungere campo `original_file_content` in `processing_jobs` (o tabella separata)
- [ ] Salvare CSV originale quando viene caricato
- [ ] Endpoint per recuperare CSV originale: `GET /api/inventory/original-csv?token=JWT&job_id=...`

### Fase 2: Tab CSV Post-Processor nel Viewer
- [ ] Aggiungere tab "CSV Post-Processor" in `index.html`
- [ ] Modificare `app.js` per gestire tab
- [ ] Endpoint già esistente: `GET /api/inventory/export.csv?token=JWT` (riutilizzare)

### Fase 3: Tab Confronto (Opzionale)
- [ ] Aggiungere tab "Confronto" in `index.html`
- [ ] Logica JavaScript per confronto CSV
- [ ] Evidenziazione differenze

### Fase 4: Testing
- [ ] Test caricamento CSV originale
- [ ] Test visualizzazione CSV post-processor
- [ ] Test confronto CSV
- [ ] Test download CSV

## 🔧 Modifiche Necessarie

### 1. Database (gioia-processor)

**Aggiungere campo per CSV originale**:
```sql
ALTER TABLE processing_jobs 
ADD COLUMN original_file_content BYTEA;
```

O creare tabella separata:
```sql
CREATE TABLE original_files (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(50) UNIQUE NOT NULL,
    file_content BYTEA NOT NULL,
    file_name VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Processor (gioia-processor)

**Modificare `api/routers/ingest.py`**:
- Salvare CSV originale quando viene caricato
- Endpoint nuovo: `GET /api/inventory/original-csv?token=JWT&job_id=...`

### 3. Viewer (Vineinventory Viewer)

**Modificare `index.html`**:
- Aggiungere tab "CSV Post-Processor"
- Aggiungere tab "Confronto" (opzionale)

**Modificare `app.js`**:
- Gestione tab
- Logica confronto CSV (opzionale)

## 📊 Flow Proposto (Con Debug CSV)

```
1. Utente carica CSV → Processor salva CSV originale
   ↓
2. Processor elabora e salva nel DB
   ↓
3. Utente → Bot: "/view"
   ↓
4. Bot genera token JWT e link viewer
   ↓
5. Utente apre viewer
   ↓
6. Viewer mostra:
   - Tab "Inventario" (attuale)
   - Tab "CSV Post-Processor" (nuovo)
   - Tab "Confronto" (opzionale)
   ↓
7. Utente può:
   - Vedere inventario (attuale)
   - Vedere/scaricare CSV post-processor
   - Confrontare CSV originale vs post-processor
```

## 🎯 Prossimi Passi

1. **Decidere approccio**: Opzione 1, 2, o 3?
2. **Implementare storage CSV originale**
3. **Aggiungere tab nel viewer**
4. **Test end-to-end**

---

**Versione**: 1.0  
**Data**: 2025-11-06  
**Status**: Studio completato, in attesa di decisione implementazione

