/* ============================================
   Digital Footprint Investigator - Main Script
   ============================================ */

// ---------- TOOL METADATA ----------
const TOOL_META = {
    // Active tools
    'port-scan':          { name: 'Port Scanning',        type: 'active',  label: 'Target host / IP', hint: 'Example: 192.168.1.1 or example.com' },
    'dns-enum':           { name: 'DNS Enumeration',      type: 'active',  label: 'Domain',           hint: 'Example: example.com' },
    'subdomain-enum':     { name: 'Subdomain Enumeration',type: 'active',  label: 'Domain',           hint: 'Example: example.com' },
    'whois':              { name: 'WHOIS Lookup',         type: 'active',  label: 'Domain',           hint: 'Example: example.com' },
    'dir-brute':          { name: 'Directory Bruteforce', type: 'active',  label: 'URL',              hint: 'Example: https://example.com' },
    'web-crawler':        { name: 'Web Crawler',          type: 'active',  label: 'URL',              hint: 'Example: https://example.com' },
    'ssl-scan':           { name: 'SSL / TLS Scanner',    type: 'active',  label: 'Host',             hint: 'Example: example.com:443' },
    'banner-grab':        { name: 'Banner Grabbing',      type: 'active',  label: 'Host : Port',      hint: 'Example: example.com:80' },

    // Passive tools
    'authentication':     { name: 'Authentication',       type: 'passive', label: 'API service name', hint: 'Configure API keys for external services.' },
    'username-lookup':    { name: 'Username Lookup',      type: 'passive', label: 'Username',         hint: 'Example: john_doe' },
    'email-investigation':{ name: 'Email Investigation',  type: 'passive', label: 'Email address',    hint: 'Example: user@example.com' },
    'domain-investigation':{ name: 'Domain Investigation',type: 'passive', label: 'Domain',           hint: 'Example: example.com' },
    'ip-investigation':   { name: 'IP Investigation',     type: 'passive', label: 'IP address',       hint: 'Example: 8.8.8.8' },
    'phone-investigation':{ name: 'Phone Investigation',  type: 'passive', label: 'Phone number',     hint: 'Include country code, e.g. +1 202-555-0123' },
    'metadata-extraction':{ name: 'Metadata Extraction',  type: 'passive', label: 'File URL or path', hint: 'Supports images, PDFs, Office docs.' },
    'website-analysis':   { name: 'Website Analysis',     type: 'passive', label: 'URL',              hint: 'Example: https://example.com' },
    'social-media':       { name: 'Social Media Search',  type: 'passive', label: 'Name or handle',   hint: 'Example: john_doe or "John Doe"' },
    'breach-check':       { name: 'Data Breach Check',    type: 'passive', label: 'Email / username', hint: 'Searches known breach databases.' },
    'reverse-image':      { name: 'Reverse Image Search', type: 'passive', label: 'Image URL',        hint: 'Example: https://example.com/photo.jpg' },
    'google-dorking':     { name: 'Google Dorking',       type: 'passive', label: 'Search query',     hint: 'Example: site:example.com filetype:pdf' },
    'public-records':     { name: 'Public Records',       type: 'passive', label: 'Name or entity',   hint: 'Searches public registries and filings.' },
    'dark-web':           { name: 'Dark Web Monitor',     type: 'passive', label: 'Keyword / target', hint: 'Searches dark web indexes for mentions.' }
};

// ---------- STATE ----------
const state = {
    results: [],
    currentTool: null
};

// ---------- DOM ----------
const $ = (id) => document.getElementById(id);
const $$ = (selector) => document.querySelectorAll(selector);

// ---------- TAB NAVIGATION ----------
function initTabs() {
    $$('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.dataset.tab;
            $$('.tab-btn').forEach(b => b.classList.remove('active'));
            $$('.tab-panel').forEach(p => p.classList.remove('active'));
            btn.classList.add('active');
            $(`tab-${target}`).classList.add('active');
        });
    });
}

// ---------- TOOL CARDS ----------
function initToolCards() {
    $$('.tool-card').forEach(card => {
        card.addEventListener('click', () => {
            const toolId = card.dataset.tool;
            openToolModal(toolId);
        });
    });
}

// ---------- MODAL ----------
function openToolModal(toolId) {
    const meta = TOOL_META[toolId];
    if (!meta) return;

    state.currentTool = toolId;
    $('modalTitle').textContent = meta.name;
    $('modalLabel').textContent = meta.label + ':';
    $('modalInput').placeholder = 'Enter ' + meta.label.toLowerCase() + '...';
    $('modalInput').value = '';
    $('modalHint').textContent = meta.hint || '';
    $('modalOverlay').classList.add('show');
    setTimeout(() => $('modalInput').focus(), 100);
}

function closeToolModal() {
    $('modalOverlay').classList.remove('show');
    state.currentTool = null;
}

function initModal() {
    $('modalClose').addEventListener('click', closeToolModal);
    $('modalCancel').addEventListener('click', closeToolModal);
    $('modalOverlay').addEventListener('click', (e) => {
        if (e.target.id === 'modalOverlay') closeToolModal();
    });
    $('modalRun').addEventListener('click', runInvestigation);
    $('modalInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') runInvestigation();
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && $('modalOverlay').classList.contains('show')) {
            closeToolModal();
        }
    });
}

// ---------- RUN INVESTIGATION (UI stub) ----------
function runInvestigation() {
    const toolId = state.currentTool;
    const target = $('modalInput').value.trim();

    if (!toolId) return;
    if (!target) {
        showToast('Please enter a target value.');
        return;
    }

    const meta = TOOL_META[toolId];
    const result = {
        id: Date.now(),
        toolId,
        toolName: meta.name,
        type: meta.type,
        target,
        timestamp: new Date().toISOString(),
        status: 'queued'
    };

    state.results.unshift(result);
    renderResults();
    closeToolModal();
    showToast(`${meta.name} queued for "${target}". Backend integration pending.`);

    // Auto-switch to results tab after a short delay
    setTimeout(() => {
        $$('.tab-btn').forEach(b => b.classList.remove('active'));
        $$('.tab-panel').forEach(p => p.classList.remove('active'));
        document.querySelector('[data-tab="results"]').classList.add('active');
        $('tab-results').classList.add('active');
    }, 400);
}

// ---------- RESULTS RENDERING ----------
function renderResults(filter = '') {
    const container = $('resultsContainer');
    const filtered = filter
        ? state.results.filter(r =>
            r.toolName.toLowerCase().includes(filter.toLowerCase()) ||
            r.target.toLowerCase().includes(filter.toLowerCase()))
        : state.results;

    if (filtered.length === 0) {
        container.innerHTML = state.results.length === 0
            ? `<div class="results-empty">
                <div class="empty-icon">&#128269;</div>
                <h3>No results yet</h3>
                <p>Run a tool from the <strong>Active</strong> or <strong>Passive</strong> tab to see results here.</p>
              </div>`
            : `<div class="results-empty">
                <div class="empty-icon">&#128269;</div>
                <h3>No matches</h3>
                <p>No results match your filter.</p>
              </div>`;
        return;
    }

    container.innerHTML = filtered.map(r => `
        <div class="result-item ${r.type}-type">
            <div class="result-header">
                <span class="result-title">${escapeHtml(r.toolName)}</span>
                <span class="result-badge ${r.type}">${r.type}</span>
            </div>
            <div class="result-target">${escapeHtml(r.target)}</div>
            <div class="result-meta">Status: ${r.status} &middot; ${formatTime(r.timestamp)}</div>
        </div>
    `).join('');
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function formatTime(iso) {
    const d = new Date(iso);
    return d.toLocaleString();
}

// ---------- RESULTS TOOLBAR ----------
function initResultsToolbar() {
    $('resultsSearch').addEventListener('input', (e) => {
        renderResults(e.target.value);
    });

    $('exportBtn').addEventListener('click', () => {
        if (state.results.length === 0) {
            showToast('No results to export.');
            return;
        }
        const blob = new Blob([JSON.stringify(state.results, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `dfi-results-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
        showToast('Results exported.');
    });

    $('clearBtn').addEventListener('click', () => {
        if (state.results.length === 0) return;
        if (confirm('Clear all results? This cannot be undone.')) {
            state.results = [];
            renderResults();
            showToast('Results cleared.');
        }
    });
}

// ---------- TOAST ----------
let toastTimer;
function showToast(message) {
    const toast = $('toast');
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 3000);
}

// ---------- INIT ----------
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initToolCards();
    initModal();
    initResultsToolbar();
});
