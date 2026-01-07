/**
 * REH_FOR_CV-2 OSINT Rehber - Frontend JavaScript
 * Full CRUD operations, JWT authentication, and interactive UI
 */

// =============================================================================
// CONFIGURATION
// =============================================================================

const API_BASE_URL = 'http://localhost:5000';

// =============================================================================
// STATE MANAGEMENT
// =============================================================================

const state = {
    accessToken: localStorage.getItem('accessToken'),
    refreshToken: localStorage.getItem('refreshToken'),
    currentUser: JSON.parse(localStorage.getItem('currentUser') || 'null'),
    contacts: [],
    currentPage: 1,
    totalPages: 1,
    selectedContact: null,
    maps: {
        mini: null,
        full: null
    },
    markers: []
};

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Make API request with authentication
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (state.accessToken) {
        headers['Authorization'] = `Bearer ${state.accessToken}`;
    }

    try {
        const response = await fetch(url, {
            ...options,
            headers
        });

        // Handle token refresh
        if (response.status === 401 && state.refreshToken && !endpoint.includes('token/refresh')) {
            const refreshed = await refreshAccessToken();
            if (refreshed) {
                headers['Authorization'] = `Bearer ${state.accessToken}`;
                return fetch(url, { ...options, headers });
            }
        }

        return response;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

/**
 * Refresh access token
 */
async function refreshAccessToken() {
    try {
        const response = await fetch(`${API_BASE_URL}/token/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.refreshToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            state.accessToken = data.access_token;
            localStorage.setItem('accessToken', data.access_token);
            return true;
        }
    } catch (error) {
        console.error('Token refresh failed:', error);
    }

    // Refresh failed, logout
    logout();
    return false;
}

/**
 * Show toast notification
 */
function showToast(title, message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type]}</span>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
    `;

    container.appendChild(toast);

    // Auto remove after 4 seconds
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

/**
 * Get initials from name
 */
function getInitials(name, surname = '') {
    let initials = name.charAt(0).toUpperCase();
    if (surname) {
        initials += surname.charAt(0).toUpperCase();
    }
    return initials;
}

/**
 * Format date
 */
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('tr-TR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// =============================================================================
// AUTHENTICATION
// =============================================================================

/**
 * Login user
 */
async function login(username, password) {
    try {
        const response = await apiRequest('/giris', {
            method: 'POST',
            body: JSON.stringify({
                kullanici_adi: username,
                sifre: password
            })
        });

        const data = await response.json();

        if (response.ok) {
            state.accessToken = data.access_token;
            state.refreshToken = data.refresh_token;
            state.currentUser = data.kullanici;

            localStorage.setItem('accessToken', data.access_token);
            localStorage.setItem('refreshToken', data.refresh_token);
            localStorage.setItem('currentUser', JSON.stringify(data.kullanici));

            showToast('Başarılı', 'Giriş yapıldı!', 'success');
            showMainApp();
        } else {
            showToast('Hata', data.error || 'Giriş başarısız', 'error');
        }
    } catch (error) {
        showToast('Hata', 'Sunucuya bağlanılamadı', 'error');
    }
}

/**
 * Register user
 */
async function register(username, email, password) {
    try {
        const response = await apiRequest('/kayit', {
            method: 'POST',
            body: JSON.stringify({
                kullanici_adi: username,
                email: email || null,
                sifre: password
            })
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Başarılı', 'Kayıt tamamlandı! Giriş yapabilirsiniz.', 'success');
            showLoginForm();
        } else {
            showToast('Hata', data.error || 'Kayıt başarısız', 'error');
        }
    } catch (error) {
        showToast('Hata', 'Sunucuya bağlanılamadı', 'error');
    }
}

/**
 * Logout user
 */
function logout() {
    state.accessToken = null;
    state.refreshToken = null;
    state.currentUser = null;
    state.contacts = [];

    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('currentUser');

    showAuthScreen();
    showToast('Bilgi', 'Çıkış yapıldı', 'warning');
}

// =============================================================================
// UI NAVIGATION
// =============================================================================

function showAuthScreen() {
    document.getElementById('authScreen').style.display = 'flex';
    document.getElementById('mainApp').style.display = 'none';
}

function showMainApp() {
    document.getElementById('authScreen').style.display = 'none';
    document.getElementById('mainApp').style.display = 'flex';

    // Set username
    document.getElementById('currentUsername').textContent = state.currentUser?.kullanici_adi || 'Kullanıcı';

    // Load initial data
    loadDashboard();
    initializeMaps();
}

function showLoginForm() {
    document.getElementById('loginForm').style.display = 'block';
    document.getElementById('registerForm').style.display = 'none';
}

function showRegisterForm() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
}

function switchView(viewName) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.view === viewName);
    });

    // Update views
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    document.getElementById(`${viewName}View`).classList.add('active');

    // Update header
    const titles = {
        dashboard: 'Dashboard',
        contacts: 'Kişiler',
        map: 'Harita',
        add: 'Kişi Ekle'
    };
    document.getElementById('pageTitle').textContent = titles[viewName] || 'Dashboard';

    // Load view data
    if (viewName === 'dashboard') loadDashboard();
    if (viewName === 'contacts') loadContacts();
    if (viewName === 'map') loadMapMarkers();
    if (viewName === 'add') resetContactForm();
}

// =============================================================================
// MAPS
// =============================================================================

function initializeMaps() {
    // Mini map for dashboard
    if (!state.maps.mini) {
        state.maps.mini = L.map('miniMap').setView([39.0, 35.0], 5);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '© OpenStreetMap © CARTO'
        }).addTo(state.maps.mini);
    }

    // Full map (lazy init)
    setTimeout(() => {
        if (!state.maps.full && document.getElementById('fullMap')) {
            state.maps.full = L.map('fullMap').setView([39.0, 35.0], 6);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                attribution: '© OpenStreetMap © CARTO'
            }).addTo(state.maps.full);
        }
    }, 500);
}

async function loadMapMarkers() {
    try {
        const response = await apiRequest('/kisiler/harita');
        const data = await response.json();

        if (response.ok && data.markers) {
            // Clear existing markers
            state.markers.forEach(marker => {
                if (state.maps.mini) state.maps.mini.removeLayer(marker);
                if (state.maps.full) state.maps.full.removeLayer(marker);
            });
            state.markers = [];

            // Add new markers
            data.markers.forEach(contact => {
                const marker = L.marker([contact.enlem, contact.boylam])
                    .bindPopup(`
                        <strong>${contact.tam_isim}</strong><br>
                        ${contact.adres || ''}
                    `);

                if (state.maps.mini) marker.addTo(state.maps.mini);
                if (state.maps.full) {
                    const fullMarker = L.marker([contact.enlem, contact.boylam])
                        .bindPopup(`
                            <strong>${contact.tam_isim}</strong><br>
                            ${contact.adres || ''}<br>
                            <button onclick="showContactDetail(${contact.id})">Detay</button>
                        `)
                        .addTo(state.maps.full);
                    state.markers.push(fullMarker);
                }
                state.markers.push(marker);
            });

            // Fit bounds if markers exist
            if (data.markers.length > 0 && state.maps.full) {
                const bounds = L.latLngBounds(data.markers.map(m => [m.enlem, m.boylam]));
                state.maps.full.fitBounds(bounds, { padding: [50, 50] });
            }
        }
    } catch (error) {
        console.error('Map markers error:', error);
    }
}

// =============================================================================
// DASHBOARD
// =============================================================================

async function loadDashboard() {
    try {
        // Load stats
        const statsResponse = await apiRequest('/kisiler/istatistikler');
        const stats = await statsResponse.json();

        if (statsResponse.ok) {
            document.getElementById('statTotalContacts').textContent = stats.toplam_kisi || 0;
            document.getElementById('statFavorites').textContent = stats.favori_kisi || 0;
            document.getElementById('statWithLocation').textContent = stats.konumlu_kisi || 0;
            document.getElementById('statWithEmail').textContent = stats.epostali_kisi || 0;
        }

        // Load recent contacts
        const contactsResponse = await apiRequest('/kisiler?limit=5&sirala=created_at&sira_yonu=desc');
        const contactsData = await contactsResponse.json();

        const recentContainer = document.getElementById('recentContacts');
        if (contactsResponse.ok && contactsData.kisiler?.length > 0) {
            recentContainer.innerHTML = contactsData.kisiler.map(contact => `
                <div class="contact-card" onclick="showContactDetail(${contact.id})">
                    <div class="contact-card-header">
                        <div class="contact-avatar">${getInitials(contact.isim, contact.soyisim)}</div>
                        <span class="contact-name">${contact.tam_isim}</span>
                    </div>
                </div>
            `).join('');
        } else {
            recentContainer.innerHTML = '<p class="empty-state">Henüz kişi eklenmemiş</p>';
        }

        // Load map markers
        loadMapMarkers();

    } catch (error) {
        console.error('Dashboard error:', error);
    }
}

// =============================================================================
// CONTACTS
// =============================================================================

async function loadContacts() {
    const container = document.getElementById('contactsList');
    container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const params = new URLSearchParams({
            sayfa: state.currentPage,
            limit: 12,
            sirala: document.getElementById('sortBy')?.value || 'isim'
        });

        const searchTerm = document.getElementById('globalSearch')?.value;
        if (searchTerm) params.set('arama', searchTerm);

        const tag = document.getElementById('filterTag')?.value;
        if (tag) params.set('etiket', tag);

        const favoritesOnly = document.getElementById('filterFavorites')?.checked;
        if (favoritesOnly) params.set('favori', 'true');

        const response = await apiRequest(`/kisiler?${params}`);
        const data = await response.json();

        if (response.ok) {
            state.contacts = data.kisiler || [];
            state.totalPages = data.sayfalama?.toplam_sayfa || 1;

            if (state.contacts.length === 0) {
                container.innerHTML = '<p class="empty-state">Henüz kişi eklenmemiş veya arama sonucu bulunamadı</p>';
            } else {
                container.innerHTML = state.contacts.map(contact => `
                    <div class="contact-card ${contact.favori ? 'favorite' : ''}" onclick="showContactDetail(${contact.id})">
                        <div class="contact-card-header">
                            <div class="contact-avatar">${getInitials(contact.isim, contact.soyisim)}</div>
                            <span class="contact-name">${contact.tam_isim}</span>
                        </div>
                        <div class="contact-info">
                            ${contact.eposta ? `<p>✉ ${contact.eposta}</p>` : ''}
                            ${contact.telefon ? `<p>☎ ${contact.telefon}</p>` : ''}
                            ${contact.adres ? `<p>◈ ${contact.adres.substring(0, 40)}${contact.adres.length > 40 ? '...' : ''}</p>` : ''}
                        </div>
                        ${contact.etiketler?.length ? `
                            <div class="contact-tags">
                                ${contact.etiketler.map(tag => `<span class="tag">${tag}</span>`).join('')}
                            </div>
                        ` : ''}
                    </div>
                `).join('');
            }

            renderPagination();
            loadTags();
        }
    } catch (error) {
        container.innerHTML = '<p class="empty-state">Yüklenirken hata oluştu</p>';
        console.error('Load contacts error:', error);
    }
}

async function loadTags() {
    try {
        const response = await apiRequest('/kisiler/etiketler');
        const data = await response.json();

        if (response.ok && data.etiketler) {
            const select = document.getElementById('filterTag');
            const currentValue = select.value;
            select.innerHTML = '<option value="">Tüm Etiketler</option>';
            data.etiketler.forEach(tag => {
                select.innerHTML += `<option value="${tag}">${tag}</option>`;
            });
            select.value = currentValue;
        }
    } catch (error) {
        console.error('Load tags error:', error);
    }
}

function renderPagination() {
    const container = document.getElementById('pagination');
    if (state.totalPages <= 1) {
        container.innerHTML = '';
        return;
    }

    let html = '';
    html += `<button ${state.currentPage === 1 ? 'disabled' : ''} onclick="goToPage(${state.currentPage - 1})">←</button>`;

    for (let i = 1; i <= state.totalPages; i++) {
        if (i === 1 || i === state.totalPages || (i >= state.currentPage - 2 && i <= state.currentPage + 2)) {
            html += `<button class="${i === state.currentPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
        } else if (i === state.currentPage - 3 || i === state.currentPage + 3) {
            html += '<button disabled>...</button>';
        }
    }

    html += `<button ${state.currentPage === state.totalPages ? 'disabled' : ''} onclick="goToPage(${state.currentPage + 1})">→</button>`;

    container.innerHTML = html;
}

function goToPage(page) {
    state.currentPage = page;
    loadContacts();
}

// =============================================================================
// CONTACT CRUD
// =============================================================================

async function showContactDetail(contactId) {
    try {
        const response = await apiRequest(`/kisi/${contactId}`);
        const data = await response.json();

        if (response.ok) {
            state.selectedContact = data.kisi;
            const contact = data.kisi;

            document.getElementById('modalContactName').textContent = contact.tam_isim;
            document.getElementById('modalContactDetails').innerHTML = `
                <div class="detail-row">
                    <span class="detail-label">İsim:</span>
                    <span class="detail-value">${contact.isim}</span>
                </div>
                ${contact.soyisim ? `
                <div class="detail-row">
                    <span class="detail-label">Soyisim:</span>
                    <span class="detail-value">${contact.soyisim}</span>
                </div>
                ` : ''}
                ${contact.eposta ? `
                <div class="detail-row">
                    <span class="detail-label">E-posta:</span>
                    <span class="detail-value">${contact.eposta}</span>
                </div>
                ` : ''}
                ${contact.telefon ? `
                <div class="detail-row">
                    <span class="detail-label">Telefon:</span>
                    <span class="detail-value">${contact.telefon}</span>
                </div>
                ` : ''}
                ${contact.telefon_2 ? `
                <div class="detail-row">
                    <span class="detail-label">Telefon 2:</span>
                    <span class="detail-value">${contact.telefon_2}</span>
                </div>
                ` : ''}
                ${contact.adres ? `
                <div class="detail-row">
                    <span class="detail-label">Adres:</span>
                    <span class="detail-value">${contact.adres}</span>
                </div>
                ` : ''}
                ${contact.sehir || contact.ulke ? `
                <div class="detail-row">
                    <span class="detail-label">Konum:</span>
                    <span class="detail-value">${[contact.sehir, contact.ulke].filter(Boolean).join(', ')}</span>
                </div>
                ` : ''}
                ${contact.etiketler?.length ? `
                <div class="detail-row">
                    <span class="detail-label">Etiketler:</span>
                    <span class="detail-value">${contact.etiketler.join(', ')}</span>
                </div>
                ` : ''}
                ${contact.notlar ? `
                <div class="detail-row">
                    <span class="detail-label">Notlar:</span>
                    <span class="detail-value">${contact.notlar}</span>
                </div>
                ` : ''}
                <div class="detail-row">
                    <span class="detail-label">Favori:</span>
                    <span class="detail-value">${contact.favori ? '★ Evet' : 'Hayır'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Eklenme:</span>
                    <span class="detail-value">${formatDate(contact.created_at)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Güncelleme:</span>
                    <span class="detail-value">${formatDate(contact.updated_at)}</span>
                </div>
            `;

            document.getElementById('contactModal').classList.add('active');
        }
    } catch (error) {
        showToast('Hata', 'Kişi detayı yüklenemedi', 'error');
    }
}

function editContact(contact) {
    document.getElementById('contactModal').classList.remove('active');

    // Fill form
    document.getElementById('editContactId').value = contact.id;
    document.getElementById('contactName').value = contact.isim || '';
    document.getElementById('contactSurname').value = contact.soyisim || '';
    document.getElementById('contactEmail').value = contact.eposta || '';
    document.getElementById('contactPhone').value = contact.telefon || '';
    document.getElementById('contactPhone2').value = contact.telefon_2 || '';
    document.getElementById('contactAddress').value = contact.adres || '';
    document.getElementById('contactCity').value = contact.sehir || '';
    document.getElementById('contactCountry').value = contact.ulke || 'Türkiye';
    document.getElementById('contactTags').value = contact.etiketler?.join(', ') || '';
    document.getElementById('contactNotes').value = contact.notlar || '';
    document.getElementById('contactFavorite').checked = contact.favori || false;

    // Update UI
    document.getElementById('formTitle').textContent = 'Kişiyi Düzenle';
    document.getElementById('submitBtnText').textContent = 'Güncelle';
    document.getElementById('cancelEdit').style.display = 'block';

    switchView('add');
}

function resetContactForm() {
    document.getElementById('contactForm').reset();
    document.getElementById('editContactId').value = '';
    document.getElementById('formTitle').textContent = 'Yeni Kişi Ekle';
    document.getElementById('submitBtnText').textContent = 'Kişi Ekle';
    document.getElementById('cancelEdit').style.display = 'none';
    document.getElementById('contactCountry').value = 'Türkiye';
}

async function saveContact(event) {
    event.preventDefault();

    const contactId = document.getElementById('editContactId').value;
    const isEdit = !!contactId;

    const tags = document.getElementById('contactTags').value
        .split(',')
        .map(t => t.trim())
        .filter(t => t.length > 0);

    const contactData = {
        isim: document.getElementById('contactName').value.trim(),
        soyisim: document.getElementById('contactSurname').value.trim() || null,
        eposta: document.getElementById('contactEmail').value.trim() || null,
        telefon: document.getElementById('contactPhone').value.trim() || null,
        telefon_2: document.getElementById('contactPhone2').value.trim() || null,
        adres: document.getElementById('contactAddress').value.trim() || null,
        sehir: document.getElementById('contactCity').value.trim() || null,
        ulke: document.getElementById('contactCountry').value.trim() || null,
        etiketler: tags.length > 0 ? tags : null,
        notlar: document.getElementById('contactNotes').value.trim() || null,
        favori: document.getElementById('contactFavorite').checked
    };

    try {
        const response = await apiRequest(
            isEdit ? `/kisi/${contactId}` : '/kisi',
            {
                method: isEdit ? 'PUT' : 'POST',
                body: JSON.stringify(contactData)
            }
        );

        const data = await response.json();

        if (response.ok) {
            showToast('Başarılı', isEdit ? 'Kişi güncellendi!' : 'Kişi eklendi!', 'success');
            resetContactForm();
            switchView('contacts');
        } else {
            showToast('Hata', data.error || 'İşlem başarısız', 'error');
        }
    } catch (error) {
        showToast('Hata', 'Sunucuya bağlanılamadı', 'error');
    }
}

function confirmDeleteContact() {
    if (!state.selectedContact) return;

    document.getElementById('deleteContactName').textContent = state.selectedContact.tam_isim;
    document.getElementById('contactModal').classList.remove('active');
    document.getElementById('deleteModal').classList.add('active');
}

async function deleteContact() {
    if (!state.selectedContact) return;

    try {
        const response = await apiRequest(`/kisi/${state.selectedContact.id}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Başarılı', data.mesaj || 'Kişi silindi!', 'success');
            document.getElementById('deleteModal').classList.remove('active');
            state.selectedContact = null;
            loadContacts();
            loadDashboard();
        } else {
            showToast('Hata', data.error || 'Silme başarısız', 'error');
        }
    } catch (error) {
        showToast('Hata', 'Sunucuya bağlanılamadı', 'error');
    }
}

async function exportEmails() {
    try {
        const response = await apiRequest('/emails/export');
        const data = await response.json();

        if (response.ok) {
            // Create downloadable file
            const blob = new Blob([data.emails.join('\n')], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'emails.txt';
            a.click();
            URL.revokeObjectURL(url);

            showToast('Başarılı', `${data.toplam} e-posta adresi dışa aktarıldı`, 'success');
        } else {
            showToast('Hata', data.error || 'Dışa aktarma başarısız', 'error');
        }
    } catch (error) {
        showToast('Hata', 'Sunucuya bağlanılamadı', 'error');
    }
}

// =============================================================================
// EVENT LISTENERS
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Check if logged in
    if (state.accessToken && state.currentUser) {
        showMainApp();
    } else {
        showAuthScreen();
    }

    // Auth form toggles
    document.getElementById('showRegister')?.addEventListener('click', (e) => {
        e.preventDefault();
        showRegisterForm();
    });

    document.getElementById('showLogin')?.addEventListener('click', (e) => {
        e.preventDefault();
        showLoginForm();
    });

    // Login form
    document.getElementById('loginFormElement')?.addEventListener('submit', (e) => {
        e.preventDefault();
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        login(username, password);
    });

    // Register form
    document.getElementById('registerFormElement')?.addEventListener('submit', (e) => {
        e.preventDefault();
        const username = document.getElementById('registerUsername').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        register(username, email, password);
    });

    // Logout
    document.getElementById('logoutBtn')?.addEventListener('click', logout);

    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            switchView(item.dataset.view);
        });
    });

    // Contact form
    document.getElementById('contactForm')?.addEventListener('submit', saveContact);
    document.getElementById('cancelEdit')?.addEventListener('click', () => {
        resetContactForm();
        switchView('contacts');
    });

    // Modals
    document.getElementById('closeModal')?.addEventListener('click', () => {
        document.getElementById('contactModal').classList.remove('active');
    });

    document.getElementById('modalEditBtn')?.addEventListener('click', () => {
        if (state.selectedContact) editContact(state.selectedContact);
    });

    document.getElementById('modalDeleteBtn')?.addEventListener('click', confirmDeleteContact);

    document.getElementById('closeDeleteModal')?.addEventListener('click', () => {
        document.getElementById('deleteModal').classList.remove('active');
    });

    document.getElementById('cancelDelete')?.addEventListener('click', () => {
        document.getElementById('deleteModal').classList.remove('active');
    });

    document.getElementById('confirmDelete')?.addEventListener('click', deleteContact);

    // Filters
    document.getElementById('sortBy')?.addEventListener('change', () => {
        state.currentPage = 1;
        loadContacts();
    });

    document.getElementById('filterTag')?.addEventListener('change', () => {
        state.currentPage = 1;
        loadContacts();
    });

    document.getElementById('filterFavorites')?.addEventListener('change', () => {
        state.currentPage = 1;
        loadContacts();
    });

    document.getElementById('globalSearch')?.addEventListener('input', debounce(() => {
        state.currentPage = 1;
        loadContacts();
    }, 500));

    // Export emails
    document.getElementById('exportEmailsBtn')?.addEventListener('click', exportEmails);

    // Close modals on backdrop click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
});

// Debounce helper
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// Make functions globally accessible
window.showContactDetail = showContactDetail;
window.goToPage = goToPage;
