# 🔐 Generazione e Configurazione JWT_SECRET_KEY

## 📋 Problema Attuale

La variabile `JWT_SECRET_KEY` non è configurata su nessun servizio. Questo causa errori di validazione token.

## ✅ Soluzione: Generare e Configurare Chiave

### **Step 1: Genera una Chiave Segreta Sicura**

Puoi generare una chiave sicura in diversi modi:

#### **Opzione A: Python (Consigliato)**
```python
import secrets
print(secrets.token_urlsafe(32))
```

#### **Opzione B: OpenSSL**
```bash
openssl rand -hex 32
```

#### **Opzione C: Online Generator**
Usa un generatore online sicuro (es. https://www.random.org/strings/)

**Esempio di chiave generata:**
```
aB3dEf9gHiJkLmNoPqRsTuVwXyZ1234567890abcdefghijklmnopqrstuvwxyz
```

---

### **Step 2: Configura su Railway**

Devi configurare **la stessa chiave** su tutti e tre i servizi:

#### **1. Bot (`telegram-ai-bot`)**
- Railway → progetto `telegram-ai-bot`
- Settings → Variables
- Aggiungi: `JWT_SECRET_KEY` = `[chiave-generata]`

#### **2. Processor (`gioia-processor`)**
- Railway → progetto `gioia-processor`
- Settings → Variables
- Aggiungi: `JWT_SECRET_KEY` = `[stessa-chiave-del-bot]`

#### **3. Viewer (`vineinventory-viewer-production`)**
- Railway → progetto `vineinventory-viewer-production`
- Settings → Variables
- Aggiungi: `JWT_SECRET_KEY` = `[stessa-chiave-del-bot]`

---

### **Step 3: Redeploy**

Dopo aver aggiunto le variabili:
1. Railway rileva automaticamente le modifiche
2. Oppure fai **Redeploy** manuale di tutti e tre i servizi

---

## ⚠️ IMPORTANTE

- **Stessa chiave**: Tutti e tre i servizi DEVONO avere la stessa `JWT_SECRET_KEY`
- **Sicurezza**: Non committare mai la chiave nel codice o su GitHub
- **Lunghezza**: Usa almeno 32 caratteri per sicurezza

---

## 🧪 Verifica

Dopo la configurazione, verifica nei log:

**Bot:**
```
[VIEWER_TOKEN] Token JWT generato con successo
```

**Viewer:**
```
[JWT_VALIDATE] Token JWT validato con successo
```

Se vedi ancora `Signature verification failed`, verifica che la chiave sia identica su tutti i servizi.

