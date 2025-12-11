# 🔍 Debug JWT Token - "Link scaduto o non valido"

## Problema
Il viewer mostra "Link scaduto o non valido" anche se il token è appena stato generato.

## Causa Probabile
La `JWT_SECRET_KEY` non corrisponde tra il **bot** (che genera il token) e il **viewer** (che lo valida).

## ✅ Verifica Rapida

### 1. Controlla Logs Railway - Viewer
Vai su Railway → `vineinventory-viewer-production` → **Logs** e cerca:

```
[JWT_VALIDATE] ❌ Firma token non valida (chiave JWT_SECRET_KEY non corrisponde)
```

Se vedi questo messaggio, significa che le chiavi non corrispondono.

### 2. Verifica Configurazione JWT_SECRET_KEY

#### Nel Bot (`telegram-ai-bot`):
1. Railway → `telegram-ai-bot` → **Settings** → **Variables**
2. Cerca `JWT_SECRET_KEY`
3. **Copia il valore** (se non esiste, devi crearla)

#### Nel Viewer (`vineinventory-viewer-production`):
1. Railway → `vineinventory-viewer-production` → **Settings** → **Variables**
2. Cerca `JWT_SECRET_KEY`
3. **Confronta con quella del bot** - DEVONO essere identiche!

### 3. Se le Chiavi Non Corrispondono

#### Opzione A: Genera Nuova Chiave Sicura
```bash
# Genera una chiave sicura (64 caratteri)
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

#### Opzione B: Usa Chiave Esistente
1. Scegli quale chiave mantenere (bot o viewer)
2. Copia quella chiave
3. Configurala in **entrambi** i servizi

### 4. Configurazione Railway

#### Bot (`telegram-ai-bot`):
1. Railway → `telegram-ai-bot` → **Settings** → **Variables**
2. Aggiungi/modifica: `JWT_SECRET_KEY` = `[chiave-generata-o-esistente]`
3. Salva

#### Viewer (`vineinventory-viewer-production`):
1. Railway → `vineinventory-viewer-production` → **Settings** → **Variables**
2. Aggiungi/modifica: `JWT_SECRET_KEY` = `[STESSA-CHIAVE-DEL-BOT]`
3. Salva

### 5. Riavvia i Servizi
Dopo aver configurato le variabili:
1. Railway → `telegram-ai-bot` → **Deployments** → **Redeploy**
2. Railway → `vineinventory-viewer-production` → **Deployments** → **Redeploy**

### 6. Verifica Logs
Dopo il redeploy, controlla i logs del viewer:

```
[JWT_VALIDATE] ✅ JWT_SECRET_KEY configurata correttamente
```

Se vedi questo, la configurazione è corretta.

## 🔍 Log Dettagliati

Dopo il deploy, i logs mostreranno:

### Viewer Logs (quando riceve un token):
```
[VIEWER_API] Token ricevuto: length=XXX, primi 50 char=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
[JWT_VALIDATE] Inizio validazione token, length=XXX
[JWT_VALIDATE] JWT_SECRET_KEY configurata: True
[JWT_VALIDATE] JWT_SECRET_KEY length: XX
[JWT_VALIDATE] JWT_SECRET_KEY (primi 20 char): [primi-20-caratteri]...
```

### Se la Chiave Non Corrisponde:
```
[JWT_VALIDATE] ❌ Firma token non valida (chiave JWT_SECRET_KEY non corrisponde)
[JWT_VALIDATE] ⚠️ Verifica che JWT_SECRET_KEY sia identica nel bot e nel viewer!
```

### Se la Chiave Corrisponde:
```
[JWT_VALIDATE] ✅ Token JWT validato con successo: telegram_id=XXX, business_name=XXX
```

## ⚠️ Importante

- **Stessa chiave**: Bot e Viewer DEVONO avere la STESSA `JWT_SECRET_KEY`
- **Sicurezza**: Non committare mai `JWT_SECRET_KEY` nel codice
- **Lunghezza**: Usa almeno 32 caratteri (consigliato 64+)

## 📝 Checklist

- [ ] `JWT_SECRET_KEY` configurata nel bot
- [ ] `JWT_SECRET_KEY` configurata nel viewer
- [ ] Le due chiavi sono **identiche**
- [ ] Entrambi i servizi sono stati riavviati dopo la configurazione
- [ ] Logs mostrano "JWT_SECRET_KEY configurata correttamente"
- [ ] Test con `/view` nel bot funziona

## 🆘 Se il Problema Persiste

1. Verifica che entrambi i servizi siano stati riavviati
2. Controlla i logs per errori specifici
3. Verifica che il token non venga troncato nell'URL (controlla la lunghezza nei logs)
4. Assicurati che non ci siano spazi o caratteri nascosti nella `JWT_SECRET_KEY`

