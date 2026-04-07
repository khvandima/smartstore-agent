// ─── КОНФИГУРАЦИЯ ───────────────────────────────────────────────
// const API_BASE = 'http://localhost:8000';
const API_BASE = '';

// ─── СОСТОЯНИЕ ──────────────────────────────────────────────────
let token = localStorage.getItem('token') || null;
let userEmail = localStorage.getItem('userEmail') || null;
let threadId = localStorage.getItem('threadId') || generateUUID();
let currentReportType = null;
let isLoading = false;

// ─── ИНИЦИАЛИЗАЦИЯ ──────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    if (token) {
        showApp();
    } else {
        showAuthScreen();
    }
});

// ─── УТИЛИТЫ ────────────────────────────────────────────────────
function generateUUID() {
    const uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
        const r = Math.random() * 16 | 0;
        return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
    localStorage.setItem('threadId', uuid);
    return uuid;
}

function api(path, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return fetch(`${API_BASE}${path}`, { ...options, headers });
}

function showToast(message, type = 'default') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 3500);
}

// ─── АВТОРИЗАЦИЯ ────────────────────────────────────────────────
function showAuthScreen() {
    document.getElementById('auth-screen').classList.remove('hidden');
    document.getElementById('app').classList.add('hidden');
}

function showApp() {
    document.getElementById('auth-screen').classList.add('hidden');
    document.getElementById('app').classList.remove('hidden');

    // Обновляем UI пользователя
    if (userEmail) {
        document.getElementById('user-email').textContent = userEmail;
        document.getElementById('user-avatar').textContent = userEmail[0].toUpperCase();
    }

    loadDocuments();
}

function switchAuthTab(tab) {
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.auth-form').forEach(f => f.classList.add('hidden'));

    event.target.classList.add('active');
    document.getElementById(`${tab}-form`).classList.remove('hidden');
}

async function login() {
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    const errorEl = document.getElementById('login-error');
    errorEl.classList.add('hidden');

    if (!email || !password) {
        errorEl.textContent = 'Заполните все поля';
        errorEl.classList.remove('hidden');
        return;
    }

    try {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);

        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            errorEl.textContent = 'Неверный email или пароль';
            errorEl.classList.remove('hidden');
            return;
        }

        const data = await res.json();
        token = data.access_token;
        userEmail = email;
        localStorage.setItem('token', token);
        localStorage.setItem('userEmail', userEmail);
        showApp();
    } catch (e) {
        errorEl.textContent = 'Ошибка подключения к серверу';
        errorEl.classList.remove('hidden');
    }
}

async function register() {
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;
    const errorEl = document.getElementById('register-error');
    errorEl.classList.add('hidden');

    if (!email || !password) {
        errorEl.textContent = 'Заполните все поля';
        errorEl.classList.remove('hidden');
        return;
    }

    if (password.length < 6) {
        errorEl.textContent = 'Пароль должен быть не менее 6 символов';
        errorEl.classList.remove('hidden');
        return;
    }

    try {
        const res = await api('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });

        if (!res.ok) {
            const data = await res.json();
            errorEl.textContent = data.detail || 'Ошибка регистрации';
            errorEl.classList.remove('hidden');
            return;
        }

        showToast('Аккаунт создан! Войдите в систему.', 'success');
        switchAuthTab('login');
        document.getElementById('login-email').value = email;
    } catch (e) {
        errorEl.textContent = 'Ошибка подключения к серверу';
        errorEl.classList.remove('hidden');
    }
}

function logout() {
    token = null;
    userEmail = null;
    localStorage.removeItem('token');
    localStorage.removeItem('userEmail');
    showAuthScreen();
}

// ─── НАВИГАЦИЯ ──────────────────────────────────────────────────
function switchTab(tab) {
    document.querySelectorAll('.tab-section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    document.getElementById(`tab-${tab}`).classList.add('active');
    document.getElementById(`nav-${tab}`).classList.add('active');

    if (tab === 'documents') loadDocuments();
}

// ─── ЧАТ ────────────────────────────────────────────────────────
function handleChatKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function newSession() {
    threadId = generateUUID();
    const messagesEl = document.getElementById('chat-messages');
    messagesEl.innerHTML = `
        <div class="message agent">
            <div class="message-avatar">AI</div>
            <div class="message-bubble">
                Новый диалог начат. Чем могу помочь?
            </div>
        </div>`;
    showToast('Новый диалог начат', 'success');
}

function addMessage(content, role = 'user') {
    const messagesEl = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = `
        <div class="message-avatar">${role === 'user' ? 'Вы' : 'AI'}</div>
        <div class="message-bubble">${content.replace(/\n/g, '<br>')}</div>
    `;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return div;
}

function showTyping() {
    const messagesEl = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'message agent';
    div.id = 'typing-indicator';
    div.innerHTML = `
        <div class="message-avatar">AI</div>
        <div class="message-bubble">
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function hideTyping() {
    const el = document.getElementById('typing-indicator');
    if (el) el.remove();
}

async function sendMessage() {
    if (isLoading) return;

    const input = document.getElementById('chat-input');
    const query = input.value.trim();
    if (!query) return;

    input.value = '';
    input.style.height = 'auto';
    isLoading = true;

    const btnSend = document.getElementById('btn-send');
    btnSend.disabled = true;

    addMessage(query, 'user');
    showTyping();

    try {
        const res = await api('/chat/', {
            method: 'POST',
            body: JSON.stringify({ query, thread_id: threadId })
        });

        hideTyping();

        if (!res.ok) {
            if (res.status === 401) { logout(); return; }
            addMessage('Ошибка агента. Попробуйте ещё раз.', 'agent');
            return;
        }

        const data = await res.json();
        addMessage(data.response, 'agent');

    } catch (e) {
        hideTyping();
        addMessage('Нет соединения с сервером.', 'agent');
    } finally {
        isLoading = false;
        btnSend.disabled = false;
        input.focus();
    }
}

// ─── ДОКУМЕНТЫ ──────────────────────────────────────────────────
async function loadDocuments() {
    try {
        const res = await api('/documents/');
        if (!res.ok) return;

        const data = await res.json();
        renderDocuments(data.documents || []);
    } catch (e) {
        console.error('Ошибка загрузки документов:', e);
    }
}

function renderDocuments(docs) {
    const listEl = document.getElementById('documents-list');

    if (!docs.length) {
        listEl.innerHTML = '<div class="empty-state">Документы не загружены</div>';
        return;
    }

    const iconMap = { txt: '📄', docx: '📝', doc: '📝', xlsx: '📊', xls: '📊' };

    listEl.innerHTML = docs.map(filename => {
        const ext = filename.split('.').pop().toLowerCase();
        const icon = iconMap[ext] || '📄';
        return `
            <div class="document-item">
                <span class="doc-icon">${icon}</span>
                <span class="doc-name">${filename}</span>
                <button class="btn-delete" onclick="deleteDocument('${filename}')" title="Удалить">🗑</button>
            </div>
        `;
    }).join('');
}

async function uploadFile(file) {
    if (!file) return;

    const progressEl = document.getElementById('upload-progress');
    const fillEl = document.getElementById('progress-fill');
    const labelEl = document.getElementById('progress-label');

    progressEl.classList.remove('hidden');
    fillEl.style.width = '30%';
    labelEl.textContent = `Загрузка ${file.name}...`;

    const formData = new FormData();
    formData.append('file', file);

    try {
        fillEl.style.width = '60%';

        const res = await fetch(`${API_BASE}/documents/upload`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        fillEl.style.width = '100%';

        if (!res.ok) {
            const data = await res.json();
            showToast(data.detail || 'Ошибка загрузки', 'error');
            return;
        }

        showToast(`${file.name} успешно загружен и проиндексирован`, 'success');
        await loadDocuments();

    } catch (e) {
        showToast('Ошибка подключения к серверу', 'error');
    } finally {
        setTimeout(() => {
            progressEl.classList.add('hidden');
            fillEl.style.width = '0%';
            document.getElementById('file-input').value = '';
        }, 800);
    }
}

async function deleteDocument(filename) {
    if (!confirm(`Удалить документ "${filename}" из базы знаний?`)) return;

    try {
        const res = await api(`/documents/${encodeURIComponent(filename)}`, { method: 'DELETE' });

        if (!res.ok) {
            showToast('Ошибка удаления документа', 'error');
            return;
        }

        showToast(`${filename} удалён`, 'default');
        await loadDocuments();
    } catch (e) {
        showToast('Ошибка подключения к серверу', 'error');
    }
}

// Drag & Drop
function handleDragOver(e) {
    e.preventDefault();
    document.getElementById('upload-zone').classList.add('drag-over');
}

function handleDragLeave() {
    document.getElementById('upload-zone').classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    document.getElementById('upload-zone').classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
}

// ─── ОТЧЁТЫ ─────────────────────────────────────────────────────
const REPORT_TITLES = {
    niche_analysis: 'Анализ ниши',
    diagnostics:    'Диагностика продаж',
    seo:            'SEO оптимизация',
    seasonal:       'Сезонный анализ',
    competitors:    'Анализ конкурентов',
};

function openReportModal(reportType) {
    currentReportType = reportType;
    document.getElementById('modal-title').textContent = REPORT_TITLES[reportType];
    document.getElementById('report-keyword').value = '';
    document.getElementById('report-error').classList.add('hidden');
    document.getElementById('report-modal').classList.remove('hidden');
    setTimeout(() => document.getElementById('report-keyword').focus(), 100);
}

function closeReportModal(e) {
    if (e && e.target !== document.getElementById('report-modal')) return;
    document.getElementById('report-modal').classList.add('hidden');
    currentReportType = null;
}

async function generateReport() {
    const keyword = document.getElementById('report-keyword').value.trim();
    const errorEl = document.getElementById('report-error');
    errorEl.classList.add('hidden');

    if (!keyword) {
        errorEl.textContent = 'Введите ключевое слово';
        errorEl.classList.remove('hidden');
        return;
    }

    const btnGenerate = document.getElementById('btn-generate');
    btnGenerate.disabled = true;
    btnGenerate.textContent = 'Генерация...';

    // Просим агента собрать данные и сгенерировать отчёт
    const prompt = `Сгенерируй отчёт типа ${currentReportType} для ключевого слова "${keyword}". Собери все необходимые данные из Naver и верни структурированный JSON для генерации PDF отчёта.`;

    try {
        // Отправляем запрос агенту
        const chatRes = await api('/chat/', {
            method: 'POST',
            body: JSON.stringify({ query: prompt, thread_id: threadId })
        });

        if (!chatRes.ok) {
            errorEl.textContent = 'Ошибка агента. Попробуйте ещё раз.';
            errorEl.classList.remove('hidden');
            return;
        }

        showToast('Агент собирает данные...', 'default');
        closeReportModal();

        // Переключаемся на чат чтобы показать процесс
        switchTab('chat');
        addMessage(prompt, 'user');
        showTyping();

        const chatData = await chatRes.json();
        hideTyping();
        addMessage(chatData.response, 'agent');

        showToast('Для скачивания PDF используйте /reports/generate API', 'success');

    } catch (e) {
        errorEl.textContent = 'Ошибка подключения к серверу';
        errorEl.classList.remove('hidden');
    } finally {
        btnGenerate.disabled = false;
        btnGenerate.textContent = 'Сгенерировать PDF';
    }
}