/* ============================================
   Digital Footprint Investigator - Frontend
   ============================================ */

const API_BASE = (location.protocol === "file:") ? "http://localhost:5000" : "";

// ---------- OPTION SCHEMAS ----------
// Each tool defines target + options[] rendered as form fields
const TOOL_META = {
    // ===== ACTIVE =====
    'port-scan': {
        name: 'Port Scanning', type: 'active',
        label: 'Target host / IP',
        placeholder: 'example.com or 192.168.1.1',
        options: [
            { name: 'mode', type: 'select', label: 'Scan Mode', default: 'basic',
              choices: [
                {v: 'basic',    l: 'Basic (~35 common ports, fastest)'},
                {v: 'advanced', l: 'Advanced (top 1000 ports)'},
                {v: 'full',     l: 'Full (1-65535, slow)'},
                {v: 'custom',   l: 'Custom range'}
              ]},
            { name: 'timing', type: 'select', label: 'Timing', default: 'normal',
              choices: [
                {v: 'fast',     l: 'Fast (0.3s timeout, may miss ports)'},
                {v: 'normal',   l: 'Normal (1s timeout)'},
                {v: 'thorough', l: 'Thorough (2.5s timeout, most accurate)'}
              ]},
            { name: 'grab_banners', type: 'checkbox', label: 'Grab service banners on open ports', default: false },
            { name: 'custom_ports', type: 'text', label: 'Custom ports (e.g. 22,80,8000-8100)',
              placeholder: '22,80,443,8000-8100', dependsOn: {mode: 'custom'} }
        ]
    },
    'dns-enum': {
        name: 'DNS Enumeration', type: 'active',
        label: 'Domain', placeholder: 'example.com',
        options: [
            { name: 'mode', type: 'select', label: 'Mode', default: 'basic',
              choices: [
                {v: 'basic',    l: 'Basic (7 record types)'},
                {v: 'advanced', l: 'Advanced (12 types + DNSSEC + SPF/DMARC)'}
              ]},
            { name: 'zone_transfer', type: 'checkbox', label: 'Attempt AXFR zone transfer', default: false },
            { name: 'reverse_lookup', type: 'checkbox', label: 'Reverse-DNS all A records', default: false },
            { name: 'check_policies', type: 'checkbox', label: 'Check SPF/DMARC policies', default: false }
        ]
    },
    'subdomain-enum': {
        name: 'Subdomain Enumeration', type: 'active',
        label: 'Domain', placeholder: 'example.com',
        options: [
            { name: 'mode', type: 'select', label: 'Mode', default: 'basic',
              choices: [
                {v: 'basic',    l: 'Basic (crt.sh only)'},
                {v: 'advanced', l: 'Advanced (crt.sh + DNS bruteforce)'}
              ]},
            { name: 'live_check', type: 'checkbox', label: 'Live check (resolve + HTTP probe)', default: false },
            { name: 'bruteforce', type: 'checkbox', label: 'Force DNS bruteforce (also in basic mode)', default: false }
        ]
    },
    'whois': {
        name: 'WHOIS Lookup', type: 'active',
        label: 'Domain', placeholder: 'example.com',
        options: []
    },
    'dir-brute': {
        name: 'Directory Bruteforce', type: 'active',
        label: 'URL', placeholder: 'https://example.com',
        options: [
            { name: 'wordlist_size', type: 'select', label: 'Wordlist Size', default: 'small',
              choices: [
                {v: 'small',  l: 'Small (~25 paths, fast)'},
                {v: 'medium', l: 'Medium (~130 paths)'},
                {v: 'large',  l: 'Large (~250 paths, slow)'}
              ]},
            { name: 'extensions', type: 'text', label: 'File extensions to try (comma-separated)',
              placeholder: 'php,html,txt,bak' },
            { name: 'follow_redirects', type: 'checkbox', label: 'Follow HTTP redirects', default: false },
            { name: 'timeout', type: 'number', label: 'Timeout (seconds)', default: 5, min: 1, max: 30 }
        ]
    },
    'web-crawler': {
        name: 'Web Crawler', type: 'active',
        label: 'URL', placeholder: 'https://example.com',
        options: [
            { name: 'max_pages', type: 'number', label: 'Max pages to crawl', default: 15, min: 1, max: 100 },
            { name: 'max_depth', type: 'number', label: 'Max link depth', default: 2, min: 1, max: 5 },
            { name: 'respect_robots', type: 'checkbox', label: 'Respect robots.txt', default: true },
            { name: 'extract_emails', type: 'checkbox', label: 'Extract email addresses', default: true },
            { name: 'extract_phones', type: 'checkbox', label: 'Extract phone numbers', default: false },
            { name: 'extract_social', type: 'checkbox', label: 'Extract social media links', default: true },
            { name: 'extract_js', type: 'checkbox', label: 'List external JS files', default: false }
        ]
    },
    'ssl-scan': {
        name: 'SSL / TLS Scanner', type: 'active',
        label: 'Host (or host:port)', placeholder: 'example.com or example.com:443',
        options: [
            { name: 'mode', type: 'select', label: 'Mode', default: 'basic',
              choices: [
                {v: 'basic',    l: 'Basic (cert + cipher + grade)'},
                {v: 'advanced', l: 'Advanced (+ protocol enumeration)'}
              ]}
        ]
    },
    'banner-grab': {
        name: 'Banner Grabbing', type: 'active',
        label: 'Host (or host:port)', placeholder: 'example.com:80',
        options: [
            { name: 'ports', type: 'text', label: 'Ports (comma-separated, overrides host:port)',
              placeholder: '21,22,25,80,443' }
        ]
    },

    // ===== PASSIVE =====
    'authentication': {
        name: 'Authentication', type: 'passive',
        label: '', options: [], special: 'auth'
    },
    'username-lookup': {
        name: 'Username Lookup', type: 'passive',
        label: 'Username', placeholder: 'e.g. torvalds',
        options: [
            { name: 'categories', type: 'select', label: 'Platform Categories', default: 'all',
              choices: [
                {v: 'all',          l: 'All (~90 platforms)'},
                {v: 'social',       l: 'Social media'},
                {v: 'dev',          l: 'Developer platforms'},
                {v: 'gaming',       l: 'Gaming'},
                {v: 'creative',     l: 'Creative / Art / Music'},
                {v: 'professional', l: 'Professional / Portfolio'},
                {v: 'forum',        l: 'Forums'},
                {v: 'misc',         l: 'Miscellaneous'}
              ]},
            { name: 'include_variations', type: 'checkbox', label: 'Also check username variations (user_, _user, user1)', default: false },
            { name: 'show_not_found', type: 'checkbox', label: 'Include not-found platforms in output', default: false }
        ]
    },
    'email-investigation': {
        name: 'Email Investigation', type: 'passive',
        label: 'Email address', placeholder: 'user@example.com',
        options: [
            { name: 'mode', type: 'select', label: 'Mode', default: 'basic',
              choices: [
                {v: 'basic',    l: 'Basic (syntax + MX + disposable check)'},
                {v: 'advanced', l: 'Advanced (+ Gravatar profile + HIBP + Hunter.io)'}
              ]},
            { name: 'check_gravatar', type: 'checkbox', label: 'Check Gravatar profile', default: true },
            { name: 'check_hibp', type: 'checkbox', label: 'Check HaveIBeenPwned breaches (needs key)', default: true },
            { name: 'check_hunter', type: 'checkbox', label: 'Verify via Hunter.io (needs key)', default: false }
        ]
    },
    'domain-investigation': {
        name: 'Domain Investigation', type: 'passive',
        label: 'Domain', placeholder: 'example.com',
        options: []
    },
    'ip-investigation': {
        name: 'IP Investigation', type: 'passive',
        label: 'IP or hostname', placeholder: '8.8.8.8',
        options: [
            { name: 'mode', type: 'select', label: 'Mode', default: 'basic',
              choices: [
                {v: 'basic',    l: 'Basic (geo + rDNS + abuse if key set)'},
                {v: 'advanced', l: 'Advanced (+ Shodan + VirusTotal, needs keys)'}
              ]},
            { name: 'check_shodan', type: 'checkbox', label: 'Force Shodan lookup', default: false },
            { name: 'check_virustotal', type: 'checkbox', label: 'Force VirusTotal lookup', default: false }
        ]
    },
    'phone-investigation': {
        name: 'Phone Investigation', type: 'passive',
        label: 'Phone number (with country code)', placeholder: '+1 202-456-1414',
        options: [
            { name: 'include_osint_links', type: 'checkbox', label: 'Include OSINT lookup links (TrueCaller, etc.)', default: true }
        ]
    },
    'metadata-extraction': {
        name: 'Metadata Extraction', type: 'passive',
        label: 'File URL or upload', placeholder: 'https://example.com/photo.jpg',
        special: 'file',
        options: [
            { name: 'mode', type: 'select', label: 'Mode', default: 'basic',
              choices: [
                {v: 'basic', l: 'Basic (essential metadata + GPS)'},
                {v: 'full',  l: 'Full (all EXIF tags + PDF text preview)'}
              ]}
        ]
    },
    'website-analysis': {
        name: 'Website Analysis', type: 'passive',
        label: 'URL', placeholder: 'https://example.com',
        options: [
            { name: 'mode', type: 'select', label: 'Mode', default: 'basic',
              choices: [
                {v: 'basic',    l: 'Basic (tech + headers + trackers)'},
                {v: 'advanced', l: 'Advanced (+ robots.txt + sitemap parsing)'}
              ]},
            { name: 'fetch_robots', type: 'checkbox', label: 'Fetch and parse robots.txt', default: true },
            { name: 'fetch_sitemap', type: 'checkbox', label: 'Fetch and parse sitemap.xml', default: false }
        ]
    },
    'social-media': {
        name: 'Social Media Search', type: 'passive',
        label: 'Name or handle', placeholder: 'John Doe or johndoe',
        options: []
    },
    'breach-check': {
        name: 'Data Breach Check', type: 'passive',
        label: 'Email or password', placeholder: 'user@example.com or password123',
        options: []
    },
    'reverse-image': {
        name: 'Reverse Image Search', type: 'passive',
        label: 'Image URL', placeholder: 'https://example.com/image.jpg',
        options: []
    },
    'google-dorking': {
        name: 'Google Dorking', type: 'passive',
        label: 'Domain or search query', placeholder: 'example.com',
        options: []
    },
    'public-records': {
        name: 'Public Records', type: 'passive',
        label: 'Name or entity', placeholder: 'Acme Corporation',
        options: []
    },
    'dark-web': {
        name: 'Dark Web Monitor', type: 'passive',
        label: 'Keyword or target', placeholder: 'example.com',
        options: []
    }
};

// ---------- STATE ----------
const state = { results: [], currentTool: null, running: false };

// ---------- DOM HELPERS ----------
const $ = (id) => document.getElementById(id);
const $$ = (sel) => document.querySelectorAll(sel);

function escapeHtml(str) {
    return String(str ?? '')
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}
function formatTime(iso) { return new Date(iso).toLocaleString(); }

// ---------- TABS ----------
function initTabs() {
    $$('.tab-btn').forEach(btn => btn.addEventListener('click', () => switchTab(btn.dataset.tab)));
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

// ---------- MODAL: DYNAMIC RENDERING ----------
async function openToolModal(toolId) {
    const meta = TOOL_META[toolId];
    if (!meta) return;

    state.currentTool = toolId;
    $('modalTitle').textContent = meta.name;
    const body = $('modalBody');

    // --- Special: Authentication tab ---
    if (meta.special === 'auth') {
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

    // --- Build target field ---
    let html = `
        <label class="field-label" for="modalInput">${escapeHtml(meta.label)}</label>
        <input type="text" id="modalInput" class="modal-input" placeholder="${escapeHtml(meta.placeholder || '')}" />
    `;

    // --- Special: file upload for metadata ---
    if (meta.special === 'file') {
        html += `
            <div class="or-divider">OR</div>
            <label class="field-label" for="modalFile">Upload file</label>
            <input type="file" id="modalFile" accept="image/*,.pdf" />
        `;
    }

    // --- Render options ---
    if (meta.options && meta.options.length > 0) {
        html += `<div class="options-section">
            <div class="options-header">
                <span>&#9881; Options</span>
                <button type="button" class="btn-link" id="resetOptions">Reset to defaults</button>
            </div>
            <div class="options-grid">`;
        for (const opt of meta.options) {
            html += renderOptionField(opt);
        }
        html += `</div></div>`;
    }

    body.innerHTML = html;
    $('modalRun').textContent = 'Run Investigation';
    $('modalOverlay').classList.add('show');

    // Bind option interactions (for dependsOn visibility)
    if (meta.options?.length) {
        bindOptionVisibility(meta.options);
        $('resetOptions')?.addEventListener('click', () => resetOptions(meta.options));
    }

    setTimeout(() => $('modalInput')?.focus(), 100);
}

function renderOptionField(opt) {
    const id = `opt_${opt.name}`;
    const isHidden = opt.dependsOn ? 'style="display:none"' : '';

    if (opt.type === 'select') {
        const choices = opt.choices.map(c =>
            `<option value="${escapeHtml(c.v)}"${c.v === opt.default ? ' selected' : ''}>${escapeHtml(c.l)}</option>`
        ).join('');
        return `<div class="option-field" data-opt-name="${opt.name}" ${isHidden}>
            <label class="field-label" for="${id}">${escapeHtml(opt.label)}</label>
            <select id="${id}" class="modal-select" data-name="${opt.name}">
                ${choices}
            </select>
        </div>`;
    }

    if (opt.type === 'checkbox') {
        return `<div class="option-field option-field-checkbox" data-opt-name="${opt.name}" ${isHidden}>
            <label class="checkbox-label">
                <input type="checkbox" id="${id}" data-name="${opt.name}" ${opt.default ? 'checked' : ''} />
                <span>${escapeHtml(opt.label)}</span>
            </label>
        </div>`;
    }

    if (opt.type === 'number') {
        return `<div class="option-field" data-opt-name="${opt.name}" ${isHidden}>
            <label class="field-label" for="${id}">${escapeHtml(opt.label)}</label>
            <input type="number" id="${id}" class="modal-input" data-name="${opt.name}"
                   value="${opt.default ?? ''}"
                   ${opt.min !== undefined ? `min="${opt.min}"` : ''}
                   ${opt.max !== undefined ? `max="${opt.max}"` : ''} />
        </div>`;
    }

    // text (default)
    return `<div class="option-field" data-opt-name="${opt.name}" ${isHidden}>
        <label class="field-label" for="${id}">${escapeHtml(opt.label)}</label>
        <input type="text" id="${id}" class="modal-input" data-name="${opt.name}"
               placeholder="${escapeHtml(opt.placeholder || '')}"
               value="${escapeHtml(opt.default ?? '')}" />
    </div>`;
}

function bindOptionVisibility(options) {
    // Handle dependsOn: hide/show fields based on other option values
    const depMap = {};
    for (const opt of options) {
        if (opt.dependsOn) {
            for (const [dep, val] of Object.entries(opt.dependsOn)) {
                depMap[dep] = depMap[dep] || [];
                depMap[dep].push({ target: opt.name, requiredValue: val });
            }
        }
    }
    for (const [dep, targets] of Object.entries(depMap)) {
        const control = document.querySelector(`[data-name="${dep}"]`);
        if (!control) continue;
        const updateVisibility = () => {
            const current = control.type === 'checkbox' ? control.checked : control.value;
            for (const t of targets) {
                const field = document.querySelector(`[data-opt-name="${t.target}"]`);
                if (field) field.style.display = (current === t.requiredValue) ? '' : 'none';
            }
        };
        control.addEventListener('change', updateVisibility);
        updateVisibility();
    }
}

function resetOptions(options) {
    for (const opt of options) {
        const el = document.querySelector(`[data-name="${opt.name}"]`);
        if (!el) continue;
        if (opt.type === 'checkbox') el.checked = !!opt.default;
        else el.value = opt.default ?? '';
        el.dispatchEvent(new Event('change'));
    }
}

function collectOptions(toolId) {
    const meta = TOOL_META[toolId];
    if (!meta.options?.length) return {};
    const opts = {};
    for (const o of meta.options) {
        const el = document.querySelector(`[data-name="${o.name}"]`);
        if (!el) continue;
        // Skip hidden fields (dependsOn not met)
        const field = document.querySelector(`[data-opt-name="${o.name}"]`);
        if (field && field.style.display === 'none') continue;
        if (o.type === 'checkbox') opts[o.name] = el.checked;
        else if (o.type === 'number') {
            const n = parseFloat(el.value);
            if (!isNaN(n)) opts[o.name] = n;
        }
        else if (el.value.trim() !== '') opts[o.name] = el.value.trim();
    }
    return opts;
}

function closeToolModal() {
    $('modalOverlay').classList.remove('show');
    state.currentTool = null;
}

function initModal() {
    $('modalClose').addEventListener('click', closeToolModal);
    $('modalCancel').addEventListener('click', closeToolModal);
    $('modalOverlay').addEventListener('click', e => {
        if (e.target.id === 'modalOverlay') closeToolModal();
    });
    $('modalRun').addEventListener('click', handleModalRun);
    $('modalOverlay').addEventListener('keydown', e => {
        if (e.key === 'Enter' && e.target.id === 'modalInput') handleModalRun();
    });
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && $('modalOverlay').classList.contains('show')) closeToolModal();
    });
}

// ---------- AUTH FORM (unchanged from previous) ----------
function renderAuthForm(services) {
    const rows = Object.entries(services).map(([id, s]) => `
        <div class="auth-row" data-service="${id}">
            <div class="auth-info">
                <div class="auth-name">${escapeHtml(s.name)}
                    <span class="auth-status ${s.configured ? 'configured' : 'missing'}">
                        ${s.configured ? '&#10003; configured' : '&#9888; not set'}
                    </span>
                </div>
                <div class="auth-used-by">Used by: ${s.used_by.join(', ')}</div>
                <a href="${escapeHtml(s.signup)}" target="_blank" class="auth-signup">Get key &rarr;</a>
            </div>
            <div class="auth-actions">
                <input type="password" class="auth-key-input" placeholder="Paste key..." />
                <button class="btn btn-primary btn-sm auth-save">Save</button>
            </div>
        </div>`).join('');
    return `<div class="auth-list">${rows}</div>`;
}

function bindAuthForm() {
    $$('.auth-save').forEach(btn => {
        btn.addEventListener('click', async e => {
            const row = e.target.closest('.auth-row');
            const service = row.dataset.service;
            const key = row.querySelector('.auth-key-input').value.trim();
            try {
                const resp = await fetch(`${API_BASE}/api/auth/update`, {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({service, key})
                });
                const data = await resp.json();
                if (data.error) return showToast(data.error);
                showToast(data.summary || 'Key saved.');
                const resp2 = await fetch(`${API_BASE}/api/auth/status`);
                const status = await resp2.json();
                $('modalBody').innerHTML = renderAuthForm(status.services);
                bindAuthForm();
            } catch (err) { showToast('Error: ' + err.message); }
        });
    });
}

// ---------- RUN HANDLER ----------
async function handleModalRun() {
    const toolId = state.currentTool;
    if (!toolId) return;
    const meta = TOOL_META[toolId];

    if (meta.special === 'auth') { closeToolModal(); return; }

    const target = $('modalInput')?.value.trim() || '';
    const fileInput = $('modalFile');
    const hasFile = fileInput && fileInput.files.length > 0;
    const options = collectOptions(toolId);

    if (!target && !hasFile) {
        showToast('Please enter a target value.');
        return;
    }
    if (state.running) return;
    state.running = true;

    const result = {
        id: Date.now(), toolId, toolName: meta.name, type: meta.type,
        target: hasFile ? `[uploaded: ${fileInput.files[0].name}]` : target,
        options: hasFile ? {mode: options.mode || 'basic'} : options,
        timestamp: new Date().toISOString(),
        status: 'running', data: null, error: null
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
            if (options.mode) fd.append('mode', options.mode);
            resp = await fetch(`${API_BASE}/api/run/${toolId}`, {method: 'POST', body: fd});
        } else {
            resp = await fetch(`${API_BASE}/api/run/${toolId}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({target, options})
            });
        }
        const data = await resp.json();
        if (data.error) { result.status = 'error'; result.error = data.error; }
        else { result.status = 'success'; result.data = data; }
    } catch (err) {
        result.status = 'error';
        result.error = `Backend unreachable: ${err.message}. Is the Flask server running?`;
    } finally {
        state.running = false;
        hideLoading();
        renderResults();
    }
}

function showLoading(text) {
    $('loadingText').textContent = text || 'Loading...';
    $('loadingOverlay').classList.add('show');
}
function hideLoading() { $('loadingOverlay').classList.remove('show'); }

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

    $$('.result-toggle').forEach(btn => btn.addEventListener('click', e => {
        const item = e.target.closest('.result-item');
        item.classList.toggle('expanded');
        btn.textContent = item.classList.contains('expanded') ? 'Collapse' : 'Expand';
    }));
    $$('.result-remove').forEach(btn => btn.addEventListener('click', e => {
        const id = parseInt(e.target.closest('.result-item').dataset.id);
        state.results = state.results.filter(r => r.id !== id);
        renderResults(filter);
    }));
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

    const optionsBadge = r.options && Object.keys(r.options).length > 0
        ? `<span class="result-options">${Object.entries(r.options).map(([k, v]) =>
            `${k}=${typeof v === 'boolean' ? (v ? 'on' : 'off') : v}`).join(' &middot; ')}</span>`
        : '';

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
        ${optionsBadge}
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
        'banner-grab':        renderBannerMulti,
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
    try { return fn(data); } catch (e) { return renderGenericJson(data); }
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
    if (!d.open_ports?.length) return `<p>No open ports found. Scanned ${d.ports_scanned} port(s) on ${escapeHtml(d.ip)}.</p>`;
    const hasBanners = d.banners_enabled;
    const header = hasBanners
        ? `<thead><tr><th>Port</th><th>Service</th><th>Banner</th></tr></thead>`
        : `<thead><tr><th>Port</th><th>Service</th></tr></thead>`;
    const rows = d.open_ports.map(p =>
        hasBanners
            ? `<tr><td><strong>${p.port}</strong></td><td>${escapeHtml(p.service)}</td>
                   <td class="banner-cell">${escapeHtml(p.banner || '-')}</td></tr>`
            : `<tr><td><strong>${p.port}</strong></td><td>${escapeHtml(p.service)}</td></tr>`);
    return `<table class="result-table">${header}<tbody>${rows.join('')}</tbody></table>
        <p class="result-note">Mode: ${escapeHtml(d.mode)} | Timing: ${escapeHtml(d.timing)} | 
        Scanned ${d.ports_scanned} port(s) on ${escapeHtml(d.ip)}</p>`;
}

function renderDnsEnum(d) {
    let out = '';
    for (const [type, vals] of Object.entries(d.records || {})) {
        out += `<div class="dns-block"><h4>${type}</h4>${
            vals.length ? '<ul>' + vals.map(v => `<li>${escapeHtml(v)}</li>`).join('') + '</ul>'
                        : '<p class="muted">No records</p>'
        }</div>`;
    }
    const ex = d.extras || {};
    if (ex.reverse_dns && Object.keys(ex.reverse_dns).length) {
        out += `<h4>Reverse DNS</h4>` + renderTable(Object.entries(ex.reverse_dns).map(([k, v]) => [k, escapeHtml(v)]));
    }
    if (ex.zone_transfer) {
        const zt = ex.zone_transfer;
        out += `<h4>Zone Transfer (AXFR)</h4>`;
        if (zt.vulnerable) {
            out += `<p class="danger"><strong>&#9888; VULNERABLE:</strong> AXFR succeeded, ${zt.records.length} records extracted.</p>`;
            out += `<pre class="result-json">${escapeHtml(zt.records.slice(0, 40).join('\n'))}</pre>`;
        } else {
            out += `<p class="success-text">&#10003; Zone transfer refused by all nameservers.</p>`;
        }
    }
    if (ex.dnssec) {
        out += `<h4>DNSSEC</h4><p>${ex.dnssec.enabled ? '&#10003; Enabled' : ex.dnssec.enabled === false ? '&#10005; Not enabled' : '? Unknown'}</p>`;
    }
    if (ex.email_policies) {
        out += `<h4>Email Policies</h4>`;
        out += `<p><strong>SPF:</strong> ${(ex.email_policies.spf || []).map(escapeHtml).join('<br>') || '<span class="muted">None</span>'}</p>`;
        out += `<p><strong>DMARC:</strong> ${(ex.email_policies.dmarc || []).map(escapeHtml).join('<br>') || '<span class="muted">None</span>'}</p>`;
    }
    return out;
}

function renderSubdomains(d) {
    if (!d.subdomains?.length) return '<p>No subdomains found.</p>';
    let out = `<p><strong>${d.count}</strong> subdomains from sources:
        ${Object.entries(d.sources || {}).map(([s, c]) => `<span class="pill">${escapeHtml(s)}: ${c}</span>`).join(' ')}
    </p>`;
    if (d.live_check) {
        const alive = d.live_check.filter(r => r.resolves);
        out += `<h4>Live Subdomains (${alive.length})</h4>
            <table class="result-table"><thead><tr><th>Subdomain</th><th>IP</th><th>HTTP</th></tr></thead><tbody>`;
        for (const r of alive) {
            out += `<tr><td><a href="https://${escapeHtml(r.subdomain)}" target="_blank">${escapeHtml(r.subdomain)}</a></td>
                <td>${escapeHtml(r.ip || '')}</td>
                <td>${r.http ? `${r.http.scheme.toUpperCase()} ${r.http.status}` : '<span class="muted">no probe</span>'}</td></tr>`;
        }
        out += `</tbody></table>`;
    } else {
        out += `<ul class="chip-list">${d.subdomains.map(s =>
            `<li><a href="https://${escapeHtml(s)}" target="_blank">${escapeHtml(s)}</a></li>`).join('')}</ul>`;
    }
    return out;
}

function renderDirBrute(d) {
    if (!d.found?.length) return `<p>No interesting paths found. Tested ${d.paths_tested} paths.</p>`;
    return `<p><strong>${d.found.length}</strong> hit(s) out of ${d.paths_tested} paths tested
        (${escapeHtml(d.wordlist_size)} wordlist, ${d.extensions.length ? 'exts: ' + d.extensions.join(',') : 'no extensions'}).</p>
        <table class="result-table"><thead><tr><th>Status</th><th>Path</th><th>Size</th><th>Server</th></tr></thead><tbody>${
        d.found.map(f =>
            `<tr><td class="status-${Math.floor(f.status/100)}xx">${f.status}</td>
                 <td><a href="${escapeHtml(f.url)}" target="_blank">${escapeHtml(f.path)}</a></td>
                 <td>${escapeHtml(f.size)}</td>
                 <td>${escapeHtml(f.server || '')}</td></tr>`).join('')}</tbody></table>`;
}

function renderCrawler(d) {
    let out = renderTable([
        ['Pages crawled', `${d.pages_crawled} / ${d.pages_limit}`],
        ['Depth limit', d.depth_limit],
        ['Respected robots.txt', d.respect_robots ? 'Yes' : 'No'],
        ['Total links', d.total_links],
        ['External hosts', d.external_hosts?.length || 0],
        ['Forms', d.forms?.length || 0],
    ]);
    if (d.emails?.length) out += `<h4>Emails (${d.emails.length})</h4><ul class="chip-list">${d.emails.map(e => `<li>${escapeHtml(e)}</li>`).join('')}</ul>`;
    if (d.phones?.length) out += `<h4>Phones (${d.phones.length})</h4><ul class="chip-list">${d.phones.map(e => `<li>${escapeHtml(e)}</li>`).join('')}</ul>`;
    if (d.social_profiles?.length) out += `<h4>Social Profiles (${d.social_profiles.length})</h4><ul class="chip-list">${d.social_profiles.map(s => `<li><a href="https://${escapeHtml(s)}" target="_blank">${escapeHtml(s)}</a></li>`).join('')}</ul>`;
    if (d.js_files?.length) out += `<h4>JavaScript Files (${d.js_files.length})</h4><ul class="chip-list">${d.js_files.map(j => `<li><a href="${escapeHtml(j)}" target="_blank">${escapeHtml(j.split('/').pop())}</a></li>`).join('')}</ul>`;
    if (d.external_hosts?.length) out += `<h4>External Hosts (${d.external_hosts.length})</h4><ul class="chip-list">${d.external_hosts.slice(0, 40).map(h => `<li>${escapeHtml(h)}</li>`).join('')}</ul>`;
    return out;
}

function renderSslScan(d) {
    const grade = d.grade || {};
    let out = `<div class="ssl-grade ssl-grade-${grade.grade || 'F'}">
        <div class="grade-letter">${escapeHtml(grade.grade || '?')}</div>
        <div class="grade-details">
            <div>Score: <strong>${grade.score ?? '?'}/100</strong></div>
            <div class="muted">${(grade.issues || []).join(' | ') || 'No issues detected'}</div>
        </div>
    </div>`;
    out += renderTable([
        ['Target', d.target], ['TLS version', d.tls_version],
        ['Cipher', d.cipher_suite], ['Bits', d.cipher_bits],
        ['Self-signed', d.self_signed ? '&#9888; Yes' : '&#10003; No (valid chain)'],
        ['Not before', d.not_before], ['Not after', d.not_after],
        ['Days until expiry', d.days_until_expiry],
        ['Subject', JSON.stringify(d.subject)], ['Issuer', JSON.stringify(d.issuer)],
        ['SAN', (d.san || []).slice(0, 10).join(', ')],
    ].map(([k, v]) => [k, escapeHtml(v)]));
    if (d.protocols_supported) {
        out += `<h4>Protocol Support</h4>` + renderTable(
            Object.entries(d.protocols_supported).map(([p, s]) => [p,
                s === 'supported' ? `<span class="${p.includes('1.2') || p.includes('1.3') ? 'success-text' : 'danger'}">${s}</span>`
                : `<span class="muted">${s}</span>`
            ]));
    }
    return out;
}

function renderBannerMulti(d) {
    if (!d.results?.length) return `<pre class="result-json">${escapeHtml(JSON.stringify(d, null, 2))}</pre>`;
    return `<table class="result-table"><thead><tr><th>Port</th><th>Service</th><th>Banner</th></tr></thead><tbody>${
        d.results.map(r => `<tr>
            <td><strong>${r.port}</strong></td>
            <td>${escapeHtml(r.service)}</td>
            <td class="banner-cell">${r.banner ? `<pre>${escapeHtml(r.banner)}</pre>` : `<span class="muted">${escapeHtml(r.error || 'no banner')}</span>`}</td>
        </tr>`).join('')}</tbody></table>`;
}

function renderUsernameLookup(d) {
    if (!d.found_on?.length) return `<p>Username not found on any checked platform.</p>`;
    let out = `<p>Found <strong>${d.found_count}</strong> match(es) across
        <strong>${Object.keys(d.found_by_category || {}).length}</strong> categories.</p>`;
    for (const [cat, list] of Object.entries(d.found_by_category || {})) {
        out += `<h4>${escapeHtml(cat.toUpperCase())} (${list.length})</h4>
            <div class="platform-grid">${list.map(p =>
                `<a href="${escapeHtml(p.url)}" target="_blank" class="platform-link">
                    <strong>${escapeHtml(p.platform)}</strong>
                    <span class="muted">${escapeHtml(p.url)}</span>
                </a>`).join('')}</div>`;
    }
    return out;
}

function renderEmail(d) {
    const rows = [
        ['Email', escapeHtml(d.email)],
        ['Valid syntax', d.valid_syntax ? '&#10003; Yes' : '&#10005; No'],
        ['Deliverable (MX)', d.deliverable ? '&#10003; Yes' : '&#10005; No'],
        ['Disposable', d.disposable ? '&#9888; Yes' : '&#10003; No'],
        ['Free provider', d.free_provider ? 'Yes' : 'No'],
        ['MX Records', (d.mx_records || []).map(escapeHtml).join('<br>')],
    ];
    if (d.gravatar) rows.push(['Gravatar', d.gravatar.has_avatar ? '&#10003; Has avatar' : 'No avatar']);
    if (d.breaches) rows.push(['Breaches', d.breaches.available
        ? `${d.breaches.count} breach(es)`
        : `<span class="muted">${escapeHtml(d.breaches.reason || 'Unknown')}</span>`]);
    let out = renderTable(rows);

    if (d.gravatar?.profile) {
        const p = d.gravatar.profile;
        out += `<h4>Gravatar Profile</h4>`;
        out += `<div class="gravatar-profile">
            <img src="${escapeHtml(d.gravatar.avatar_url)}" class="gravatar-avatar" alt="avatar" />
            <div>
                ${p.display_name ? `<div><strong>${escapeHtml(p.display_name)}</strong></div>` : ''}
                ${p.location ? `<div>&#128205; ${escapeHtml(p.location)}</div>` : ''}
                ${p.bio ? `<div class="muted">${escapeHtml(p.bio)}</div>` : ''}
            </div>
        </div>`;
        if (p.accounts?.length) {
            out += `<p><strong>Linked accounts:</strong></p><ul class="chip-list">${p.accounts.map(a =>
                `<li><a href="${escapeHtml(a.url)}" target="_blank">${escapeHtml(a.domain || a.url)}</a></li>`).join('')}</ul>`;
        }
    }

    if (d.breaches?.breaches?.length) {
        out += `<h4>Breach Details</h4><ul>${d.breaches.breaches.map(b =>
            `<li><strong>${escapeHtml(b.name)}</strong> (${escapeHtml(b.date)})
                 — ${(b.pwn_count || 0).toLocaleString()} accounts<br>
                 <span class="muted">Data: ${escapeHtml((b.data_classes||[]).join(', '))}</span></li>`).join('')}</ul>`;
    }

    if (d.hunter?.available) {
        out += `<h4>Hunter.io Verification</h4>` + renderTable([
            ['Status', d.hunter.status], ['Result', d.hunter.result],
            ['Score', d.hunter.score], ['SMTP check', d.hunter.smtp_check ? 'Passed' : 'Failed'],
            ['Accept-all domain', d.hunter.accept_all ? 'Yes' : 'No'],
            ['Sources found', d.hunter.sources_count],
        ].map(([k, v]) => [k, escapeHtml(v)]));
    }
    return out;
}

function renderDomain(d) {
    let out = '<h4>WHOIS</h4>' + (d.whois?.error ? `<p class="muted">${escapeHtml(d.whois.error)}</p>` : renderKeyValue({whois: d.whois}));
    out += '<h4>DNS</h4>' + (d.dns?.error ? `<p class="muted">${escapeHtml(d.dns.error)}</p>` : renderDnsEnum({records: d.dns}));
    out += '<h4>Reputation</h4>';
    if (d.reputation?.available) {
        out += renderTable([
            ['Reputation', d.reputation.reputation], ['Malicious', d.reputation.malicious],
            ['Suspicious', d.reputation.suspicious], ['Harmless', d.reputation.harmless],
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
        ['Proxy/VPN', g.proxy ? '&#9888; Yes' : 'No'],
        ['Hosting', g.hosting ? 'Yes' : 'No'],
    ].map(([k, v]) => [k, escapeHtml(v)]));

    if (d.abuse_reports?.available) {
        out += '<h4>Abuse Reports (AbuseIPDB)</h4>' + renderTable([
            ['Confidence score', d.abuse_reports.abuse_confidence_score],
            ['Total reports', d.abuse_reports.total_reports],
            ['Distinct users', d.abuse_reports.num_distinct_users],
            ['Last reported', d.abuse_reports.last_reported],
            ['Usage type', d.abuse_reports.usage_type],
            ['Is Tor', d.abuse_reports.is_tor ? 'Yes' : 'No'],
            ['Whitelisted', d.abuse_reports.is_whitelisted ? 'Yes' : 'No'],
        ].map(([k, v]) => [k, escapeHtml(v)]));
    } else if (d.abuse_reports?.reason) {
        out += `<p class="muted">Abuse check: ${escapeHtml(d.abuse_reports.reason)}</p>`;
    }

    if (d.shodan?.available && d.shodan.ports) {
        out += `<h4>Shodan Intel</h4>` + renderTable([
            ['OS', d.shodan.os],
            ['Hostnames', (d.shodan.hostnames || []).join(', ')],
            ['Open ports', (d.shodan.ports || []).join(', ')],
            ['Vulnerabilities', (d.shodan.vulns || []).join(', ') || 'None'],
            ['Tags', (d.shodan.tags || []).join(', ')],
        ].map(([k, v]) => [k, escapeHtml(v)]));
        if (d.shodan.services?.length) {
            out += `<h4>Shodan Services</h4><ul>${d.shodan.services.map(s =>
                `<li><strong>${s.port}/${s.transport}</strong> ${escapeHtml(s.product || '')} ${escapeHtml(s.version || '')}<br>
                <span class="muted">${escapeHtml(s.banner || '')}</span></li>`).join('')}</ul>`;
        }
    } else if (d.shodan?.reason) {
        out += `<p class="muted">Shodan: ${escapeHtml(d.shodan.reason)}</p>`;
    }

    if (d.virustotal?.available) {
        out += `<h4>VirusTotal</h4>` + renderTable([
            ['Reputation', d.virustotal.reputation],
            ['Malicious', d.virustotal.malicious], ['Suspicious', d.virustotal.suspicious],
            ['Harmless', d.virustotal.harmless], ['AS Owner', d.virustotal.as_owner],
        ].map(([k, v]) => [k, escapeHtml(v)]));
    }

    if (g.lat && g.lon) {
        out += `<p><a href="https://www.google.com/maps?q=${g.lat},${g.lon}" target="_blank">View on Google Maps &rarr;</a></p>`;
    }
    return out;
}

function renderPhone(d) {
    let out = renderTable([
        ['Number', escapeHtml(d.target)],
        ['Valid', d.valid ? '&#10003;' : '&#10005;'],
        ['International', escapeHtml(d.international)],
        ['National', escapeHtml(d.national)],
        ['E.164', escapeHtml(d.e164)],
        ['RFC3966', escapeHtml(d.rfc3966)],
        ['Region', escapeHtml(d.region)],
        ['Carrier', escapeHtml(d.carrier || 'Unknown')],
        ['Line type', escapeHtml(d.line_type)],
        ['Timezones', escapeHtml((d.timezones || []).join(', '))],
        ['Country code', '+' + d.country_code],
    ]);
    if (d.osint_lookup_links) {
        out += `<h4>OSINT Lookup Links</h4><ul class="link-list">${
            Object.entries(d.osint_lookup_links).map(([n, u]) =>
                `<li><a href="${escapeHtml(u)}" target="_blank">${escapeHtml(n)}</a></li>`).join('')
        }</ul>`;
    }
    return out;
}

function renderMetadata(d) {
    const m = d.metadata || {};
    let out = renderTable([
        ['File', escapeHtml(d.filename)],
        ['Type', escapeHtml(d.file_type)],
        ['Mode', escapeHtml(d.mode || 'basic')],
        ['Size', `${d.size_bytes.toLocaleString()} bytes`],
    ]);
    if (m.size) out += `<p><strong>Dimensions:</strong> ${m.size.width} &times; ${m.size.height}</p>`;
    if (m.gps_coordinates) {
        out += `<h4>&#128205; GPS Location Found!</h4>
            <p><strong>${m.gps_coordinates.lat}, ${m.gps_coordinates.lon}</strong></p>
            <p><a href="${m.gps_coordinates.google_maps}" target="_blank">Google Maps &rarr;</a>
              &middot; <a href="${m.gps_coordinates.openstreetmap}" target="_blank">OpenStreetMap &rarr;</a></p>`;
    }
    if (m.camera_summary && Object.keys(m.camera_summary).length) {
        out += '<h4>Camera & Copyright Info</h4>' +
            renderTable(Object.entries(m.camera_summary).map(([k, v]) => [k, escapeHtml(v)]));
    }
    if (m.exif && Object.keys(m.exif).length) {
        out += '<h4>Full EXIF</h4>' + renderTable(Object.entries(m.exif).map(([k, v]) => [k, escapeHtml(v)]));
    }
    if (m.metadata && Object.keys(m.metadata).length) {
        out += '<h4>PDF Metadata</h4>' + renderTable(Object.entries(m.metadata).map(([k, v]) => [k, escapeHtml(v)]));
    }
    if (m.text_preview?.length) {
        out += '<h4>PDF Text Preview</h4>';
        for (const t of m.text_preview) {
            out += `<div class="pdf-page"><strong>Page ${t.page}</strong><pre>${escapeHtml(t.preview)}</pre></div>`;
        }
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
        out += `<h4>Technologies Detected (${d.technologies.length})</h4><ul class="chip-list">${
            d.technologies.map(t => `<li>${escapeHtml(t)}</li>`).join('')}</ul>`;
    }
    if (d.trackers_detected?.length) {
        out += `<h4>&#128065; Trackers Detected (${d.trackers_detected.length})</h4><ul class="chip-list warning">${
            d.trackers_detected.map(t => `<li>${escapeHtml(t)}</li>`).join('')}</ul>`;
    }
    if (d.server_headers && Object.keys(d.server_headers).length) {
        out += '<h4>Server Headers</h4>' + renderTable(Object.entries(d.server_headers).map(([k, v]) => [k, escapeHtml(v)]));
    }
    if (d.security_headers) {
        out += '<h4>Security Headers</h4>' + renderTable(Object.entries(d.security_headers).map(([k, v]) =>
            [k, v === 'MISSING' ? '<span class="danger">MISSING</span>' : escapeHtml(v)]));
    }
    if (d.cookies?.length) {
        out += `<h4>Cookies (${d.cookies.length})</h4><ul>${d.cookies.map(c =>
            `<li>${escapeHtml(c.name)} <span class="muted">(secure: ${c.secure ? 'yes' : 'no'}, httponly: ${c.httponly ? 'yes' : 'no'})</span></li>`).join('')}</ul>`;
    }
    if (d.robots_txt?.exists) {
        out += `<h4>robots.txt</h4><p>${d.robots_txt.disallow_count} disallow rule(s), ${d.robots_txt.sitemaps.length} sitemap(s)</p>`;
        if (d.robots_txt.disallowed_paths?.length) {
            out += `<ul class="chip-list">${d.robots_txt.disallowed_paths.slice(0, 20).map(p => `<li>${escapeHtml(p)}</li>`).join('')}</ul>`;
        }
    }
    if (d.sitemaps?.length) {
        out += `<h4>Sitemaps</h4>`;
        for (const s of d.sitemaps) {
            out += `<div><strong><a href="${escapeHtml(s.url)}" target="_blank">${escapeHtml(s.url)}</a></strong>`;
            if (s.url_count) out += ` &mdash; ${s.url_count} URLs`;
            out += `</div>`;
            if (s.urls?.length) {
                out += `<ul class="chip-list">${s.urls.slice(0, 15).map(u =>
                    `<li><a href="${escapeHtml(u)}" target="_blank">${escapeHtml(u)}</a></li>`).join('')}</ul>`;
            }
        }
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
        out += '<h4>Username Lookup Results</h4>' + renderUsernameLookup(d.username_lookup);
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
    $('resultsSearch').addEventListener('input', e => renderResults(e.target.value));
    $('exportBtn').addEventListener('click', () => {
        if (state.results.length === 0) { showToast('No results to export.'); return; }
        const blob = new Blob([JSON.stringify(state.results, null, 2)], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = `dfi-results-${Date.now()}.json`; a.click();
        URL.revokeObjectURL(url);
        showToast('Exported.');
    });
    $('clearBtn').addEventListener('click', () => {
        if (state.results.length === 0) return;
        if (confirm('Clear all results?')) {
            state.results = []; renderResults(); showToast('Cleared.');
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

// ---------- BACKEND HEALTH ----------
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

// ---------- THEME TOGGLE ----------
const THEME_KEY = 'dfi-theme';

function getPreferredTheme() {
    const stored = localStorage.getItem(THEME_KEY);
    if (stored === 'light' || stored === 'dark') return stored;
    return window.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
    const btn = $('themeToggle');
    if (btn) btn.title = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
}

function initTheme() {
    applyTheme(getPreferredTheme());
    const btn = $('themeToggle');
    if (!btn) return;
    btn.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme') || 'dark';
        applyTheme(current === 'dark' ? 'light' : 'dark');
    });
    // Follow OS preference change if user hasn't picked one manually
    window.matchMedia?.('(prefers-color-scheme: light)').addEventListener?.('change', (e) => {
        if (!localStorage.getItem(THEME_KEY + '-manual')) {
            applyTheme(e.matches ? 'light' : 'dark');
        }
    });
    btn.addEventListener('click', () => localStorage.setItem(THEME_KEY + '-manual', '1'), { once: true });
}

// ---------- INIT ----------
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initTabs(); initToolCards(); initModal(); initResultsToolbar(); checkBackend();
});
