/**
 * PPTX Studio — Intelligent Edition
 * Frontend SPA Controller
 */

const API_BASE = '';

// Estado global
let currentModels = [];
let generatedStructure = null;

// DOM Elements
const modelSelector = document.getElementById('modelSelector');
const modelInfo = document.getElementById('modelInfo');
const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');
const generateBtn = document.getElementById('generateBtn');
const terminalBody = document.getElementById('terminalBody');
const terminalStatus = document.getElementById('terminalStatus');
const previewContent = document.getElementById('previewContent');
const jsonModal = document.getElementById('jsonModal');
const jsonContent = document.getElementById('jsonContent');
const previewJsonBtn = document.getElementById('previewJsonBtn');
const closeModal = document.getElementById('closeModal');

// ── Inicialización ───────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    loadModels();
    setupEventListeners();
    log('Sistema inicializado. Listo para generar presentaciones.', 'system');
});

// ── Carga de Modelos ─────────────────────────────────────────────────────

async function loadModels() {
    try {
        const response = await fetch(`${API_BASE}/models`);
        const data = await response.json();
        currentModels = data.models || [];
        
        // Poblar selector
        modelSelector.innerHTML = currentModels.map(m => 
            `<option value="${m.id}">${m.name}</option>`
        ).join('');
        
        // Seleccionar default
        if (data.default_model) {
            modelSelector.value = data.default_model;
        }
        
        updateModelInfo();
        log(`Modelos cargados: ${currentModels.length} disponibles`, 'success');
    } catch (error) {
        log(`Error cargando modelos: ${error.message}`, 'error');
        modelSelector.innerHTML = '<option>Error cargando</option>';
    }
}

function updateModelInfo() {
    const selected = currentModels.find(m => m.id === modelSelector.value);
    if (selected) {
        modelInfo.textContent = selected.description;
    }
}

// ── Event Listeners ──────────────────────────────────────────────────────

function setupEventListeners() {
    // Tabs
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            switchTab(tab);
        });
    });
    
    // Model selector
    modelSelector.addEventListener('change', updateModelInfo);
    
    // Generate
    generateBtn.addEventListener('click', generatePresentation);
    
    // JSON Modal
    previewJsonBtn.addEventListener('click', showJsonModal);
    closeModal.addEventListener('click', hideJsonModal);
    jsonModal.addEventListener('click', (e) => {
        if (e.target === jsonModal) hideJsonModal();
    });
}

function switchTab(tabName) {
    tabBtns.forEach(b => b.classList.toggle('active', b.dataset.tab === tabName));
    tabContents.forEach(c => c.classList.toggle('active', c.id === `tab-${tabName}`));
}

// ── Generación de Presentación ───────────────────────────────────────────

async function generatePresentation() {
    const activeTab = document.querySelector('.tab-btn.active').dataset.tab;
    const modelId = modelSelector.value;
    
    // Obtener input según tab activo
    let prompt = '';
    let inputType = '';
    let file = null;
    
    switch(activeTab) {
        case 'summary':
            prompt = document.getElementById('promptInput').value;
            inputType = 'summary';
            break;
        case 'extensive':
            prompt = document.getElementById('extensiveInput').value;
            inputType = 'extensive_notes';
            break;
        case 'research':
            prompt = document.getElementById('researchInput').value;
            inputType = 'research';
            break;
        case 'import':
            prompt = document.getElementById('importPrompt').value;
            inputType = 'pptx_import';
            file = document.getElementById('pptxFile').files[0];
            break;
    }
    
    if (!prompt.trim() && !file) {
        log('❌ Error: El prompt no puede estar vacío', 'error');
        return;
    }
    
    const includeImages = document.getElementById('includeImages').checked;
    const filename = document.getElementById('filename').value || 'presentacion.pptx';
    
    // UI Estado de carga
    generateBtn.disabled = true;
    generateBtn.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">GENERANDO...</span>';
    terminalStatus.textContent = '● Procesando';
    terminalStatus.classList.add('processing');
    log(`🚀 Iniciando generación con modelo: ${modelId}`, 'info');
    log(`📝 Tipo de entrada: ${inputType}`, 'info');
    
    try {
        // Si es importación, primero subimos el archivo
        let formData = new FormData();
        formData.append('prompt', prompt);
        formData.append('input_type', inputType);
        formData.append('model_id', modelId);
        formData.append('include_images', includeImages);
        formData.append('filename', filename);
        const theme = document.getElementById('themeSelector')?.value || 'pitchsync_dark';
        formData.append('theme', theme);
        
        if (file) {
            formData.append('file', file);
            log(`📁 Archivo adjunto: ${file.name}`, 'info');
        }
        
        // Primero: obtener preview JSON
        log('🤖 Consultando IA para estructura...', 'info');
        const theme = document.getElementById('themeSelector')?.value || 'pitchsync_dark';
        
        const jsonResponse = await fetch(`${API_BASE}/generate/json`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                prompt: prompt,
                input_type: inputType,
                model_id: modelId,
                theme: theme
            })
        });
        
        const jsonData = await jsonResponse.json();
        
        if (!jsonData.success) {
            throw new Error(jsonData.error || 'Error generando estructura');
        }
        
        generatedStructure = jsonData.structure;
        log('✅ Estructura JSON recibida', 'success');
        renderPreview(generatedStructure);
        
        // Segundo: generar el PPTX completo
        log('🎨 Generando archivo PPTX...', 'info');
        
        const pptxResponse = await fetch(`${API_BASE}/generate`, {
            method: 'POST',
            body: formData
        });
        
        if (!pptxResponse.ok) {
            const errorText = await pptxResponse.text();
            throw new Error(`Error ${pptxResponse.status}: ${errorText}`);
        }
        
        // Descargar archivo
        const blob = await pptxResponse.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        // Leer headers de respuesta
        const modelUsed = pptxResponse.headers.get('X-Model-Used') || 'unknown';
        const slideCount = pptxResponse.headers.get('X-Slide-Count') || '?';
        
        log(`✅ ¡Presentación generada exitosamente!`, 'success');
        log(`📊 Modelo: ${modelUsed} | Slides: ${slideCount}`, 'success');
        log(`💾 Descargado: ${filename}`, 'success');
        
    } catch (error) {
        log(`❌ Error: ${error.message}`, 'error');
        console.error(error);
    } finally {
        // Restaurar UI
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<span class="btn-icon">⚡</span><span class="btn-text">GENERAR PRESENTACIÓN</span>';
        terminalStatus.textContent = '● Listo';
        terminalStatus.classList.remove('processing');
    }
}

// ── Renderizado de Preview ───────────────────────────────────────────────

function renderPreview(structure) {
    if (!structure || !structure.slides) {
        previewContent.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚠️</div>
                <p>No se pudo cargar la estructura</p>
            </div>
        `;
        return;
    }
    
    const slides = structure.slides;
    const title = structure.title || 'Sin título';
    const subtitle = structure.subtitle || '';
    
    let html = `
        <div style="margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-color);">
            <h2 style="color: var(--neon-primary); font-family: var(--font-title); margin-bottom: 0.3rem;">
                ${escapeHtml(title)}
            </h2>
            ${subtitle ? `<p style="color: var(--text-secondary);">${escapeHtml(subtitle)}</p>` : ''}
            <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 0.5rem;">
                ${slides.length} diapositivas • Modelo: ${structure._meta?.model_name || 'Unknown'}
            </p>
        </div>
    `;
    
    slides.forEach((slide, index) => {
        const slideType = slide.type || 'content_slide';
        const typeLabels = {
            'title_slide': 'Portada',
            'content_slide': 'Contenido',
            'split_slide': 'Dividido',
            'image_slide': 'Imagen',
            'section_divider': 'Sección'
        };
        
        html += `
            <div class="slide-preview">
                <div class="slide-preview-header">
                    <span class="slide-number">#${index + 1}</span>
                    <span class="slide-type">${typeLabels[slideType] || slideType}</span>
                </div>
                <h4>${escapeHtml(slide.title || 'Sin título')}</h4>
                ${renderBullets(slide.bullets)}
                ${slide.notes ? `<div class="slide-notes">📝 ${escapeHtml(slide.notes.substring(0, 100))}${slide.notes.length > 100 ? '...' : ''}</div>` : ''}
                ${slide.image_prompt ? `<div style="margin-top: 0.5rem; color: var(--neon-secondary); font-size: 0.8rem;">🖼️ Imagen: ${escapeHtml(slide.image_prompt.substring(0, 60))}...</div>` : ''}
            </div>
        `;
    });
    
    previewContent.innerHTML = html;
}

function renderBullets(bullets) {
    if (!bullets || bullets.length === 0) return '';
    
    const items = bullets.slice(0, 4).map(b => `<li>${escapeHtml(b)}</li>`).join('');
    const more = bullets.length > 4 ? `<li style="color: var(--text-muted);">+ ${bullets.length - 4} más...</li>` : '';
    
    return `<ul>${items}${more}</ul>`;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ── Terminal Logging ─────────────────────────────────────────────────────

function log(message, type = 'info') {
    const line = document.createElement('div');
    line.className = `terminal-line ${type}`;
    
    const timestamp = new Date().toLocaleTimeString('es-ES', { 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit' 
    });
    
    line.textContent = `[${timestamp}] ${message}`;
    terminalBody.appendChild(line);
    terminalBody.scrollTop = terminalBody.scrollHeight;
}

// ── Modal JSON ───────────────────────────────────────────────────────────

function showJsonModal() {
    if (!generatedStructure) {
        log('⚠️ No hay estructura para mostrar', 'warning');
        return;
    }
    
    jsonContent.textContent = JSON.stringify(generatedStructure, null, 2);
    jsonModal.classList.add('active');
}

function hideJsonModal() {
    jsonModal.classList.remove('active');
}

// ── Utilidades ───────────────────────────────────────────────────────────

function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// ── Drag & Drop para archivo ─────────────────────────────────────────────

const fileUpload = document.querySelector('.file-upload');
const fileInput = document.getElementById('pptxFile');

if (fileUpload && fileInput) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        fileUpload.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        fileUpload.addEventListener(eventName, () => {
            fileUpload.querySelector('label').style.borderColor = 'var(--neon-primary)';
            fileUpload.querySelector('label').style.background = 'rgba(0, 229, 204, 0.1)';
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        fileUpload.addEventListener(eventName, () => {
            fileUpload.querySelector('label').style.borderColor = '';
            fileUpload.querySelector('label').style.background = '';
        }, false);
    });
    
    fileUpload.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        fileInput.files = files;
        
        if (files[0]) {
            const label = fileUpload.querySelector('label');
            label.textContent = `📁 ${files[0].name} (${formatBytes(files[0].size)})`;
            log(`📁 Archivo seleccionado: ${files[0].name}`, 'info');
        }
    }
    
    fileInput.addEventListener('change', () => {
        if (fileInput.files[0]) {
            const label = fileUpload.querySelector('label');
            label.textContent = `📁 ${fileInput.files[0].name} (${formatBytes(fileInput.files[0].size)})`;
            log(`📁 Archivo seleccionado: ${fileInput.files[0].name}`, 'info');
        }
    });
}

// ── Keyboard Shortcuts ───────────────────────────────────────────────────

document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Enter para generar
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        generatePresentation();
    }
    
    // Escape para cerrar modal
    if (e.key === 'Escape') {
        hideJsonModal();
    }
});

log('Atajos de teclado: Ctrl+Enter = Generar, Escape = Cerrar modal', 'info');