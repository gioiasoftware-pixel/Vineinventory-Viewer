# 🍷 Alternative per Implementare Editing Vini nel Viewer

## 📋 Obiettivo

Permettere la modifica di ogni parametro di un vino direttamente dal viewer web:
- Annata (vintage)
- Prezzo vendita (selling_price)
- Prezzo costo (cost_price)
- Quantità (quantity)
- Cantina (producer)
- Fornitore (supplier)
- Tipologia (wine_type)
- Uvaggio (grape_variety)
- Regione (region)
- Paese (country)
- Classificazione (classification)
- Gradazione alcolica (alcohol_content)
- Descrizione (description)
- Note (notes)
- Scorta minima (min_quantity)

## 🔍 Analisi Situazione Attuale

### Viewer Attuale
- **Frontend**: HTML/CSS/JS vanilla (nessun framework)
- **Backend**: Server Python semplice (`server.py`) con endpoint API
- **Database**: Accesso diretto PostgreSQL tramite `viewer_db.py`
- **Autenticazione**: Token JWT temporaneo
- **Funzionalità**: Solo lettura (snapshot, export CSV, grafici movimenti)

### Processor API Esistente
✅ **Endpoint già disponibile**: `POST /admin/update-wine-field`
- Permette aggiornamento singolo campo per vino
- Campi supportati: producer, supplier, vintage, grape_variety, classification, selling_price, cost_price, alcohol_content, description, notes
- Validazione tipi e valori inclusa
- Richiede: `telegram_id`, `business_name`, `wine_id`, `field`, `value`

### Database Schema
- Tabella inventario: `"{telegram_id}/{business_name} INVENTARIO"`
- Campi disponibili: name, producer, supplier, vintage, quantity, selling_price, cost_price, wine_type, grape_variety, region, country, classification, alcohol_content, description, notes, min_quantity
- Identificazione vino: `id` (PK) + `user_id`

---

## 🎯 Alternative di Implementazione

### **Alternativa 1: Editing Inline nella Tabella (Approccio Minimale)**

#### Descrizione
Permettere editing diretto cliccando sulle celle della tabella. Le celle diventano editabili al click.

#### Vantaggi
- ✅ Implementazione semplice e veloce
- ✅ UX intuitiva (come Excel/Google Sheets)
- ✅ Nessuna modifica strutturale al layout
- ✅ Modifiche immediate visibili

#### Svantaggi
- ❌ Difficile su mobile (touch)
- ❌ Limitato spazio per campi complessi (descrizione, note)
- ❌ Validazione in tempo reale più complessa
- ❌ Rischio modifiche accidentali

#### Implementazione Tecnica
```javascript
// Frontend (app.js)
- Aggiungere classe "editable-cell" alle celle modificabili
- Event listener click → trasforma cella in input
- Event listener blur/Enter → salva modifica via API
- Mostra loading spinner durante salvataggio
- Validazione client-side prima di inviare

// Backend (server.py)
- Nuovo endpoint: POST /api/inventory/update-field
- Valida token JWT
- Chiama processor API: POST /admin/update-wine-field
- Restituisce conferma o errore

// Styling (styles.css)
- Celle editabili: cursor: pointer, hover effect
- Input inline: border highlight, focus state
- Loading state: spinner overlay
```

#### Tempo Stimato
- Frontend: 4-6 ore
- Backend: 2-3 ore
- Testing: 2 ore
- **Totale: 8-11 ore**

---

### **Alternativa 2: Modal di Editing Completo (Approccio Standard)**

#### Descrizione
Click su riga vino → apre modal con form completo per modificare tutti i campi del vino.

#### Vantaggi
- ✅ Spazio sufficiente per tutti i campi
- ✅ Validazione completa prima di salvare
- ✅ Possibilità di modificare più campi contemporaneamente
- ✅ UX professionale e chiara
- ✅ Mobile-friendly

#### Svantaggi
- ❌ Richiede creazione modal e form
- ❌ Più codice da mantenere
- ❌ Modifiche multiple richiedono salvataggio batch

#### Implementazione Tecnica
```javascript
// Frontend (app.js)
- Aggiungere pulsante "Modifica" o icona edit su ogni riga
- Click → apre modal con form pre-compilato
- Form con tutti i campi editabili (input, select, textarea)
- Validazione form completa prima di submit
- Pulsante "Salva" → invia tutte le modifiche
- Pulsante "Annulla" → chiude senza salvare

// Backend (server.py)
- Nuovo endpoint: POST /api/inventory/update-wine
- Accetta JSON con tutti i campi da aggiornare
- Chiama processor API per ogni campo modificato (o batch update)
- Restituisce conferma con vino aggiornato

// Styling (styles.css)
- Modal overlay: backdrop blur, centrato
- Form layout: grid responsive
- Input styling: consistente con design esistente
- Pulsanti: primary/secondary con hover states
```

#### Tempo Stimato
- Frontend: 8-12 ore
- Backend: 4-6 ore
- Testing: 3-4 ore
- **Totale: 15-22 ore**

---

### **Alternativa 3: Riga Espandibile con Form (Approccio Ibrido)**

#### Descrizione
Espandere la riga esistente (già implementata per dettagli) con form di editing invece di sola visualizzazione.

#### Vantaggi
- ✅ Riutilizza UI esistente (riga espandibile)
- ✅ Modifiche contestuali (vedi dati mentre modifichi)
- ✅ Meno codice rispetto a modal
- ✅ UX fluida

#### Svantaggi
- ❌ Spazio limitato nella riga espandibile
- ❌ Scroll necessario per molti campi
- ❌ Layout più complesso

#### Implementazione Tecnica
```javascript
// Frontend (app.js)
- Modificare riga dettagli esistente (.wine-details-row)
- Aggiungere toggle "Modifica" / "Visualizza"
- In modalità modifica: mostra input invece di span
- Salvataggio: pulsante "Salva modifiche" nella riga espansa
- Dopo salvataggio: aggiorna dati e ricarica snapshot

// Backend
- Stesso di Alternativa 2 (endpoint update-wine)

// Styling
- Form nella riga espansa: layout compatto
- Input inline con label
- Pulsanti azione: salva/annulla
```

#### Tempo Stimato
- Frontend: 6-10 ore
- Backend: 4-6 ore
- Testing: 2-3 ore
- **Totale: 12-19 ore**

---

### **Alternativa 4: Editing Batch Multi-Riga (Approccio Avanzato)**

#### Descrizione
Permettere selezione multipla di vini e modifica batch di campi comuni (es. aggiorna prezzo per tutti i vini selezionati).

#### Vantaggi
- ✅ Molto efficiente per modifiche massive
- ✅ UX professionale per gestione inventario
- ✅ Riduce operazioni ripetitive

#### Svantaggi
- ❌ Complessità alta
- ❌ Rischio errori batch
- ❌ Richiede sistema di selezione/checkbox
- ❌ Validazione più complessa

#### Implementazione Tecnica
```javascript
// Frontend
- Checkbox su ogni riga per selezione
- Toolbar con azioni batch: "Modifica prezzo", "Modifica fornitore", etc.
- Modal batch editing con campo da modificare + valore nuovo
- Preview modifiche prima di confermare
- Conferma con lista vini che verranno modificati

// Backend
- Endpoint: POST /api/inventory/batch-update
- Accetta array di wine_id + campo + valore
- Esegue update multipli in transazione
- Rollback su errore
```

#### Tempo Stimato
- Frontend: 12-16 ore
- Backend: 6-8 ore
- Testing: 4-5 ore
- **Totale: 22-29 ore**

---

### **Alternativa 5: Editing con Validazione AI (Approccio Innovativo)**

#### Descrizione
Editing standard + suggerimenti AI per correzioni automatiche (es. normalizzazione nomi cantine, validazione annate).

#### Vantaggi
- ✅ Migliora qualità dati
- ✅ Riduce errori manuali
- ✅ UX avanzata con suggerimenti intelligenti

#### Svantaggi
- ❌ Richiede integrazione OpenAI
- ❌ Costi API aggiuntivi
- ❌ Complessità alta
- ❌ Latency per suggerimenti

#### Implementazione Tecnica
```javascript
// Frontend
- Editing standard (come Alternativa 2 o 3)
- Input con autocomplete AI
- Suggerimenti in tempo reale durante digitazione
- Pulsante "Applica suggerimento" per ogni campo

// Backend
- Endpoint: POST /api/inventory/ai-suggest
- Chiama OpenAI per normalizzazione/suggerimenti
- Cache risultati per performance
```

#### Tempo Stimato
- Frontend: 10-14 ore
- Backend: 8-12 ore
- Testing: 4-6 ore
- **Totale: 22-32 ore**

---

## 🔧 Architettura Backend Proposta

### **Opzione A: Viewer Gestisce Direttamente Database**
```python
# viewer_db.py
async def update_wine_field(
    telegram_id: int,
    business_name: str,
    wine_id: int,
    field: str,
    value: Any
) -> Dict[str, Any]:
    """Aggiorna campo vino direttamente nel database"""
    # UPDATE query diretta
    # Validazione campo
    # Return vino aggiornato
```

**Vantaggi**: 
- ✅ Nessuna dipendenza processor
- ✅ Latency minima
- ✅ Controllo completo

**Svantaggi**:
- ❌ Duplicazione logica (già nel processor)
- ❌ Mantenimento doppio codice

### **Opzione B: Viewer Chiama Processor API** ⭐ **CONSIGLIATA**
```python
# server.py
async def update_wine_field_endpoint(token, wine_id, field, value):
    """Endpoint viewer che chiama processor"""
    # Valida token JWT
    # Estrai telegram_id, business_name
    # Chiama processor: POST /admin/update-wine-field
    # Return risultato
```

**Vantaggi**:
- ✅ Riutilizza logica esistente processor
- ✅ Single source of truth
- ✅ Validazione centralizzata
- ✅ Facile manutenzione

**Svantaggi**:
- ❌ Dipendenza da processor (ma già presente)
- ❌ Latency leggermente maggiore (HTTP call)

---

## 📊 Confronto Alternative

| Alternativa | Complessità | Tempo | UX | Mobile | Scalabilità |
|------------|-------------|-------|----|----|----| 
| 1. Inline Editing | ⭐⭐ | 8-11h | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| 2. Modal Completo | ⭐⭐⭐ | 15-22h | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 3. Riga Espandibile | ⭐⭐⭐ | 12-19h | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 4. Batch Editing | ⭐⭐⭐⭐⭐ | 22-29h | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 5. AI Editing | ⭐⭐⭐⭐⭐ | 22-32h | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 🎯 Raccomandazione

### **Fase 1: Implementazione Base (Alternativa 2 - Modal Completo)**
Implementare editing completo tramite modal per:
- ✅ UX professionale
- ✅ Supporto mobile
- ✅ Validazione completa
- ✅ Facile estensione futura

### **Fase 2: Estensioni Future (Opzionali)**
- **Alternativa 1**: Aggiungere editing inline per campi semplici (quantità, prezzo)
- **Alternativa 4**: Aggiungere batch editing per operazioni massive
- **Alternativa 5**: Integrare suggerimenti AI per qualità dati

---

## 📝 Dettagli Implementazione Consigliata (Alternativa 2)

### **Frontend Changes**

#### 1. Aggiungere Pulsante Modifica
```html
<!-- In renderTable(), aggiungere colonna "Azioni" -->
<th>Azioni</th>

<!-- In ogni riga -->
<td class="actions-cell">
    <button class="edit-btn" data-wine-id="${wineId}" onclick="openEditModal(${wineId})">
        ✏️ Modifica
    </button>
</td>
```

#### 2. Creare Modal HTML
```html
<!-- Aggiungere dopo modal movimenti -->
<div id="edit-wine-modal" class="modal hidden">
    <div class="modal-content modal-large">
        <div class="modal-header">
            <h2>Modifica Vino</h2>
            <button class="modal-close" onclick="closeEditModal()">&times;</button>
        </div>
        <div class="modal-body">
            <form id="edit-wine-form">
                <input type="hidden" id="edit-wine-id">
                
                <div class="form-grid">
                    <div class="form-group">
                        <label>Nome</label>
                        <input type="text" id="edit-name" readonly>
                    </div>
                    
                    <div class="form-group">
                        <label>Cantina</label>
                        <input type="text" id="edit-producer">
                    </div>
                    
                    <div class="form-group">
                        <label>Fornitore</label>
                        <input type="text" id="edit-supplier">
                    </div>
                    
                    <div class="form-group">
                        <label>Annata</label>
                        <input type="number" id="edit-vintage" min="1800" max="2100">
                    </div>
                    
                    <div class="form-group">
                        <label>Quantità</label>
                        <input type="number" id="edit-quantity" min="0" step="1">
                    </div>
                    
                    <div class="form-group">
                        <label>Prezzo Vendita (€)</label>
                        <input type="number" id="edit-selling-price" min="0" step="0.01">
                    </div>
                    
                    <div class="form-group">
                        <label>Prezzo Costo (€)</label>
                        <input type="number" id="edit-cost-price" min="0" step="0.01">
                    </div>
                    
                    <div class="form-group">
                        <label>Tipologia</label>
                        <select id="edit-wine-type">
                            <option value="">Seleziona...</option>
                            <option value="Rosso">Rosso</option>
                            <option value="Bianco">Bianco</option>
                            <option value="Spumante">Spumante</option>
                            <option value="Rosato">Rosato</option>
                            <option value="Dolce">Dolce</option>
                            <option value="Altro">Altro</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Uvaggio</label>
                        <input type="text" id="edit-grape-variety">
                    </div>
                    
                    <div class="form-group">
                        <label>Regione</label>
                        <input type="text" id="edit-region">
                    </div>
                    
                    <div class="form-group">
                        <label>Paese</label>
                        <input type="text" id="edit-country">
                    </div>
                    
                    <div class="form-group">
                        <label>Classificazione</label>
                        <input type="text" id="edit-classification">
                    </div>
                    
                    <div class="form-group">
                        <label>Gradazione Alcolica (%)</label>
                        <input type="number" id="edit-alcohol-content" min="0" max="100" step="0.1">
                    </div>
                    
                    <div class="form-group full-width">
                        <label>Descrizione</label>
                        <textarea id="edit-description" rows="3"></textarea>
                    </div>
                    
                    <div class="form-group full-width">
                        <label>Note</label>
                        <textarea id="edit-notes" rows="3"></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label>Scorta Minima</label>
                        <input type="number" id="edit-min-quantity" min="0" step="1">
                    </div>
                </div>
                
                <div class="form-actions">
                    <button type="button" class="btn-secondary" onclick="closeEditModal()">Annulla</button>
                    <button type="submit" class="btn-primary">Salva Modifiche</button>
                </div>
            </form>
        </div>
    </div>
</div>
```

#### 3. JavaScript Functions
```javascript
// Apri modal con dati vino
async function openEditModal(wineId) {
    const token = getTokenFromURL();
    const wine = findWineById(wineId); // Trova vino nei dati caricati
    
    // Popola form
    document.getElementById('edit-wine-id').value = wineId;
    document.getElementById('edit-name').value = wine.name || '';
    document.getElementById('edit-producer').value = wine.winery || '';
    document.getElementById('edit-supplier').value = wine.supplier || '';
    document.getElementById('edit-vintage').value = wine.vintage || '';
    document.getElementById('edit-quantity').value = wine.qty || 0;
    document.getElementById('edit-selling-price').value = wine.price || 0;
    document.getElementById('edit-cost-price').value = wine.cost_price || '';
    document.getElementById('edit-wine-type').value = wine.type || '';
    document.getElementById('edit-grape-variety').value = wine.grape_variety || '';
    document.getElementById('edit-region').value = wine.region || '';
    document.getElementById('edit-country').value = wine.country || '';
    document.getElementById('edit-classification').value = wine.classification || '';
    document.getElementById('edit-alcohol-content').value = wine.alcohol_content || '';
    document.getElementById('edit-description').value = wine.description || '';
    document.getElementById('edit-notes').value = wine.notes || '';
    document.getElementById('edit-min-quantity').value = wine.min_quantity || '';
    
    // Mostra modal
    document.getElementById('edit-wine-modal').classList.remove('hidden');
}

// Chiudi modal
function closeEditModal() {
    document.getElementById('edit-wine-modal').classList.add('hidden');
    document.getElementById('edit-wine-form').reset();
}

// Salva modifiche
async function saveWineChanges(e) {
    e.preventDefault();
    
    const token = getTokenFromURL();
    const wineId = document.getElementById('edit-wine-id').value;
    
    // Raccogli tutti i campi modificati
    const fields = {
        producer: document.getElementById('edit-producer').value,
        supplier: document.getElementById('edit-supplier').value,
        vintage: document.getElementById('edit-vintage').value,
        quantity: document.getElementById('edit-quantity').value,
        selling_price: document.getElementById('edit-selling-price').value,
        cost_price: document.getElementById('edit-cost-price').value,
        wine_type: document.getElementById('edit-wine-type').value,
        grape_variety: document.getElementById('edit-grape-variety').value,
        region: document.getElementById('edit-region').value,
        country: document.getElementById('edit-country').value,
        classification: document.getElementById('edit-classification').value,
        alcohol_content: document.getElementById('edit-alcohol-content').value,
        description: document.getElementById('edit-description').value,
        notes: document.getElementById('edit-notes').value,
        min_quantity: document.getElementById('edit-min-quantity').value
    };
    
    // Mostra loading
    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Salvataggio...';
    
    try {
        // Invia modifiche campo per campo (o batch se endpoint disponibile)
        const updates = [];
        for (const [field, value] of Object.entries(fields)) {
            if (value !== '') {
                updates.push(updateWineField(token, wineId, field, value));
            }
        }
        
        await Promise.all(updates);
        
        // Ricarica dati
        await loadData();
        
        // Chiudi modal
        closeEditModal();
        
        // Mostra notifica successo
        showNotification('Vino aggiornato con successo!', 'success');
        
    } catch (error) {
        console.error('Errore salvataggio:', error);
        showNotification('Errore durante il salvataggio: ' + error.message, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Salva Modifiche';
    }
}

// Chiamata API per aggiornare campo
async function updateWineField(token, wineId, field, value) {
    const baseUrl = CONFIG.apiBase || window.location.origin;
    const url = `${baseUrl}/api/inventory/update-field`;
    
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            token: token,
            wine_id: wineId,
            field: field,
            value: value
        })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Errore aggiornamento campo');
    }
    
    return await response.json();
}

// Setup form submit
document.getElementById('edit-wine-form').addEventListener('submit', saveWineChanges);
```

### **Backend Changes**

#### 1. Nuovo Endpoint in server.py
```python
def handle_update_field_endpoint(self):
    """Gestisci endpoint POST /api/inventory/update-field"""
    try:
        # Leggi body JSON
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        data = json.loads(body.decode('utf-8'))
        
        token = data.get('token')
        wine_id = data.get('wine_id')
        field = data.get('field')
        value = data.get('value')
        
        if not all([token, wine_id, field, value is not None]):
            self.send_error(400, "Parametri mancanti")
            return
        
        # Valida token
        from viewer_db import validate_viewer_token
        token_data = validate_viewer_token(token)
        if not token_data:
            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"detail": "Token scaduto o non valido"}).encode('utf-8'))
            return
        
        telegram_id = token_data["telegram_id"]
        business_name = token_data["business_name"]
        
        # Chiama processor API
        import aiohttp
        import asyncio
        
        processor_url = os.getenv('PROCESSOR_URL', 'https://gioia-processor-production.up.railway.app')
        update_url = f"{processor_url}/admin/update-wine-field"
        
        async def call_processor():
            async with aiohttp.ClientSession() as session:
                form_data = aiohttp.FormData()
                form_data.add_field('telegram_id', str(telegram_id))
                form_data.add_field('business_name', business_name)
                form_data.add_field('wine_id', str(wine_id))
                form_data.add_field('field', field)
                form_data.add_field('value', str(value))
                
                async with session.post(update_url, data=form_data) as resp:
                    return await resp.json()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(call_processor())
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"[UPDATE_FIELD] Errore: {e}", exc_info=True)
        self.send_response(500)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"detail": f"Errore interno: {str(e)}"}).encode('utf-8'))

# Aggiungere in do_POST
if parsed_path.path == '/api/inventory/update-field':
    self.handle_update_field_endpoint()
    return
```

#### 2. Alternativa: Endpoint Batch Update (Più Efficiente)
```python
def handle_batch_update_endpoint(self):
    """Gestisci endpoint POST /api/inventory/batch-update"""
    # Accetta array di modifiche: [{wine_id, field, value}, ...]
    # Esegue tutte le modifiche in parallelo
    # Return risultato aggregato
```

---

## 🎨 Styling CSS Aggiuntivo

```css
/* Modal Editing */
.modal-large {
    max-width: 800px;
    max-height: 90vh;
    overflow-y: auto;
}

.form-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
    margin: 1.5rem 0;
}

.form-group {
    display: flex;
    flex-direction: column;
}

.form-group.full-width {
    grid-column: 1 / -1;
}

.form-group label {
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: #333;
}

.form-group input,
.form-group select,
.form-group textarea {
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-family: 'Inter', sans-serif;
    font-size: 14px;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
    outline: none;
    border-color: #9a182e;
    box-shadow: 0 0 0 3px rgba(154, 24, 46, 0.1);
}

.form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 1rem;
    margin-top: 2rem;
    padding-top: 1.5rem;
    border-top: 1px solid #eee;
}

.btn-primary,
.btn-secondary {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 4px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-primary {
    background: #9a182e;
    color: white;
}

.btn-primary:hover:not(:disabled) {
    background: #7a1425;
}

.btn-secondary {
    background: #f5f5f5;
    color: #333;
}

.btn-secondary:hover {
    background: #e5e5e5;
}

.btn-primary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

/* Pulsante Modifica */
.edit-btn {
    padding: 0.5rem 1rem;
    background: #9a182e;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    transition: background 0.2s;
}

.edit-btn:hover {
    background: #7a1425;
}

.actions-cell {
    text-align: center;
}

/* Notifiche */
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 1rem 1.5rem;
    border-radius: 4px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 10000;
    animation: slideIn 0.3s ease-out;
}

.notification.success {
    background: #28a745;
    color: white;
}

.notification.error {
    background: #dc3545;
    color: white;
}

@keyframes slideIn {
    from {
        transform: translateX(400px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
```

---

## ✅ Checklist Implementazione

### Frontend
- [ ] Aggiungere colonna "Azioni" nella tabella
- [ ] Creare modal HTML per editing
- [ ] Implementare funzione `openEditModal()`
- [ ] Implementare funzione `saveWineChanges()`
- [ ] Implementare funzione `updateWineField()`
- [ ] Aggiungere validazione form client-side
- [ ] Aggiungere notifiche successo/errore
- [ ] Styling modal e form
- [ ] Test su desktop
- [ ] Test su mobile

### Backend
- [ ] Creare endpoint `POST /api/inventory/update-field`
- [ ] Integrare chiamata processor API
- [ ] Gestione errori e validazione
- [ ] Logging operazioni
- [ ] Test endpoint

### Testing
- [ ] Test modifica singolo campo
- [ ] Test modifica multipli campi
- [ ] Test validazione campi (annata, prezzo, etc.)
- [ ] Test errori (token scaduto, vino non trovato)
- [ ] Test mobile responsiveness
- [ ] Test performance con molti vini

---

## 📚 Note Aggiuntive

### Identificazione Vino
**Problema**: Il viewer attualmente non ha `wine_id` nei dati snapshot.

**Soluzione**:
1. **Opzione A**: Modificare `viewer_db.py` per includere `id` nello snapshot
2. **Opzione B**: Usare combinazione `name + vintage + producer` come identificatore (meno affidabile)

**Raccomandazione**: Opzione A - aggiungere `id` nello snapshot.

### Aggiornamento Quantità
**Nota**: L'endpoint processor `/admin/update-wine-field` non supporta `quantity` direttamente.

**Soluzione**:
1. Aggiungere supporto `quantity` nell'endpoint processor
2. Oppure creare movimento invece di update diretto (più corretto per tracciabilità)

### Permessi e Sicurezza
- ✅ Token JWT già valida utente
- ✅ Verifica `user_id` nel database per sicurezza
- ✅ Validazione campi lato server
- ✅ Rate limiting (da implementare se necessario)

---

## 🚀 Prossimi Passi

1. **Decidere alternativa** (raccomandato: Alternativa 2)
2. **Aggiungere `id` nello snapshot** (`viewer_db.py`)
3. **Implementare endpoint backend** (`server.py`)
4. **Implementare frontend** (`app.js`, `index.html`, `styles.css`)
5. **Testing completo**
6. **Deploy e monitoraggio**

---

**Documento creato**: 2025-01-XX  
**Versione**: 1.0  
**Autore**: Analisi Viewer GIOIA.prod
