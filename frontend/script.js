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
        network: 'Ağ Grafiği',
        osint: 'OSINT Araçları',
        add: 'Kişi Ekle'
    };
    document.getElementById('pageTitle').textContent = titles[viewName] || 'Dashboard';

    // Load view data
    if (viewName === 'dashboard') loadDashboard();
    if (viewName === 'contacts') loadContacts();
    if (viewName === 'map') loadMapMarkers();
    if (viewName === 'network') loadNetworkGraph();
    if (viewName === 'osint') loadOsintTools();
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

            // Update map stats
            document.getElementById('mapContactCount').textContent = `${data.markers.length} kişi`;
        }
    } catch (error) {
        console.error('Map markers error:', error);
    }
}

// =============================================================================
// PHASE 4: LOCATION INTELLIGENCE
// =============================================================================

// Map state
const mapState = {
    mode: 'markers', // markers, heatmap, clusters
    heatLayer: null,
    clusterGroup: null,
    proximityMode: false,
    proximityCircle: null,
    markerData: []
};

/**
 * Switch map display mode
 */
async function setMapMode(mode) {
    mapState.mode = mode;

    // Update button states
    document.querySelectorAll('.map-controls .btn-group .btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });

    // Clear existing layers
    clearMapLayers();

    if (!state.maps.full) return;

    switch (mode) {
        case 'markers':
            await loadMapMarkers();
            break;
        case 'heatmap':
            await loadHeatmap();
            break;
        case 'clusters':
            await loadClusters();
            break;
    }
}

/**
 * Clear all map layers
 */
function clearMapLayers() {
    // Clear markers
    state.markers.forEach(marker => {
        if (state.maps.full) state.maps.full.removeLayer(marker);
    });
    state.markers = [];

    // Clear heatmap
    if (mapState.heatLayer && state.maps.full) {
        state.maps.full.removeLayer(mapState.heatLayer);
        mapState.heatLayer = null;
    }

    // Clear clusters
    if (mapState.clusterGroup && state.maps.full) {
        state.maps.full.removeLayer(mapState.clusterGroup);
        mapState.clusterGroup = null;
    }
}

/**
 * Load heatmap layer
 */
async function loadHeatmap() {
    try {
        const response = await apiRequest('/kisiler/heatmap');
        const data = await response.json();

        if (response.ok && data.heatmap && state.maps.full) {
            // Create heatmap layer
            mapState.heatLayer = L.heatLayer(data.heatmap, {
                radius: 25,
                blur: 15,
                maxZoom: 17,
                gradient: {
                    0.0: '#000000',
                    0.2: '#2c0a0d',
                    0.4: '#5c1a1f',
                    0.6: '#8B0A1A',
                    0.8: '#B91C2C',
                    1.0: '#FF4444'
                }
            }).addTo(state.maps.full);

            // Fit bounds
            if (data.bounds) {
                state.maps.full.fitBounds([
                    [data.bounds.min_lat, data.bounds.min_lng],
                    [data.bounds.max_lat, data.bounds.max_lng]
                ], { padding: [50, 50] });
            }

            document.getElementById('mapContactCount').textContent = `${data.heatmap.length} konum`;
            showToast('Bilgi', 'Isı haritası yüklendi', 'success');
        }
    } catch (error) {
        console.error('Heatmap error:', error);
        showToast('Hata', 'Isı haritası yüklenemedi', 'error');
    }
}

/**
 * Load clustered markers
 */
async function loadClusters() {
    try {
        const response = await apiRequest('/kisiler/harita');
        const data = await response.json();

        if (response.ok && data.markers && state.maps.full) {
            // Create marker cluster group
            mapState.clusterGroup = L.markerClusterGroup({
                spiderfyOnMaxZoom: true,
                showCoverageOnHover: true,
                zoomToBoundsOnClick: true,
                iconCreateFunction: function (cluster) {
                    const count = cluster.getChildCount();
                    let size = 'small';
                    if (count >= 10) size = 'medium';
                    if (count >= 50) size = 'large';

                    return L.divIcon({
                        html: `<div class="cluster-icon cluster-${size}">${count}</div>`,
                        className: 'custom-cluster',
                        iconSize: L.point(40, 40)
                    });
                }
            });

            // Add markers to cluster group
            data.markers.forEach(contact => {
                const marker = L.marker([contact.enlem, contact.boylam])
                    .bindPopup(`
                        <strong>${contact.tam_isim}</strong><br>
                        ${contact.adres || ''}<br>
                        <button onclick="showContactDetail(${contact.id})" class="popup-btn">Detay</button>
                    `);
                mapState.clusterGroup.addLayer(marker);
            });

            state.maps.full.addLayer(mapState.clusterGroup);

            // Fit bounds
            if (data.markers.length > 0) {
                const bounds = L.latLngBounds(data.markers.map(m => [m.enlem, m.boylam]));
                state.maps.full.fitBounds(bounds, { padding: [50, 50] });
            }

            // Get cluster count from API
            const clusterResponse = await apiRequest('/kisiler/clusters?radius=10');
            const clusterData = await clusterResponse.json();

            document.getElementById('mapContactCount').textContent = `${data.markers.length} kişi`;
            document.getElementById('mapClusterCount').textContent = `(${clusterData.clusters?.length || 0} küme)`;

            showToast('Bilgi', 'Kümeleme yüklendi', 'success');
        }
    } catch (error) {
        console.error('Clusters error:', error);
        showToast('Hata', 'Kümeleme yüklenemedi', 'error');
    }
}

/**
 * Enable proximity search mode
 */
function enableProximitySearch() {
    mapState.proximityMode = !mapState.proximityMode;

    const btn = document.getElementById('enableProximity');
    btn.classList.toggle('active', mapState.proximityMode);
    btn.textContent = mapState.proximityMode ? '❌ İptal' : '🎯 Haritaya Tıkla';

    if (mapState.proximityMode) {
        showToast('Bilgi', 'Haritada bir noktaya tıklayın', 'warning');
        state.maps.full?.getContainer().style.cursor = 'crosshair';
    } else {
        state.maps.full?.getContainer().style.cursor = '';
        clearProximityCircle();
    }
}

/**
 * Handle map click for proximity search
 */
async function handleProximityClick(e) {
    if (!mapState.proximityMode) return;

    const { lat, lng } = e.latlng;
    const radius = parseFloat(document.getElementById('proximityRadius').value) || 5;

    // Clear previous circle
    clearProximityCircle();

    // Draw circle
    mapState.proximityCircle = L.circle([lat, lng], {
        radius: radius * 1000, // km to meters
        color: '#8B0A1A',
        fillColor: '#8B0A1A',
        fillOpacity: 0.2,
        weight: 2
    }).addTo(state.maps.full);

    // Search nearby contacts
    try {
        const response = await apiRequest(`/kisiler/proximity?lat=${lat}&lng=${lng}&radius=${radius}`);
        const data = await response.json();

        if (response.ok) {
            showProximityResults(data.results, lat, lng, radius);
        }
    } catch (error) {
        console.error('Proximity search error:', error);
        showToast('Hata', 'Yakınlık araması başarısız', 'error');
    }

    // Disable proximity mode
    mapState.proximityMode = false;
    document.getElementById('enableProximity').classList.remove('active');
    document.getElementById('enableProximity').textContent = '🎯 Haritaya Tıkla';
    state.maps.full?.getContainer().style.cursor = '';
}

/**
 * Show proximity search results
 */
function showProximityResults(results, lat, lng, radius) {
    const panel = document.getElementById('proximityPanel');
    const container = document.getElementById('proximityResults');

    if (results.length === 0) {
        container.innerHTML = '<p class="empty-state">Bu alanda kişi bulunamadı</p>';
    } else {
        container.innerHTML = `
            <p class="results-summary">${results.length} kişi ${radius} km içinde</p>
            <div class="proximity-list">
                ${results.map(r => `
                    <div class="proximity-item" onclick="showContactDetail(${r.contact_id})">
                        <span class="proximity-name">${r.label}</span>
                        <span class="proximity-distance">${r.distance_km} km</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    panel.style.display = 'block';
}

/**
 * Clear proximity circle
 */
function clearProximityCircle() {
    if (mapState.proximityCircle && state.maps.full) {
        state.maps.full.removeLayer(mapState.proximityCircle);
        mapState.proximityCircle = null;
    }
    document.getElementById('proximityPanel').style.display = 'none';
}

/**
 * Initialize map event listeners
 */
function initMapEvents() {
    // Map mode buttons
    document.getElementById('mapModeMarkers')?.addEventListener('click', () => setMapMode('markers'));
    document.getElementById('mapModeHeatmap')?.addEventListener('click', () => setMapMode('heatmap'));
    document.getElementById('mapModeClusters')?.addEventListener('click', () => setMapMode('clusters'));

    // Proximity search
    document.getElementById('enableProximity')?.addEventListener('click', enableProximitySearch);
    document.getElementById('closeProximity')?.addEventListener('click', clearProximityCircle);

    // Map click handler
    setTimeout(() => {
        if (state.maps.full) {
            state.maps.full.on('click', handleProximityClick);
        }
    }, 1000);
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
    // Phase 2: Use skeleton loading instead of spinner
    container.innerHTML = generateSkeletonCards(6);


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
                // Phase 2: Add stagger animation class to grid
                container.className = 'contacts-grid stagger-animation';
                container.innerHTML = state.contacts.map((contact, index) => `
                    <div class="contact-card ${contact.favori ? 'favorite' : ''} animate-slide-up" 
                         style="animation-delay: ${index * 0.05}s"
                         onclick="showContactDetail(${contact.id})"
                         tabindex="0"
                         role="button"
                         aria-label="${contact.tam_isim} kişi kartı">
                        <div class="contact-card-header">
                            <div class="contact-avatar">${getInitials(contact.isim, contact.soyisim)}</div>
                            <span class="contact-name">${contact.tam_isim}</span>
                        </div>
                        <div class="contact-info">
                            ${contact.eposta ? `<p class="tooltip" data-tooltip="Kopyalamak için tıklayın" onclick="event.stopPropagation(); copyToClipboard('${contact.eposta}', 'E-posta')">✉ ${contact.eposta}</p>` : ''}
                            ${contact.telefon ? `<p class="tooltip" data-tooltip="Kopyalamak için tıklayın" onclick="event.stopPropagation(); copyToClipboard('${contact.telefon}', 'Telefon')">☎ ${contact.telefon}</p>` : ''}
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
        container.innerHTML = generateEmptyState('⚠', 'Bağlantı Hatası', 'Kişiler yüklenirken bir hata oluştu. Lütfen tekrar deneyin.', 'Yeniden Dene', 'loadContacts()');
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
// PHASE 3: DATA ENRICHMENT
// =============================================================================

/**
 * Enrich a single contact
 */
async function enrichContact(contactId) {
    showToast('Bilgi', 'Kişi zenginleştiriliyor...', 'warning');

    try {
        const response = await apiRequest(`/kisi/${contactId}/enrich`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Başarılı', 'Kişi zenginleştirildi!', 'success');

            // Show enrichment results in modal
            showEnrichmentResults(data.sonuc);

            // Refresh contact detail if open
            if (state.selectedContact?.id === contactId) {
                showContactDetail(contactId);
            }
        } else {
            showToast('Hata', data.error || 'Zenginleştirme başarısız', 'error');
        }
    } catch (error) {
        showToast('Hata', 'Sunucuya bağlanılamadı', 'error');
    }
}

/**
 * Enrich all contacts (batch)
 */
async function enrichAllContacts() {
    showToast('Bilgi', 'Toplu zenginleştirme başlatıldı...', 'warning');

    try {
        const response = await apiRequest('/kisiler/enrich-all', {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Başarılı', `${data.zenginlestirilen} kişi zenginleştirildi. Kalan: ${data.kalan}`, 'success');
            loadContacts();
        } else {
            showToast('Hata', data.error || 'Zenginleştirme başarısız', 'error');
        }
    } catch (error) {
        showToast('Hata', 'Sunucuya bağlanılamadı', 'error');
    }
}

/**
 * Analyze email address
 */
async function analyzeEmail(email) {
    try {
        const response = await apiRequest('/enrich/email', {
            method: 'POST',
            body: JSON.stringify({ email })
        });

        const data = await response.json();
        return data.sonuc;
    } catch (error) {
        console.error('Email analysis error:', error);
        return null;
    }
}

/**
 * Analyze phone number
 */
async function analyzePhone(phone) {
    try {
        const response = await apiRequest('/enrich/phone', {
            method: 'POST',
            body: JSON.stringify({ phone })
        });

        const data = await response.json();
        return data.sonuc;
    } catch (error) {
        console.error('Phone analysis error:', error);
        return null;
    }
}

/**
 * Search social media profiles
 */
async function searchSocialProfiles(email = null, username = null) {
    try {
        const response = await apiRequest('/enrich/social', {
            method: 'POST',
            body: JSON.stringify({ email, username })
        });

        const data = await response.json();
        return data.sonuc;
    } catch (error) {
        console.error('Social search error:', error);
        return null;
    }
}

/**
 * Show enrichment results in a modal or section
 */
function showEnrichmentResults(results) {
    if (!results) return;

    let html = '<div class="enrichment-results">';

    // Email enrichment
    if (results.email_enrichment) {
        const e = results.email_enrichment;
        html += `
            <div class="enrichment-section">
                <h4>📧 E-posta Analizi</h4>
                <div class="enrichment-grid">
                    <div class="enrichment-item">
                        <span class="label">Geçerli:</span>
                        <span class="value ${e.valid ? 'success' : 'error'}">${e.valid ? 'Evet' : 'Hayır'}</span>
                    </div>
                    <div class="enrichment-item">
                        <span class="label">Tip:</span>
                        <span class="value">${getEmailTypeLabel(e.email_type)}</span>
                    </div>
                    <div class="enrichment-item">
                        <span class="label">Domain:</span>
                        <span class="value">${e.domain || '-'}</span>
                    </div>
                    <div class="enrichment-item">
                        <span class="label">MX Kaydı:</span>
                        <span class="value ${e.has_mx_record ? 'success' : 'warning'}">${e.has_mx_record ? 'Var' : 'Yok'}</span>
                    </div>
                    ${e.has_gravatar ? `
                    <div class="enrichment-item">
                        <span class="label">Gravatar:</span>
                        <img src="${e.gravatar_url}" alt="Gravatar" class="gravatar-mini">
                    </div>` : ''}
                </div>
            </div>
        `;
    }

    // Phone enrichment
    if (results.phone_enrichment) {
        const p = results.phone_enrichment;
        html += `
            <div class="enrichment-section">
                <h4>📱 Telefon Analizi</h4>
                <div class="enrichment-grid">
                    <div class="enrichment-item">
                        <span class="label">Ülke:</span>
                        <span class="value">${p.country || '-'}</span>
                    </div>
                    <div class="enrichment-item">
                        <span class="label">Tip:</span>
                        <span class="value">${getPhoneTypeLabel(p.phone_type)}</span>
                    </div>
                    ${p.carrier ? `
                    <div class="enrichment-item">
                        <span class="label">Operatör:</span>
                        <span class="value">${p.carrier}</span>
                    </div>` : ''}
                    <div class="enrichment-item">
                        <span class="label">Format:</span>
                        <span class="value">${p.international_format || '-'}</span>
                    </div>
                </div>
            </div>
        `;
    }

    // Social profiles
    if (results.social_profiles?.social_profiles?.found_profiles?.length > 0) {
        const profiles = results.social_profiles.social_profiles.found_profiles;
        html += `
            <div class="enrichment-section">
                <h4>🌐 Sosyal Medya Profilleri</h4>
                <div class="social-profiles">
                    ${profiles.map(p => `
                        <a href="${p.url}" target="_blank" class="social-profile-link badge badge-${p.platform}">
                            ${p.icon || '🔗'} ${p.platform_name || p.platform}
                        </a>
                    `).join('')}
                </div>
            </div>
        `;
    }

    html += '</div>';

    // Create or update enrichment modal
    let enrichModal = document.getElementById('enrichmentModal');
    if (!enrichModal) {
        enrichModal = document.createElement('div');
        enrichModal.id = 'enrichmentModal';
        enrichModal.className = 'modal';
        enrichModal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Zenginleştirme Sonuçları</h2>
                    <button class="btn btn-ghost" onclick="closeEnrichmentModal()">✕</button>
                </div>
                <div class="modal-body" id="enrichmentContent"></div>
            </div>
        `;
        document.body.appendChild(enrichModal);
    }

    document.getElementById('enrichmentContent').innerHTML = html;
    enrichModal.classList.add('active');
}

function closeEnrichmentModal() {
    const modal = document.getElementById('enrichmentModal');
    if (modal) modal.classList.remove('active');
}

function getEmailTypeLabel(type) {
    const labels = {
        'personal': '👤 Kişisel',
        'corporate': '🏢 Kurumsal',
        'disposable': '⚠️ Tek Kullanımlık',
        'educational': '🎓 Eğitim',
        'government': '🏛️ Devlet',
        'organization': '🏛️ Kuruluş'
    };
    return labels[type] || type || '-';
}

function getPhoneTypeLabel(type) {
    const labels = {
        'mobile': '📱 Mobil',
        'landline': '☎️ Sabit Hat',
        'special': '🔧 Özel Servis'
    };
    return labels[type] || type || '-';
}

// =============================================================================
// PHASE 5: NETWORK GRAPH
// =============================================================================

// Network state
const networkState = {
    simulation: null,
    svg: null,
    nodes: [],
    links: [],
    initialized: false
};

// Relationship type colors
const RELATIONSHIP_COLORS = {
    'aile': '#E91E63',
    'is': '#2196F3',
    'arkadas': '#4CAF50',
    'tanidik': '#FF9800',
    'diger': '#9E9E9E'
};

/**
 * Load and render network graph
 */
async function loadNetworkGraph() {
    try {
        const response = await apiRequest('/network/graph');
        const data = await response.json();

        if (response.ok && data.graph) {
            networkState.nodes = data.graph.nodes || [];
            networkState.links = data.graph.links || [];

            // Update stats
            document.getElementById('nodeCount').textContent = `${networkState.nodes.length} düğüm`;
            document.getElementById('edgeCount').textContent = `${networkState.links.length} bağlantı`;

            renderNetworkGraph();
        }
    } catch (error) {
        console.error('Network graph error:', error);
        showToast('Hata', 'Ağ grafiği yüklenemedi', 'error');
    }
}

/**
 * Render D3.js force-directed graph
 */
function renderNetworkGraph() {
    const container = document.querySelector('.network-container');
    if (!container) return;

    const width = container.clientWidth || 800;
    const height = container.clientHeight || 600;

    // Clear previous
    d3.select('#networkGraph').selectAll('*').remove();

    if (networkState.nodes.length === 0) {
        d3.select('#networkGraph')
            .append('text')
            .attr('x', width / 2)
            .attr('y', height / 2)
            .attr('text-anchor', 'middle')
            .attr('fill', '#888')
            .text('Kişi veya ilişki bulunamadı');
        return;
    }

    const svg = d3.select('#networkGraph')
        .attr('width', width)
        .attr('height', height);

    networkState.svg = svg;

    // Create simulation
    networkState.simulation = d3.forceSimulation(networkState.nodes)
        .force('link', d3.forceLink(networkState.links)
            .id(d => d.id)
            .distance(d => 100 - (d.strength || 1) * 5))
        .force('charge', d3.forceManyBody().strength(-200))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(40));

    // Zoom behavior
    const zoom = d3.zoom()
        .scaleExtent([0.3, 3])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        });

    svg.call(zoom);

    const g = svg.append('g');

    // Draw links
    const link = g.append('g')
        .attr('class', 'links')
        .selectAll('line')
        .data(networkState.links)
        .enter()
        .append('line')
        .attr('stroke', d => RELATIONSHIP_COLORS[d.type] || '#9E9E9E')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', d => Math.max(1, (d.strength || 1) / 2));

    // Draw nodes
    const node = g.append('g')
        .attr('class', 'nodes')
        .selectAll('g')
        .data(networkState.nodes)
        .enter()
        .append('g')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));

    // Node circles
    node.append('circle')
        .attr('r', d => 15 + (d.degree || 0) * 2)
        .attr('fill', d => d.degree > 3 ? '#8B0A1A' : '#5c1a1f')
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .style('cursor', 'pointer')
        .on('click', (event, d) => {
            showContactDetail(d.id);
        });

    // Node labels
    node.append('text')
        .text(d => d.label?.split(' ')[0] || '')
        .attr('dy', 4)
        .attr('text-anchor', 'middle')
        .attr('fill', '#fff')
        .attr('font-size', '10px')
        .attr('pointer-events', 'none');

    // Node tooltips
    node.append('title')
        .text(d => `${d.label}\n${d.degree || 0} bağlantı`);

    // Simulation tick
    networkState.simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    // Drag functions
    function dragstarted(event, d) {
        if (!event.active) networkState.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    function dragended(event, d) {
        if (!event.active) networkState.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    networkState.initialized = true;
}

/**
 * Auto-detect relationships
 */
async function autoDetectRelationships() {
    showToast('Bilgi', 'İlişkiler tespit ediliyor...', 'warning');

    try {
        const response = await apiRequest('/iliskiler/auto-detect', {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Başarılı', data.mesaj, 'success');
            loadNetworkGraph();
        } else {
            showToast('Hata', data.error || 'Tespit başarısız', 'error');
        }
    } catch (error) {
        showToast('Hata', 'Sunucuya bağlanılamadı', 'error');
    }
}

/**
 * Show add relationship modal
 */
function showAddRelationshipModal() {
    // Simple prompt for now - can be enhanced with proper modal
    const kisi1 = prompt('Kişi 1 ID:');
    const kisi2 = prompt('Kişi 2 ID:');
    const tip = prompt('İlişki tipi (aile, is, arkadas, tanidik, diger):') || 'diger';

    if (kisi1 && kisi2) {
        createRelationship(parseInt(kisi1), parseInt(kisi2), tip);
    }
}

/**
 * Create new relationship
 */
async function createRelationship(kisi1Id, kisi2Id, tip) {
    try {
        const response = await apiRequest('/iliski', {
            method: 'POST',
            body: JSON.stringify({
                kisi_1_id: kisi1Id,
                kisi_2_id: kisi2Id,
                iliski_tipi: tip,
                guc: 5
            })
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Başarılı', 'İlişki oluşturuldu', 'success');
            loadNetworkGraph();
        } else {
            showToast('Hata', data.error || 'İlişki oluşturulamadı', 'error');
        }
    } catch (error) {
        showToast('Hata', 'Sunucuya bağlanılamadı', 'error');
    }
}

/**
 * Initialize network event listeners
 */
function initNetworkEvents() {
    document.getElementById('autoDetectBtn')?.addEventListener('click', autoDetectRelationships);
    document.getElementById('addRelationshipBtn')?.addEventListener('click', showAddRelationshipModal);
}

// =============================================================================
// PHASE 6: OSINT TOOLS
// =============================================================================

/**
 * Load OSINT view and API status
 */
async function loadOsintTools() {
    try {
        const response = await apiRequest('/api/external/status');
        const data = await response.json();

        if (response.ok) {
            const statusEl = document.getElementById('osintApiStatus');
            const apis = data.apis;

            statusEl.innerHTML = `
                <div class="api-status-grid">
                    <span class="api-status ${apis.haveibeenpwned ? 'active' : 'inactive'}">
                        🔓 HIBP ${apis.haveibeenpwned ? '✓' : '✗'}
                    </span>
                    <span class="api-status ${apis.hunter ? 'active' : 'inactive'}">
                        📧 Hunter ${apis.hunter ? '✓' : '✗'}
                    </span>
                    <span class="api-status ${apis.shodan ? 'active' : 'inactive'}">
                        🌐 Shodan ${apis.shodan ? '✓' : '✗'}
                    </span>
                    <span class="api-status ${apis.virustotal ? 'active' : 'inactive'}">
                        🛡️ VirusTotal ${apis.virustotal ? '✓' : '✗'}
                    </span>
                </div>
                <p class="api-hint">${data.configured_count}/${data.total_count} API yapılandırılmış. 
                API olmadan şifre kontrolü çalışır.</p>
            `;
        }
    } catch (error) {
        console.error('OSINT status error:', error);
    }
}

/**
 * Check email breaches (HIBP)
 */
async function checkHibpEmail() {
    const email = document.getElementById('hibpEmail').value;
    if (!email) {
        showToast('Uyarı', 'E-posta adresi girin', 'warning');
        return;
    }

    const resultEl = document.getElementById('hibpResult');
    resultEl.innerHTML = '<div class="loading">Kontrol ediliyor...</div>';

    try {
        const response = await apiRequest('/api/external/hibp/email', {
            method: 'POST',
            body: JSON.stringify({ email })
        });

        const data = await response.json();

        if (response.ok && data.sonuc) {
            const result = data.sonuc;
            if (result.error) {
                resultEl.innerHTML = `<div class="result-error">⚠️ ${result.error}</div>`;
            } else if (result.pwned) {
                resultEl.innerHTML = `
                    <div class="result-danger">
                        <h4>⚠️ ${result.breach_count} ihlalde bulundu!</h4>
                        <div class="breach-list">
                            ${result.breaches.map(b => `
                                <div class="breach-item">
                                    <strong>${b.title}</strong>
                                    <span class="breach-date">${b.breach_date}</span>
                                    <div class="breach-data">${b.data_classes.join(', ')}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            } else {
                resultEl.innerHTML = `<div class="result-success">✅ Bu e-posta bilinen ihlallerde bulunamadı.</div>`;
            }
        } else {
            resultEl.innerHTML = `<div class="result-error">Hata: ${data.error || 'Bilinmeyen hata'}</div>`;
        }
    } catch (error) {
        resultEl.innerHTML = `<div class="result-error">Bağlantı hatası</div>`;
    }
}

/**
 * Check password breaches (HIBP k-Anonymity)
 */
async function checkHibpPassword() {
    const password = document.getElementById('hibpPassword').value;
    if (!password) {
        showToast('Uyarı', 'Şifre girin', 'warning');
        return;
    }

    const resultEl = document.getElementById('passwordResult');
    resultEl.innerHTML = '<div class="loading">Kontrol ediliyor...</div>';

    try {
        const response = await apiRequest('/api/external/hibp/password', {
            method: 'POST',
            body: JSON.stringify({ password })
        });

        const data = await response.json();

        if (response.ok && data.sonuc) {
            const result = data.sonuc;
            if (result.pwned) {
                resultEl.innerHTML = `
                    <div class="result-danger">
                        ⚠️ Bu şifre <strong>${result.count.toLocaleString()}</strong> kez veri ihlallerinde görülmüş!
                        <p>Bu şifreyi kullanmayın veya hemen değiştirin.</p>
                    </div>
                `;
            } else {
                resultEl.innerHTML = `<div class="result-success">✅ Bu şifre bilinen ihlallerde bulunamadı.</div>`;
            }
        }
    } catch (error) {
        resultEl.innerHTML = `<div class="result-error">Bağlantı hatası</div>`;
    }
}

/**
 * Verify email with Hunter.io
 */
async function verifyHunterEmail() {
    const email = document.getElementById('hunterEmail').value;
    if (!email) {
        showToast('Uyarı', 'E-posta adresi girin', 'warning');
        return;
    }

    const resultEl = document.getElementById('hunterResult');
    resultEl.innerHTML = '<div class="loading">Doğrulanıyor...</div>';

    try {
        const response = await apiRequest('/api/external/hunter/verify', {
            method: 'POST',
            body: JSON.stringify({ email })
        });

        const data = await response.json();

        if (response.ok && data.sonuc) {
            const r = data.sonuc;
            if (r.error) {
                resultEl.innerHTML = `<div class="result-error">⚠️ ${r.error}</div>`;
            } else {
                const statusClass = r.result === 'deliverable' ? 'success' :
                    r.result === 'risky' ? 'warning' : 'danger';
                resultEl.innerHTML = `
                    <div class="result-${statusClass}">
                        <div class="result-header">
                            <strong>${r.result?.toUpperCase()}</strong>
                            <span class="score">Skor: ${r.score}/100</span>
                        </div>
                        <div class="result-details">
                            <span>MX Kayıtları: ${r.mx_records ? '✓' : '✗'}</span>
                            <span>SMTP Doğrulama: ${r.smtp_check ? '✓' : '✗'}</span>
                            <span>Webmail: ${r.webmail ? 'Evet' : 'Hayır'}</span>
                            <span>Tek Kullanımlık: ${r.disposable ? '⚠️ Evet' : 'Hayır'}</span>
                        </div>
                    </div>
                `;
            }
        }
    } catch (error) {
        resultEl.innerHTML = `<div class="result-error">Bağlantı hatası</div>`;
    }
}

/**
 * Search domain emails with Hunter.io
 */
async function searchHunterDomain() {
    const domain = document.getElementById('hunterDomain').value;
    if (!domain) {
        showToast('Uyarı', 'Domain girin', 'warning');
        return;
    }

    const resultEl = document.getElementById('domainSearchResult');
    resultEl.innerHTML = '<div class="loading">Aranıyor...</div>';

    try {
        const response = await apiRequest('/api/external/hunter/domain', {
            method: 'POST',
            body: JSON.stringify({ domain })
        });

        const data = await response.json();

        if (response.ok && data.sonuc) {
            const r = data.sonuc;
            if (r.error) {
                resultEl.innerHTML = `<div class="result-error">⚠️ ${r.error}</div>`;
            } else {
                resultEl.innerHTML = `
                    <div class="result-info">
                        <div class="result-header">
                            <strong>${r.organization || domain}</strong>
                            <span>${r.email_count} e-posta bulundu</span>
                        </div>
                        ${r.emails.length > 0 ? `
                            <div class="email-list">
                                ${r.emails.slice(0, 10).map(e => `
                                    <div class="email-item">
                                        <span class="email-value">${e.value}</span>
                                        <span class="email-meta">${e.first_name || ''} ${e.last_name || ''}</span>
                                    </div>
                                `).join('')}
                            </div>
                        ` : '<p>E-posta bulunamadı.</p>'}
                    </div>
                `;
            }
        }
    } catch (error) {
        resultEl.innerHTML = `<div class="result-error">Bağlantı hatası</div>`;
    }
}

/**
 * Lookup IP with Shodan
 */
async function lookupShodanIp() {
    const ip = document.getElementById('shodanIp').value;
    if (!ip) {
        showToast('Uyarı', 'IP adresi girin', 'warning');
        return;
    }

    const resultEl = document.getElementById('shodanResult');
    resultEl.innerHTML = '<div class="loading">Aranıyor...</div>';

    try {
        const response = await apiRequest('/api/external/shodan/ip', {
            method: 'POST',
            body: JSON.stringify({ ip })
        });

        const data = await response.json();

        if (response.ok && data.sonuc) {
            const r = data.sonuc;
            if (r.error) {
                resultEl.innerHTML = `<div class="result-error">⚠️ ${r.error}</div>`;
            } else if (r.found) {
                resultEl.innerHTML = `
                    <div class="result-info">
                        <div class="result-header">
                            <strong>${r.ip_str}</strong>
                            <span>${r.country_name || ''}</span>
                        </div>
                        <div class="result-grid">
                            <div><strong>ISP:</strong> ${r.isp || '-'}</div>
                            <div><strong>Org:</strong> ${r.org || '-'}</div>
                            <div><strong>ASN:</strong> ${r.asn || '-'}</div>
                            <div><strong>Şehir:</strong> ${r.city || '-'}</div>
                            <div><strong>OS:</strong> ${r.os || '-'}</div>
                            <div><strong>Portlar:</strong> ${r.ports?.join(', ') || '-'}</div>
                        </div>
                        ${r.vulns && r.vulns.length > 0 ? `
                            <div class="vulns-warning">
                                ⚠️ <strong>${r.vulns.length}</strong> güvenlik açığı tespit edildi:
                                <span>${r.vulns.slice(0, 5).join(', ')}</span>
                            </div>
                        ` : ''}
                        ${r.hostnames && r.hostnames.length > 0 ? `
                            <div><strong>Hostnames:</strong> ${r.hostnames.join(', ')}</div>
                        ` : ''}
                    </div>
                `;
            } else {
                resultEl.innerHTML = `<div class="result-warning">${r.message || 'IP bulunamadı'}</div>`;
            }
        }
    } catch (error) {
        resultEl.innerHTML = `<div class="result-error">Bağlantı hatası</div>`;
    }
}

/**
 * Analyze domain with VirusTotal
 */
async function analyzeVtDomain() {
    const domain = document.getElementById('vtDomain').value;
    if (!domain) {
        showToast('Uyarı', 'Domain girin', 'warning');
        return;
    }

    const resultEl = document.getElementById('vtDomainResult');
    resultEl.innerHTML = '<div class="loading">Analiz ediliyor...</div>';

    try {
        const response = await apiRequest('/api/external/virustotal/domain', {
            method: 'POST',
            body: JSON.stringify({ domain })
        });

        const data = await response.json();

        if (response.ok && data.sonuc) {
            const r = data.sonuc;
            if (r.error) {
                resultEl.innerHTML = `<div class="result-error">⚠️ ${r.error}</div>`;
            } else if (r.analyzed) {
                const stats = r.last_analysis_stats || {};
                const isSafe = stats.malicious === 0 && stats.suspicious === 0;

                resultEl.innerHTML = `
                    <div class="result-${isSafe ? 'success' : 'danger'}">
                        <div class="result-header">
                            <strong>${domain}</strong>
                            <span class="reputation">Reputation: ${r.reputation || 0}</span>
                        </div>
                        <div class="vt-stats">
                            <span class="stat safe">✓ ${stats.harmless || 0} Güvenli</span>
                            <span class="stat danger">✗ ${stats.malicious || 0} Zararlı</span>
                            <span class="stat warning">⚠ ${stats.suspicious || 0} Şüpheli</span>
                            <span class="stat neutral">? ${stats.undetected || 0} Bilinmiyor</span>
                        </div>
                        ${r.categories ? `
                            <div><strong>Kategoriler:</strong> ${Object.values(r.categories).join(', ')}</div>
                        ` : ''}
                    </div>
                `;
            } else {
                resultEl.innerHTML = `<div class="result-warning">${r.message || 'Domain bulunamadı'}</div>`;
            }
        }
    } catch (error) {
        resultEl.innerHTML = `<div class="result-error">Bağlantı hatası</div>`;
    }
}

/**
 * Analyze URL with VirusTotal
 */
async function analyzeVtUrl() {
    const url = document.getElementById('vtUrl').value;
    if (!url) {
        showToast('Uyarı', 'URL girin', 'warning');
        return;
    }

    const resultEl = document.getElementById('vtUrlResult');
    resultEl.innerHTML = '<div class="loading">Kontrol ediliyor...</div>';

    try {
        const response = await apiRequest('/api/external/virustotal/url', {
            method: 'POST',
            body: JSON.stringify({ url })
        });

        const data = await response.json();

        if (response.ok && data.sonuc) {
            const r = data.sonuc;
            if (r.error) {
                resultEl.innerHTML = `<div class="result-error">⚠️ ${r.error}</div>`;
            } else if (r.analyzed) {
                const stats = r.last_analysis_stats || {};
                const isSafe = stats.malicious === 0;

                resultEl.innerHTML = `
                    <div class="result-${isSafe ? 'success' : 'danger'}">
                        <h4>${isSafe ? '✅ Güvenli görünüyor' : '⚠️ Zararlı içerik tespit edildi!'}</h4>
                        <div class="vt-stats">
                            <span class="stat safe">✓ ${stats.harmless || 0}</span>
                            <span class="stat danger">✗ ${stats.malicious || 0}</span>
                            <span class="stat warning">⚠ ${stats.suspicious || 0}</span>
                        </div>
                        ${r.title ? `<div><strong>Sayfa:</strong> ${r.title}</div>` : ''}
                    </div>
                `;
            } else if (r.scan_submitted) {
                resultEl.innerHTML = `<div class="result-info">📤 ${r.message}</div>`;
            }
        }
    } catch (error) {
        resultEl.innerHTML = `<div class="result-error">Bağlantı hatası</div>`;
    }
}

/**
 * Switch OSINT tabs
 */
function switchOsintTab(tabName) {
    // Update tabs
    document.querySelectorAll('.osint-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    // Update content
    document.querySelectorAll('.osint-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}Tab`)?.classList.add('active');
}

/**
 * Initialize OSINT event listeners
 */
function initOsintEvents() {
    // Tab switching
    document.querySelectorAll('.osint-tab').forEach(tab => {
        tab.addEventListener('click', () => switchOsintTab(tab.dataset.tab));
    });

    // HIBP
    document.getElementById('checkHibpBtn')?.addEventListener('click', checkHibpEmail);
    document.getElementById('checkPasswordBtn')?.addEventListener('click', checkHibpPassword);

    // Hunter
    document.getElementById('verifyHunterBtn')?.addEventListener('click', verifyHunterEmail);
    document.getElementById('searchDomainBtn')?.addEventListener('click', searchHunterDomain);

    // Shodan
    document.getElementById('lookupIpBtn')?.addEventListener('click', lookupShodanIp);

    // VirusTotal
    document.getElementById('analyzeDomainBtn')?.addEventListener('click', analyzeVtDomain);
    document.getElementById('analyzeUrlBtn')?.addEventListener('click', analyzeVtUrl);
}

// =============================================================================
// PHASE 7: EXPORT/IMPORT
// =============================================================================

/**
 * Export contacts in specified format
 */
async function exportContacts(format) {
    showToast('Bilgi', `${format.toUpperCase()} hazırlanıyor...`, 'warning');

    try {
        const response = await apiRequest(`/api/export/${format}`);

        if (response.ok) {
            const blob = await response.blob();
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `kisiler.${format}`;

            if (contentDisposition) {
                const match = contentDisposition.match(/filename=(.+)/);
                if (match) filename = match[1];
            }

            // Download
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            showToast('Başarılı', `${format.toUpperCase()} dosyası indirildi`, 'success');
        } else {
            const data = await response.json();
            showToast('Hata', data.error || 'Export başarısız', 'error');
        }
    } catch (error) {
        showToast('Hata', 'Bağlantı hatası', 'error');
    }
}

/**
 * Import contacts from file
 */
async function importContacts(file) {
    if (!file) return;

    showToast('Bilgi', 'Dosya işleniyor...', 'warning');

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/api/import/auto`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${state.accessToken}`
            },
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Başarılı', data.mesaj || `${data.imported} kişi import edildi`, 'success');

            if (data.errors && data.errors.length > 0) {
                console.warn('Import errors:', data.errors);
            }

            // Refresh contacts list
            loadContacts();
            loadDashboard();
        } else {
            showToast('Hata', data.error || 'Import başarısız', 'error');
        }
    } catch (error) {
        showToast('Hata', 'Bağlantı hatası', 'error');
    }
}

/**
 * Toggle dropdown menu
 */
function toggleDropdown(dropdownId) {
    const dropdown = document.getElementById(dropdownId);
    if (dropdown) {
        dropdown.classList.toggle('open');
    }
}

/**
 * Close all dropdowns
 */
function closeAllDropdowns() {
    document.querySelectorAll('.dropdown.open').forEach(d => {
        d.classList.remove('open');
    });
}

/**
 * Initialize export/import events
 */
function initExportImportEvents() {
    // Dropdown toggle
    document.getElementById('exportBtn')?.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleDropdown('exportDropdown');
    });

    // Export buttons
    document.querySelectorAll('[data-export]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const format = e.target.dataset.export;
            exportContacts(format);
            closeAllDropdowns();
        });
    });

    // Import file button
    document.getElementById('importFileBtn')?.addEventListener('click', () => {
        document.getElementById('importFileInput')?.click();
        closeAllDropdowns();
    });

    // Import file input
    document.getElementById('importFileInput')?.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            importContacts(file);
            e.target.value = ''; // Reset
        }
    });

    // Close dropdown on outside click
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.dropdown')) {
            closeAllDropdowns();
        }
    });
}

// =============================================================================
// PHASE 8: SECURITY & OPSEC
// =============================================================================

/**
 * Load audit logs
 */
async function loadAuditLogs(page = 1) {
    const list = document.getElementById('auditLogList');
    if (!list) return;

    list.innerHTML = '<tr><td colspan="4" class="text-center">Yükleniyor...</td></tr>';

    try {
        const action = document.getElementById('auditActionFilter').value;
        let url = `/api/security/audit-logs?page=${page}`;
        if (action) url += `&action=${action}`;

        const response = await apiRequest(url);
        const data = await response.json();

        if (response.ok) {
            if (data.logs && data.logs.length > 0) {
                list.innerHTML = data.logs.map(log => `
                    <tr>
                        <td>${log.formatted_time}</td>
                        <td>${renderActionIcon(log.action)} ${log.action}</td>
                        <td title="${escapeHtml(log.details)}">${escapeHtml(log.details)}</td>
                        <td><span class="badge badge-secondary">${log.ip_address || '-'}</span></td>
                    </tr>
                `).join('');

                renderPagination(data.sayfa, data.toplam_sayfa, 'auditPagination', loadAuditLogs);
            } else {
                list.innerHTML = '<tr><td colspan="4" class="text-center">Kayıt bulunamadı</td></tr>';
            }
        } else {
            list.innerHTML = `<tr><td colspan="4" class="text-center text-danger">Hata: ${data.error}</td></tr>`;
        }
    } catch (error) {
        list.innerHTML = '<tr><td colspan="4" class="text-center text-danger">Bağlantı hatası</td></tr>';
    }
}

function renderActionIcon(action) {
    const icons = {
        'create': '➕', 'read': '👁️', 'update': '✏️', 'delete': '🗑️',
        'login': '🔐', 'logout': '🚪', 'export': '📤', 'import': '📥'
    };
    return icons[action] || '●';
}

/**
 * Load security configuration
 */
async function loadSecurityConfig() {
    try {
        const response = await apiRequest('/api/security/config');
        const data = await response.json();

        if (response.ok) {
            const form = document.getElementById('securityConfigForm');
            if (form) {
                form.innerHTML = Object.entries(data.config).map(([key, value]) => `
                    <div class="form-group">
                        <label>${formatConfigKey(key)}</label>
                        ${renderConfigInput(key, value)}
                    </div>
                `).join('');
            }
        }
    } catch (error) {
        showToast('Hata', 'Ayarlar yüklenemedi', 'error');
    }
}

function formatConfigKey(key) {
    return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function renderConfigInput(key, value) {
    if (typeof value === 'boolean') {
        return `
            <select class="select-input" name="${key}">
                <option value="true" ${value ? 'selected' : ''}>Aktif</option>
                <option value="false" ${!value ? 'selected' : ''}>Pasif</option>
            </select>
        `;
    } else if (typeof value === 'number') {
        return `<input type="number" class="input-lg" name="${key}" value="${value}">`;
    } else {
        return `<input type="text" class="input-lg" name="${key}" value="${value}">`;
    }
}

/**
 * Save security configuration
 */
async function saveSecurityConfig() {
    const form = document.getElementById('securityConfigForm');
    const inputs = form.querySelectorAll('input, select');
    const config = {};

    inputs.forEach(input => {
        let value = input.value;
        if (input.type === 'number') value = parseInt(value);
        if (input.tagName === 'SELECT' && (value === 'true' || value === 'false')) {
            value = value === 'true';
        }
        config[input.name] = value;
    });

    try {
        const response = await apiRequest('/api/security/config', 'PUT', config);
        const data = await response.json();

        if (response.ok) {
            showToast('Başarılı', data.mesaj, 'success');
        } else {
            showToast('Hata', data.error, 'error');
        }
    } catch (error) {
        showToast('Hata', 'Kaydedilemedi', 'error');
    }
}

/**
 * Check password strength
 */
async function checkPasswordStrength() {
    const password = document.getElementById('strengthInput').value;
    if (!password) return;

    try {
        const response = await apiRequest('/api/security/password-strength', 'POST', { password });
        const data = await response.json();
        const resultDiv = document.getElementById('strengthResult');

        if (response.ok) {
            const result = data.result;
            let color = 'red';
            if (result.strength === 'medium') color = 'orange';
            if (result.strength === 'strong') color = 'green';

            resultDiv.innerHTML = `
                <div class="result-box result-${color}">
                    <h4>Güç: ${result.strength.toUpperCase()} (${result.score}/5)</h4>
                    ${result.issues.length ? '<ul>' + result.issues.map(i => `<li>${i}</li>`).join('') + '</ul>' : '<p>✅ Güçlü şifre</p>'}
                </div>
            `;
        }
    } catch (error) {
        console.error(error);
    }
}

/**
 * Mask data
 */
async function maskData() {
    const type = document.getElementById('maskType').value;
    const value = document.getElementById('maskInput').value;

    try {
        const response = await apiRequest('/api/security/mask', 'POST', { type, value });
        const data = await response.json();

        if (response.ok) {
            document.getElementById('maskResult').innerHTML = `
                <div class="result-box result-info">
                    <strong>Maskelenmiş:</strong> ${data.masked}
                </div>
            `;
        }
    } catch (error) {
        console.error(error);
    }
}

/**
 * Encrypt/Decrypt
 */
async function handleCrypto(action) {
    const endpoint = action === 'encrypt' ? '/api/security/encrypt' : '/api/security/decrypt';
    const input = document.getElementById('cryptoInput').value;

    try {
        const response = await apiRequest(endpoint, 'POST', { data: input });
        const data = await response.json();

        if (response.ok) {
            document.getElementById('cryptoOutput').value = action === 'encrypt' ? data.encrypted : data.decrypted;
        } else {
            showToast('Hata', data.error, 'error');
        }
    } catch (error) {
        showToast('Hata', 'İşlem başarısız', 'error');
    }
}

/**
 * Initialize security events
 */
function initSecurityEvents() {
    // Tabs
    document.querySelectorAll('[data-sec-tab]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('[data-sec-tab]').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.security-tab-content').forEach(c => c.classList.remove('active'));

            e.target.classList.add('active');
            const tabId = e.target.dataset.secTab + 'Tab';
            document.getElementById(tabId).classList.add('active');

            if (tabId === 'auditTab') loadAuditLogs();
            if (tabId === 'configTab') loadSecurityConfig();
        });
    });

    // Audit Logs
    document.getElementById('refreshAuditBtn')?.addEventListener('click', () => loadAuditLogs());
    document.getElementById('auditActionFilter')?.addEventListener('change', () => loadAuditLogs());

    // Config
    document.getElementById('saveConfigBtn')?.addEventListener('click', saveSecurityConfig);

    // Tor
    document.getElementById('torToggle')?.addEventListener('change', async (e) => {
        const enable = e.target.checked;
        const port = document.getElementById('torPort').value;

        try {
            const response = await apiRequest('/api/security/proxy/tor', 'POST', { enable, port });
            const data = await response.json();

            if (response.ok) {
                document.getElementById('torStatusText').textContent = enable ? 'Tor aktif (Bağlanılıyor...)' : 'Tor devre dışı';
                showToast('Bilgi', data.mesaj, 'info');
            }
        } catch (error) {
            e.target.checked = !enable; // Revert
            showToast('Hata', 'Tor ayarı değiştirilemedi', 'error');
        }
    });

    // Proxy Test
    document.getElementById('testProxyBtn')?.addEventListener('click', async () => {
        const resultDiv = document.getElementById('proxyTestResult');
        resultDiv.innerHTML = '<p>Test ediliyor...</p>';

        try {
            const response = await apiRequest('/api/security/proxy/test', 'POST');
            const data = await response.json();

            if (response.ok && data.result.success) {
                resultDiv.innerHTML = `
                    <div class="result-box result-success">
                        <p>✅ Bağlantı Başarılı</p>
                        <p>IP: ${data.result.ip}</p>
                        <p>Tor: ${data.result.tor_active ? 'Aktif' : 'Pasif'}</p>
                    </div>
                `;
            } else {
                resultDiv.innerHTML = `<div class="result-box result-danger">❌ Hata: ${data.result?.error || 'Bilinmeyen hata'}</div>`;
            }
        } catch (error) {
            resultDiv.innerHTML = '<div class="result-box result-danger">❌ Bağlantı hatası</div>';
        }
    });

    // Tools
    document.getElementById('checkStrengthBtn')?.addEventListener('click', checkPasswordStrength);
    document.getElementById('maskBtn')?.addEventListener('click', maskData);
    document.getElementById('encryptBtn')?.addEventListener('click', () => handleCrypto('encrypt'));
    document.getElementById('decryptBtn')?.addEventListener('click', () => handleCrypto('decrypt'));
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

    // Phase 4: Initialize map events
    initMapEvents();

    // Phase 5: Initialize network events
    initNetworkEvents();

    // Phase 6: Initialize OSINT events
    initOsintEvents();

    // Phase 7: Initialize export/import events
    initExportImportEvents();

    // Phase 8: Initialize security events
    initSecurityEvents();

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

    // Phase 3: Enrich button
    document.getElementById('modalEnrichBtn')?.addEventListener('click', () => {
        if (state.selectedContact) enrichContact(state.selectedContact.id);
    });

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

    // =========================================================================
    // PHASE 2: Mobile Menu & Keyboard Shortcuts
    // =========================================================================

    // Mobile Menu Toggle
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.querySelector('.sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    menuToggle?.addEventListener('click', () => {
        menuToggle.classList.toggle('active');
        sidebar?.classList.toggle('open');
        sidebarOverlay?.classList.toggle('active');
    });

    sidebarOverlay?.addEventListener('click', () => {
        menuToggle?.classList.remove('active');
        sidebar?.classList.remove('open');
        sidebarOverlay?.classList.remove('active');
    });

    // Close mobile menu on nav item click
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                menuToggle?.classList.remove('active');
                sidebar?.classList.remove('open');
                sidebarOverlay?.classList.remove('active');
            }
        });
    });

    // Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl+K - Focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.getElementById('globalSearch');
            if (searchInput) {
                searchInput.focus();
                switchView('contacts');
            }
        }

        // Escape - Close modals
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.active').forEach(modal => {
                modal.classList.remove('active');
            });
            // Close mobile menu
            menuToggle?.classList.remove('active');
            sidebar?.classList.remove('open');
            sidebarOverlay?.classList.remove('active');
        }

        // Ctrl+N - New contact
        if ((e.ctrlKey || e.metaKey) && e.key === 'n' && state.accessToken) {
            e.preventDefault();
            switchView('add');
        }
    });

    // Resize handler for mobile menu
    window.addEventListener('resize', debounce(() => {
        if (window.innerWidth > 768) {
            menuToggle?.classList.remove('active');
            sidebar?.classList.remove('open');
            sidebarOverlay?.classList.remove('active');
        }
    }, 100));
});

// =============================================================================
// UTILITY FUNCTIONS (Phase 2)
// =============================================================================

/**
 * Debounce helper
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

/**
 * Generate skeleton loading cards
 */
function generateSkeletonCards(count = 6) {
    let html = '';
    for (let i = 0; i < count; i++) {
        html += `
            <div class="skeleton-card animate-slide-up" style="animation-delay: ${i * 0.05}s">
                <div class="contact-card-header">
                    <div class="skeleton skeleton-avatar"></div>
                    <div style="flex: 1;">
                        <div class="skeleton skeleton-text short"></div>
                    </div>
                </div>
                <div class="contact-info">
                    <div class="skeleton skeleton-text medium"></div>
                    <div class="skeleton skeleton-text long"></div>
                </div>
            </div>
        `;
    }
    return html;
}

/**
 * Generate empty state HTML
 */
function generateEmptyState(icon, title, text, actionText = null, actionCallback = null) {
    let html = `
        <div class="empty-state">
            <div class="empty-state-icon">${icon}</div>
            <h3 class="empty-state-title">${title}</h3>
            <p class="empty-state-text">${text}</p>
    `;

    if (actionText && actionCallback) {
        html += `
            <button class="btn btn-primary empty-state-action" onclick="${actionCallback}">
                ${actionText}
            </button>
        `;
    }

    html += '</div>';
    return html;
}

/**
 * Format relative time
 */
function formatRelativeTime(dateString) {
    if (!dateString) return '';

    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Az önce';
    if (diffMins < 60) return `${diffMins} dakika önce`;
    if (diffHours < 24) return `${diffHours} saat önce`;
    if (diffDays < 7) return `${diffDays} gün önce`;

    return formatDate(dateString);
}

/**
 * Copy text to clipboard with toast feedback
 */
async function copyToClipboard(text, label = 'Metin') {
    try {
        await navigator.clipboard.writeText(text);
        showToast('Kopyalandı', `${label} panoya kopyalandı`, 'success');
    } catch (err) {
        showToast('Hata', 'Kopyalama başarısız', 'error');
    }
}

/**
 * Add ripple effect to element
 */
function addRippleEffect(element) {
    element.classList.add('ripple');
}

// Make functions globally accessible
window.showContactDetail = showContactDetail;
window.goToPage = goToPage;
window.copyToClipboard = copyToClipboard;
window.generateEmptyState = generateEmptyState;
window.enrichContact = enrichContact;
window.enrichAllContacts = enrichAllContacts;
window.closeEnrichmentModal = closeEnrichmentModal;
window.loadContacts = loadContacts;

