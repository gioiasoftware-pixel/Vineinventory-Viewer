// Configuration
// Il viewer gestisce tutto autonomamente - chiama direttamente il database
let CONFIG = {
    apiBase: "",  // Vuoto = stesso dominio del viewer (endpoint locale)
    endpointSnapshot: "/api/inventory/snapshot",
    endpointCsv: "/api/inventory/export.csv",
    endpointMovements: "/api/inventory/movements",
    pageSize: 50
};

// Chart instance
let movementsChart = null;

console.log("[VIEWER] ✅ Configurazione: viewer gestisce tutto autonomamente");
console.log("[VIEWER] ✅ Endpoint locale:", CONFIG.endpointSnapshot);

// State
let allData = {
    rows: [],
    facets: {},
    meta: {}
};
let filteredData = [];
let currentPage = 1;
let activeFilters = {
    type: null,
    vintage: null,
    winery: null,
    supplier: null
};
let searchQuery = "";

// Mock data per sviluppo (quando token=FAKE)
const MOCK_DATA = {
    rows: [
        { name: "Brunello di Montalcino", winery: "Biondi Santi", vintage: 2017, qty: 1, price: 49.00, type: "Rosso", critical: true },
        { name: "Langhe Nebbiolo", winery: "Gaja", vintage: 2020, qty: 3, price: 21.00, type: "Rosso", critical: true },
        { name: "Pinot Bianco", winery: "Alois Lageder", vintage: 2022, qty: 4, price: 16.00, type: "Bianco", critical: true },
        { name: "Chianti Classico", winery: "Antinori", vintage: 2019, qty: 12, price: 25.50, type: "Rosso", critical: false },
        { name: "Prosecco", winery: "La Marca", vintage: 2021, qty: 24, price: 15.00, type: "Spumante", critical: false },
        { name: "Barolo", winery: "Paolo Scavino", vintage: 2018, qty: 6, price: 89.90, type: "Rosso", critical: false },
        { name: "Etna Rosso", winery: "Girolamo Russo", vintage: 2021, qty: 30, price: 42.00, type: "Rosso", critical: false },
        { name: "Franciacorta Satèn", winery: "Ca' del Bosco", vintage: 2019, qty: 22, price: 49.00, type: "Spumante", critical: false },
        { name: "Chablis", winery: "Domaine Raveneau", vintage: 2021, qty: 5, price: 220.00, type: "Bianco", critical: false },
        { name: "Sassicaia", winery: "Tenuta San Guido", vintage: 2020, qty: 8, price: 320.00, type: "Rosso", critical: false }
    ],
    facets: {
        type: { "Rosso": 150, "Bianco": 84, "Spumante": 12, "Altro": 8 },
        vintage: { "2017": 23, "2018": 45, "2019": 32, "2020": 67, "2021": 42, "2022": 25 },
        winery: { "Biondi Santi": 5, "Gaja": 3, "Antinori": 18, "Paolo Scavino": 12, "Girolamo Russo": 8, "Ca' del Bosco": 6, "Domaine Raveneau": 4, "Tenuta San Guido": 3 }
    },
    meta: {
        total_rows: 234,
        last_update: new Date().toISOString()
    }
};

// Get token from URL
function getTokenFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('token') || null;
}

// Format relative time
function formatRelativeTime(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "appena ora";
    if (diffMins < 60) return `${diffMins} minuti fa`;
    if (diffHours < 24) return `${diffHours} ore fa`;
    return `${diffDays} giorni fa`;
}

// Fetch snapshot from API
async function fetchSnapshot(token) {
    const baseUrl = CONFIG.apiBase || window.location.origin;
    const url = `${baseUrl}${CONFIG.endpointSnapshot}?token=${encodeURIComponent(token)}`;

    console.log("[VIEWER] ===== DEBUG INFO =====");
    console.log("[VIEWER] CONFIG.apiBase:", CONFIG.apiBase);
    console.log("[VIEWER] window.VIEWER_CONFIG:", window.VIEWER_CONFIG);
    console.log("[VIEWER] window.location.origin:", window.location.origin);
    console.log("[VIEWER] Base URL utilizzato:", baseUrl);
    console.log("[VIEWER] Endpoint completo:", CONFIG.endpointSnapshot);
    console.log("[VIEWER] URL completo:", url);
    console.log("[VIEWER] Token length:", token ? token.length : 0);
    console.log("[VIEWER] =====================");

    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
            },
            // Non aggiungere mode: 'cors' esplicitamente - fetch lo gestisce automaticamente
        });
        
        console.log("[VIEWER] Response status:", response.status);
        console.log("[VIEWER] Response headers:", Object.fromEntries(response.headers.entries()));
        
        if (response.status === 401 || response.status === 410) {
            showError("Link scaduto o non valido");
            return null;
        }

        if (!response.ok) {
            const errorText = await response.text();
            console.error("[VIEWER] Error response body:", errorText);
            throw new Error(`HTTP ${response.status}: ${errorText.substring(0, 200)}`);
        }

        const data = await response.json();
        console.log("[VIEWER] Data received successfully:", {
            rows: data.rows ? data.rows.length : 0,
            facets: data.facets ? Object.keys(data.facets).length : 0,
            meta: data.meta
        });
        return data;
    } catch (error) {
        console.error("[VIEWER] Error fetching snapshot:", error);
        console.error("[VIEWER] Error name:", error.name);
        console.error("[VIEWER] Error message:", error.message);
        console.error("[VIEWER] Error stack:", error.stack);
        
        // Messaggio errore più dettagliato
        let errorMsg = "Errore nel caricamento dei dati";
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            errorMsg = "Errore di connessione: impossibile raggiungere il server. Verifica la configurazione API.";
        } else if (error.message) {
            errorMsg = `Errore: ${error.message}`;
        }
        
        showError(errorMsg);
        return null;
    }
}

// Load data (mock or real)
async function loadData() {
    const token = getTokenFromURL();
    
    if (!token) {
        showError("Token mancante nell'URL");
        return;
    }

    let data;

    // Se token è FAKE, usa mock data
    if (token === "FAKE" || token === "fake") {
        data = MOCK_DATA;
        // Simula delay
        await new Promise(resolve => setTimeout(resolve, 500));
    } else {
        data = await fetchSnapshot(token);
        if (!data) return;
    }

    allData = data;
    filteredData = [...data.rows];
    
    console.log('[LOAD_DATA] allData.rows.length:', allData.rows ? allData.rows.length : 0);
    console.log('[LOAD_DATA] filteredData.length:', filteredData.length);
    
    // Debug: verifica struttura dati ricevuti
    if (data.rows && data.rows.length > 0) {
        const firstRow = data.rows[0];
        console.log('[LOAD_DATA] ⚠️ Prima riga dati ricevuti dal backend:', {
            name: firstRow.name,
            winery: firstRow.winery,
            'winery type': typeof firstRow.winery,
            supplier: firstRow.supplier,
            'supplier type': typeof firstRow.supplier,
            vintage: firstRow.vintage,
            'vintage type': typeof firstRow.vintage,
            'TUTTE LE CHIAVI': Object.keys(firstRow)
        });
        
        // Verifica se winery è presente o se è undefined/null
        if (!firstRow.winery || firstRow.winery === '-' || firstRow.winery === 'null') {
            console.warn('[LOAD_DATA] ⚠️ ATTENZIONE: winery è vuoto/null per la prima riga!');
        }
        if (!firstRow.supplier || firstRow.supplier === '-' || firstRow.supplier === 'null') {
            console.warn('[LOAD_DATA] ⚠️ ATTENZIONE: supplier è vuoto/null per la prima riga!');
        }
    }
    
    console.log('[LOAD_DATA] Chiamando updateMeta, renderFilters, renderTable...');
    
    updateMeta();
    renderFilters();
    console.log('[LOAD_DATA] Prima di chiamare renderTable, filteredData.length:', filteredData.length);
    renderTable();
    console.log('[LOAD_DATA] Dopo renderTable');
    updatePagination();
    
    // Setup CSV download link
    setupCsvDownload(token);
}

// Show error banner
function showError(message) {
    const banner = document.getElementById('error-banner');
    banner.querySelector('span').textContent = `⚠️ ${message}`;
    banner.classList.remove('hidden');
    
    // Hide loading/table content
    document.getElementById('table-body').innerHTML = 
        `<tr><td colspan="7" class="empty-state">${message}</td></tr>`;
}

// Update meta info
function updateMeta() {
    const metaEl = document.getElementById('meta-info');
    const total = allData.meta.total_rows || filteredData.length;
    const lastUpdate = allData.meta.last_update 
        ? formatRelativeTime(allData.meta.last_update)
        : "sconosciuto";
    
    metaEl.textContent = `${total} records • Last updated ${lastUpdate}`;
}

// Render filters sidebar
function renderFilters() {
    renderFilterSection('type', allData.facets.type || {});
    renderFilterSection('vintage', allData.facets.vintage || {});
    renderFilterSection('winery', allData.facets.winery || {});
    renderFilterSection('supplier', allData.facets.supplier || {});
}

function renderFilterSection(filterType, facets) {
    const container = document.getElementById(`filter-${filterType}`);
    if (!container) {
        console.warn(`[VIEWER] Container filter-${filterType} non trovato`);
        return;
    }
    container.innerHTML = '';

    // Filtra facets vuoti o placeholder (per supplier e winery)
    let filteredFacets = Object.entries(facets);
    
    if (filterType === 'supplier' || filterType === 'winery') {
        filteredFacets = filteredFacets.filter(([key]) => 
            key && key !== "-" && key !== "" && key !== "null" && key !== "None"
        );
    }

    if (filteredFacets.length === 0) {
        container.innerHTML = '<div class="filter-item" style="opacity: 0.5; font-style: italic;">Nessun dato disponibile</div>';
        return;
    }

    const sortedFacets = filteredFacets
        .sort((a, b) => b[1] - a[1]); // Sort by count desc

    sortedFacets.forEach(([key, count]) => {
        const item = document.createElement('div');
        item.className = 'filter-item';
        // Per vintage, confronta come stringa per matching corretto
        const filterKey = filterType === 'vintage' ? String(key) : key;
        const activeKey = activeFilters[filterType] ? String(activeFilters[filterType]) : null;
        if (activeKey === filterKey) {
            item.classList.add('active');
        }
        item.innerHTML = `
            <span>${key}</span>
            <span class="filter-count">${count}</span>
        `;
        item.addEventListener('click', () => {
            toggleFilter(filterType, key);
        });
        container.appendChild(item);
    });
}

// Toggle filter
function toggleFilter(filterType, value) {
    // Per vintage, normalizza come stringa per matching consistente
    const normalizedValue = filterType === 'vintage' ? String(value) : value;
    
    if (activeFilters[filterType] === normalizedValue || 
        (filterType === 'vintage' && String(activeFilters[filterType]) === normalizedValue)) {
        activeFilters[filterType] = null;
    } else {
        activeFilters[filterType] = normalizedValue;
    }
    
    applyFilters();
    renderFilters();
}

// Apply filters and search
function applyFilters() {
    filteredData = allData.rows.filter(row => {
        // Type filter - case-insensitive matching con trim
        if (activeFilters.type) {
            const rowType = (row.type || "").trim();
            const filterType = activeFilters.type.trim();
            if (rowType.toLowerCase() !== filterType.toLowerCase()) {
                return false;
            }
        }
        
        // Vintage filter - normalizza per matching (numero o stringa)
        if (activeFilters.vintage) {
            const rowVintage = row.vintage !== null && row.vintage !== undefined ? String(row.vintage).trim() : "";
            const filterVintage = String(activeFilters.vintage).trim();
            if (rowVintage !== filterVintage) {
                return false;
            }
        }
        
        // Winery filter - case-insensitive matching con trim
        if (activeFilters.winery) {
            const rowWinery = (row.winery || "").trim();
            const filterWinery = activeFilters.winery.trim();
            if (rowWinery.toLowerCase() !== filterWinery.toLowerCase()) {
                return false;
            }
        }
        
        // Supplier filter - case-insensitive matching con trim
        if (activeFilters.supplier) {
            const rowSupplier = (row.supplier || "").trim();
            const filterSupplier = activeFilters.supplier.trim();
            if (rowSupplier.toLowerCase() !== filterSupplier.toLowerCase()) {
                return false;
            }
        }
        
        // Search filter
        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            const nameMatch = row.name?.toLowerCase().includes(query);
            const wineryMatch = row.winery?.toLowerCase().includes(query);
            const supplierMatch = row.supplier?.toLowerCase().includes(query);
            const vintageMatch = String(row.vintage).includes(query);
            
            if (!nameMatch && !wineryMatch && !supplierMatch && !vintageMatch) {
                return false;
            }
        }
        
        return true;
    });
    
    currentPage = 1;
    renderTable();
    updatePagination();
    updateMeta();
}

// Render table
function renderTable() {
    console.log('[RENDER_TABLE] ===== INIZIO RENDER_TABLE =====');
    const tbody = document.getElementById('table-body');
    
    if (!tbody) {
        console.error('[RENDER_TABLE] ERRORE: tbody non trovato!');
        return;
    }
    
    console.log('[RENDER_TABLE] filteredData.length:', filteredData.length);
    console.log('[RENDER_TABLE] currentPage:', currentPage);
    
    if (filteredData.length === 0) {
        console.log('[RENDER_TABLE] Nessun dato, mostro empty state');
        tbody.innerHTML = '<tr><td colspan="8" class="empty-state">Nessun risultato trovato</td></tr>';
        return;
    }
    
    const start = (currentPage - 1) * CONFIG.pageSize;
    const end = start + CONFIG.pageSize;
    const pageData = filteredData.slice(start, end);
    
    console.log('[RENDER_TABLE] Rendering', pageData.length, 'righe');
    
    tbody.innerHTML = pageData.map((row, index) => {
        const wineName = escapeHtml(row.name || '');
        const wineId = `wine-${index}-${Date.now()}`;
        const isExpanded = false; // Stato iniziale non espanso
        
        // Debug: verifica i dati ricevuti per le prime 3 righe
        if (index < 3) {
            console.log(`[RENDER_TABLE] Riga ${index} - dati completi:`, {
                name: row.name,
                winery: row.winery,
                supplier: row.supplier,
                vintage: row.vintage,
                qty: row.qty,
                price: row.price,
                'row.winery type': typeof row.winery,
                'row.supplier type': typeof row.supplier,
                'row.vintage type': typeof row.vintage
            });
        }
        
        // IMPORTANTE: Usa winery e supplier, NON vintage
        // Se winery è vuoto/null/undefined, mostra '-' invece di vintage
        const wineryDisplay = (row.winery && row.winery !== '-' && row.winery !== 'null' && row.winery !== 'None') 
            ? escapeHtml(String(row.winery)) 
            : '-';
        const supplierDisplay = (row.supplier && row.supplier !== '-' && row.supplier !== 'null' && row.supplier !== 'None') 
            ? escapeHtml(String(row.supplier)) 
            : '-';
        
        // Debug per verificare cosa viene renderizzato
        if (index < 3) {
            console.log(`[RENDER_TABLE] Riga ${index} - valori renderizzati:`, {
                wineryDisplay: wineryDisplay,
                supplierDisplay: supplierDisplay,
                'NOT using vintage': row.vintage
            });
        }
        
        // FORZATURA: Assicurati che NON venga mai usato vintage nella colonna Cantina
        // Se wineryDisplay è '-', NON usare vintage come fallback
        const cantinaValue = wineryDisplay; // SEMPRE usa wineryDisplay, mai vintage
        
        // LOG FORZATO per debug - sempre eseguito per le prime 3 righe
        if (index < 3) {
            console.error(`[DEBUG RIGA ${index}] cantinaValue="${cantinaValue}", wineryDisplay="${wineryDisplay}", row.winery="${row.winery}", row.vintage=${row.vintage}`);
        }
        
        return `
        <tr class="wine-row" data-wine-id="${wineId}" data-expanded="false">
            <td class="wine-name-cell clickable-cell">${wineName || '-'}</td>
            <td class="clickable-cell" data-field="cantina" data-debug-winery="${row.winery}" data-debug-vintage="${row.vintage}">${cantinaValue}</td>
            <td class="clickable-cell">${row.qty || 0}</td>
            <td class="clickable-cell">€${(row.price || 0).toFixed(2)}</td>
            <td class="clickable-cell" data-field="fornitore">${supplierDisplay}</td>
            <td class="clickable-cell">${row.critical || row.qty <= 3 ? '<span class="critical-badge">Critica</span>' : '-'}</td>
            <td class="chart-action-cell">
                <button class="chart-btn" data-wine-name="${wineName}" title="Visualizza grafico movimenti" type="button" onclick="event.stopPropagation(); showMovementsChart('${wineName}');">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M3 3V21H21" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M7 16L12 11L16 15L21 10" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M21 10V4H15" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </button>
            </td>
            <td class="actions-cell">
                <button class="edit-btn" data-wine-id="${row.id}" onclick="event.stopPropagation(); openEditModal(${row.id});" title="Modifica vino">
                    ✏️ Modifica
                </button>
            </td>
        </tr>
        <tr class="wine-details-row" data-wine-id="${wineId}" style="display: none;">
            <td colspan="8" class="wine-details-cell">
                <div class="wine-details-content">
                    <h3>Dettagli Vino: ${wineName}</h3>
                    <div class="wine-details-grid">
                        <div class="detail-item">
                            <span class="detail-label">Nome:</span>
                            <span class="detail-value">${wineName || '-'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Cantina:</span>
                            <span class="detail-value">${escapeHtml(row.winery || '-')}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Annata:</span>
                            <span class="detail-value">${row.vintage || '-'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Quantità:</span>
                            <span class="detail-value">${row.qty || 0} bottiglie</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Prezzo vendita:</span>
                            <span class="detail-value">€${(row.price || 0).toFixed(2)}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Fornitore:</span>
                            <span class="detail-value">${escapeHtml(row.supplier || '-')}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Tipologia:</span>
                            <span class="detail-value">${escapeHtml(row.type || '-')}</span>
                        </div>
                        ${row.grape_variety ? `<div class="detail-item">
                            <span class="detail-label">Uvaggio:</span>
                            <span class="detail-value">${escapeHtml(row.grape_variety)}</span>
                        </div>` : ''}
                        ${row.region ? `<div class="detail-item">
                            <span class="detail-label">Regione:</span>
                            <span class="detail-value">${escapeHtml(row.region)}</span>
                        </div>` : ''}
                        ${row.country ? `<div class="detail-item">
                            <span class="detail-label">Paese:</span>
                            <span class="detail-value">${escapeHtml(row.country)}</span>
                        </div>` : ''}
                        ${row.classification ? `<div class="detail-item">
                            <span class="detail-label">Classificazione:</span>
                            <span class="detail-value">${escapeHtml(row.classification)}</span>
                        </div>` : ''}
                        ${row.cost_price ? `<div class="detail-item">
                            <span class="detail-label">Prezzo costo:</span>
                            <span class="detail-value">€${row.cost_price.toFixed(2)}</span>
                        </div>` : ''}
                        ${row.alcohol_content ? `<div class="detail-item">
                            <span class="detail-label">Gradazione:</span>
                            <span class="detail-value">${row.alcohol_content}%</span>
                        </div>` : ''}
                        ${row.description ? `<div class="detail-item full-width">
                            <span class="detail-label">Descrizione:</span>
                            <span class="detail-value">${escapeHtml(row.description)}</span>
                        </div>` : ''}
                        ${row.notes ? `<div class="detail-item full-width">
                            <span class="detail-label">Note:</span>
                            <span class="detail-value">${escapeHtml(row.notes)}</span>
                        </div>` : ''}
                    </div>
                </div>
            </td>
        </tr>
        `;
    }).join('');
    
    // Debug: verifica che i pulsanti siano stati creati
    const buttons = document.querySelectorAll('.chart-btn');
    console.log('[RENDER_TABLE] Pulsanti trovati:', buttons.length);
    
    // Aggiungi event listener per click sulle righe vino (per espansione)
    document.querySelectorAll('.wine-row').forEach(row => {
        row.style.cursor = 'pointer';
        row.addEventListener('click', (e) => {
            // Non espandere se il click è sul pulsante grafico
            if (e.target.closest('.chart-btn')) {
                return;
            }
            
            const wineId = row.dataset.wineId;
            const isExpanded = row.dataset.expanded === 'true';
            const detailsRow = document.querySelector(`.wine-details-row[data-wine-id="${wineId}"]`);
            
            if (detailsRow) {
                if (isExpanded) {
                    // Chiudi
                    detailsRow.style.display = 'none';
                    row.dataset.expanded = 'false';
                    row.classList.remove('expanded');
                } else {
                    // Chiudi tutte le altre righe espanse
                    document.querySelectorAll('.wine-row[data-expanded="true"]').forEach(expRow => {
                        const expWineId = expRow.dataset.wineId;
                        const expDetailsRow = document.querySelector(`.wine-details-row[data-wine-id="${expWineId}"]`);
                        if (expDetailsRow) {
                            expDetailsRow.style.display = 'none';
                            expRow.dataset.expanded = 'false';
                            expRow.classList.remove('expanded');
                        }
                    });
                    
                    // Apri questa riga
                    detailsRow.style.display = 'table-row';
                    row.dataset.expanded = 'true';
                    row.classList.add('expanded');
                }
            }
        });
    });
}

// Update pagination
function updatePagination() {
    const totalPages = Math.ceil(filteredData.length / CONFIG.pageSize);
    const pagination = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Previous button
    html += `<button class="pagination-btn" ${currentPage === 1 ? 'disabled' : ''} onclick="goToPage(${currentPage - 1})">Precedente</button>`;
    
    // Page numbers
    const maxVisible = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    
    if (endPage - startPage < maxVisible - 1) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }
    
    if (startPage > 1) {
        html += `<button class="pagination-btn" onclick="goToPage(1)">1</button>`;
        if (startPage > 2) {
            html += `<span class="pagination-info">...</span>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="pagination-btn ${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            html += `<span class="pagination-info">...</span>`;
        }
        html += `<button class="pagination-btn" onclick="goToPage(${totalPages})">${totalPages}</button>`;
    }
    
    // Next button
    html += `<button class="pagination-btn" ${currentPage === totalPages ? 'disabled' : ''} onclick="goToPage(${currentPage + 1})">Successiva</button>`;
    
    // Info
    html += `<span class="pagination-info">Pagina ${currentPage} di ${totalPages}</span>`;
    
    pagination.innerHTML = html;
}

// Go to page
function goToPage(page) {
    const totalPages = Math.ceil(filteredData.length / CONFIG.pageSize);
    if (page < 1 || page > totalPages) return;
    
    currentPage = page;
    renderTable();
    updatePagination();
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Setup CSV download
function setupCsvDownload(token) {
    const baseUrl = CONFIG.apiBase || window.location.origin;
    const csvUrl = `${baseUrl}${CONFIG.endpointCsv}?token=${encodeURIComponent(token)}`;
    
    const downloadBtn = document.getElementById('download-csv');
    
    // Per token FAKE, genera CSV mock dal frontend
    if (token === "FAKE" || token === "fake") {
        downloadBtn.addEventListener('click', (e) => {
            e.preventDefault();
            // Generate mock CSV dai dati caricati
            const csv = generateMockCSV();
            downloadCSV(csv, 'inventario.csv');
        });
        downloadBtn.href = "#";
    } else {
        // Per token reali, usa l'endpoint del server
        downloadBtn.href = csvUrl;
        downloadBtn.addEventListener('click', (e) => {
            // Il download avverrà automaticamente tramite href
            // Nessun preventDefault necessario
            console.log("[VIEWER] Download CSV avviato:", csvUrl);
        });
    }
}

// Generate mock CSV (per sviluppo/test con token FAKE)
function generateMockCSV() {
    // Usa i dati filtrati se disponibili, altrimenti tutti i dati
    const dataToExport = filteredData.length > 0 ? filteredData : allData.rows;
    
    const headers = ['Nome', 'Cantina', 'Fornitore', 'Annata', 'Quantità', 'Prezzo (€)', 'Tipo', 'Scorta Critica'];
    const rows = dataToExport.map(row => [
        row.name || '',
        row.winery || '',
        row.supplier || '',
        row.vintage || '',
        row.qty || 0,
        row.price || 0.0,
        row.type || '',
        row.critical ? 'Sì' : 'No'
    ]);
    
    const csvRows = [headers.join(',')];
    rows.forEach(row => {
        csvRows.push(row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','));
    });
    
    return csvRows.join('\n');
}

// Download CSV
function downloadCSV(content, filename) {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close modal
function closeMovementsModal() {
    const modal = document.getElementById('movements-modal');
    modal.classList.add('hidden');
}

// Show movements chart modal
async function showMovementsChart(wineName) {
    const token = getTokenFromURL();
    if (!token) {
        alert('Token non valido');
        return;
    }
    
    const modal = document.getElementById('movements-modal');
    const modalTitle = document.getElementById('modal-wine-name');
    const chartContainer = document.getElementById('movements-chart-container');
    
    modalTitle.textContent = `Movimenti: ${wineName}`;
    modal.classList.remove('hidden');
    
    // Mostra loading
    chartContainer.innerHTML = '<div class="loading">Caricamento movimenti...</div>';
    
    try {
        const baseUrl = CONFIG.apiBase || window.location.origin;
        const url = `${baseUrl}${CONFIG.endpointMovements}?token=${encodeURIComponent(token)}&wine_name=${encodeURIComponent(wineName)}`;
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        const movements = data.movements || [];
        
        if (movements.length === 0) {
            // Mostra grafico vuoto anche senza movimenti
            chartContainer.innerHTML = '<canvas id="movements-chart"></canvas>';
            const ctx = document.getElementById('movements-chart').getContext('2d');
            
            if (movementsChart) {
                movementsChart.destroy();
            }
            
            movementsChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: []
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Nessun movimento registrato per questo vino',
                            font: {
                                size: 14,
                                color: '#666'
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
            return;
        }
        
        // Prepara dati per grafico
        const labels = [];
        const consumiData = [];
        const rifornimentiData = [];
        const quantitaData = [];
        
        movements.forEach(mov => {
            const date = new Date(mov.date);
            labels.push(date.toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit', year: 'numeric' }));
            
            if (mov.type === 'consumo') {
                consumiData.push(Math.abs(mov.quantity_change));
                rifornimentiData.push(null);
            } else {
                consumiData.push(null);
                rifornimentiData.push(mov.quantity_change);
            }
            
            quantitaData.push(mov.quantity_after);
        });
        
        // Crea grafico
        chartContainer.innerHTML = '<canvas id="movements-chart"></canvas>';
        const ctx = document.getElementById('movements-chart').getContext('2d');
        
        // Distruggi grafico precedente se esiste
        if (movementsChart) {
            movementsChart.destroy();
        }
        
        movementsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Consumi',
                        data: consumiData,
                        borderColor: '#9a182e',
                        backgroundColor: 'rgba(154, 24, 46, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Rifornimenti',
                        data: rifornimentiData,
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Quantità Stock',
                        data: quantitaData,
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        tension: 0.4,
                        fill: false,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    title: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Bottiglie (Consumi/Rifornimenti)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Stock'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
        
    } catch (error) {
        console.error('[VIEWER] Errore caricamento movimenti:', error);
        chartContainer.innerHTML = `<div class="error-state">Errore nel caricamento dei movimenti: ${error.message}</div>`;
    }
}

// Filter section toggle
document.addEventListener('DOMContentLoaded', () => {
    // Setup filter section toggles
    document.querySelectorAll('.filter-header').forEach(header => {
        header.addEventListener('click', () => {
            const filterType = header.dataset.filter;
            const content = document.getElementById(`filter-${filterType}`);
            const icon = header.querySelector('.filter-icon');
            
            content.classList.toggle('hidden');
            icon.classList.toggle('expanded');
        });
    });
    
    // Setup search
    const searchInput = document.getElementById('search-input');
    let searchTimeout;
    
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchQuery = e.target.value.trim();
            applyFilters();
        }, 300); // Debounce 300ms
    });
    
    // Event listeners per modal
    const modal = document.getElementById('movements-modal');
    const closeBtn = document.getElementById('modal-close');
    
    if (closeBtn) {
        closeBtn.addEventListener('click', closeMovementsModal);
    }
    
    // Chiudi modal cliccando fuori
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeMovementsModal();
            }
        });
    }
    
    // Chiudi con ESC
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal && !modal.classList.contains('hidden')) {
            closeMovementsModal();
        }
    });
    
    // Load data
    loadData();
    
    // Setup edit modal
    const editModal = document.getElementById('edit-wine-modal');
    const editCloseBtn = document.getElementById('edit-modal-close');
    const editCancelBtn = document.getElementById('edit-cancel-btn');
    const editForm = document.getElementById('edit-wine-form');
    
    if (editCloseBtn) {
        editCloseBtn.addEventListener('click', closeEditModal);
    }
    
    if (editCancelBtn) {
        editCancelBtn.addEventListener('click', closeEditModal);
    }
    
    if (editModal) {
        editModal.addEventListener('click', (e) => {
            if (e.target === editModal) {
                closeEditModal();
            }
        });
    }
    
    if (editForm) {
        editForm.addEventListener('submit', saveWineChanges);
    }
    
    // Chiudi con ESC
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && editModal && !editModal.classList.contains('hidden')) {
            closeEditModal();
        }
    });
});

// ===== FUNZIONI EDITING VINO =====

// Trova vino per ID nei dati caricati
function findWineById(wineId) {
    return allData.rows.find(wine => wine.id === wineId);
}

// Apri modal editing con dati vino
async function openEditModal(wineId) {
    const wine = findWineById(wineId);
    
    if (!wine) {
        showNotification('Vino non trovato', 'error');
        return;
    }
    
    // Popola form con dati vino
    document.getElementById('edit-wine-id').value = wineId;
    document.getElementById('edit-name').value = wine.name || '';
    document.getElementById('edit-producer').value = wine.winery && wine.winery !== '-' ? wine.winery : '';
    document.getElementById('edit-supplier').value = wine.supplier && wine.supplier !== '-' ? wine.supplier : '';
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

// Chiudi modal editing
function closeEditModal() {
    document.getElementById('edit-wine-modal').classList.add('hidden');
    document.getElementById('edit-wine-form').reset();
}

// Salva modifiche vino
async function saveWineChanges(e) {
    e.preventDefault();
    
    const token = getTokenFromURL();
    if (!token) {
        showNotification('Token non valido', 'error');
        return;
    }
    
    const wineId = parseInt(document.getElementById('edit-wine-id').value);
    if (!wineId) {
        showNotification('ID vino non valido', 'error');
        return;
    }
    
    // Raccogli tutti i campi modificati
    const fields = {
        producer: document.getElementById('edit-producer').value.trim(),
        supplier: document.getElementById('edit-supplier').value.trim(),
        vintage: document.getElementById('edit-vintage').value.trim(),
        quantity: document.getElementById('edit-quantity').value.trim(),
        selling_price: document.getElementById('edit-selling-price').value.trim(),
        cost_price: document.getElementById('edit-cost-price').value.trim(),
        wine_type: document.getElementById('edit-wine-type').value.trim(),
        grape_variety: document.getElementById('edit-grape-variety').value.trim(),
        region: document.getElementById('edit-region').value.trim(),
        country: document.getElementById('edit-country').value.trim(),
        classification: document.getElementById('edit-classification').value.trim(),
        alcohol_content: document.getElementById('edit-alcohol-content').value.trim(),
        description: document.getElementById('edit-description').value.trim(),
        notes: document.getElementById('edit-notes').value.trim(),
        min_quantity: document.getElementById('edit-min-quantity').value.trim()
    };
    
    // Mostra loading
    const submitBtn = document.getElementById('edit-save-btn');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Salvataggio...';
    
    try {
        // Invia modifiche campo per campo
        const updates = [];
        for (const [field, value] of Object.entries(fields)) {
            // Mappa field name dal form al nome campo database
            const fieldMapping = {
                'producer': 'producer',
                'supplier': 'supplier',
                'vintage': 'vintage',
                'quantity': 'quantity',
                'selling_price': 'selling_price',
                'cost_price': 'cost_price',
                'wine_type': 'wine_type',
                'grape_variety': 'grape_variety',
                'region': 'region',
                'country': 'country',
                'classification': 'classification',
                'alcohol_content': 'alcohol_content',
                'description': 'description',
                'notes': 'notes',
                'min_quantity': 'min_quantity'
            };
            
            const dbField = fieldMapping[field];
            if (!dbField) {
                console.warn(`Campo sconosciuto: ${field}`);
                continue;
            }
            
            // Campi supportati dall'endpoint processor:
            // producer, supplier, vintage, grape_variety, classification,
            // selling_price, cost_price, alcohol_content, description, notes
            // NOTA: quantity e wine_type NON sono supportati dall'endpoint attuale
            
            if (field === 'quantity') {
                // Quantity dovrebbe essere gestita tramite movimenti, non update diretto
                console.warn('Campo quantity non supportato tramite update-wine-field. Usa movimenti per modificare quantità.');
                showNotification('Nota: La quantità deve essere modificata tramite movimenti (consumi/rifornimenti)', 'error');
                continue;
            }
            
            if (field === 'wine_type') {
                // Wine_type non è supportato dall'endpoint attuale
                console.warn('Campo wine_type non supportato dall\'endpoint update-wine-field');
                continue;
            }
            
            if (field === 'min_quantity') {
                // Min_quantity non è supportato dall'endpoint attuale
                console.warn('Campo min_quantity non supportato dall\'endpoint update-wine-field');
                continue;
            }
            
            // Skip campi vuoti per alcuni campi numerici obbligatori
            if (field === 'selling_price' || field === 'vintage') {
                // Campi numerici - invia solo se non vuoto
                if (value !== '' && value !== null) {
                    updates.push(updateWineField(token, wineId, dbField, value));
                }
            } else {
                // Campi opzionali - invia anche se vuoto per pulire campo
                updates.push(updateWineField(token, wineId, dbField, value || null));
            }
        }
        
        if (updates.length === 0) {
            showNotification('Nessuna modifica da salvare', 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            return;
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
        showNotification('Errore durante il salvataggio: ' + (error.message || 'Errore sconosciuto'), 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

// Chiamata API per aggiornare campo vino
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
        const errorData = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
        throw new Error(errorData.detail || 'Errore aggiornamento campo');
    }
    
    return await response.json();
}

// Mostra notifica temporanea
function showNotification(message, type = 'success') {
    // Rimuovi notifiche esistenti
    const existing = document.querySelector('.notification');
    if (existing) {
        existing.remove();
    }
    
    // Crea notifica
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Rimuovi dopo 3 secondi
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

