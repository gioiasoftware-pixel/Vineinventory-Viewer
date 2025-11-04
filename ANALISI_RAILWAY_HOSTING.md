# 🚂 Analisi Railway come Server per Vineinventory Viewer

**Data analisi:** 2025-11-03  
**Status:** Da valutare

---

## 📋 Opzioni Hosting Viewer Statico

### 1. **Railway** (da valutare)
### 2. **Vercel** (alternativa)
### 3. **Netlify** (alternativa)
### 4. **GitHub Pages** (gratuito, limitato)

---

## 🚂 Railway: Analisi Dettagliata

### ✅ **Vantaggi di usare Railway**

1. **Stessa Infrastruttura**
   - Processor già su Railway → stesso provider
   - Dashboard unificata per gestire tutto
   - Facile gestione variabili ambiente condivise
   - Deployment coordinato

2. **Semplicità Setup**
   - Integrazione GitHub già configurata
   - Deploy automatico da push
   - Build automatico (Nixpacks)
   - Health check e restart automatici

3. **Gestione CORS Semplice**
   - Viewer e processor stesso dominio/base → CORS non necessario
   - Oppure stesso progetto Railway → variabili condivise
   - Zero configurazione CORS aggiuntiva

4. **Costi**
   - Piano gratuito: $5 crediti/mese
   - Viewer statico → consumo minimo (solo traffico)
   - Probabilmente dentro i limiti gratuiti
   - Stesso billing account del processor

5. **Sicurezza**
   - HTTPS incluso automaticamente
   - Certificati SSL automatici
   - Stessi standard sicurezza del processor

---

### ⚠️ **Svantaggi/Considerazioni Railway**

1. **Overkill per Statico**
   - Railway è ottimizzato per app dinamiche (Python, Node, etc.)
   - Per solo HTML/CSS/JS potrebbe essere eccessivo
   - Build process non necessario per statici

2. **Configurazione Necessaria**
   - Serve un server HTTP semplice (es. Python `http.server` o Node `serve`)
   - O configurazione Nixpacks per static site
   - Non è "plug and play" come Vercel/Netlify

3. **Costi (se fuori limiti)**
   - Se traffico alto → costi aggiuntivi
   - Piano Hobby: $20 crediti/mese base
   - Traffico uscita: $0.10 per GB

4. **Performance**
   - Non ha CDN globale come Vercel/Netlify
   - Potrebbe essere più lento per utenti lontani dal server Railway
   - Per viewer con pochi utenti → non è un problema

---

## 🔧 Come Implementare su Railway

### **Opzione 1: Server Python Semplice** (Consigliato)

#### Struttura Progetto
```
Vineinventory Viewer/
├── index.html
├── styles.css
├── app.js
├── assets/
│   └── logo.png
├── server.py          # NUOVO - server HTTP semplice
├── requirements.txt    # NUOVO - solo python-dotenv (opzionale)
├── Procfile           # NUOVO
├── railway.json        # NUOVO (opzionale)
└── README.md
```

#### File `server.py`
```python
#!/usr/bin/env python3
"""Server HTTP semplice per viewer statico"""
import http.server
import socketserver
import os

PORT = int(os.getenv("PORT", 8080))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)
    
    def end_headers(self):
        # CORS headers se necessario (se viewer e processor domini diversi)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Server avviato su porta {PORT}")
        httpd.serve_forever()
```

#### File `Procfile`
```
web: python server.py
```

#### File `railway.json` (opzionale)
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python server.py",
    "healthcheckPath": "/",
    "healthcheckTimeout": 10,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### File `requirements.txt`
```txt
# Nessuna dipendenza necessaria (Python stdlib)
# Opzionale: python-dotenv se vuoi variabili ambiente da file
```

**Vantaggi:**
- ✅ Zero dipendenze (Python stdlib)
- ✅ Build veloce
- ✅ Server semplice e affidabile
- ✅ Facile da testare localmente

---

### **Opzione 2: Node.js Serve** (Alternativa)

#### File `package.json`
```json
{
  "name": "vineinventory-viewer",
  "version": "1.0.0",
  "scripts": {
    "start": "serve -p $PORT"
  },
  "dependencies": {
    "serve": "^14.2.1"
  }
}
```

#### File `Procfile`
```
web: npm start
```

**Vantaggi:**
- ✅ Serve ottimizzato per statici
- ✅ Headers CORS configurabili
- ✅ Cache headers
- ⚠️ Richiede Node.js (build più lento)

---

### **Opzione 3: Servire dal Processor** (Non Consigliato)

Servire i file statici direttamente dal processor FastAPI:
- ✅ Un solo servizio
- ❌ Mescola responsabilità (API + static files)
- ❌ Deploy più complesso
- ❌ Performance peggiore

**Sconsigliato** perché separazione concerns è migliore.

---

## 🌐 Configurazione CORS

### Scenario A: Viewer e Processor stesso dominio base

**Esempio:** 
- Processor: `https://gioia-processor.railway.app`
- Viewer: `https://gioia-viewer.railway.app`

**CORS:** Non necessario se:
- Viewer chiama API con URL completo
- Processor ha CORS già configurato (`allow_origins=["*"]`)

**Configurazione Viewer:**
```javascript
const CONFIG = {
    apiBase: "https://gioia-processor.railway.app",  // URL completo processor
    endpointSnapshot: "/api/inventory/snapshot",
    endpointCsv: "/api/inventory/export.csv",
    pageSize: 50
};
```

### Scenario B: Viewer e Processor stesso progetto Railway

**Setup:**
1. Stesso progetto Railway
2. Due servizi: `processor` e `viewer`
3. Variabili ambiente condivise

**CORS:** Non necessario (stessa origine)

**Configurazione Viewer:**
```javascript
const CONFIG = {
    apiBase: "",  // Vuoto = stesso dominio
    endpointSnapshot: "/api/inventory/snapshot",
    endpointCsv: "/api/inventory/export.csv",
    pageSize: 50
};
```

---

## 💰 Analisi Costi Railway

### **Piano Gratuito**
- $5 crediti/mese
- 0.5 GB RAM, 1 vCPU
- 0.5 GB storage

### **Consumo Viewer Statico**

**Stima mensile:**
- **RAM:** ~50 MB (server Python semplice)
- **CPU:** ~0.1 vCPU (solo serve file statici)
- **Storage:** ~5 MB (HTML/CSS/JS/assets)
- **Traffico:** Dipende da utilizzo
  - 1000 visite/mese: ~50 MB → $0.005
  - 10000 visite/mese: ~500 MB → $0.05

**Conclusione:** Viewer statico rientra ampiamente nel piano gratuito.

### **Costi Totali Sistema**

Se processor + viewer nello stesso progetto:
- Processor: ~$3-5/mese (con utilizzo medio)
- Viewer: ~$0.10/mese (traffico minimo)
- **Totale:** ~$3-6/mese

**Alternativa:** Piano Hobby ($20 crediti/mese base) se superi limiti gratuiti.

---

## 🆚 Confronto con Alternative

### **Vercel**
**Vantaggi:**
- ✅ Ottimizzato per statici
- ✅ CDN globale (performance superiore)
- ✅ Deploy istantaneo
- ✅ Gratuito per progetti personali
- ✅ Zero configurazione (auto-detect)

**Svantaggi:**
- ❌ Provider diverso dal processor
- ❌ CORS da configurare manualmente
- ❌ Gestione separata dashboard

**Costo:** Gratuito (piano hobby)

---

### **Netlify**
**Vantaggi:**
- ✅ Ottimizzato per statici
- ✅ CDN globale
- ✅ Form builder, serverless functions
- ✅ Gratuito generoso

**Svantaggi:**
- ❌ Provider diverso dal processor
- ❌ CORS da configurare
- ❌ Dashboard separata

**Costo:** Gratuito (piano starter)

---

### **GitHub Pages**
**Vantaggi:**
- ✅ Completamente gratuito
- ✅ CDN globale
- ✅ Zero configurazione

**Svantaggi:**
- ❌ Solo repository pubblici (o GitHub Pro)
- ❌ Limitato a HTML/CSS/JS (no server-side)
- ❌ CORS restrittivo

**Costo:** Gratuito

---

## ✅ Raccomandazione Finale

### **Scenario Consigliato: Railway**

**Perché:**
1. ✅ **Stessa infrastruttura** del processor → gestione unificata
2. ✅ **CORS semplice** (stesso dominio base o variabili condivise)
3. ✅ **Costi contenuti** (dentro piano gratuito per viewer)
4. ✅ **Deploy coordinato** (push a processor → anche viewer aggiornato)
5. ✅ **HTTPS incluso** automaticamente
6. ✅ **Gestione unificata** variabili ambiente

**Setup:**
- **Opzione A:** Servizio separato Railway (consigliato)
  - Progetto Railway separato: `vineinventory-viewer`
  - Deploy da repository GitHub
  - Server Python semplice (`server.py`)
  
- **Opzione B:** Stesso progetto Railway, servizio multiplo
  - Aggiungere servizio "viewer" al progetto esistente
  - Condividere variabili ambiente
  - CORS non necessario

**Configurazione:**
```javascript
// Se stesso progetto Railway
const CONFIG = {
    apiBase: "",  // Vuoto = stesso dominio
    endpointSnapshot: "/api/inventory/snapshot",
    endpointCsv: "/api/inventory/export.csv",
    pageSize: 50
};

// Se progetti separati
const CONFIG = {
    apiBase: process.env.PROCESSOR_URL || "https://gioia-processor.railway.app",
    endpointSnapshot: "/api/inventory/snapshot",
    endpointCsv: "/api/inventory/export.csv",
    pageSize: 50
};
```

---

## 📝 File Necessari per Deploy Railway

### 1. **server.py** (Nuovo)
```python
#!/usr/bin/env python3
"""Server HTTP semplice per viewer statico"""
import http.server
import socketserver
import os

PORT = int(os.getenv("PORT", 8080))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)
    
    def end_headers(self):
        # Headers CORS se necessario
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'public, max-age=3600')
        super().end_headers()

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🍷 Vineinventory Viewer server avviato su porta {PORT}")
        httpd.serve_forever()
```

### 2. **Procfile** (Nuovo)
```
web: python server.py
```

### 3. **railway.json** (Nuovo, opzionale)
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python server.py",
    "healthcheckPath": "/",
    "healthcheckTimeout": 10
  }
}
```

### 4. **requirements.txt** (Nuovo, opzionale - può essere vuoto)
```txt
# Nessuna dipendenza necessaria (Python stdlib)
# Railway richiede comunque questo file per progetti Python
```

### 5. **.railwayignore** (Opzionale)
```
immagini/
README.md
ANALISI_*.md
*.md
!README.md
```

---

## 🔄 Flusso Deploy Railway

1. **Push su GitHub**
   - Repository separato o cartella dedicata
   - Railway rileva automaticamente Python project

2. **Deploy Automatico**
   - Railway build con Nixpacks
   - Installa Python (se necessario)
   - Esegue `python server.py`

3. **Configurazione**
   - Variabile `PORT` → Railway la setta automaticamente
   - Variabile `PROCESSOR_URL` → URL processor per API calls
   - Variabile `VIEWER_URL` → URL viewer per link nel bot

4. **Test**
   - Health check: `https://viewer.railway.app/`
   - Test con token: `https://viewer.railway.app/?token=FAKE`

---

## ⚡ Performance Railway vs Alternative

### **Railway**
- **CDN:** No (serve da singolo server)
- **Cache:** Headers manuali
- **Latency:** Dipende da posizione server Railway
- **Build:** ~30-60 secondi

### **Vercel/Netlify**
- **CDN:** Sì (globale, edge locations)
- **Cache:** Automatico
- **Latency:** Migliore (edge nearest user)
- **Build:** ~10-20 secondi

**Conclusione:** Per viewer con pochi utenti, differenza impercettibile. Per scale, Vercel/Netlify meglio.

---

## 🔐 Sicurezza e Configurazione

### **HTTPS**
- ✅ Railway fornisce HTTPS automatico
- ✅ Certificati SSL auto-rinnovati
- ✅ Zero configurazione

### **Variabili Ambiente**
```env
# Railway Dashboard → Variables
PROCESSOR_URL=https://gioia-processor.railway.app
VIEWER_URL=https://gioia-viewer.railway.app
JWT_SECRET_KEY=your-secret-key-shared-with-processor
```

### **CORS (se necessario)**
Nel processor (`main.py`):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://gioia-viewer.railway.app",
        "http://localhost:8080"  # Per sviluppo locale
    ],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)
```

---

## 📊 Decision Matrix

| Criterio | Railway | Vercel | Netlify | GitHub Pages |
|----------|---------|--------|---------|--------------|
| **Integrazione con processor** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐ |
| **Facilità setup** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Performance** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Costi** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Gestione unificata** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐ |
| **CORS setup** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |

**Vincitore:** **Railway** per integrazione e gestione unificata.

---

## ✅ Conclusione e Raccomandazione

### **Railway è la scelta migliore perché:**

1. ✅ **Stessa infrastruttura** → gestione unificata
2. ✅ **CORS semplice** → stesso dominio base
3. ✅ **Costi contenuti** → viewer statico dentro piano gratuito
4. ✅ **Deploy coordinato** → push GitHub aggiorna tutto
5. ✅ **HTTPS automatico** → zero configurazione
6. ✅ **Variabili ambiente condivise** → se stesso progetto

### **Setup Consigliato:**

**Opzione A: Progetto Separato Railway** (Più pulito)
- Repository GitHub: `vineinventory-viewer`
- Nuovo progetto Railway: `vineinventory-viewer`
- Server Python semplice (`server.py`)
- Deploy automatico da GitHub

**Opzione B: Stesso Progetto Railway, Servizio Multiplo**
- Aggiungere servizio "viewer" al progetto esistente
- Cartella `viewer/` nel repository processor
- Condividere variabili ambiente
- Deploy coordinato

**Raccomandazione:** Opzione A (progetto separato) per separazione concerns migliore.

---

**Prossimi Passi:**
1. Creare `server.py` nel viewer
2. Aggiungere `Procfile` e `railway.json`
3. Push su GitHub (repository separato o cartella dedicata)
4. Creare nuovo progetto Railway
5. Configurare variabili ambiente
6. Test deploy

---

**Versione:** 1.0  
**Data:** 2025-11-03  
**Status:** Analisi completata - Railway raccomandato ✅



**Data analisi:** 2025-11-03  
**Status:** Da valutare

---

## 📋 Opzioni Hosting Viewer Statico

### 1. **Railway** (da valutare)
### 2. **Vercel** (alternativa)
### 3. **Netlify** (alternativa)
### 4. **GitHub Pages** (gratuito, limitato)

---

## 🚂 Railway: Analisi Dettagliata

### ✅ **Vantaggi di usare Railway**

1. **Stessa Infrastruttura**
   - Processor già su Railway → stesso provider
   - Dashboard unificata per gestire tutto
   - Facile gestione variabili ambiente condivise
   - Deployment coordinato

2. **Semplicità Setup**
   - Integrazione GitHub già configurata
   - Deploy automatico da push
   - Build automatico (Nixpacks)
   - Health check e restart automatici

3. **Gestione CORS Semplice**
   - Viewer e processor stesso dominio/base → CORS non necessario
   - Oppure stesso progetto Railway → variabili condivise
   - Zero configurazione CORS aggiuntiva

4. **Costi**
   - Piano gratuito: $5 crediti/mese
   - Viewer statico → consumo minimo (solo traffico)
   - Probabilmente dentro i limiti gratuiti
   - Stesso billing account del processor

5. **Sicurezza**
   - HTTPS incluso automaticamente
   - Certificati SSL automatici
   - Stessi standard sicurezza del processor

---

### ⚠️ **Svantaggi/Considerazioni Railway**

1. **Overkill per Statico**
   - Railway è ottimizzato per app dinamiche (Python, Node, etc.)
   - Per solo HTML/CSS/JS potrebbe essere eccessivo
   - Build process non necessario per statici

2. **Configurazione Necessaria**
   - Serve un server HTTP semplice (es. Python `http.server` o Node `serve`)
   - O configurazione Nixpacks per static site
   - Non è "plug and play" come Vercel/Netlify

3. **Costi (se fuori limiti)**
   - Se traffico alto → costi aggiuntivi
   - Piano Hobby: $20 crediti/mese base
   - Traffico uscita: $0.10 per GB

4. **Performance**
   - Non ha CDN globale come Vercel/Netlify
   - Potrebbe essere più lento per utenti lontani dal server Railway
   - Per viewer con pochi utenti → non è un problema

---

## 🔧 Come Implementare su Railway

### **Opzione 1: Server Python Semplice** (Consigliato)

#### Struttura Progetto
```
Vineinventory Viewer/
├── index.html
├── styles.css
├── app.js
├── assets/
│   └── logo.png
├── server.py          # NUOVO - server HTTP semplice
├── requirements.txt    # NUOVO - solo python-dotenv (opzionale)
├── Procfile           # NUOVO
├── railway.json        # NUOVO (opzionale)
└── README.md
```

#### File `server.py`
```python
#!/usr/bin/env python3
"""Server HTTP semplice per viewer statico"""
import http.server
import socketserver
import os

PORT = int(os.getenv("PORT", 8080))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)
    
    def end_headers(self):
        # CORS headers se necessario (se viewer e processor domini diversi)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Server avviato su porta {PORT}")
        httpd.serve_forever()
```

#### File `Procfile`
```
web: python server.py
```

#### File `railway.json` (opzionale)
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python server.py",
    "healthcheckPath": "/",
    "healthcheckTimeout": 10,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### File `requirements.txt`
```txt
# Nessuna dipendenza necessaria (Python stdlib)
# Opzionale: python-dotenv se vuoi variabili ambiente da file
```

**Vantaggi:**
- ✅ Zero dipendenze (Python stdlib)
- ✅ Build veloce
- ✅ Server semplice e affidabile
- ✅ Facile da testare localmente

---

### **Opzione 2: Node.js Serve** (Alternativa)

#### File `package.json`
```json
{
  "name": "vineinventory-viewer",
  "version": "1.0.0",
  "scripts": {
    "start": "serve -p $PORT"
  },
  "dependencies": {
    "serve": "^14.2.1"
  }
}
```

#### File `Procfile`
```
web: npm start
```

**Vantaggi:**
- ✅ Serve ottimizzato per statici
- ✅ Headers CORS configurabili
- ✅ Cache headers
- ⚠️ Richiede Node.js (build più lento)

---

### **Opzione 3: Servire dal Processor** (Non Consigliato)

Servire i file statici direttamente dal processor FastAPI:
- ✅ Un solo servizio
- ❌ Mescola responsabilità (API + static files)
- ❌ Deploy più complesso
- ❌ Performance peggiore

**Sconsigliato** perché separazione concerns è migliore.

---

## 🌐 Configurazione CORS

### Scenario A: Viewer e Processor stesso dominio base

**Esempio:** 
- Processor: `https://gioia-processor.railway.app`
- Viewer: `https://gioia-viewer.railway.app`

**CORS:** Non necessario se:
- Viewer chiama API con URL completo
- Processor ha CORS già configurato (`allow_origins=["*"]`)

**Configurazione Viewer:**
```javascript
const CONFIG = {
    apiBase: "https://gioia-processor.railway.app",  // URL completo processor
    endpointSnapshot: "/api/inventory/snapshot",
    endpointCsv: "/api/inventory/export.csv",
    pageSize: 50
};
```

### Scenario B: Viewer e Processor stesso progetto Railway

**Setup:**
1. Stesso progetto Railway
2. Due servizi: `processor` e `viewer`
3. Variabili ambiente condivise

**CORS:** Non necessario (stessa origine)

**Configurazione Viewer:**
```javascript
const CONFIG = {
    apiBase: "",  // Vuoto = stesso dominio
    endpointSnapshot: "/api/inventory/snapshot",
    endpointCsv: "/api/inventory/export.csv",
    pageSize: 50
};
```

---

## 💰 Analisi Costi Railway

### **Piano Gratuito**
- $5 crediti/mese
- 0.5 GB RAM, 1 vCPU
- 0.5 GB storage

### **Consumo Viewer Statico**

**Stima mensile:**
- **RAM:** ~50 MB (server Python semplice)
- **CPU:** ~0.1 vCPU (solo serve file statici)
- **Storage:** ~5 MB (HTML/CSS/JS/assets)
- **Traffico:** Dipende da utilizzo
  - 1000 visite/mese: ~50 MB → $0.005
  - 10000 visite/mese: ~500 MB → $0.05

**Conclusione:** Viewer statico rientra ampiamente nel piano gratuito.

### **Costi Totali Sistema**

Se processor + viewer nello stesso progetto:
- Processor: ~$3-5/mese (con utilizzo medio)
- Viewer: ~$0.10/mese (traffico minimo)
- **Totale:** ~$3-6/mese

**Alternativa:** Piano Hobby ($20 crediti/mese base) se superi limiti gratuiti.

---

## 🆚 Confronto con Alternative

### **Vercel**
**Vantaggi:**
- ✅ Ottimizzato per statici
- ✅ CDN globale (performance superiore)
- ✅ Deploy istantaneo
- ✅ Gratuito per progetti personali
- ✅ Zero configurazione (auto-detect)

**Svantaggi:**
- ❌ Provider diverso dal processor
- ❌ CORS da configurare manualmente
- ❌ Gestione separata dashboard

**Costo:** Gratuito (piano hobby)

---

### **Netlify**
**Vantaggi:**
- ✅ Ottimizzato per statici
- ✅ CDN globale
- ✅ Form builder, serverless functions
- ✅ Gratuito generoso

**Svantaggi:**
- ❌ Provider diverso dal processor
- ❌ CORS da configurare
- ❌ Dashboard separata

**Costo:** Gratuito (piano starter)

---

### **GitHub Pages**
**Vantaggi:**
- ✅ Completamente gratuito
- ✅ CDN globale
- ✅ Zero configurazione

**Svantaggi:**
- ❌ Solo repository pubblici (o GitHub Pro)
- ❌ Limitato a HTML/CSS/JS (no server-side)
- ❌ CORS restrittivo

**Costo:** Gratuito

---

## ✅ Raccomandazione Finale

### **Scenario Consigliato: Railway**

**Perché:**
1. ✅ **Stessa infrastruttura** del processor → gestione unificata
2. ✅ **CORS semplice** (stesso dominio base o variabili condivise)
3. ✅ **Costi contenuti** (dentro piano gratuito per viewer)
4. ✅ **Deploy coordinato** (push a processor → anche viewer aggiornato)
5. ✅ **HTTPS incluso** automaticamente
6. ✅ **Gestione unificata** variabili ambiente

**Setup:**
- **Opzione A:** Servizio separato Railway (consigliato)
  - Progetto Railway separato: `vineinventory-viewer`
  - Deploy da repository GitHub
  - Server Python semplice (`server.py`)
  
- **Opzione B:** Stesso progetto Railway, servizio multiplo
  - Aggiungere servizio "viewer" al progetto esistente
  - Condividere variabili ambiente
  - CORS non necessario

**Configurazione:**
```javascript
// Se stesso progetto Railway
const CONFIG = {
    apiBase: "",  // Vuoto = stesso dominio
    endpointSnapshot: "/api/inventory/snapshot",
    endpointCsv: "/api/inventory/export.csv",
    pageSize: 50
};

// Se progetti separati
const CONFIG = {
    apiBase: process.env.PROCESSOR_URL || "https://gioia-processor.railway.app",
    endpointSnapshot: "/api/inventory/snapshot",
    endpointCsv: "/api/inventory/export.csv",
    pageSize: 50
};
```

---

## 📝 File Necessari per Deploy Railway

### 1. **server.py** (Nuovo)
```python
#!/usr/bin/env python3
"""Server HTTP semplice per viewer statico"""
import http.server
import socketserver
import os

PORT = int(os.getenv("PORT", 8080))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)
    
    def end_headers(self):
        # Headers CORS se necessario
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'public, max-age=3600')
        super().end_headers()

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🍷 Vineinventory Viewer server avviato su porta {PORT}")
        httpd.serve_forever()
```

### 2. **Procfile** (Nuovo)
```
web: python server.py
```

### 3. **railway.json** (Nuovo, opzionale)
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python server.py",
    "healthcheckPath": "/",
    "healthcheckTimeout": 10
  }
}
```

### 4. **requirements.txt** (Nuovo, opzionale - può essere vuoto)
```txt
# Nessuna dipendenza necessaria (Python stdlib)
# Railway richiede comunque questo file per progetti Python
```

### 5. **.railwayignore** (Opzionale)
```
immagini/
README.md
ANALISI_*.md
*.md
!README.md
```

---

## 🔄 Flusso Deploy Railway

1. **Push su GitHub**
   - Repository separato o cartella dedicata
   - Railway rileva automaticamente Python project

2. **Deploy Automatico**
   - Railway build con Nixpacks
   - Installa Python (se necessario)
   - Esegue `python server.py`

3. **Configurazione**
   - Variabile `PORT` → Railway la setta automaticamente
   - Variabile `PROCESSOR_URL` → URL processor per API calls
   - Variabile `VIEWER_URL` → URL viewer per link nel bot

4. **Test**
   - Health check: `https://viewer.railway.app/`
   - Test con token: `https://viewer.railway.app/?token=FAKE`

---

## ⚡ Performance Railway vs Alternative

### **Railway**
- **CDN:** No (serve da singolo server)
- **Cache:** Headers manuali
- **Latency:** Dipende da posizione server Railway
- **Build:** ~30-60 secondi

### **Vercel/Netlify**
- **CDN:** Sì (globale, edge locations)
- **Cache:** Automatico
- **Latency:** Migliore (edge nearest user)
- **Build:** ~10-20 secondi

**Conclusione:** Per viewer con pochi utenti, differenza impercettibile. Per scale, Vercel/Netlify meglio.

---

## 🔐 Sicurezza e Configurazione

### **HTTPS**
- ✅ Railway fornisce HTTPS automatico
- ✅ Certificati SSL auto-rinnovati
- ✅ Zero configurazione

### **Variabili Ambiente**
```env
# Railway Dashboard → Variables
PROCESSOR_URL=https://gioia-processor.railway.app
VIEWER_URL=https://gioia-viewer.railway.app
JWT_SECRET_KEY=your-secret-key-shared-with-processor
```

### **CORS (se necessario)**
Nel processor (`main.py`):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://gioia-viewer.railway.app",
        "http://localhost:8080"  # Per sviluppo locale
    ],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)
```

---

## 📊 Decision Matrix

| Criterio | Railway | Vercel | Netlify | GitHub Pages |
|----------|---------|--------|---------|--------------|
| **Integrazione con processor** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐ |
| **Facilità setup** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Performance** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Costi** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Gestione unificata** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐ |
| **CORS setup** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |

**Vincitore:** **Railway** per integrazione e gestione unificata.

---

## ✅ Conclusione e Raccomandazione

### **Railway è la scelta migliore perché:**

1. ✅ **Stessa infrastruttura** → gestione unificata
2. ✅ **CORS semplice** → stesso dominio base
3. ✅ **Costi contenuti** → viewer statico dentro piano gratuito
4. ✅ **Deploy coordinato** → push GitHub aggiorna tutto
5. ✅ **HTTPS automatico** → zero configurazione
6. ✅ **Variabili ambiente condivise** → se stesso progetto

### **Setup Consigliato:**

**Opzione A: Progetto Separato Railway** (Più pulito)
- Repository GitHub: `vineinventory-viewer`
- Nuovo progetto Railway: `vineinventory-viewer`
- Server Python semplice (`server.py`)
- Deploy automatico da GitHub

**Opzione B: Stesso Progetto Railway, Servizio Multiplo**
- Aggiungere servizio "viewer" al progetto esistente
- Cartella `viewer/` nel repository processor
- Condividere variabili ambiente
- Deploy coordinato

**Raccomandazione:** Opzione A (progetto separato) per separazione concerns migliore.

---

**Prossimi Passi:**
1. Creare `server.py` nel viewer
2. Aggiungere `Procfile` e `railway.json`
3. Push su GitHub (repository separato o cartella dedicata)
4. Creare nuovo progetto Railway
5. Configurare variabili ambiente
6. Test deploy

---

**Versione:** 1.0  
**Data:** 2025-11-03  
**Status:** Analisi completata - Railway raccomandato ✅


