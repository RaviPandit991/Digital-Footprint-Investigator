/* ============================================
   Digital Footprint Investigator - Frontend
   ============================================ */

const API_BASE = (location.protocol === "file:") ? "http://localhost:5000" : "";

// ---------- TOOL METADATA ----------
const TOOL_META = {
    // Active tools
    'port-scan':          { name: 'Port Scanning',        type: 'active',  label: 'Target host / IP', hint: 'Example: 192.168.1.1 or example.com' },
    'dns-enum':           { name: 'DNS Enumeration',      type: 'active',  label: 'Domain',           hint: 'Example: example.com' },
    'subdomain-enum':     { name: 'Subdomain Enumeration',type: 'active',  label: 'Domain',           hint: 'Uses crt.sh certificate transparency logs.' },
    'whois':              { name: 'WHOIS Lookup',         type: 'active',  label: 'Domain',           hint: 'Example: example.com' },
    'dir-brute':          { name: 'Directory Bruteforce', type: 'active',  label: 'URL',              hint: 'Tests common paths. Example: https://example.com' },
    'web-crawler':        { name: 'Web Crawler',          type: 'active',  label: 'URL',              hint: 'Crawls up to 15 pages, depth 2.' },
    'ssl-scan':           { name: 'SSL / TLS Scanner',    type: 'active',  label: 'Host',             hint: 'Example: example.com or example.com:443' },
    'banner-grab':        { name: 'Banner Grabbing',      type: 'active',  label: 'Host : Port',      hint: 'Example: example.com:80' },

    // Passive tools
    'authentication':     { name: 'Authentication',       type: 'passive', label: '',                 hint: '', special: 'auth' },
    'username-lookup':    { name: 'Username Lookup',      type: 'passive', label: 'Username',         hint: 'Checks 40+ platforms.' },
    'email-investigation':{ name: 'Email Investigation',  type: 'passive', label: 'Email address',    hint: 'Syntax, MX, disposable check, Gravatar, HIBP.' },
    'domain-investigation':{ name: 'Domain Investigation',type: 'passive', label: 'Domain',           hint: 'WHOIS + DNS + reputation.' },
    'ip-investigation':   { name: 'IP Investigation',     type: 'passive', label: 'IP or hostname',   hint: 'Geolocation, ISP, ASN, abuse reports.' },
    'phone-investigation':{ name: 'Phone Investigation',  type: 'passive', label: 'Phone number',     hint: 'Include country code, e.g. +1 202-555-0123' },
    'metadata-extraction':{ name: 'Metadata Extraction',  type: 'passive', label: 'File URL or upload', hint: 'Images (EXIF/GPS) and PDFs.', special: 'file' },
    'website-analysis':   { name: 'Website Analysis',     type: 'passive', label: 'URL',              hint: 'Tech stack, headers, cookies, security.' },
    'social-media':       { name: 'Social Media Search',  type: 'passive', label: 'Name or handle',   hint: 'Aggregates search across platforms.' },
    'breach-check':       { name: 'Data Breach Check',    type: 'passive', label: 'Email or password',hint: 'Passwords via k-anonymity (no key). Emails require HIBP key.' },
    'reverse-image':      { name: 'Reverse Image Search', type: 'passive', label: 'Image URL',        hint: 'Generates search URLs for major engines.' },
    'google-dorking':     { name: 'Google Dorking',       type: 'passive', label: 'Domain or query',  hint: 'Generates 18 dork templates for a domain.' },
    'public-records':     { name: 'Public Records',       type: 'passive', label: 'Name or entity',   hint: 'Multi-jurisdiction registry search links.' },
    'dark-web':           { name: 'Dark Web Monitor',     type: 'passive', label: 'Keyword',          hint: 'Searches Ahmia.fi Tor index.' }
};

// ---------- STATE ----------
const state = {
    results: [],
    currentTool: null,
    running: false,
};

// ---------- DOM ----------
const $ = (id) => document.getElementById(id);
const $$ = (selector) => document.querySelectorAll(selector);

// ---------- UTILITIES ----------
function escapeHtml(str) {
    return String(str ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function formatTime(iso) {
    return new Date(iso).toLocaleString();
}

// ---------- TAB NAVIGATION ----------
function initTabs() {
    $$('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
}

function switchTab(target) {
    $$('.tab-btn').forEach(b => b.classList.remove('active'));
    $$('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelector(`[data-tab="${target}"]`).classList.add('active');
    $(`tab-${target}`).classList.add('active');
}

// ---------- TOOL CARDS ----------
function initToolCards() {
    $$('.tool-card').forEach(card => {
        card.addEventListener('click', () => openToolModal(card.dataset.tool));
    });
}

// ---------- MODAL: DYNAMIC BODY ----------
async function openToolModal(toolId) {
    const meta = TOOL_META[toolId];
    if (!meta) return;

    state.currentTool = toolId;
    $('modalTitle').textContent = meta.name;
    const body = $('modalBody');

    if (meta.special === 'auth') {
        // Load auth status and render key config UI
        body.innerHTML = '<p class="modal-hint">Loading API key status...</p>';
        $('modalOverlay').classList.add('show');
        try {
            const resp = await fetch(`${API_BASE}/api/auth/status`);
            const data = await resp.json();
            body.innerHTML = renderAuthForm(data.services);
            bindAuthForm();
        } catch (e) {
            body.innerHTML = `<p class="modal-error">Cannot reach backend: ${escapeHtml(e.message)}</p>`;
        }
        $('modalRun').textContent = 'Close';
        return;
    }

    if (meta.special === 'file') {
        body.innerHTML = `
            <label for="modalInput">${escapeHtml(meta.label)}:</label>
            <input type="text" id="modalInput" placeholder="Enter file URL..." />
            <div class="or-divider">OR</div>
            <label for="modalFile">Upload file:</label>
            <input type="file" id="modalFile" accept="image/*,.pdf" />
            <p class="modal-hint">${escapeHtml(meta.hint)}</p>
        `;
    } else {
        body.innerHTML = `
            <label for="modalInput">${escapeHtml(meta.label)}:</label>
            <input type="text" id="modalInput" placeholder="Enter ${escapeHtml(meta.label.toLowerCase())}..." />
            <p class="modal-hint">${escapeHtml(meta.hint || '')}</p>
        `;
    }

    $('modalRun').textContent = 'Run Investigation';
    $('modalOverlay').classList.add('show');
    setTimeout(() => $('modalInput')?.focus(), 100);
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
    $('modalRun').addEventListener('click', handleModalRun);
    $('modalOverlay').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.target.tagName === 'INPUT' && e.target.type !== 'file') {
            handleModalRun();
        }
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && $('modalOverlay').classList.contains('show')) {
            closeToolModal();
        }
    });
}

// ---------- AUTHENTICATION FORM ----------
function renderAuthForm(services) {
    const rows = Object.entries(services).map(([id, s]) => `
        <div class="auth-row" data-service="${id}">
            <div class="auth-info">
                <div class="auth-name">
                    ${escapeHtml(s.name)}
                    <span class="auth-status ${s.configured ? 'configured' : 'missing'}">
                        ${s.configured ? '&#10003; configured' : '&#9888; not set'}
                    </span>
                </div>
                <div class="auth-used-by">Used by: ${s.used_by.join(', ')}</div>
                <a href="${escapeHtml(s.signup)}" target="_blank" class="auth-signup">Get key &rarr;</a>
            </div>
            <div class="auth-actions">
                <input type="password" class="auth-key-input" placeholder="Paste key here..." />
                <button class="btn btn-primary btn-sm auth-save">Save</button>
            </div>
        </div>
    `).join('');
    return `<div class="auth-list">${rows}</div>`;
}

function bindAuthForm() {
    $$('.auth-save').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const row = e.target.closest('.auth-row');
            const service = row.dataset.service;
            const key = row.querySelector('.auth-key-input').value.trim();
            try {
                const resp = await fetch(`${API_BASE}/api/auth/update`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ service, key })
                });
                const data = await resp.json();
                if (data.error) {
                    showToast(data.error);
                } else {
                    showToast(data.summary || 'Key saved.');
                    // Refresh
                    const resp2 = await fetch(`${API_BASE}/api/auth/status`);
                    const status = await resp2.json();
                    $('modalBody').innerHTML = renderAuthForm(status.services);
                    bindAuthForm();
                }
            } catch (err) {
                showToast('Error: ' + err.message);
            }
        });
    });
}

// ---------- MAIN RUN HANDLER ----------
async function handleModalRun() {
    const toolId = state.currentTool;
    if (!toolId) return;

    const meta = TOOL_META[toolId];
    if (meta.special === 'auth') {
        closeToolModal();
        return;
    }

    const targetInput = $('modalInput');
    const target = targetInput ? targetInput.value.trim() : '';
    const fileInput = $('modalFile');
    const hasFile = fileInput && fileInput.files.length > 0;

    if (!target && !hasFile) {
        showToast('Please enter a target value.');
        return;
    }

    if (state.running) return;
    state.running = true;

    // Create placeholder result
    const result = {
        id: Date.now(),
        toolId,
        toolName: meta.name,
        type: meta.type,
        target: hasFile ? `[uploaded: ${fileInput.files[0].name}]` : target,
        timestamp: new Date().toISOString(),
        status: 'running',
        data: null,
        error: null
    };
    state.results.unshift(result);
    closeToolModal();
    switchTab('results');
    renderResults();
    showLoading(`Running ${meta.name}...`);

    try {
        let resp;
        if (hasFile) {
            const fd = new FormData();
            fd.append('file', fileInput.files[0]);
            resp = await fetch(`${API_BASE}/api/run/${toolId}`, { method: 'POST', body: fd });
        } else {
            resp = await fetch(`${API_BASE}/api/run/${toolId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target })
            });
        }
        const data = await resp.json();
        if (data.error) {
            result.status = 'error';
            result.error = data.error;
        } else {
            result.status = 'success';
            result.data = data;
        }
    } catch (err) {
        result.status = 'error';
        result.error = `Backend unreachable: ${err.message}. Is the Flask server running?`;
    } finally {
        state.running = false;
        hideLoading();
        renderResults();
    }
}

// ---------- LOADING OVERLAY ----------
function showLoading(text) {
    $('loadingText').textContent = text || 'Loading...';
    $('loadingOverlay').classList.add('show');
}
function hideLoading() {
    $('loadingOverlay').classList.remove('show');
}

// ---------- RESULT RENDERING ----------
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
                <p>Run a tool from the <strong>Active</strong> or <strong>Passive</strong> tab.</p>
              </div>`
            : `<div class="results-empty"><h3>No matches</h3></div>`;
        return;
    }

    container.innerHTML = filtered.map(r => renderResultItem(r)).join('');

    // Bind toggle handlers
    $$('.result-toggle').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const item = e.target.closest('.result-item');
            item.classList.toggle('expanded');
            btn.textContent = item.classList.contains('expanded') ? 'Collapse' : 'Expand';
        });
    });
    $$('.result-remove').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const id = parseInt(e.target.closest('.result-item').dataset.id);
            state.results = state.results.filter(r => r.id !== id);
            renderResults(filter);
        });
    });
}

function renderResultItem(r) {
    const statusBadge = {
        running: '<span class="result-badge running">Running...</span>',
        success: '<span class="result-badge success">Success</span>',
        error:   '<span class="result-badge error">Error</span>',
    }[r.status] || '';

    const summary = r.data?.summary || r.error || 'Processing...';
    const details = r.status === 'success'
        ? renderToolResult(r.toolId, r.data)
        : (r.status === 'error'
            ? `<pre class="result-error">${escapeHtml(r.error)}</pre>`
            : '<div class="result-loader">Processing...</div>');

    return `
    <div class="result-item ${r.type}-type ${r.status}" data-id="${r.id}">
        <div class="result-header">
            <div>
                <span class="result-title">${escapeHtml(r.toolName)}</span>
                <span class="result-badge type-${r.type}">${r.type}</span>
                ${statusBadge}
            </div>
            <div class="result-actions">
                ${r.status !== 'running' ? '<button class="btn-icon result-toggle">Expand</button>' : ''}
                <button class="btn-icon result-remove">&times;</button>
            </div>
        </div>
        <div class="result-target">${escapeHtml(r.target)}</div>
        <div class="result-summary">${escapeHtml(summary)}</div>
        <div class="result-details">${details}</div>
        <div class="result-meta">${formatTime(r.timestamp)}</div>
    </div>`;
}

// ---------- PER-TOOL RESULT RENDERERS ----------
function renderToolResult(toolId, data) {
    const renderers = {
        'port-scan':          renderPortScan,
        'dns-enum':           renderDnsEnum,
        'subdomain-enum':     renderSubdomains,
        'whois':              renderKeyValue,
        'dir-brute':          renderDirBrute,
        'web-crawler':        renderCrawler,
        'ssl-scan':           renderSslScan,
        'banner-grab':        renderBanner,
        'username-lookup':    renderUsernameLookup,
        'email-investigation': renderEmail,
        'domain-investigation': renderDomain,
        'ip-investigation':   renderIp,
        'phone-investigation':renderPhone,
        'metadata-extraction':renderMetadata,
        'website-analysis':   renderWebsite,
        'social-media':       renderSocial,
        'breach-check':       renderBreach,
        'reverse-image':      renderReverseImage,
        'google-dorking':     renderDorking,
        'public-records':     renderPublicRecords,
        'dark-web':           renderDarkWeb,
    };
    const fn = renderers[toolId] || renderGenericJson;
    try {
        return fn(data);
    } catch (e) {
        return renderGenericJson(data);
    }
}

function renderGenericJson(data) {
    return `<pre class="result-json">${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
}

function renderTable(rows) {
    return `<table class="result-table">${rows.map(r =>
        `<tr><td class="k">${escapeHtml(r[0])}</td><td>${r[1]}</td></tr>`
    ).join('')}</table>`;
}

function renderKeyValue(data) {
    const obj = data.whois || data;
    const rows = Object.entries(obj)
        .filter(([k]) => k !== 'summary' && k !== 'target')
        .map(([k, v]) => [k, escapeHtml(Array.isArray(v) ? v.join(', ') : (typeof v === 'object' ? JSON.stringify(v) : v))]);
    return renderTable(rows);
}

function renderPortScan(d) {
    if (!d.open_ports?.length) return '<p>No open ports found.</p>';
    const rows = d.open_ports.map(p =>
        `<tr><td>${p.port}</td><td>${escapeHtml(p.service)}</td></tr>`);
    return `<table class="result-table"><thead><tr><th>Port</th><th>Service</th></tr></thead>
        <tbody>${rows.join('')}</tbody></table>
        <p class="result-note">Scanned ${d.ports_scanned} ports on ${escapeHtml(d.ip)}</p>`;
}

function renderDnsEnum(d) {
    return Object.entries(d.records || {}).map(([type, vals]) =>
        `<div class="dns-block"><h4>${type}</h4>${
            vals.length ? '<ul>' + vals.map(v => `<li>${escapeHtml(v)}</li>`).join('') + '</ul>'
                        : '<p class="muted">No records</p>'
        }</div>`
    ).join('');
}

function renderSubdomains(d) {
    if (!d.subdomains?.length) return '<p>No subdomains found.</p>';
    return `<p><strong>${d.count}</strong> subdomains via ${escapeHtml(d.source)}</p>
        <ul class="chip-list">${d.subdomains.map(s =>
            `<li><a href="https://${escapeHtml(s)}" target="_blank">${escapeHtml(s)}</a></li>`).join('')}</ul>`;
}

function renderDirBrute(d) {
    if (!d.found?.length) return '<p>No interesting paths found.</p>';
    return `<table class="result-table"><thead><tr><th>Status</th><th>Path</th><th>Size</th></tr></thead><tbody>${
        d.found.map(f =>
            `<tr><td class="status-${Math.floor(f.status/100)}xx">${f.status}</td>
                 <td><a href="${escapeHtml(f.url)}" target="_blank">${escapeHtml(f.path)}</a></td>
                 <td>${escapeHtml(f.size)}</td></tr>`).join('')}</tbody></table>`;
}

function renderCrawler(d) {
    return `
        ${renderTable([
            ['Pages crawled', d.pages_crawled],
            ['Total links', d.total_links],
            ['Emails found', d.emails?.length || 0],
            ['External hosts', d.external_hosts?.length || 0],
            ['Forms', d.forms?.length || 0],
        ])}
        ${d.emails?.length ? `<h4>Emails</h4><ul class="chip-list">${d.emails.map(e => `<li>${escapeHtml(e)}</li>`).join('')}</ul>` : ''}
        ${d.external_hosts?.length ? `<h4>External Hosts</h4><ul class="chip-list">${d.external_hosts.slice(0, 30).map(h => `<li>${escapeHtml(h)}</li>`).join('')}</ul>` : ''}
    `;
}

function renderSslScan(d) {
    const rows = [
        ['Target', d.target], ['TLS version', d.tls_version],
        ['Cipher', d.cipher_suite], ['Bits', d.cipher_bits],
        ['Not before', d.not_before], ['Not after', d.not_after],
        ['Days until expiry', d.days_until_expiry],
        ['Subject', JSON.stringify(d.subject)], ['Issuer', JSON.stringify(d.issuer)],
        ['SAN', (d.san || []).join(', ')],
    ].map(([k, v]) => [k, escapeHtml(v)]);
    return renderTable(rows);
}

function renderBanner(d) {
    return renderTable([
        ['Target', escapeHtml(d.target)],
        ['Detected service', escapeHtml(d.detected_service)],
        ['Banner', `<pre class="result-json">${escapeHtml(d.banner)}</pre>`],
    ]);
}

function renderUsernameLookup(d) {
    if (!d.found_on?.length) return `<p>Username "<strong>${escapeHtml(d.username)}</strong>" not found on any checked platform.</p>`;
    return `<p>Found on <strong>${d.found_on.length}</strong> of ${d.platforms_checked} platforms:</p>
        <div class="platform-grid">${d.found_on.map(p =>
            `<a href="${escapeHtml(p.url)}" target="_blank" class="platform-link">
                <strong>${escapeHtml(p.platform)}</strong>
                <span class="muted">${escapeHtml(p.url)}</span>
            </a>`).join('')}</div>`;
}

function renderEmail(d) {
    const rows = [
        ['Email', escapeHtml(d.email)],
        ['Valid syntax', d.valid_syntax ? '&#10003; Yes' : '&#10005; No'],
        ['Deliverable (MX)', d.deliverable ? '&#10003; Yes' : '&#10005; No'],
        ['Disposable', d.disposable ? '&#9888; Yes' : '&#10003; No'],
        ['MX Records', escapeHtml((d.mx_records || []).join('<br>'))],
        ['Gravatar', d.gravatar?.has_avatar ? '&#10003; Has avatar' : 'No avatar'],
        ['Breaches', d.breaches?.available
            ? `${d.breaches.count} breach(es)`
            : `<span class="muted">${escapeHtml(d.breaches?.reason || 'Unknown')}</span>`],
    ];
    let out = renderTable(rows);
    if (d.breaches?.breaches?.length) {
        out += `<h4>Breach Details</h4><ul>${d.breaches.breaches.map(b =>
            `<li><strong>${escapeHtml(b.name)}</strong> (${escapeHtml(b.date)}) — ${escapeHtml((b.data_classes||[]).join(', '))}</li>`).join('')}</ul>`;
    }
    return out;
}

function renderDomain(d) {
    let out = '<h4>WHOIS</h4>' + (d.whois?.error ? `<p class="muted">${escapeHtml(d.whois.error)}</p>` : renderKeyValue({whois: d.whois}));
    out += '<h4>DNS</h4>' + (d.dns?.error ? `<p class="muted">${escapeHtml(d.dns.error)}</p>` : renderDnsEnum({records: d.dns}));
    out += '<h4>Reputation</h4>';
    if (d.reputation?.available) {
        out += renderTable([
            ['Reputation', d.reputation.reputation],
            ['Malicious', d.reputation.malicious],
            ['Suspicious', d.reputation.suspicious],
            ['Harmless', d.reputation.harmless],
            ['Categories', JSON.stringify(d.reputation.categories)],
        ].map(([k, v]) => [k, escapeHtml(v)]));
    } else {
        out += `<p class="muted">${escapeHtml(d.reputation?.reason || '')}</p>`;
    }
    return out;
}

function renderIp(d) {
    const g = d.geolocation || {};
    let out = renderTable([
        ['IP', d.ip], ['Reverse DNS', d.reverse_dns || '-'],
        ['Country', `${g.country || ''} (${g.country_code || ''})`],
        ['Region', g.region], ['City', g.city], ['Zip', g.zip],
        ['Coords', g.lat && g.lon ? `${g.lat}, ${g.lon}` : ''],
        ['Timezone', g.timezone], ['ISP', g.isp], ['Org', g.org], ['ASN', g.asn],
        ['Mobile', g.mobile ? 'Yes' : 'No'],
        ['Proxy', g.proxy ? '&#9888; Yes' : 'No'],
        ['Hosting', g.hosting ? 'Yes' : 'No'],
    ].map(([k, v]) => [k, escapeHtml(v)]));
    if (d.abuse_reports?.available) {
        out += '<h4>Abuse Reports (AbuseIPDB)</h4>' + renderTable([
            ['Confidence score', d.abuse_reports.abuse_confidence_score],
            ['Total reports', d.abuse_reports.total_reports],
            ['Last reported', d.abuse_reports.last_reported],
            ['Usage type', d.abuse_reports.usage_type],
        ].map(([k, v]) => [k, escapeHtml(v)]));
    } else if (d.abuse_reports?.reason) {
        out += `<p class="muted">Abuse check: ${escapeHtml(d.abuse_reports.reason)}</p>`;
    }
    if (g.lat && g.lon) {
        out += `<p><a href="https://www.google.com/maps?q=${g.lat},${g.lon}" target="_blank">View on Google Maps &rarr;</a></p>`;
    }
    return out;
}

function renderPhone(d) {
    return renderTable([
        ['Number', escapeHtml(d.target)],
        ['Valid', d.valid ? '&#10003;' : '&#10005;'],
        ['International', escapeHtml(d.international)],
        ['E.164', escapeHtml(d.e164)],
        ['Region', escapeHtml(d.region)],
        ['Carrier', escapeHtml(d.carrier || 'Unknown')],
        ['Line type', escapeHtml(d.line_type)],
        ['Timezones', escapeHtml((d.timezones || []).join(', '))],
        ['Country code', '+' + d.country_code],
    ]);
}

function renderMetadata(d) {
    const m = d.metadata || {};
    let out = renderTable([
        ['File', escapeHtml(d.filename)],
        ['Type', escapeHtml(d.file_type)],
        ['Size', d.size_bytes + ' bytes'],
    ]);
    if (m.size) out += `<p><strong>Dimensions:</strong> ${m.size.width} &times; ${m.size.height}</p>`;
    if (m.gps_coordinates) {
        out += `<h4>&#128205; GPS Location Found!</h4>
            <p>${m.gps_coordinates.lat}, ${m.gps_coordinates.lon}
            <a href="${m.gps_coordinates.google_maps}" target="_blank">View on Maps &rarr;</a></p>`;
    }
    if (m.exif && Object.keys(m.exif).length) {
        out += '<h4>EXIF</h4>' + renderTable(Object.entries(m.exif).map(([k, v]) => [k, escapeHtml(v)]));
    }
    if (m.metadata && Object.keys(m.metadata).length) {
        out += '<h4>PDF Metadata</h4>' + renderTable(Object.entries(m.metadata).map(([k, v]) => [k, escapeHtml(v)]));
    }
    return out;
}

function renderWebsite(d) {
    let out = renderTable([
        ['Final URL', escapeHtml(d.final_url)],
        ['Status', d.status_code],
        ['Title', escapeHtml(d.title)],
        ['Description', escapeHtml(d.description)],
    ]);
    if (d.technologies?.length) {
        out += `<h4>Technologies Detected</h4><ul class="chip-list">${
            d.technologies.map(t => `<li>${escapeHtml(t)}</li>`).join('')}</ul>`;
    }
    if (d.server_headers && Object.keys(d.server_headers).length) {
        out += '<h4>Server Headers</h4>' + renderTable(Object.entries(d.server_headers).map(([k, v]) => [k, escapeHtml(v)]));
    }
    if (d.security_headers) {
        out += '<h4>Security Headers</h4>' + renderTable(Object.entries(d.security_headers).map(([k, v]) =>
            [k, v === 'MISSING' ? '<span class="muted">MISSING</span>' : escapeHtml(v)]));
    }
    if (d.cookies?.length) {
        out += `<h4>Cookies</h4><ul>${d.cookies.map(c =>
            `<li>${escapeHtml(c.name)} (secure: ${c.secure ? 'yes' : 'no'})</li>`).join('')}</ul>`;
    }
    return out;
}

function renderSocial(d) {
    let out = '<h4>Search Links</h4><ul class="link-list">';
    for (const [name, url] of Object.entries(d.search_links || {})) {
        out += `<li><a href="${escapeHtml(url)}" target="_blank">${escapeHtml(name)}</a></li>`;
    }
    out += '</ul>';
    if (d.username_lookup) {
        out += '<h4>Username Lookup</h4>' + renderUsernameLookup(d.username_lookup);
    }
    return out;
}

function renderBreach(d) {
    const r = d.result || {};
    if (d.type === 'password') {
        return `<p class="${r.pwned ? 'danger' : 'success-text'}">${escapeHtml(r.message || '')}</p>`;
    }
    if (r.available === false) {
        return `<p class="muted">${escapeHtml(r.reason)}</p>
                ${r.fallback ? `<p><a href="${escapeHtml(r.fallback)}" target="_blank">Manual check &rarr;</a></p>` : ''}`;
    }
    if (!r.breaches?.length) return '<p class="success-text">&#10003; No known breaches for this account.</p>';
    return `<p>Found in <strong>${r.count}</strong> breach(es):</p>
        <ul>${r.breaches.map(b =>
            `<li><strong>${escapeHtml(b.title || b.name)}</strong> (${escapeHtml(b.date)}) —
             ${(b.pwn_count || 0).toLocaleString()} accounts affected<br>
             <span class="muted">Data: ${escapeHtml((b.data_classes||[]).join(', '))}</span></li>`).join('')}</ul>`;
}

function renderReverseImage(d) {
    return `<p>${escapeHtml(d.note)}</p>
        <ul class="link-list">${Object.entries(d.search_engines).map(([name, url]) =>
            `<li><a href="${escapeHtml(url)}" target="_blank">${escapeHtml(name)}</a></li>`).join('')}</ul>`;
}

function renderDorking(d) {
    let out = '';
    if (d.live_results?.available) {
        out += `<h4>Live Google Results (${d.live_results.total_results || '?'})</h4><ul>`;
        for (const r of d.live_results.results || []) {
            out += `<li><a href="${escapeHtml(r.link)}" target="_blank"><strong>${escapeHtml(r.title)}</strong></a>
                <br><span class="muted">${escapeHtml(r.snippet)}</span></li>`;
        }
        out += '</ul>';
    } else if (d.live_results?.reason) {
        out += `<p class="muted">Live search: ${escapeHtml(d.live_results.reason)}</p>`;
    }
    out += '<h4>Dork Queries</h4><div class="dork-list">';
    for (const [name, q] of Object.entries(d.dorks || {})) {
        out += `<div class="dork-item">
            <strong>${escapeHtml(name)}</strong>
            <code>${escapeHtml(q.query)}</code>
            <div><a href="${escapeHtml(q.google_url)}" target="_blank">Google</a>
              &middot; <a href="${escapeHtml(q.duckduckgo_url)}" target="_blank">DuckDuckGo</a></div>
        </div>`;
    }
    out += '</div>';
    return out;
}

function renderPublicRecords(d) {
    let out = `<p>${escapeHtml(d.note || '')}</p>`;
    for (const [region, registries] of Object.entries(d.registries || {})) {
        out += `<h4>${escapeHtml(region)}</h4><ul class="link-list">`;
        for (const [name, url] of Object.entries(registries)) {
            out += `<li><a href="${escapeHtml(url)}" target="_blank">${escapeHtml(name)}</a></li>`;
        }
        out += '</ul>';
    }
    return out;
}

function renderDarkWeb(d) {
    if (!d.results?.length) return `<p>No results found on Ahmia for "${escapeHtml(d.target)}".</p>`;
    return `<p>${escapeHtml(d.note)}</p>
        <ul class="dark-list">${d.results.map(r => `
            <li>
                <strong>${escapeHtml(r.title)}</strong>
                <div class="muted onion-url">${escapeHtml(r.onion_url)}</div>
                <p>${escapeHtml(r.description)}</p>
            </li>`).join('')}</ul>`;
}

// ---------- RESULTS TOOLBAR ----------
function initResultsToolbar() {
    $('resultsSearch').addEventListener('input', (e) => renderResults(e.target.value));

    $('exportBtn').addEventListener('click', () => {
        if (state.results.length === 0) {
            showToast('No results to export.'); return;
        }
        const blob = new Blob([JSON.stringify(state.results, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `dfi-results-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
        showToast('Exported.');
    });

    $('clearBtn').addEventListener('click', () => {
        if (state.results.length === 0) return;
        if (confirm('Clear all results?')) {
            state.results = [];
            renderResults();
            showToast('Cleared.');
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
    toastTimer = setTimeout(() => toast.classList.remove('show'), 3500);
}

// ---------- BACKEND HEALTH CHECK ----------
async function checkBackend() {
    try {
        const r = await fetch(`${API_BASE}/api/health`);
        if (r.ok) {
            const data = await r.json();
            document.querySelector('.header-status span:last-child').textContent =
                `Backend online (${data.tools_available.length} tools)`;
        }
    } catch {
        const s = document.querySelector('.header-status');
        s.querySelector('.status-dot').style.background = 'var(--danger)';
        s.querySelector('span:last-child').textContent = 'Backend offline';
        showToast('Backend not reachable. Start it with: python -m backend.app');
    }
}

// ---------- INIT ----------
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initToolCards();
    initModal();
    initResultsToolbar();
    checkBackend();
});
