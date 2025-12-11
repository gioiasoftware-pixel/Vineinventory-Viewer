// Configuration
// Il viewer gestisce tutto autonomamente - chiama direttamente il database
let CONFIG = {
    apiBase: "",  // Vuoto = stesso dominio del viewer (endpoint locale)
    endpointSnapshot: "/api/inventory/snapshot",
    endpointCsv: "/api/inventory/export.csv",
    pageSize: 50
};

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
    
    updateMeta();
    renderFilters();
    renderTable();
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
        `<tr><td colspan="5" class="empty-state">${message}</td></tr>`;
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
    container.innerHTML = '';

    const sortedFacets = Object.entries(facets)
        .sort((a, b) => b[1] - a[1]); // Sort by count desc

    sortedFacets.forEach(([key, count]) => {
        const item = document.createElement('div');
        item.className = 'filter-item';
        if (activeFilters[filterType] === key) {
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
    if (activeFilters[filterType] === value) {
        activeFilters[filterType] = null;
    } else {
        activeFilters[filterType] = value;
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
        
        // Vintage filter
        if (activeFilters.vintage && String(row.vintage) !== String(activeFilters.vintage)) {
            return false;
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
    const tbody = document.getElementById('table-body');
    
    if (filteredData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-state">Nessun risultato trovato</td></tr>';
        return;
    }
    
    const start = (currentPage - 1) * CONFIG.pageSize;
    const end = start + CONFIG.pageSize;
    const pageData = filteredData.slice(start, end);
    
    tbody.innerHTML = pageData.map(row => `
        <tr>
            <td>${escapeHtml(row.name || '-')}</td>
            <td>${row.vintage || '-'}</td>
            <td>${row.qty || 0}</td>
            <td>€${(row.price || 0).toFixed(2)}</td>
            <td>${row.critical || row.qty <= 3 ? '<span class="critical-badge">Critica</span>' : '-'}</td>
        </tr>
    `).join('');
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
    downloadBtn.href = csvUrl;
    
    if (token === "FAKE" || token === "fake") {
        downloadBtn.addEventListener('click', (e) => {
            e.preventDefault();
            // Generate mock CSV
            const csv = generateMockCSV();
            downloadCSV(csv, 'inventario.csv');
        });
    }
}

// Generate mock CSV
function generateMockCSV() {
    const headers = ['Nome', 'Annata', 'Quantità', 'Prezzo (€)', 'Cantina', 'Tipo'];
    const rows = allData.rows.map(row => [
        row.name || '',
        row.vintage || '',
        row.qty || 0,
        row.price || 0,
        row.winery || '',
        row.type || ''
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
    
    // Load data
    loadData();
});

