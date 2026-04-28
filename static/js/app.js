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
    
    if (!prompt.trim()) {
        log('❌ Error: El prompt no puede estar vacío', 'error');
        return;
    }
    
    // UI Estado de carga
    generateBtn.disabled = true;
    generateBtn.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">GENERANDO...</span>';
    terminalStatus.textContent = '● Procesando';
    terminalStatus.classList.add('processing');
    log(`🚀 Iniciando generación con modelo: ${modelId}`, 'info');
    log(`📝 Tipo de entrada: ${inputType}`, 'info');
    
    try {
        // Primero: obtener preview JSON
        log('🤖 Consultando IA para estructura...', 'info');
        const jsonResponse = await fetch(`${API_BASE}/generate/json`, {
            method: 'POST',
            headers: