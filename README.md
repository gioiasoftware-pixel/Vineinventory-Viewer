# 🍷 Vineinventory Viewer

Frontend web **solo lettura** per visualizzare l'inventario vini dell'utente attraverso un link con token temporaneo generato dal bot Telegram.

## 📁 Struttura Progetto

```
Vineinventory Viewer/
├── index.html          # Markup principale
├── styles.css          # Stili (palette granaccia/bianco/nero)
├── app.js              # Logica JavaScript (fetch, filtri, ricerca, CSV)
├── assets/
│   └── logo.png        # Logo Gio.ia
└── README.md           # Questo file
```

## 🎨 Design

- **Palette colori:** Granaccia (#9a182e), Bianco, Nero
- **Typography:** Inter (Google Fonts)
- **Layout:** Single page con sidebar filtri a sinistra e tabella a destra
- **Responsive:** ≤ 980px stack verticale (sidebar sopra, tabella sotto)
- **Nessun elemento decorativo** (no pennellate/pallini)

## 🚀 Test Locale

### Con server statico

```bash
# Opzione 1: Python
python -m http.server 8080

# Opzione 2: Node.js serve
npx serve .

# Opzione 3: PHP
php -S localhost:8080
```

Poi apri nel browser:
- **Con token mock:** `http://localhost:8080/?token=FAKE`
- **Con token reale:** `http://localhost:8080/?token=<JWT_TOKEN>`

### Token FAKE

Quando il token è `FAKE` o `fake`, l'app carica dati mock per testare l'interfaccia senza backend.

## 📋 Funzionalità

### ✅ Implementato

- ✅ Lettura token da URL (`?token=...`)
- ✅ Fetch snapshot da API (o mock se token=FAKE)
- ✅ Visualizzazione meta ("234 records • Last updated...")
- ✅ Sidebar filtri (Tipologia, Annata, Cantina) con conteggi
- ✅ Filtri espandibili/collassabili
- ✅ Tabella dati (Nome, Annata, Quantità, Prezzo, Scorta critica)
- ✅ Ricerca istantanea (debounced 300ms) su Nome/Annata/Cantina
- ✅ Paginazione (50 righe/pagina)
- ✅ Download CSV
- ✅ Gestione errori (token scaduto/non valido)
- ✅ Responsive design

### ⏳ Da Implementare (quando collegato al backend)

- 🔗 Collegamento endpoint processor `/api/inventory/snapshot`
- 🔗 Collegamento endpoint processor `/api/inventory/export.csv`
- 🔗 Validazione token JWT reale

## ⚙️ Configurazione

In `app.js`, oggetto `CONFIG`:

```javascript
const CONFIG = {
    apiBase: "",                         // se vuoto usa lo stesso dominio del viewer
    endpointSnapshot: "/api/inventory/snapshot",
    endpointCsv: "/api/inventory/export.csv",
    pageSize: 50
};
```

### Se viewer e processor su domini diversi:

Modificare `apiBase` con l'URL completo del processor:
```javascript
apiBase: "https://processor.gioia.app"
```

## 🔌 API Richieste (dal Processor)

### GET `/api/inventory/snapshot?token=JWT`

**Response 200:**
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

**Response 401/410:** Token scaduto/non valido

### GET `/api/inventory/export.csv?token=JWT`

**Response:** CSV file (`Content-Type: text/csv`)

**Response 401/410:** Token scaduto/non valido

## 🎯 Prossimi Passi

1. ✅ Frontend completato (questo progetto)
2. ⏳ Backend processor: aggiungere endpoint `/api/inventory/snapshot` e `/api/inventory/export.csv`
3. ⏳ Bot Telegram: aggiungere comando "Vedi tutto" che genera token JWT e link
4. ⏳ Test end-to-end
5. ⏳ Deploy viewer su hosting statico (Vercel/Netlify/Railway)

## 📝 Note

- Il viewer è completamente statico (HTML/CSS/JS vanilla)
- Nessuna dipendenza esterna (tranne Google Fonts per Inter)
- Compatibile con tutti i browser moderni
- SEO-friendly (single page application)

---

**Versione:** 1.0  
**Data:** 2025-11-03  
**Status:** Frontend completato, in attesa di integrazione backend




Frontend web **solo lettura** per visualizzare l'inventario vini dell'utente attraverso un link con token temporaneo generato dal bot Telegram.

## 📁 Struttura Progetto

```
Vineinventory Viewer/
├── index.html          # Markup principale
├── styles.css          # Stili (palette granaccia/bianco/nero)
├── app.js              # Logica JavaScript (fetch, filtri, ricerca, CSV)
├── assets/
│   └── logo.png        # Logo Gio.ia
└── README.md           # Questo file
```

## 🎨 Design

- **Palette colori:** Granaccia (#9a182e), Bianco, Nero
- **Typography:** Inter (Google Fonts)
- **Layout:** Single page con sidebar filtri a sinistra e tabella a destra
- **Responsive:** ≤ 980px stack verticale (sidebar sopra, tabella sotto)
- **Nessun elemento decorativo** (no pennellate/pallini)

## 🚀 Test Locale

### Con server statico

```bash
# Opzione 1: Python
python -m http.server 8080

# Opzione 2: Node.js serve
npx serve .

# Opzione 3: PHP
php -S localhost:8080
```

Poi apri nel browser:
- **Con token mock:** `http://localhost:8080/?token=FAKE`
- **Con token reale:** `http://localhost:8080/?token=<JWT_TOKEN>`

### Token FAKE

Quando il token è `FAKE` o `fake`, l'app carica dati mock per testare l'interfaccia senza backend.

## 📋 Funzionalità

### ✅ Implementato

- ✅ Lettura token da URL (`?token=...`)
- ✅ Fetch snapshot da API (o mock se token=FAKE)
- ✅ Visualizzazione meta ("234 records • Last updated...")
- ✅ Sidebar filtri (Tipologia, Annata, Cantina) con conteggi
- ✅ Filtri espandibili/collassabili
- ✅ Tabella dati (Nome, Annata, Quantità, Prezzo, Scorta critica)
- ✅ Ricerca istantanea (debounced 300ms) su Nome/Annata/Cantina
- ✅ Paginazione (50 righe/pagina)
- ✅ Download CSV
- ✅ Gestione errori (token scaduto/non valido)
- ✅ Responsive design

### ⏳ Da Implementare (quando collegato al backend)

- 🔗 Collegamento endpoint processor `/api/inventory/snapshot`
- 🔗 Collegamento endpoint processor `/api/inventory/export.csv`
- 🔗 Validazione token JWT reale

## ⚙️ Configurazione

In `app.js`, oggetto `CONFIG`:

```javascript
const CONFIG = {
    apiBase: "",                         // se vuoto usa lo stesso dominio del viewer
    endpointSnapshot: "/api/inventory/snapshot",
    endpointCsv: "/api/inventory/export.csv",
    pageSize: 50
};
```

### Se viewer e processor su domini diversi:

Modificare `apiBase` con l'URL completo del processor:
```javascript
apiBase: "https://processor.gioia.app"
```

## 🔌 API Richieste (dal Processor)

### GET `/api/inventory/snapshot?token=JWT`

**Response 200:**
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

**Response 401/410:** Token scaduto/non valido

### GET `/api/inventory/export.csv?token=JWT`

**Response:** CSV file (`Content-Type: text/csv`)

**Response 401/410:** Token scaduto/non valido

## 🎯 Prossimi Passi

1. ✅ Frontend completato (questo progetto)
2. ⏳ Backend processor: aggiungere endpoint `/api/inventory/snapshot` e `/api/inventory/export.csv`
3. ⏳ Bot Telegram: aggiungere comando "Vedi tutto" che genera token JWT e link
4. ⏳ Test end-to-end
5. ⏳ Deploy viewer su hosting statico (Vercel/Netlify/Railway)

## 📝 Note

- Il viewer è completamente statico (HTML/CSS/JS vanilla)
- Nessuna dipendenza esterna (tranne Google Fonts per Inter)
- Compatibile con tutti i browser moderni
- SEO-friendly (single page application)

---

**Versione:** 1.0  
**Data:** 2025-11-03  
**Status:** Frontend completato, in attesa di integrazione backend


# 🍷 Vineinventory Viewer

Frontend web **solo lettura** per visualizzare l'inventario vini dell'utente attraverso un link con token temporaneo generato dal bot Telegram.

## 📁 Struttura Progetto

```
Vineinventory Viewer/
├── index.html          # Markup principale
├── styles.css          # Stili (palette granaccia/bianco/nero)
├── app.js              # Logica JavaScript (fetch, filtri, ricerca, CSV)
├── assets/
│   └── logo.png        # Logo Gio.ia
└── README.md           # Questo file
```

## 🎨 Design

- **Palette colori:** Granaccia (#9a182e), Bianco, Nero
- **Typography:** Inter (Google Fonts)
- **Layout:** Single page con sidebar filtri a sinistra e tabella a destra
- **Responsive:** ≤ 980px stack verticale (sidebar sopra, tabella sotto)
- **Nessun elemento decorativo** (no pennellate/pallini)

## 🚀 Test Locale

### Con server statico

```bash
# Opzione 1: Python
python -m http.server 8080

# Opzione 2: Node.js serve
npx serve .

# Opzione 3: PHP
php -S localhost:8080
```

Poi apri nel browser:
- **Con token mock:** `http://localhost:8080/?token=FAKE`
- **Con token reale:** `http://localhost:8080/?token=<JWT_TOKEN>`

### Token FAKE

Quando il token è `FAKE` o `fake`, l'app carica dati mock per testare l'interfaccia senza backend.

## 📋 Funzionalità

### ✅ Implementato

- ✅ Lettura token da URL (`?token=...`)
- ✅ Fetch snapshot da API (o mock se token=FAKE)
- ✅ Visualizzazione meta ("234 records • Last updated...")
- ✅ Sidebar filtri (Tipologia, Annata, Cantina) con conteggi
- ✅ Filtri espandibili/collassabili
- ✅ Tabella dati (Nome, Annata, Quantità, Prezzo, Scorta critica)
- ✅ Ricerca istantanea (debounced 300ms) su Nome/Annata/Cantina
- ✅ Paginazione (50 righe/pagina)
- ✅ Download CSV
- ✅ Gestione errori (token scaduto/non valido)
- ✅ Responsive design

### ⏳ Da Implementare (quando collegato al backend)

- 🔗 Collegamento endpoint processor `/api/inventory/snapshot`
- 🔗 Collegamento endpoint processor `/api/inventory/export.csv`
- 🔗 Validazione token JWT reale

## ⚙️ Configurazione

In `app.js`, oggetto `CONFIG`:

```javascript
const CONFIG = {
    apiBase: "",                         // se vuoto usa lo stesso dominio del viewer
    endpointSnapshot: "/api/inventory/snapshot",
    endpointCsv: "/api/inventory/export.csv",
    pageSize: 50
};
```

### Se viewer e processor su domini diversi:

Modificare `apiBase` con l'URL completo del processor:
```javascript
apiBase: "https://processor.gioia.app"
```

## 🔌 API Richieste (dal Processor)

### GET `/api/inventory/snapshot?token=JWT`

**Response 200:**
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

**Response 401/410:** Token scaduto/non valido

### GET `/api/inventory/export.csv?token=JWT`

**Response:** CSV file (`Content-Type: text/csv`)

**Response 401/410:** Token scaduto/non valido

## 🎯 Prossimi Passi

1. ✅ Frontend completato (questo progetto)
2. ⏳ Backend processor: aggiungere endpoint `/api/inventory/snapshot` e `/api/inventory/export.csv`
3. ⏳ Bot Telegram: aggiungere comando "Vedi tutto" che genera token JWT e link
4. ⏳ Test end-to-end
5. ⏳ Deploy viewer su hosting statico (Vercel/Netlify/Railway)

## 📝 Note

- Il viewer è completamente statico (HTML/CSS/JS vanilla)
- Nessuna dipendenza esterna (tranne Google Fonts per Inter)
- Compatibile con tutti i browser moderni
- SEO-friendly (single page application)

---

**Versione:** 1.0  
**Data:** 2025-11-03  
**Status:** Frontend completato, in attesa di integrazione backend




Frontend web **solo lettura** per visualizzare l'inventario vini dell'utente attraverso un link con token temporaneo generato dal bot Telegram.

## 📁 Struttura Progetto

```
Vineinventory Viewer/
├── index.html          # Markup principale
├── styles.css          # Stili (palette granaccia/bianco/nero)
├── app.js              # Logica JavaScript (fetch, filtri, ricerca, CSV)
├── assets/
│   └── logo.png        # Logo Gio.ia
└── README.md           # Questo file
```

## 🎨 Design

- **Palette colori:** Granaccia (#9a182e), Bianco, Nero
- **Typography:** Inter (Google Fonts)
- **Layout:** Single page con sidebar filtri a sinistra e tabella a destra
- **Responsive:** ≤ 980px stack verticale (sidebar sopra, tabella sotto)
- **Nessun elemento decorativo** (no pennellate/pallini)

## 🚀 Test Locale

### Con server statico

```bash
# Opzione 1: Python
python -m http.server 8080

# Opzione 2: Node.js serve
npx serve .

# Opzione 3: PHP
php -S localhost:8080
```

Poi apri nel browser:
- **Con token mock:** `http://localhost:8080/?token=FAKE`
- **Con token reale:** `http://localhost:8080/?token=<JWT_TOKEN>`

### Token FAKE

Quando il token è `FAKE` o `fake`, l'app carica dati mock per testare l'interfaccia senza backend.

## 📋 Funzionalità

### ✅ Implementato

- ✅ Lettura token da URL (`?token=...`)
- ✅ Fetch snapshot da API (o mock se token=FAKE)
- ✅ Visualizzazione meta ("234 records • Last updated...")
- ✅ Sidebar filtri (Tipologia, Annata, Cantina) con conteggi
- ✅ Filtri espandibili/collassabili
- ✅ Tabella dati (Nome, Annata, Quantità, Prezzo, Scorta critica)
- ✅ Ricerca istantanea (debounced 300ms) su Nome/Annata/Cantina
- ✅ Paginazione (50 righe/pagina)
- ✅ Download CSV
- ✅ Gestione errori (token scaduto/non valido)
- ✅ Responsive design

### ⏳ Da Implementare (quando collegato al backend)

- 🔗 Collegamento endpoint processor `/api/inventory/snapshot`
- 🔗 Collegamento endpoint processor `/api/inventory/export.csv`
- 🔗 Validazione token JWT reale

## ⚙️ Configurazione

In `app.js`, oggetto `CONFIG`:

```javascript
const CONFIG = {
    apiBase: "",                         // se vuoto usa lo stesso dominio del viewer
    endpointSnapshot: "/api/inventory/snapshot",
    endpointCsv: "/api/inventory/export.csv",
    pageSize: 50
};
```

### Se viewer e processor su domini diversi:

Modificare `apiBase` con l'URL completo del processor:
```javascript
apiBase: "https://processor.gioia.app"
```

## 🔌 API Richieste (dal Processor)

### GET `/api/inventory/snapshot?token=JWT`

**Response 200:**
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

**Response 401/410:** Token scaduto/non valido

### GET `/api/inventory/export.csv?token=JWT`

**Response:** CSV file (`Content-Type: text/csv`)

**Response 401/410:** Token scaduto/non valido

## 🎯 Prossimi Passi

1. ✅ Frontend completato (questo progetto)
2. ⏳ Backend processor: aggiungere endpoint `/api/inventory/snapshot` e `/api/inventory/export.csv`
3. ⏳ Bot Telegram: aggiungere comando "Vedi tutto" che genera token JWT e link
4. ⏳ Test end-to-end
5. ⏳ Deploy viewer su hosting statico (Vercel/Netlify/Railway)

## 📝 Note

- Il viewer è completamente statico (HTML/CSS/JS vanilla)
- Nessuna dipendenza esterna (tranne Google Fonts per Inter)
- Compatibile con tutti i browser moderni
- SEO-friendly (single page application)

---

**Versione:** 1.0  
**Data:** 2025-11-03  
**Status:** Frontend completato, in attesa di integrazione backend


