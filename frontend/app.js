// Claim GPS Game - Frontend JavaScript
// Configuration
const API_BASE = window.location.origin + '/api';
const WS_BASE = (window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host + '/ws';

// State
let map, playerMarker, trackingLayer, heatmapLayer;
let currentPosition = null;
let followMode = false;
let trackingActive = false;
let compassEnabled = false;
let heatmapVisible = false;
let authToken = null;
let ws = null;
let currentUser = null;
let activeTrackId = null;

// Map markers storage
const spotMarkers = new Map();
const playerMarkers = new Map();

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);

function init() {
    // Check for existing auth
    authToken = localStorage.getItem('claim_token');
    
    if (!authToken) {
        showLoginModal();
    } else {
        hideLoginModal();
        initializeApp();
    }
    
    // Setup event listeners
    setupEventListeners();
}

function setupEventListeners() {
    // Auth buttons
    document.getElementById('btn-login').addEventListener('click', handleLogin);
    document.getElementById('btn-register').addEventListener('click', handleRegister);
    document.getElementById('show-register').addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('login-form').classList.add('hidden');
        document.getElementById('register-form').classList.remove('hidden');
    });
    document.getElementById('show-login').addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('register-form').classList.add('hidden');
        document.getElementById('login-form').classList.remove('hidden');
    });
    
    // Action buttons
    document.getElementById('btn-tracking').addEventListener('click', toggleTracking);
    document.getElementById('btn-follow').addEventListener('click', toggleFollow);
    document.getElementById('btn-compass').addEventListener('click', toggleCompass);
    document.getElementById('btn-center').addEventListener('click', centerMap);
    document.getElementById('btn-heatmap').addEventListener('click', toggleHeatmap);
    document.getElementById('btn-layers').addEventListener('click', showLayerMenu);
    
    // Stats toggle
    document.getElementById('stats-toggle').addEventListener('click', toggleStatsDetail);
}

// Authentication
async function handleLogin() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    
    if (!username || !password) {
        showMessage('Please enter username and password', 'error');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await fetch(`${API_BASE}/auth/token`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Login failed');
        }
        
        const data = await response.json();
        authToken = data.access_token;
        localStorage.setItem('claim_token', authToken);
        
        showMessage('Login successful!', 'success');
        setTimeout(() => {
            hideLoginModal();
            initializeApp();
        }, 500);
    } catch (error) {
        showMessage('Login failed: ' + error.message, 'error');
    }
}

async function handleRegister() {
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    
    if (!username || !email || !password) {
        showMessage('Please fill all fields', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, password })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Registration failed');
        }
        
        showMessage('Registration successful! Please login.', 'success');
        setTimeout(() => {
            document.getElementById('register-form').classList.add('hidden');
            document.getElementById('login-form').classList.remove('hidden');
        }, 1000);
    } catch (error) {
        showMessage('Registration failed: ' + error.message, 'error');
    }
}

function showMessage(text, type) {
    const messageEl = document.getElementById('auth-message');
    messageEl.textContent = text;
    messageEl.className = 'message ' + type;
}

function showLoginModal() {
    document.getElementById('login-modal').classList.remove('hidden');
}

function hideLoginModal() {
    document.getElementById('login-modal').classList.add('hidden');
}

// Main App Initialization
async function initializeApp() {
    try {
        // Fetch current user
        const response = await apiRequest('/auth/me');
        currentUser = response;
        
        // Initialize map
        initMap();
        
        // Start GPS tracking
        startGPSTracking();
        
        // Connect WebSocket
        connectWebSocket();
        
        // Load initial data
        loadStats();
        loadNearbySpots();
        
        // Start update loops
        setInterval(updateAutoLog, 5000); // Check auto-log every 5 seconds
        setInterval(loadStats, 30000); // Update stats every 30 seconds
    } catch (error) {
        console.error('App initialization error:', error);
        localStorage.removeItem('claim_token');
        showLoginModal();
    }
}

// Map Initialization
function initMap() {
    map = L.map('map', {
        zoomControl: false,
        attributionControl: false,
        touchZoom: false,
        doubleClickZoom: false,
        scrollWheelZoom: true,
        dragging: true,
        tap: false
    }).setView([51.505, -0.09], 13);
    
    // Base layers
    const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19
    });
    
    const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19
    });
    
    const topoLayer = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
        maxZoom: 17
    });
    
    // Add default layer
    osmLayer.addTo(map);
    
    // Store layers for switching
    window.mapLayers = {
        'Street': osmLayer,
        'Satellite': satelliteLayer,
        'Topo': topoLayer
    };
    
    // Initialize tracking layer
    trackingLayer = L.layerGroup().addTo(map);
    
    // Initialize heatmap layer
    heatmapLayer = L.layerGroup();
}

// GPS Tracking
function startGPSTracking() {
    if (!navigator.geolocation) {
        showNotification('GPS Error', 'Geolocation not supported', 'error');
        return;
    }
    
    navigator.geolocation.watchPosition(
        (position) => {
            currentPosition = {
                lat: position.coords.latitude,
                lng: position.coords.longitude,
                heading: position.coords.heading,
                accuracy: position.coords.accuracy
            };
            
            updatePlayerPosition();
            
            if (followMode) {
                map.setView([currentPosition.lat, currentPosition.lng], map.getZoom());
            }
            
            // Send position via WebSocket
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    event_type: 'position_update',
                    data: {
                        latitude: currentPosition.lat,
                        longitude: currentPosition.lng,
                        heading: currentPosition.heading
                    }
                }));
            }
            
            // Update track if active
            if (trackingActive && activeTrackId) {
                addTrackPoint(currentPosition);
            }
        },
        (error) => {
            console.error('GPS error:', error);
            showNotification('GPS Error', 'Cannot access location', 'error');
        },
        {
            enableHighAccuracy: true,
            maximumAge: 0,
            timeout: 5000
        }
    );
}

function updatePlayerPosition() {
    if (!currentPosition) return;
    
    if (playerMarker) {
        playerMarker.setLatLng([currentPosition.lat, currentPosition.lng]);
        
        // Update heading if compass enabled
        if (compassEnabled && currentPosition.heading !== null) {
            const icon = playerMarker.getElement();
            if (icon) {
                icon.style.transform += ` rotate(${currentPosition.heading}deg)`;
            }
        }
    } else {
        playerMarker = L.marker([currentPosition.lat, currentPosition.lng], {
            icon: L.divIcon({
                className: 'player-marker',
                iconSize: [20, 20]
            })
        }).addTo(map);
    }
}

// WebSocket
function connectWebSocket() {
    if (!authToken) return;
    
    ws = new WebSocket(`${WS_BASE}?token=${authToken}`);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
        console.log('WebSocket closed, reconnecting...');
        setTimeout(connectWebSocket, 5000);
    };
}

function handleWebSocketMessage(message) {
    const { event_type, data } = message;
    
    switch (event_type) {
        case 'connected':
            console.log('Connected:', data.message);
            break;
            
        case 'position_update':
            updateOtherPlayerPosition(data);
            break;
            
        case 'log_event':
            showLogNotification(data);
            break;
            
        case 'loot_spawn':
            showLootSpawn(data);
            break;
            
        case 'claim_update':
            updateClaimHeatmap();
            break;
            
        case 'tracking_update':
            console.log('Tracking update:', data);
            break;
    }
}

function updateOtherPlayerPosition(data) {
    const { user_id, username, latitude, longitude } = data;
    
    if (playerMarkers.has(user_id)) {
        playerMarkers.get(user_id).setLatLng([latitude, longitude]);
    } else {
        const marker = L.marker([latitude, longitude], {
            icon: L.divIcon({
                className: 'player-marker',
                html: `<div style="background: #f59e0b;"></div>`,
                iconSize: [15, 15]
            })
        }).addTo(map);
        marker.bindPopup(username);
        playerMarkers.set(user_id, marker);
    }
}

// API Helpers
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    const response = await fetch(url, {
        ...options,
        headers
    });
    
    if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
    }
    
    return response.json();
}

// Data Loading
async function loadStats() {
    try {
        const stats = await apiRequest('/stats');
        
        document.getElementById('level').textContent = stats.level;
        document.getElementById('claims').textContent = stats.total_claim_points;
        document.getElementById('total-logs').textContent = stats.total_logs;
        document.getElementById('spots-claimed').textContent = stats.total_spots_claimed;
        document.getElementById('active-tracks').textContent = stats.active_tracks;
        document.getElementById('inventory-count').textContent = stats.inventory_count;
        
        // Update XP bar
        const xpProgress = (stats.xp % 100) / 100 * 100;
        document.getElementById('xp-fill').style.width = xpProgress + '%';
        document.getElementById('xp-text').textContent = `${stats.xp % 100}/100`;
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

async function loadNearbySpots() {
    if (!currentPosition) {
        setTimeout(loadNearbySpots, 1000);
        return;
    }
    
    try {
        const spots = await apiRequest(
            `/spots/nearby?latitude=${currentPosition.lat}&longitude=${currentPosition.lng}&radius=1000`
        );
        
        // Clear existing markers
        spotMarkers.forEach(marker => marker.remove());
        spotMarkers.clear();
        
        // Add new markers
        spots.forEach(spot => {
            const marker = L.marker([spot.latitude, spot.longitude], {
                icon: L.divIcon({
                    className: spot.is_loot ? 'loot-marker' : 'spot-marker',
                    iconSize: [15, 15]
                })
            }).addTo(map);
            
            marker.bindPopup(`
                <b>${spot.name}</b><br>
                ${spot.description || ''}<br>
                <button onclick="logSpot(${spot.id})">Log Spot</button>
            `);
            
            spotMarkers.set(spot.id, marker);
        });
    } catch (error) {
        console.error('Failed to load spots:', error);
    }
}

// Auto-logging
async function updateAutoLog() {
    if (!currentPosition) return;
    
    spotMarkers.forEach((marker, spotId) => {
        const spotPos = marker.getLatLng();
        const distance = map.distance(
            [currentPosition.lat, currentPosition.lng],
            [spotPos.lat, spotPos.lng]
        );
        
        // Auto-log at 20m
        if (distance <= 20) {
            performAutoLog(spotId);
        }
    });
}

async function performAutoLog(spotId) {
    try {
        const log = await apiRequest('/logs/', {
            method: 'POST',
            body: JSON.stringify({
                spot_id: spotId,
                latitude: currentPosition.lat,
                longitude: currentPosition.lng
            })
        });
        
        showNotification(
            'Auto Log!',
            `+${log.xp_gained} XP, +${log.claim_points} Claims`,
            'log-event'
        );
        
        loadStats();
    } catch (error) {
        // Cooldown or error - silently ignore
    }
}

window.logSpot = async function(spotId) {
    if (!currentPosition) return;
    
    try {
        const log = await apiRequest('/logs/', {
            method: 'POST',
            body: JSON.stringify({
                spot_id: spotId,
                latitude: currentPosition.lat,
                longitude: currentPosition.lng
            })
        });
        
        showNotification(
            'Logged!',
            `+${log.xp_gained} XP, +${log.claim_points} Claims`,
            'log-event'
        );
        
        loadStats();
        map.closePopup();
    } catch (error) {
        showNotification('Error', error.message, 'error');
    }
};

// Action Buttons
function toggleTracking() {
    trackingActive = !trackingActive;
    const btn = document.getElementById('btn-tracking');
    
    if (trackingActive) {
        btn.classList.add('active');
        startTrack();
    } else {
        btn.classList.remove('active');
        endTrack();
    }
}

async function startTrack() {
    try {
        const track = await apiRequest('/tracks/', {
            method: 'POST',
            body: JSON.stringify({
                name: `Track ${new Date().toLocaleString()}`
            })
        });
        
        activeTrackId = track.id;
        showNotification('Tracking', 'Started tracking your route', 'success');
    } catch (error) {
        console.error('Failed to start track:', error);
    }
}

async function endTrack() {
    if (!activeTrackId) return;
    
    try {
        await apiRequest(`/tracks/${activeTrackId}/end`, {
            method: 'POST'
        });
        
        showNotification('Tracking', 'Track saved', 'success');
        activeTrackId = null;
    } catch (error) {
        console.error('Failed to end track:', error);
    }
}

async function addTrackPoint(position) {
    if (!activeTrackId) return;
    
    try {
        await apiRequest(`/tracks/${activeTrackId}/points`, {
            method: 'POST',
            body: JSON.stringify({
                latitude: position.lat,
                longitude: position.lng,
                heading: position.heading,
                accuracy: position.accuracy
            })
        });
    } catch (error) {
        console.error('Failed to add track point:', error);
    }
}

function toggleFollow() {
    followMode = !followMode;
    const btn = document.getElementById('btn-follow');
    
    if (followMode) {
        btn.classList.add('active');
        if (currentPosition) {
            map.setView([currentPosition.lat, currentPosition.lng], map.getZoom());
        }
    } else {
        btn.classList.remove('active');
    }
}

function toggleCompass() {
    compassEnabled = !compassEnabled;
    const btn = document.getElementById('btn-compass');
    
    if (compassEnabled) {
        btn.classList.add('active');
        requestDeviceOrientation();
    } else {
        btn.classList.remove('active');
    }
}

function requestDeviceOrientation() {
    if (typeof DeviceOrientationEvent.requestPermission === 'function') {
        DeviceOrientationEvent.requestPermission()
            .then(permissionState => {
                if (permissionState === 'granted') {
                    window.addEventListener('deviceorientation', handleOrientation);
                }
            })
            .catch(console.error);
    } else {
        window.addEventListener('deviceorientation', handleOrientation);
    }
}

function handleOrientation(event) {
    if (!compassEnabled) return;
    
    const heading = event.alpha; // 0-360 degrees
    if (playerMarker && heading !== null) {
        const icon = playerMarker.getElement();
        if (icon) {
            icon.style.transform = `rotate(${heading}deg)`;
        }
    }
}

function centerMap() {
    if (currentPosition) {
        map.setView([currentPosition.lat, currentPosition.lng], map.getZoom());
    }
}

async function toggleHeatmap() {
    heatmapVisible = !heatmapVisible;
    const btn = document.getElementById('btn-heatmap');
    
    if (heatmapVisible) {
        btn.classList.add('active');
        await loadHeatmap();
        heatmapLayer.addTo(map);
    } else {
        btn.classList.remove('active');
        heatmapLayer.remove();
    }
}

async function loadHeatmap() {
    try {
        const heatmaps = await apiRequest('/claims/heatmap/all?limit=5');
        
        heatmapLayer.clearLayers();
        
        heatmaps.forEach(heatmap => {
            const points = heatmap.points.map(p => [p.latitude, p.longitude, p.intensity]);
            const heat = L.heatLayer(points, {
                radius: 25,
                blur: 35,
                maxZoom: 17
            });
            heatmapLayer.addLayer(heat);
        });
    } catch (error) {
        console.error('Failed to load heatmap:', error);
    }
}

async function updateClaimHeatmap() {
    if (heatmapVisible) {
        await loadHeatmap();
    }
}

function showLayerMenu() {
    // Simple layer switching (could be enhanced with a proper UI)
    const layers = Object.keys(window.mapLayers);
    const currentIndex = layers.findIndex(name => map.hasLayer(window.mapLayers[name]));
    const nextIndex = (currentIndex + 1) % layers.length;
    
    map.eachLayer(layer => {
        if (layer instanceof L.TileLayer) {
            map.removeLayer(layer);
        }
    });
    
    window.mapLayers[layers[nextIndex]].addTo(map);
    showNotification('Map Layer', `Switched to ${layers[nextIndex]}`, 'success');
}

function toggleStatsDetail() {
    const detail = document.getElementById('stats-detail');
    detail.classList.toggle('hidden');
}

// Notifications
function showNotification(title, message, type = '') {
    const container = document.getElementById('notifications');
    const notification = document.createElement('div');
    notification.className = 'notification ' + type;
    notification.innerHTML = `
        <h4>${title}</h4>
        <p>${message}</p>
    `;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

function showLogNotification(data) {
    showNotification(
        `${data.username} logged a spot!`,
        `${data.spot_name} (+${data.xp_gained} XP)`,
        'log-event'
    );
}

function showLootSpawn(data) {
    const marker = L.marker([data.latitude, data.longitude], {
        icon: L.divIcon({
            className: 'loot-marker',
            iconSize: [20, 20]
        })
    }).addTo(map);
    
    marker.bindPopup(`
        <b>Loot Spot!</b><br>
        +${data.xp} XP<br>
        ${data.item_name ? `Item: ${data.item_name}` : ''}<br>
        <button onclick="logSpot(${data.spot_id})">Collect</button>
    `);
    
    showNotification('Loot Spawned!', `+${data.xp} XP nearby`, 'loot-event');
    
    spotMarkers.set(data.spot_id, marker);
}
