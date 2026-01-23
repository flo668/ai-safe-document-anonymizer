/**
 * Flask Anonimiseren Tool - Frontend JavaScript
 * Handles file uploads, rule management, processing, and downloads
 */

// ========== State Management ==========
const state = {
    activeTab: 'text',
    files: {
        text: [],
        excel: []
    },
    rules: {
        text: [],
        excel: []
    },
    sessionId: null,
    processing: false,
    previewCache: {}  // Cache voor Excel previews: { fileId: previewData }
};

// ========== Utility Functions ==========
function generateId() {
    return Date.now().toString() + Math.random().toString(36).substr(2, 9);
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.querySelector('main').insertBefore(alertDiv, document.querySelector('main').firstChild);

    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// ========== File Upload Handling ==========
function setupDropzones() {
    ['text', 'excel'].forEach(type => {
        const dropzone = document.getElementById(`dropzone-${type}`);
        const fileInput = document.getElementById(`file-input-${type}`);

        // Click to upload
        dropzone.addEventListener('click', () => fileInput.click());

        // Drag and drop
        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });

        dropzone.addEventListener('dragleave', () => {
            dropzone.classList.remove('dragover');
        });

        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
            handleFiles(e.dataTransfer.files, type);
        });

        // File input change
        fileInput.addEventListener('change', (e) => {
            handleFiles(e.target.files, type);
        });
    });
}

async function handleFiles(files, type) {
    const formData = new FormData();

    for (let file of files) {
        formData.append('files[]', file);
    }

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            state.sessionId = data.sessionId;
            state.files[type] = state.files[type].concat(data.files);
            renderFileList(type);
            showAlert(`${data.files.length} bestand(en) succesvol geüpload`, 'success');
        } else {
            showAlert(data.error || 'Upload mislukt', 'danger');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showAlert('Fout bij uploaden: ' + error.message, 'danger');
    }
}

function renderFileList(type) {
    const listDiv = document.getElementById(`file-list-${type}`);
    const files = state.files[type];

    if (files.length === 0) {
        listDiv.innerHTML = '';
        return;
    }

    listDiv.innerHTML = files.map(file => {
        const isExcel = file.originalName.match(/\.(xlsx|csv)$/i);
        const showPreview = type === 'excel' && isExcel;

        return `
        <div class="file-item" data-file-id="${file.id}">
            <div>
                <strong>${file.originalName}</strong>
                <small class="text-muted ms-2">${formatFileSize(file.size)}</small>
            </div>
            <div>
                ${showPreview ?
                    `<button class="btn btn-sm btn-success ms-2" onclick="showExcelPreview('${file.id}')" style="background-color: #217346; border-color: #217346;">
                        <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16" style="vertical-align: middle;">
                            <path d="M10.5 8a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0z"/>
                            <path d="M0 8s3-5.5 8-5.5S16 8 16 8s-3 5.5-8 5.5S0 8 0 8zm8 3.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z"/>
                        </svg>
                        Preview
                    </button>` :
                    ''}
                <button class="btn btn-sm btn-danger ms-2" onclick="removeFile('${file.id}', '${type}')">×</button>
            </div>
        </div>
        `;
    }).join('');
}

function removeFile(fileId, type) {
    state.files[type] = state.files[type].filter(f => f.id !== fileId);
    // Clear preview cache voor dit bestand
    if (state.previewCache[fileId]) {
        delete state.previewCache[fileId];
    }
    renderFileList(type);
}

// ========== Rule Management ==========
function setupRuleInputs() {
    // Text rules
    document.getElementById('add-rule-btn').addEventListener('click', addTextRule);

    // Excel rules
    document.getElementById('add-excel-rule-btn').addEventListener('click', addExcelRule);

    // Excel column type change (filters available methods)
    document.getElementById('excel-column-type').addEventListener('change', updateExcelMethodOptions);

    // Excel anonymization type change
    document.getElementById('excel-anonymization-type').addEventListener('change', updateExcelRuleInputs);

    // Excel anon mode radio buttons (fixed vs reversible)
    document.querySelectorAll('input[name="excel-anon-mode"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            const fixedInput = document.getElementById('excel-fixed-input');
            if (e.target.value === 'reversible') {
                fixedInput.style.opacity = '0.5';
                document.getElementById('excel-replace-with').disabled = true;
            } else {
                fixedInput.style.opacity = '1';
                document.getElementById('excel-replace-with').disabled = false;
            }
        });
    });

    // Excel price strategy change
    const priceStrategySelect = document.getElementById('excel-price-strategy');
    if (priceStrategySelect) {
        priceStrategySelect.addEventListener('change', updatePriceStrategyInputs);
    }

    // Initialize method options on load
    updateExcelMethodOptions();
}

function updateExcelMethodOptions() {
    const columnTypeRaw = document.getElementById('excel-column-type').value;
    const methodSelect = document.getElementById('excel-anonymization-type');
    const options = methodSelect.options;

    // Parse column type (bijv. "text:supplier" → "text")
    const columnType = columnTypeRaw.split(':')[0];

    // Reset all options visibility
    for (let i = 0; i < options.length; i++) {
        options[i].classList.add('d-none');
        options[i].disabled = true;
    }

    // Show relevant options based on column type
    if (columnType === 'text') {
        // Text: Vervangen, Jabber
        methodSelect.querySelector('[value="replace"]').classList.remove('d-none');
        methodSelect.querySelector('[value="replace"]').disabled = false;
        methodSelect.querySelector('[value="jabber"]').classList.remove('d-none');
        methodSelect.querySelector('[value="jabber"]').disabled = false;
        methodSelect.value = 'replace';
    } else if (columnType === 'date') {
        // Datum: alleen Datum offset
        methodSelect.querySelector('[value="date_offset"]').classList.remove('d-none');
        methodSelect.querySelector('[value="date_offset"]').disabled = false;
        methodSelect.value = 'date_offset';
    } else if (columnType === 'number') {
        // Prijs/Nummer: alleen Vermenigvuldigen
        methodSelect.querySelector('[value="number_multiply"]').classList.remove('d-none');
        methodSelect.querySelector('[value="number_multiply"]').disabled = false;
        methodSelect.value = 'number_multiply';
    }

    // Trigger update to show/hide input fields
    updateExcelRuleInputs();
}

function updatePriceStrategyInputs() {
    const strategy = document.getElementById('excel-price-strategy').value;
    const fixedInput = document.getElementById('excel-fixed-multiplier-input');
    const rangeInput = document.getElementById('excel-random-range-input');

    // Hide all first
    fixedInput.classList.add('d-none');
    rangeInput.classList.add('d-none');

    // Show relevant input
    if (strategy === 'fixed_multiplier') {
        fixedInput.classList.remove('d-none');
    } else if (strategy === 'random_range') {
        rangeInput.classList.remove('d-none');
    }
    // random_per_price needs no extra input
}

function addTextRule() {
    const originalTerm = document.getElementById('original-term').value.trim();
    const replacementTerm = document.getElementById('replacement-term').value.trim();
    const isRegex = document.getElementById('is-regex').checked;
    const caseSensitive = document.getElementById('case-sensitive').checked;
    const removeInstead = document.getElementById('remove-instead').checked;

    if (!originalTerm) {
        showAlert('Vul een originele term in', 'warning');
        return;
    }

    const rule = {
        id: generateId(),
        originalTerm,
        replacementTerm,
        isRegex,
        caseSensitive,
        removeInsteadOfReplace: removeInstead
    };

    state.rules.text.push(rule);
    renderRulesList('text');

    // Clear inputs
    document.getElementById('original-term').value = '';
    document.getElementById('replacement-term').value = '';
    document.getElementById('is-regex').checked = false;
    document.getElementById('case-sensitive').checked = false;
    document.getElementById('remove-instead').checked = false;

    showAlert('Regel toegevoegd', 'success');
}

function addExcelRule() {
    const columnName = document.getElementById('excel-column-name').value.trim();
    const columnTypeRaw = document.getElementById('excel-column-type').value;
    const anonymizationType = document.getElementById('excel-anonymization-type').value;

    if (!columnName) {
        showAlert('Vul een kolomnaam in', 'warning');
        return;
    }

    // Parse column type (bijv. "text:supplier" → type="text", subtype="supplier")
    let columnType, columnSubtype;
    if (columnTypeRaw.includes(':')) {
        [columnType, columnSubtype] = columnTypeRaw.split(':');
    } else {
        columnType = columnTypeRaw;
        columnSubtype = null;
    }

    const rule = {
        id: generateId(),
        columnName,
        columnType,
        columnSubtype,
        anonymizationType
    };

    // Add type-specific parameters
    if (anonymizationType === 'replace' || anonymizationType === 'jabber') {
        const anonMode = document.querySelector('input[name="excel-anon-mode"]:checked')?.value || 'fixed';
        rule.reversible = (anonMode === 'reversible');
        rule.replaceWith = rule.reversible ? '' : (document.getElementById('excel-replace-with').value || '[ANONIEM]');
    } else if (anonymizationType === 'date_offset') {
        rule.dateOffsetDays = parseInt(document.getElementById('excel-date-offset').value) || 7;
    } else if (anonymizationType === 'number_multiply') {
        const priceStrategy = document.getElementById('excel-price-strategy').value;
        rule.priceStrategy = priceStrategy;

        if (priceStrategy === 'fixed_multiplier') {
            rule.numberMultiplier = parseFloat(document.getElementById('excel-number-multiplier').value) || 0.25;
        } else if (priceStrategy === 'random_range') {
            rule.randomRangePercent = parseFloat(document.getElementById('excel-random-range-percent').value) || 10;
        }
        // random_per_price heeft geen extra parameters
    }

    state.rules.excel.push(rule);
    renderRulesList('excel');

    // Clear inputs
    document.getElementById('excel-column-name').value = '';
    document.getElementById('excel-mode-fixed').checked = true;
    document.getElementById('excel-replace-with').value = '';

    showAlert('Excel regel toegevoegd', 'success');
}

function updateExcelRuleInputs() {
    const columnTypeRaw = document.getElementById('excel-column-type').value;
    const anonymizationType = document.getElementById('excel-anonymization-type').value;

    // Parse column type
    const columnType = columnTypeRaw.split(':')[0];

    // Hide all divs first
    document.getElementById('excel-replace-div').classList.add('d-none');
    document.getElementById('excel-date-div').classList.add('d-none');
    document.getElementById('excel-number-div').classList.add('d-none');

    // Show relevant div based on anonymization type
    if (anonymizationType === 'replace' || anonymizationType === 'jabber') {
        // Alleen tonen voor text types
        if (columnType === 'text') {
            document.getElementById('excel-replace-div').classList.remove('d-none');
        }
    } else if (anonymizationType === 'date_offset') {
        document.getElementById('excel-date-div').classList.remove('d-none');
    } else if (anonymizationType === 'number_multiply') {
        document.getElementById('excel-number-div').classList.remove('d-none');
    }
}

function renderRulesList(type) {
    const listDiv = document.getElementById(type === 'text' ? 'rules-list' : 'excel-rules-list');
    const rules = state.rules[type];

    if (rules.length === 0) {
        const alertStyle = type === 'excel'
            ? 'style="background-color: #d4edda; border-color: #217346;"'
            : 'alert-info';
        const alertClass = type === 'excel' ? 'alert' : 'alert alert-info';

        listDiv.innerHTML = `<div class="${alertClass} mb-0" ${type === 'excel' ? alertStyle : ''}>
            <small>Nog geen ${type === 'excel' ? 'Excel ' : ''}regels toegevoegd.</small>
        </div>`;
        return;
    }

    listDiv.innerHTML = rules.map(rule => {
        if (type === 'text') {
            return `
                <div class="rule-item">
                    <div>
                        <strong>${rule.originalTerm}</strong> → ${rule.removeInsteadOfReplace ? '[VERWIJDERD]' : rule.replacementTerm}
                        ${rule.isRegex ? '<span class="badge bg-info ms-2">Regex</span>' : ''}
                        ${rule.caseSensitive ? '<span class="badge bg-warning ms-2">Case</span>' : ''}
                    </div>
                    <button class="btn btn-sm btn-danger" onclick="removeRule('${rule.id}', 'text')">×</button>
                </div>
            `;
        } else {
            let details = '';
            let typeLabel = rule.columnSubtype ? rule.columnSubtype : rule.columnType;

            if (rule.anonymizationType === 'replace') {
                details = rule.reversible ? ` <span class="badge bg-success">Reversible</span>` : ` → ${rule.replaceWith}`;
            } else if (rule.anonymizationType === 'jabber') {
                details = rule.reversible ? ` <span class="badge bg-success">Reversible</span>` : ' → jabber';
            } else if (rule.anonymizationType === 'date_offset') {
                details = ` (${rule.dateOffsetDays} dagen)`;
            } else if (rule.anonymizationType === 'number_multiply') {
                details = ` (×${rule.numberMultiplier})`;
            }

            return `
                <div class="rule-item excel-rule-item">
                    <div>
                        <strong>${rule.columnName}</strong>
                        <span class="status-label excel-green">${typeLabel}</span>
                        <span class="status-label excel-green">${rule.anonymizationType}</span>
                        ${details}
                    </div>
                    <button class="btn btn-sm btn-danger" onclick="removeRule('${rule.id}', 'excel')">×</button>
                </div>
            `;
        }
    }).join('');
}

function removeRule(ruleId, type) {
    state.rules[type] = state.rules[type].filter(r => r.id !== ruleId);
    renderRulesList(type);
    showAlert('Regel verwijderd', 'info');
}

// ========== Processing ==========
function setupProcessing() {
    document.getElementById('process-text-btn').addEventListener('click', () => processFiles('text'));
    document.getElementById('process-excel-btn').addEventListener('click', () => processFiles('excel'));
}

async function processFiles(type) {
    if (state.processing) return;

    const files = state.files[type];
    const rules = state.rules[type];

    if (files.length === 0) {
        showAlert('Geen bestanden om te verwerken', 'warning');
        return;
    }

    // Lees customizable settings uit UI
    const phonePlaceholder = document.getElementById('phone-placeholder')?.value || '[TEL VERWIJDERD]';
    const emailPlaceholder = document.getElementById('email-placeholder')?.value || '[EMAIL VERWIJDERD]';
    const generalPlaceholder = '[ANONIEM]'; // Voor handmatige regels
    const autoDetectEnabled = document.getElementById('auto-detect-enabled')?.checked ?? true;

    // Check beide reversible mode checkboxes (Word en Excel tabs)
    const reversibleModeText = document.getElementById('reversible-mode-text')?.checked ?? false;
    const reversibleModeExcel = document.getElementById('reversible-mode-enabled')?.checked ?? false;
    const reversibleMode = reversibleModeText || reversibleModeExcel;

    // Check preserve formatting checkbox (alleen voor text/docx)
    const preserveFormatting = document.getElementById('preserve-formatting')?.checked ?? false;

    // Voor text: auto-detectie ALTIJD actief (indien enabled), regels zijn optioneel
    // Voor excel: geen auto-detectie, regels zijn verplicht
    if (type === 'excel' && rules.length === 0) {
        showAlert('Voeg eerst Excel regels toe', 'warning');
        return;
    }

    state.processing = true;
    const progressDiv = document.getElementById(`progress-${type}`);
    const progressBar = progressDiv.querySelector('.progress-bar');
    progressDiv.classList.remove('d-none');
    progressBar.style.width = '30%';
    progressBar.textContent = '30%';

    try {
        const response = await fetch('/api/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                fileIds: files.map(f => f.id),
                rules: type === 'text' ? rules : [],
                excelRules: type === 'excel' ? rules : [],
                activeTab: type,
                // Nieuwe parameters
                phonePlaceholder,
                emailPlaceholder,
                generalPlaceholder,
                autoDetectEnabled,
                reversibleMode,
                preserveFormatting
            })
        });

        const data = await response.json();

        progressBar.style.width = '70%';
        progressBar.textContent = '70%';

        if (data.success) {
            // NIET de upload lijst updaten - die blijft altijd "uploaded" status tonen
            // Alleen de resultaten sectie toont de geanonimiseerde versies

            renderResults(data.results, data.logs, data.statistics, type);
            showAlert('Anonimisatie succesvol!', 'success');

            // Count successfully anonymized files
            const anonymizedCount = data.results.filter(r => r.status === 'anonymized').length;

            // Show download all button only if:
            // - Multiple files (2+) were anonymized, OR
            // - Reversible mode is active (mapping.json needs to be included)
            if (anonymizedCount >= 2 || data.mappingAvailable) {
                document.getElementById('download-all-section').classList.remove('d-none');
            } else {
                // Hide ZIP button for single file without reversible mode
                document.getElementById('download-all-section').classList.add('d-none');
            }

            // Show mapping download button if reversible mode was used
            if (data.mappingAvailable && data.mappingId) {
                const mappingBtn = document.getElementById('download-mapping-btn');
                const mappingBadge = document.getElementById('mapping-count-badge');

                mappingBtn.classList.remove('d-none');
                mappingBtn.setAttribute('data-mapping-id', data.mappingId);

                if (data.totalMappings) {
                    mappingBadge.textContent = data.totalMappings;
                }
            }
        } else {
            showAlert(data.error || 'Processing mislukt', 'danger');
        }

        progressBar.style.width = '100%';
        progressBar.textContent = '100%';
        setTimeout(() => {
            progressDiv.classList.add('d-none');
            progressBar.style.width = '0%';
            progressBar.textContent = '0%';
        }, 1000);

    } catch (error) {
        console.error('Processing error:', error);
        showAlert('Fout bij verwerken: ' + error.message, 'danger');
        progressDiv.classList.add('d-none');
    } finally {
        state.processing = false;
    }
}

function renderResults(results, logs, statistics, type) {
    const resultsDiv = document.getElementById(`results-${type}`);

    let html = '';

    // Color scheme based on tab type
    const borderColor = type === 'text' ? '#2b579a' : '#217346';  // Word blue for text, green for excel
    const badgeClass = type === 'text' ? 'text-white' : 'bg-success';
    const badgeStyle = type === 'text' ? 'background-color: #0d267f;' : '';
    const manualColor = type === 'text' ? 'color: #0d267f;' : 'color: #217346;';

    // Statistieken sectie (alleen voor text tab met auto-detectie)
    if (statistics && (statistics.total_phones > 0 || statistics.total_emails > 0 || statistics.total_manual_replacements > 0)) {
        const totalItems = statistics.total_phones + statistics.total_emails + statistics.total_manual_replacements;

        html += `
            <div class="card mb-4" style="border-left: 4px solid ${borderColor};">
                <div class="card-body">
                    <h6 class="fw-bold mb-3">
                        Anonimisatie Statistieken
                    </h6>
                    <div class="row g-3">
                        <div class="col-md-4">
                            <div class="p-3 bg-light rounded">
                                <div class="text-muted small">Telefoonnummers</div>
                                <div class="fs-4 fw-bold" style="${manualColor}">${statistics.total_phones}</div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="p-3 bg-light rounded">
                                <div class="text-muted small">E-mailadressen</div>
                                <div class="fs-4 fw-bold" style="${manualColor}">${statistics.total_emails}</div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="p-3 bg-light rounded">
                                <div class="text-muted small">Handmatige Vervangingen</div>
                                <div class="fs-4 fw-bold" style="${manualColor}">${statistics.total_manual_replacements}</div>
                            </div>
                        </div>
                    </div>
                    <div class="mt-3 p-3 bg-white border rounded">
                        <strong>Totaal vervangen:</strong>
                        <span class="badge ${badgeClass} fs-6" style="${badgeStyle}">${totalItems} items</span>
                    </div>
                </div>
            </div>
        `;
    }

    // Eerst de Anonimisatie Log
    if (logs && logs.length > 0) {
        // Splits logs in auto-detect en manual
        const autoLogs = logs.filter(log => log.ruleId === 'auto_phone' || log.ruleId === 'auto_email');
        const manualLogs = logs.filter(log => log.ruleId !== 'auto_phone' && log.ruleId !== 'auto_email');

        html += `<h6 class="fw-bold mt-4 mb-3">Anonimisatie Log:</h6>`;

        // Auto-detectie logs
        if (autoLogs.length > 0) {
            html += `
                <div class="mb-3">
                    <div class="badge bg-info mb-2">Automatische Detectie</div>
                    <div class="table-responsive">
                        <table class="table ${type === 'excel' ? 'table-excel' : ''} table-sm table-striped">
                            <thead class="table-light">
                                <tr>
                                    <th>Type</th>
                                    <th>Pattern</th>
                                    <th>Vervangen door</th>
                                    <th>Aantal</th>
                                </tr>
                            </thead>
                            <tbody>
            `;

            autoLogs.forEach(log => {
                html += `
                    <tr>
                        <td><span class="badge bg-info">${log.ruleId === 'auto_phone' ? 'Telefoon' : 'Email'}</span></td>
                        <td>${escapeHtml(log.appliedPattern)}</td>
                        <td>${escapeHtml(log.replacedWith)}</td>
                        <td><strong>${log.count}</strong></td>
                    </tr>
                `;
            });

            html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        }

        // Handmatige logs
        if (manualLogs.length > 0) {
            html += `
                <div class="mb-3">
                    <div class="badge bg-secondary mb-2">Handmatige Regels (eerste 5)</div>
                    <div class="table-responsive">
                        <table class="table ${type === 'excel' ? 'table-excel' : ''} table-sm table-striped">
                            <thead class="table-light">
                                <tr>
                                    <th>Origineel</th>
                                    <th>Patroon/Kolom</th>
                                    <th>Vervangen door</th>
                                    <th>Aantal</th>
                                </tr>
                            </thead>
                            <tbody>
            `;

            manualLogs.slice(0, 5).forEach(log => {
                html += `
                    <tr>
                        <td>${escapeHtml(log.originalTermDisplay)}</td>
                        <td>${escapeHtml(log.appliedPattern)}</td>
                        <td>${escapeHtml(log.replacedWith)}</td>
                        <td>${log.count}</td>
                    </tr>
                `;
            });

            html += `
                            </tbody>
                        </table>
                    </div>
            `;

            if (manualLogs.length > 5) {
                html += `<p class="text-muted small">... en ${manualLogs.length - 5} meer log entries</p>`;
            }

            html += `</div>`;
        }
    }

    // Dan de Verwerkte Bestanden (downloads onderaan)
    html += '<h6 class="fw-bold mt-4 mb-3">Verwerkte Bestanden:</h6>';

    results.forEach(result => {
        const resultBorderClass = result.status === 'error' ? 'border-danger' : (type === 'text' ? 'success-blue' : 'success');

        html += `
            <div class="result-item ${resultBorderClass}">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong>${result.originalName}</strong>
                        ${result.status === 'anonymized' ?
                            `<span class="status-label ${type === 'excel' ? 'excel-green' : ''}">ANONYMIZED</span>` :
                            result.status === 'error' ?
                                `<span class="badge bg-danger ms-2">${result.status}</span>` :
                                `<span class="badge bg-secondary ms-2">${result.status}</span>`}
                    </div>
                    ${result.status === 'anonymized' ?
                        `<button class="btn btn-sm ${type === 'excel' ? 'btn-excel-green' : 'btn-word-blue'}" onclick="downloadFile('${result.id}')">
                            Download
                        </button>` :
                        ''}
                </div>
                ${result.error ? `<div class="text-danger mt-2 small">${result.error}</div>` : ''}
            </div>
        `;
    });

    resultsDiv.innerHTML = html;

    // Toon Excel waarschuwing info alleen voor Excel tab en alleen als er downloads zijn
    const hasDownloads = results.some(r => r.status === 'anonymized');
    const excelWarningInfo = document.getElementById('excel-warning-info');
    if (type === 'excel' && hasDownloads && excelWarningInfo) {
        excelWarningInfo.classList.remove('d-none');
    } else if (excelWarningInfo) {
        excelWarningInfo.classList.add('d-none');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ========== Download Functions ==========
function downloadFile(fileId) {
    window.location.href = `/api/download/${fileId}`;
}

function setupDownloadAll() {
    document.getElementById('download-all-btn').addEventListener('click', () => {
        window.location.href = '/api/download-all';
    });

    document.getElementById('download-mapping-btn').addEventListener('click', () => {
        const mappingId = document.getElementById('download-mapping-btn').getAttribute('data-mapping-id');
        if (mappingId) {
            window.location.href = `/api/download-mapping/${mappingId}`;
        } else {
            showAlert('Mapping ID niet gevonden', 'danger');
        }
    });

    // Setup beide clear session knoppen (top en bottom)
    const setupClearSession = (buttonId) => {
        const button = document.getElementById(buttonId);
        if (button) {
            button.addEventListener('click', async () => {
                if (!confirm('Weet je zeker dat je een nieuwe sessie wilt starten? Alle huidige bestanden en regels worden verwijderd.')) {
                    return;
                }

                try {
                    const response = await fetch('/api/cleanup', {
                        method: 'POST'
                    });

                    if (response.ok) {
                        showAlert('Sessie opgeschoond! Pagina wordt herladen...', 'success');

                        // Reset state
                        state.files.text = [];
                        state.files.excel = [];
                        state.rules.text = [];
                        state.rules.excel = [];

                        // Reload page after short delay
                        setTimeout(() => {
                            window.location.reload();
                        }, 1500);
                    } else {
                        showAlert('Fout bij opschonen van sessie', 'danger');
                    }
                } catch (error) {
                    console.error('Cleanup error:', error);
                    showAlert('Fout bij opschonen: ' + error.message, 'danger');
                }
            });
        }
    };

    setupClearSession('clear-session-btn-top');  // Knop in instellingen (altijd zichtbaar)
    setupClearSession('clear-session-btn');      // Knop na downloads (optioneel)
}

// ========== Tab Management ==========
function setupTabs() {
    document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
        tab.addEventListener('shown.bs.tab', (e) => {
            const target = e.target.getAttribute('data-bs-target');
            state.activeTab = target.includes('text') ? 'text' : 'excel';

            // Update de-anonimisatie sectie kleuren op basis van actieve tab
            updateDeanonColors(state.activeTab);
        });
    });

    // Set initial color (text tab is standaard actief)
    updateDeanonColors('text');
}

function updateDeanonColors(tab) {
    const deanonCard = document.querySelector('.deanon-card');
    const deanonHeader = document.querySelector('.deanon-header');
    const deanonButton = document.querySelector('.deanon-button');
    const downloadAllBtn = document.querySelector('.download-all-btn');

    if (tab === 'excel') {
        deanonCard?.classList.add('excel-mode');
        deanonHeader?.classList.add('excel-mode');
        deanonButton?.classList.add('excel-mode');

        // Download All button: groen voor Excel
        downloadAllBtn?.classList.remove('btn-word-blue');
        downloadAllBtn?.classList.add('btn-excel-green');

        // NIET het excel warning info tonen - dat doet renderResults()
    } else {
        deanonCard?.classList.remove('excel-mode');
        deanonHeader?.classList.remove('excel-mode');
        deanonButton?.classList.remove('excel-mode');

        // Download All button: blauw voor Text
        downloadAllBtn?.classList.remove('btn-excel-green');
        downloadAllBtn?.classList.add('btn-word-blue');

        // Verberg Excel waarschuwing info bij text tab
        const excelWarningInfo = document.getElementById('excel-warning-info');
        excelWarningInfo?.classList.add('d-none');
    }
}

// ========== De-Anonimisatie ==========
function setupDeanonymization() {
    document.getElementById('deanonymize-btn').addEventListener('click', async () => {
        const anonymizedFileInput = document.getElementById('reverse-anonymized-file');
        const mappingFileInput = document.getElementById('reverse-mapping-file');
        const resultsDiv = document.getElementById('reverse-results');

        // Valideer dat beide bestanden zijn geselecteerd
        if (!anonymizedFileInput.files.length || !mappingFileInput.files.length) {
            showAlert('Selecteer beide bestanden (geanonimiseerd bestand + mapping.json)', 'warning');
            return;
        }

        const anonymizedFile = anonymizedFileInput.files[0];
        const mappingFile = mappingFileInput.files[0];

        // Valideer mapping file extensie
        if (!mappingFile.name.endsWith('.json')) {
            showAlert('Mapping bestand moet een .json bestand zijn', 'danger');
            return;
        }

        try {
            // Maak FormData
            const formData = new FormData();
            formData.append('anonymized_file', anonymizedFile);
            formData.append('mapping_file', mappingFile);

            // Toon loading state
            resultsDiv.innerHTML = `
                <div class="alert alert-info">
                    <div class="spinner-border spinner-border-sm me-2" role="status">
                        <span class="visually-hidden">Laden...</span>
                    </div>
                    Bezig met de-anonimiseren...
                </div>
            `;

            // Send request
            const response = await fetch('/api/reverse', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                // Download het bestand
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `deanon_${anonymizedFile.name}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                // Toon success
                resultsDiv.innerHTML = `
                    <div class="alert alert-success">
                        <strong>✓ Succes!</strong> Het bestand is succesvol de-geanonimiseerd en gedownload.
                        <br><small>Bestandsnaam: deanon_${anonymizedFile.name}</small>
                    </div>
                `;

                showAlert('De-anonimisatie succesvol!', 'success');

                // Clear file inputs
                anonymizedFileInput.value = '';
                mappingFileInput.value = '';
            } else {
                const errorData = await response.json();
                resultsDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>✗ Fout:</strong> ${errorData.error || 'Onbekende fout'}
                    </div>
                `;
                showAlert(errorData.error || 'De-anonimisatie mislukt', 'danger');
            }
        } catch (error) {
            console.error('De-anonymization error:', error);
            resultsDiv.innerHTML = `
                <div class="alert alert-danger">
                    <strong>✗ Fout:</strong> ${error.message}
                </div>
            `;
            showAlert('Fout bij de-anonimiseren: ' + error.message, 'danger');
        }
    });
}

// ========== Initialization ==========
document.addEventListener('DOMContentLoaded', () => {
    setupDropzones();
    setupRuleInputs();
    setupProcessing();
    setupDownloadAll();
    setupTabs();
    setupDeanonymization();

    // Initialiseer Bootstrap tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

    console.log('Flask Anonimiseren Tool initialized');
});

// ========== Excel Preview ==========
function showPreviewModal(data) {
    // Auto-detect column content types
    const autoDetections = detectColumnTypes(data.headers, data.rows);

    // Build auto-detect suggestions HTML
    let suggestionsHtml = '';
    if (autoDetections.length > 0) {
        suggestionsHtml = `
            <div class="alert alert-info mt-0 mb-3" id="auto-detect-suggestions">
                <h6><i class="bi bi-lightbulb me-2"></i>Auto-detect Suggesties</h6>
                <p class="mb-2">De volgende kolommen bevatten mogelijk gevoelige informatie:</p>
                <div id="suggestions-list">
                    ${autoDetections.map(det => `
                        <div class="suggestion-item mb-2 p-2 bg-white rounded" data-column="${escapeHtml(det.column)}">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>${escapeHtml(det.column)}</strong> bevat <span class="badge bg-warning text-dark">${det.type}</span>
                                    <small class="text-muted d-block">Suggestie: Maskeer met "${escapeHtml(det.suggested_mask)}"</small>
                                </div>
                                <div class="btn-group btn-group-sm">
                                    <button class="btn btn-success accept-suggestion" data-column="${escapeHtml(det.column)}" data-type="${det.type}" data-mask="${escapeHtml(det.suggested_mask)}">
                                        <i class="bi bi-check-lg"></i> Accepteer
                                    </button>
                                    <button class="btn btn-outline-secondary reject-suggestion" data-column="${escapeHtml(det.column)}">
                                        <i class="bi bi-x-lg"></i> Negeer
                                    </button>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // Maak table HTML
    let tableHtml = `
        <div class="alert mb-3" style="background-color: #d4edda; border-color: #217346;">
            <strong>${data.filename}</strong><br>
            <small>Totaal aantal rijen (excl. header): ${data.total_rows}</small>
        </div>
        ${suggestionsHtml}

        <!-- Column Search Box -->
        <div class="mb-3">
            <div class="input-group">
                <span class="input-group-text"><i class="bi bi-search"></i></span>
                <input type="text" class="form-control" id="column-search" placeholder="Zoek kolommen... (bijv. 'email', 'naam', 'adres')">
                <button class="btn btn-outline-secondary" id="clear-search" type="button">
                    <i class="bi bi-x-lg"></i>
                </button>
            </div>
            <small class="text-muted">Gevonden: <span id="column-count-display">${data.headers.length}</span> van ${data.headers.length} kolommen</small>
        </div>

        <!-- Column Headers (Visual Pills) -->
        <div class="column-headers-container mb-3">
            <div class="column-headers" id="column-headers">
                ${data.headers.map((col, idx) => `
                    <div class="column-header" data-column-name="${escapeHtml(col).toLowerCase()}" data-column-index="${idx}" onclick="fillColumnName('${escapeHtml(col).replace(/'/g, "\\'")}', 'excelPreviewModal')" title="Klik om '${escapeHtml(col)}' in te vullen">
                        ${escapeHtml(col)}
                    </div>
                `).join('')}
            </div>
        </div>

        <p class="text-muted small mb-2">
            <strong>💡 Tip:</strong> Klik op een kolomnaam om deze automatisch in te vullen bij "Stap 1: Kolomnaam"
        </p>

        <!-- Preview Data Table -->
        <div class="table-responsive">
            <table class="table table-sm table-bordered">
                <thead style="background-color: #217346 !important; color: white !important;">
                    <tr>
                        ${data.headers.map(h => `<th style="background-color: #217346 !important; color: white !important;">${escapeHtml(h)}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${data.rows.map(row => `
                        <tr>
                            ${row.map(cell => `<td>${escapeHtml(cell)}</td>`).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
        <p class="text-muted small mt-2">Toont eerste 5 rijen.</p>
    `;

    // Maak complete modal HTML
    const modalHtml = `
        <div class="modal fade" id="excelPreviewModal" tabindex="-1">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header" style="background-color: #217346; color: white; border: none;">
                        <h5 class="modal-title">Excel Preview</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        ${tableHtml}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-success" data-bs-dismiss="modal" style="background-color: #217346; border-color: #217346;">Sluiten</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Verwijder oude modal als die er is
    const oldModal = document.getElementById('excelPreviewModal');
    if (oldModal) {
        const instance = bootstrap.Modal.getInstance(oldModal);
        if (instance) instance.dispose();
        oldModal.remove();
    }

    // Voeg modal toe en toon
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modalElement = document.getElementById('excelPreviewModal');
    const modal = new bootstrap.Modal(modalElement);
    modal.show();

    // Cleanup na sluiten
    const cleanupModal = () => {
        const element = document.getElementById('excelPreviewModal');
        if (element) {
            const instance = bootstrap.Modal.getInstance(element);
            if (instance) instance.dispose();
            element.remove();
        }
    };

    modalElement.addEventListener('hidden.bs.modal', cleanupModal, { once: true });

    // Setup event handlers for auto-detect suggestions and column search
    setupPreviewEventHandlers();
}

function detectColumnTypes(headers, previewRows) {
    /**
     * Detect column content types from preview data.
     * Returns array of detections with column name, type, and suggested mask.
     */
    const detections = [];

    headers.forEach((colName, colIdx) => {
        // Extract column values from preview (filter out empty values)
        const colValues = previewRows
            .map(row => row[colIdx])
            .filter(v => v !== null && v !== undefined && String(v).trim() !== '');

        if (colValues.length === 0) {
            return; // Skip empty columns
        }

        // Email detection (simple pattern)
        const emailPattern = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/;
        const emailCount = colValues.filter(v => emailPattern.test(String(v))).length;
        if (emailCount / colValues.length > 0.5) {  // >50% emails
            detections.push({
                column: colName,
                type: 'emails',
                suggested_mask: '[EMAIL VERWIJDERD]'
            });
            return;
        }

        // Phone detection (Dutch patterns - simplified)
        const phonePattern = /(\+31|0031|0)[1-9]\d{8}|(\(0\d{2,3}\)|0\d{2,3})[-\s]?\d{7}/;
        const phoneCount = colValues.filter(v => phonePattern.test(String(v).replace(/\s/g, ''))).length;
        if (phoneCount / colValues.length > 0.5) {  // >50% phones
            detections.push({
                column: colName,
                type: 'telefoonnummers',
                suggested_mask: '[TEL VERWIJDERD]'
            });
        }
    });

    return detections;
}

// Global flag to prevent duplicate event listeners
let previewEventHandlersSetup = false;

function setupPreviewEventHandlers() {
    // Only setup once to avoid duplicate listeners
    if (previewEventHandlersSetup) return;
    previewEventHandlersSetup = true;

    // ===== Auto-detect Suggestion Handlers =====
    // Use vanilla JS event delegation on document since modal is dynamic

    // Accept suggestion handler
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('accept-suggestion') || e.target.closest('.accept-suggestion')) {
            const button = e.target.classList.contains('accept-suggestion') ? e.target : e.target.closest('.accept-suggestion');
            const column = button.getAttribute('data-column');
            const type = button.getAttribute('data-type');
            const mask = button.getAttribute('data-mask');

            // Create Excel rule directly
            const rule = {
                id: generateId(),
                columnName: column,
                columnType: 'text',
                anonymizationType: 'replace',
                replaceWith: mask,
                reversible: false
            };

            state.rules.excel.push(rule);
            renderRulesList('excel');

            // Remove suggestion
            const suggestionItem = button.closest('.suggestion-item');
            if (suggestionItem) {
                suggestionItem.style.opacity = '0';
                suggestionItem.style.transition = 'opacity 300ms';
                setTimeout(() => {
                    suggestionItem.remove();

                    // Hide container if no more suggestions
                    const suggestionsList = document.getElementById('suggestions-list');
                    if (suggestionsList && suggestionsList.querySelectorAll('.suggestion-item').length === 0) {
                        const autoDetectBox = document.getElementById('auto-detect-suggestions');
                        if (autoDetectBox) {
                            autoDetectBox.style.opacity = '0';
                            autoDetectBox.style.transition = 'opacity 300ms';
                            setTimeout(() => autoDetectBox.remove(), 300);
                        }
                    }
                }, 300);
            }

            // Show success alert
            showAlert(`Regel toegevoegd: "${column}" wordt vervangen door "${mask}"`, 'success');
        }
    });

    // Reject suggestion handler
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('reject-suggestion') || e.target.closest('.reject-suggestion')) {
            const button = e.target.classList.contains('reject-suggestion') ? e.target : e.target.closest('.reject-suggestion');

            // Remove suggestion
            const suggestionItem = button.closest('.suggestion-item');
            if (suggestionItem) {
                suggestionItem.style.opacity = '0';
                suggestionItem.style.transition = 'opacity 300ms';
                setTimeout(() => {
                    suggestionItem.remove();

                    // Hide container if no more suggestions
                    const suggestionsList = document.getElementById('suggestions-list');
                    if (suggestionsList && suggestionsList.querySelectorAll('.suggestion-item').length === 0) {
                        const autoDetectBox = document.getElementById('auto-detect-suggestions');
                        if (autoDetectBox) {
                            autoDetectBox.style.opacity = '0';
                            autoDetectBox.style.transition = 'opacity 300ms';
                            setTimeout(() => autoDetectBox.remove(), 300);
                        }
                    }
                }, 300);
            }
        }
    });

    // ===== Column Search Handlers =====

    // Column search input handler
    document.addEventListener('input', function(e) {
        if (e.target.id === 'column-search') {
            const searchTerm = e.target.value.toLowerCase().trim();
            const columnHeaders = document.querySelectorAll('.column-header');
            const totalColumns = columnHeaders.length;

            if (searchTerm === '') {
                // Show all columns
                columnHeaders.forEach(header => header.style.display = '');
                updateColumnCount(totalColumns, totalColumns);
                return;
            }

            // Filter columns
            let visibleCount = 0;
            columnHeaders.forEach(header => {
                const columnName = header.getAttribute('data-column-name');

                if (columnName && columnName.includes(searchTerm)) {
                    header.style.display = '';
                    visibleCount++;
                } else {
                    header.style.display = 'none';
                }
            });

            updateColumnCount(visibleCount, totalColumns);
        }
    });

    // Clear search button handler
    document.addEventListener('click', function(e) {
        if (e.target.id === 'clear-search' || e.target.closest('#clear-search')) {
            const searchInput = document.getElementById('column-search');
            if (searchInput) {
                searchInput.value = '';
                const columnHeaders = document.querySelectorAll('.column-header');
                const totalColumns = columnHeaders.length;
                columnHeaders.forEach(header => header.style.display = '');
                updateColumnCount(totalColumns, totalColumns);
            }
        }
    });
}

function updateColumnCount(visible, total) {
    const countDisplay = document.getElementById('column-count-display');
    if (countDisplay) {
        countDisplay.textContent = visible;

        // Highlight if filtering
        if (visible < total) {
            countDisplay.classList.add('text-warning', 'fw-bold');
        } else {
            countDisplay.classList.remove('text-warning', 'fw-bold');
        }
    }
}

async function showExcelPreview(fileId) {
    // Check of we al cached data hebben
    const cachedData = state.previewCache[fileId];

    if (cachedData) {
        // Gebruik cached data - toon direct zonder loading
        showPreviewModal(cachedData);
        return;
    }

    // Toon loading indicator (alleen bij eerste keer)
    const loadingHtml = `
        <div class="modal fade" id="excelPreviewModal" tabindex="-1">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-body text-center py-5">
                        <div class="spinner-border text-success" role="status" style="color: #217346 !important;">
                            <span class="visually-hidden">Laden...</span>
                        </div>
                        <p class="mt-3 text-muted">Preview laden...</p>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Toon loading modal direct
    document.body.insertAdjacentHTML('beforeend', loadingHtml);
    const loadingModal = new bootstrap.Modal(document.getElementById('excelPreviewModal'));
    loadingModal.show();

    try {
        const response = await fetch(`/api/excel-preview/${fileId}`);
        const data = await response.json();

        if (!data.success) {
            // Verwijder loading modal bij error
            loadingModal.hide();
            setTimeout(() => {
                const loadingEl = document.getElementById('excelPreviewModal');
                if (loadingEl) loadingEl.remove();
            }, 300);
            showAlert(data.error || 'Preview laden mislukt', 'danger');
            return;
        }

        // Transform multi-sheet structure to single-sheet format for preview
        // (Use first sheet for now)
        const firstSheet = data.sheets && data.sheets.length > 0 ? data.sheets[0] : null;

        if (!firstSheet) {
            loadingModal.hide();
            setTimeout(() => {
                const loadingEl = document.getElementById('excelPreviewModal');
                if (loadingEl) loadingEl.remove();
            }, 300);
            showAlert('Geen sheets gevonden in Excel bestand', 'danger');
            return;
        }

        // Transform to old format expected by showPreviewModal
        const transformedData = {
            filename: data.filename,
            headers: firstSheet.columns || [],
            rows: firstSheet.preview || [],
            total_rows: firstSheet.rows || 0
        };

        // Cache de data
        state.previewCache[fileId] = transformedData;

        // Verwijder loading modal en toon preview
        loadingModal.hide();
        setTimeout(() => {
            const loadingEl = document.getElementById('excelPreviewModal');
            if (loadingEl) loadingEl.remove();
            showPreviewModal(transformedData);
        }, 300);

    } catch (error) {
        // Verwijder loading modal ook bij exception
        const loadingEl = document.getElementById('excelPreviewModal');
        if (loadingEl) {
            const instance = bootstrap.Modal.getInstance(loadingEl);
            if (instance) instance.dispose();
            loadingEl.remove();
        }
        console.error('Preview error:', error);
        showAlert('Fout bij laden van preview: ' + error.message, 'danger');
    }
}

// Fill column name from preview
function fillColumnName(columnName, modalId) {
    // Vul de kolomnaam in
    const columnInput = document.getElementById('excel-column-name');
    if (columnInput) {
        columnInput.value = columnName;
        columnInput.focus();
    }

    // Sluit de modal
    const modalElement = document.getElementById(modalId);
    if (modalElement) {
        const modalInstance = bootstrap.Modal.getInstance(modalElement);
        if (modalInstance) {
            modalInstance.hide();
        }
    }
}

// Make functions globally accessible for onclick handlers
window.removeFile = removeFile;
window.removeRule = removeRule;
window.downloadFile = downloadFile;
window.fillColumnName = fillColumnName;
window.showExcelPreview = showExcelPreview;
