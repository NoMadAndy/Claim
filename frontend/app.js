// Claim GPS Game - Frontend JavaScript
// Configuration
const API_BASE = window.location.origin + '/api';
const WS_BASE = (window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host + '/ws';

// Sound Manager
class SoundManager {
    constructor() {
        this.audioContext = null;
        this.audioInitialized = false;
        this.soundsEnabled = localStorage.getItem('claim_sounds_enabled') !== 'false'; // Default: true
        this.volume = parseFloat(localStorage.getItem('claim_sound_volume')) || 0.3;
        this.sounds = {};
        this.contextResumed = false;
        this.resumeAttempts = 0;
        this.setupGlobalListeners();
        // Do NOT auto-create AudioContext on load (iOS blocks it). Create lazily on first gesture or play.
    }

    setupGlobalListeners() {
        // Aggressive resume on ANY user interaction
        const events = ['click', 'touchstart', 'touchend', 'keydown', 'scroll'];
        events.forEach(event => {
            document.addEventListener(event, () => this.resumeContext(), { once: false, capture: true });
        });
    }

    initAudioContext() {
        try {
            if (!this.audioContext) {
                const AudioContext = window.AudioContext || window.webkitAudioContext;
                if (AudioContext) {
                    this.audioContext = new AudioContext();
                    console.log('AudioContext created, state:', this.audioContext.state);
                    if (window.debugLog) window.debugLog('🎵 AudioContext created, state: ' + this.audioContext.state);
                }
            }
        } catch (e) {
            console.warn('AudioContext not available:', e);
            if (window.debugLog) window.debugLog('🎵 AudioContext error: ' + e.message);
        }
    }

    resumeContext() {
        if (!this.audioContext) return;
        
        if (this.audioContext.state === 'suspended') {
            this.resumeAttempts++;
            if (window.debugLog) window.debugLog('⏸️ Resume attempt #' + this.resumeAttempts);
            this.audioContext.resume().then(() => {
                this.contextResumed = true;
                console.log('✓ AudioContext resumed (attempt', this.resumeAttempts + ')');
                if (window.debugLog) window.debugLog('✓ AudioContext resumed #' + this.resumeAttempts);
            }).catch(err => {
                console.warn('Resume failed:', err);
                if (window.debugLog) window.debugLog('✗ Resume failed: ' + err.message);
            });
        } else if (this.audioContext.state === 'running') {
            this.contextResumed = true;
        }
    }

    playHaptic(pattern) {
        // Vibration API fallback for iOS
        try {
            if (navigator.vibrate) {
                const result = navigator.vibrate(pattern);
                console.log('📳 Haptic triggered:', pattern, 'result:', result);
                if (window.debugLog) window.debugLog('📳 Haptic: ' + JSON.stringify(pattern) + ' result: ' + result);
            } else {
                console.log('📳 Vibration API not available');
                if (window.debugLog) window.debugLog('📳 Vibration API not available');
            }
        } catch (e) {
            console.log('📳 Haptic error:', e);
            if (window.debugLog) window.debugLog('📳 Haptic error: ' + e.message);
        }
    }

    playSound(type) {
        const msg = '🔊 playSound: ' + type + ' enabled:' + this.soundsEnabled + ' vol:' + this.volume;
        console.log(msg);
        if (window.debugLog) window.debugLog(msg);
        
        // Always try vibration as fallback
        if (!this.soundsEnabled) {
            console.log('🔊 Sound disabled - using haptics only');
            if (window.debugLog) window.debugLog('🔊 Sound disabled - haptics only');
            switch (type) {
                case 'log':
                    this.playHaptic([30, 30, 30]);
                    break;
                case 'loot':
                    this.playHaptic([50, 50, 50]);
                    break;
                case 'levelup':
                    this.playHaptic([100, 50, 100, 50, 100]);
                    break;
                case 'error':
                    this.playHaptic([200]);
                    break;
            }
            return;
        }

        if (!this.audioContext) {
            console.log('🔊 AudioContext not initialized');
            if (window.debugLog) window.debugLog('🔊 AudioContext not initialized');
            this.playHaptic([30]);
            return;
        }

        const ctxState = this.audioContext.state;
        console.log('🔊 AudioContext state:', ctxState);
        if (window.debugLog) window.debugLog('🔊 AudioContext state: ' + ctxState);

        // Always try to resume
        if (this.audioContext.state !== 'running') {
            console.log('🔊 Attempting to resume AudioContext...');
            if (window.debugLog) window.debugLog('🔊 Attempting resume...');
            this.resumeContext();
        }

        try {
            // If context still not running, use haptics
            if (this.audioContext.state !== 'running') {
                console.log('🔊 AudioContext still suspended - using haptics');
                if (window.debugLog) window.debugLog('🔊 Still suspended - haptics');
                this.playHaptic([30]);
                return;
            }

            const now = this.audioContext.currentTime;
            const osc = this.audioContext.createOscillator();
            const gain = this.audioContext.createGain();
            osc.connect(gain);
            gain.connect(this.audioContext.destination);

            gain.gain.setValueAtTime(this.volume, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.3);

            switch (type) {
                case 'log': // Success beep
                    osc.frequency.setValueAtTime(800, now);
                    osc.frequency.setValueAtTime(1000, now + 0.1);
                    osc.start(now);
                    osc.stop(now + 0.15);
                    this.playHaptic([30, 30, 30]);
                    break;
                case 'loot': // Ding
                    osc.frequency.setValueAtTime(1200, now);
                    osc.frequency.setValueAtTime(1500, now + 0.05);
                    osc.start(now);
                    osc.stop(now + 0.2);
                    this.playHaptic([50, 50, 50]);
                    break;
                case 'levelup': // Ascending tones
                    for (let i = 0; i < 3; i++) {
                        const osc2 = this.audioContext.createOscillator();
                        const gain2 = this.audioContext.createGain();
                        osc2.connect(gain2);
                        gain2.connect(this.audioContext.destination);
                        osc2.frequency.value = 600 + (i * 200);
                        gain2.gain.setValueAtTime(this.volume * 0.7, now + i * 0.1);
                        gain2.gain.exponentialRampToValueAtTime(0.01, now + i * 0.1 + 0.15);
                        osc2.start(now + i * 0.1);
                        osc2.stop(now + i * 0.1 + 0.15);
                    }
                    this.playHaptic([100, 50, 100, 50, 100]);
                    break;
                case 'error': // Low buzz
                    osc.frequency.setValueAtTime(300, now);
                    osc.frequency.setValueAtTime(250, now + 0.1);
                    osc.start(now);
                    osc.stop(now + 0.25);
                    this.playHaptic([200]);
                    break;
            }
        } catch (e) {
            console.warn('Sound playback failed:', e);
            this.playHaptic([30]);
        }
    }

    toggle() {
        this.soundsEnabled = !this.soundsEnabled;
        localStorage.setItem('claim_sounds_enabled', this.soundsEnabled);
        return this.soundsEnabled;
    }

    setVolume(vol) {
        this.volume = Math.max(0, Math.min(1, vol));
        localStorage.setItem('claim_sound_volume', this.volume);
    }
}

const soundManager = new SoundManager();

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
let wakeLock = null;
let wakeLockEnabled = false; // Initial aus
let heatmapUpdateInterval = null; // Interval für Heatmap-Refresh
let currentLevel = 0; // Track for level-up detection

// Map markers storage
const spotMarkers = new Map();
const playerMarkers = new Map();
const trackLayers = new Map(); // Store track polylines
let activeTrackPoints = []; // Current track points for live drawing

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
    
    // Logout button
    const logoutBtn = document.getElementById('btn-logout');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
    
    // Action buttons
    document.getElementById('btn-tracking').addEventListener('click', toggleTracking);
    document.getElementById('btn-follow').addEventListener('click', toggleFollow);
    document.getElementById('btn-compass').addEventListener('click', toggleCompass);
    document.getElementById('btn-layers').addEventListener('click', showLayerMenu);
    document.getElementById('btn-create-spot').addEventListener('click', toggleSpotCreationMode);
    document.getElementById('btn-wakelock').addEventListener('click', toggleWakeLock);
    document.getElementById('btn-settings').addEventListener('click', showSettings);
    
    // Settings modal
    document.getElementById('btn-close-settings').addEventListener('click', closeSettings);
    document.getElementById('setting-sound-toggle').addEventListener('change', toggleSound);
    document.getElementById('setting-volume-slider').addEventListener('input', changeVolume);
    
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

function handleLogout() {
    // Clear auth token and user data
    localStorage.removeItem('claim_token');
    authToken = null;
    currentUser = null;
    
    // Stop tracking and reset state
    if (trackingActive) {
        trackingActive = false;
        document.getElementById('btn-tracking').classList.remove('active');
    }
    if (ws) {
        ws.close();
        ws = null;
    }
    
    // Stop heatmap refresh interval
    if (heatmapUpdateInterval) {
        clearInterval(heatmapUpdateInterval);
        heatmapUpdateInterval = null;
    }
    
    // Show logout message
    showNotification('Logout', 'Successfully logged out', 'success');
    
    // Redirect to login
    setTimeout(() => {
        showLoginModal();
    }, 500);
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
        // Initialize debug
        if (window.debugLog) {
            window.debugLog('🎮 App initializing...');
            window.debugLog('🎵 SoundManager: ' + (soundManager ? 'OK' : 'FAIL'));
            window.debugLog('📱 AudioContext: ' + (soundManager?.audioContext ? soundManager.audioContext.state : 'null'));
        }
        
        // Fetch current user
        const response = await apiRequest('/auth/me');
        currentUser = response;
        
        // Update logout button with username
        const logoutBtn = document.getElementById('btn-logout');
        if (logoutBtn && currentUser.username) {
            logoutBtn.textContent = `Logout (${currentUser.username})`;
        }
        
        // Hide Create Spot button for travellers
        if (currentUser.role === 'traveller') {
            const createBtn = document.getElementById('btn-create-spot');
            if (createBtn) {
                createBtn.style.display = 'none';
            }
        }
        
        // Initialize map
        initMap();
        
        // Start GPS tracking
        startGPSTracking();
        
        // Enable follow mode initially
        followMode = true;
        document.getElementById('btn-follow').classList.add('active');
        
        // Don't automatically start tracking - let user decide via button
        trackingActive = false;
        
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
    // Start with default location (will be updated when GPS position arrives)
    map = L.map('map', {
        zoomControl: true,
        attributionControl: false,
        touchZoom: true,
        doubleClickZoom: true,
        scrollWheelZoom: true,
        dragging: true,
        tap: false
    }).setView([51.505, -0.09], 18);
    
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
    
    // Add click handler for creating spots
    map.on('click', handleMapClick);
}

// Handle map click for spot creation
let spotCreationMode = false;

function handleMapClick(e) {
    if (!spotCreationMode) return;
    
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;
    
    // Generate random spot name
    const adjectives = ['Mystischer', 'Geheimer', 'Verlassener', 'Alter', 'Neuer', 'Wilder', 'Ruhiger', 'Dunkler', 'Heller', 'Magischer'];
    const nouns = ['Ort', 'Platz', 'Punkt', 'Spot', 'Bereich', 'Zone', 'Fleck', 'Winkel', 'Ecke', 'Stelle'];
    const randomName = `${adjectives[Math.floor(Math.random() * adjectives.length)]} ${nouns[Math.floor(Math.random() * nouns.length)]} ${Math.floor(Math.random() * 1000)}`;
    
    // Create spot directly
    createSpotAtLocation(lat, lng, randomName);
    
    // Exit spot creation mode
    spotCreationMode = false;
    document.getElementById('btn-create-spot').classList.remove('active');
    showNotification('Spot erstellt', randomName, 'success');
}

// Toggle spot creation mode
function toggleSpotCreationMode() {
    spotCreationMode = !spotCreationMode;
    const btn = document.getElementById('btn-create-spot');
    
    if (spotCreationMode) {
        btn.classList.add('active');
        showNotification('Spot-Modus', 'Tippe auf die Karte um einen Spot zu erstellen', 'info');
    } else {
        btn.classList.remove('active');
    }
}

// Create spot at specific location
async function createSpotAtLocation(lat, lng, name) {
    if (!currentUser) {
        showMessage('Please login first', 'error');
        return;
    }
    
    // Check if user is creator or admin
    if (currentUser.role !== 'creator' && currentUser.role !== 'admin') {
        showMessage('Only creators and admins can create spots', 'error');
        return;
    }
    
    try {
        const response = await apiRequest('/spots/', {
            method: 'POST',
            body: JSON.stringify({
                name: name,
                description: '',
                latitude: lat,
                longitude: lng,
                is_permanent: true,
                is_loot: false
            }),
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        loadNearbySpots();
    } catch (error) {
        console.error('Create spot error:', error);
        showMessage('Failed to create spot', 'error');
    }
}

// GPS Tracking
function startGPSTracking() {
    if (!navigator.geolocation) {
        showNotification('GPS Error', 'Geolocation not supported', 'error');
        return;
    }
    
    // Get initial position and center map
    // Use longer timeout for initial request (may need time to get first fix)
    navigator.geolocation.getCurrentPosition(
        (position) => {
            map.setView([position.coords.latitude, position.coords.longitude], 18);
            console.log('Initial GPS position acquired');
        },
        (error) => {
            console.warn('Initial GPS error (code: ' + error.code + '):', error.message);
            // Don't show error for initial position - it's not critical
            // The watchPosition will continue trying
        },
        {
            enableHighAccuracy: true,
            timeout: 10000, // Increased timeout for initial position
            maximumAge: 30000 // Accept cached position up to 30s old
        }
    );
    
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
            // Handle different GPS error codes
            let errorMsg = 'Cannot access location';
            if (error.code === 1) {
                errorMsg = 'Permission denied - enable location in settings';
            } else if (error.code === 2) {
                errorMsg = 'Position unavailable - check GPS signal';
            } else if (error.code === 3) {
                errorMsg = 'GPS Timeout - trying to reconnect...';
            }
            
            console.warn('GPS error (code: ' + error.code + '):', error.message);
            // Only show notification for permission errors, not timeouts
            if (error.code === 1) {
                showNotification('GPS Error', errorMsg, 'error');
            }
        },
        {
            enableHighAccuracy: true,
            maximumAge: 5000, // Accept position up to 5s old for continuous tracking
            timeout: 10000 // Longer timeout to allow GPS to acquire fix
        }
    );
}

function updatePlayerPosition() {
    if (!currentPosition || !map) return;
    
    if (playerMarker) {
        // Just update position
        playerMarker.setLatLng([currentPosition.lat, currentPosition.lng]);
    } else {
        // Create marker with appropriate SVG based on compass state
        let arrowSvg;
        
        if (compassEnabled) {
            // Rotatable arrow
            arrowSvg = `
                <div style="width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; transform: rotate(${currentPosition.heading || 0}deg);">
                    <svg width="28" height="28" viewBox="0 0 28 28" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="14" cy="14" r="12" fill="#667eea" stroke="white" stroke-width="1.5"/>
                        <polygon points="14,6 18,12 10,12" fill="white"/>
                        <rect x="12.5" y="12" width="3" height="7" fill="white"/>
                    </svg>
                </div>
            `;
        } else {
            // Static arrow (no rotation)
            arrowSvg = `
                <svg width="28" height="28" viewBox="0 0 28 28" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="14" cy="14" r="12" fill="#667eea" stroke="white" stroke-width="1.5"/>
                    <polygon points="14,6 18,12 10,12" fill="white"/>
                    <rect x="12.5" y="12" width="3" height="7" fill="white"/>
                </svg>
            `;
        }
        
        playerMarker = L.marker([currentPosition.lat, currentPosition.lng], {
            icon: L.divIcon({
                html: arrowSvg,
                className: 'player-marker-container',
                iconSize: [28, 28],
                iconAnchor: [14, 14],
                popupAnchor: [0, -14]
            })
        }).addTo(map);
        
        // Bring player marker to front (above spots and other layers)
        playerMarker.setZIndexOffset(10000);
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
            // Aktualisiere Heatmap wenn sichtbar
            if (heatmapVisible) {
                loadHeatmap();
            }
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
        let errorDetail = response.statusText;
        try {
            const errorBody = await response.json();
            errorDetail = errorBody.detail || errorBody.message || errorBody.error || response.statusText;
        } catch (e) {
            // If response body is not JSON, use status text
        }
        
        const error = new Error(`API Error: ${errorDetail}`);
        error.status = response.status;
        error.detail = errorDetail;
        throw error;
    }
    
    return response.json();
}

// Data Loading
async function loadStats() {
    try {
        const stats = await apiRequest('/stats');
        
        // Check for level-up
        if (stats.level > currentLevel) {
            soundManager.playSound('levelup');
            showNotification('🎉 LEVEL UP!', `Du bist jetzt Level ${stats.level}!`, 'levelup');
            currentLevel = stats.level;
        } else if (currentLevel === 0) {
            currentLevel = stats.level; // Initialize on first load
        }
        
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
        
        soundManager.playSound('log');
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
        
        soundManager.playSound('log');
        showNotification(
            'Logged!',
            `+${log.xp_gained} XP, +${log.claim_points} Claims`,
            'log-event'
        );
        
        loadStats();
        map.closePopup();
    } catch (error) {
        // Check for 429 Too Many Requests (rate limiting/cooldown)
        if (error.status === 429) {
            soundManager.playSound('error');
            showNotification(
                '⏱️ Cooldown Active',
                error.detail || 'Please wait before logging this spot',
                'warning'
            );
        } else {
            showNotification('Error', error.message || 'Failed to log spot', 'error');
        }
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

async function startTrack(retryCount = 0) {
    try {
        const track = await apiRequest('/tracks/', {
            method: 'POST',
            body: JSON.stringify({
                name: `Track ${new Date().toLocaleString()}`
            })
        });
        
        activeTrackId = track.id;
        activeTrackPoints = []; // Reset live track points
        showNotification('Tracking', 'Started tracking your route', 'success');
    } catch (error) {
        console.error('Failed to start track:', error);
        
        // If there's already an active track, try to end it first
        if (error.detail && error.detail.includes('already have an active track') && retryCount < 5) {
            const waitTime = 500 + (retryCount * 500); // Progressive backoff: 500ms, 1s, 1.5s, 2s, 2.5s
            console.log(`Attempting to clean up old track (attempt ${retryCount + 1}/5, waiting ${waitTime}ms)...`);
            try {
                // Get list of active tracks and end them
                const myTracks = await apiRequest('/tracks/me?active_only=true');
                if (myTracks && myTracks.length > 0) {
                    console.log(`Found ${myTracks.length} active track(s), ending them...`);
                    for (const oldTrack of myTracks) {
                        await apiRequest(`/tracks/${oldTrack.id}/end`, { method: 'POST' });
                        console.log(`Ended old track ${oldTrack.id}`);
                    }
                }
                // Wait progressively longer before retrying
                await new Promise(r => setTimeout(r, waitTime));
                return startTrack(retryCount + 1);
            } catch (cleanupError) {
                console.error('Failed to clean up old tracks:', cleanupError);
                showNotification('Tracking', 'Failed to clean up old track: ' + (cleanupError.detail || cleanupError.message), 'error');
            }
        } else if (retryCount >= 5) {
            showNotification('Tracking', 'Failed: Could not clean up old tracks after 5 attempts', 'error');
        } else {
            showNotification('Tracking', 'Failed to start: ' + (error.detail || error.message || 'Unknown error'), 'error');
        }
    }
}

async function endTrack() {
    if (!activeTrackId) return;
    
    try {
        await apiRequest(`/tracks/${activeTrackId}/end`, {
            method: 'POST'
        });
        
        showNotification('Tracking', 'Track saved', 'success');
        
        // Clear active track visualization
        if (trackLayers.has('active')) {
            trackingLayer.removeLayer(trackLayers.get('active'));
            trackLayers.delete('active');
        }
        activeTrackPoints = [];
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
        
        // Add point to live track visualization
        activeTrackPoints.push([position.lat, position.lng]);
        updateActiveTrackLine();
    } catch (error) {
        console.error('Failed to add track point:', error);
    }
}

function updateActiveTrackLine() {
    // Remove old line if exists
    if (trackLayers.has('active')) {
        trackingLayer.removeLayer(trackLayers.get('active'));
    }
    
    // Draw new line with all points
    if (activeTrackPoints.length > 1) {
        const polyline = L.polyline(activeTrackPoints, {
            color: '#667eea',
            weight: 3,
            opacity: 0.8
        });
        trackingLayer.addLayer(polyline);
        trackLayers.set('active', polyline);
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
        // REQUEST ORIENTATION FIRST to set up listener before flag is toggled
        requestDeviceOrientation();
        // Recreate marker for compass mode - gets real heading from deviceorientation event
        if (playerMarker && map) {
            map.removeLayer(playerMarker);
            playerMarker = null;
        }
        // Don't call updatePlayerPosition yet - wait for first orientation event
        // to ensure we have a real heading value
    } else {
        btn.classList.remove('active');
        // Recreate marker for non-compass mode
        if (playerMarker && map) {
            map.removeLayer(playerMarker);
            playerMarker = null;
            updatePlayerPosition();
        }
    }
}

function requestDeviceOrientation() {
    // iOS 13+: Request permission for motion and orientation
    if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {
        DeviceOrientationEvent.requestPermission()
            .then(permissionState => {
                if (permissionState === 'granted') {
                    // iOS uses relative orientation with magnetometer when available
                    // The magnetometer is accessed via deviceorientation with absolute property check
                    window.addEventListener('deviceorientation', handleOrientationEvent, false);
                    document.getElementById('debug-heading').textContent = 'Compass active (WebKit)...';
                }
            })
            .catch(err => {
                document.getElementById('debug-heading').textContent = 'Permission denied';
            });
    } else {
        // Non-iOS: Try deviceorientationabsolute
        window.addEventListener('deviceorientationabsolute', handleOrientationEvent, false);
        document.getElementById('debug-heading').textContent = 'Compass active...';
    }
}

// Unified handler for both orientation events
function handleOrientationEvent(event) {
    if (!compassEnabled) return;
    
    const rawAlpha = event.alpha;
    const beta = event.beta;
    const gamma = event.gamma;
    
    // iOS WebKit: Use webkitCompassHeading if available (this is the magnetometer!)
    let heading;
    if (typeof event.webkitCompassHeading !== 'undefined') {
        // Direct magnetometer heading from WebKit
        heading = event.webkitCompassHeading;
        document.getElementById('debug-heading').textContent = Math.round(heading) + '° (webkitCompassHeading)';
    } else if (event.absolute) {
        // deviceorientationabsolute with magnetometer
        heading = rawAlpha;
        document.getElementById('debug-heading').textContent = Math.round(heading) + '° (absolute)';
    } else {
        // Fallback: relative orientation - apply correction formula
        // raw 270° = North, need to convert to 0°
        heading = (270 - rawAlpha) % 360;
        document.getElementById('debug-heading').textContent = Math.round(heading) + '° (relative, corrected)';
    }
    
    currentPosition.heading = heading;
    
    document.getElementById('debug-beta').textContent = Math.round(beta);
    document.getElementById('debug-gamma').textContent = Math.round(gamma);
    
    if (!playerMarker) {
        updatePlayerPosition();
    } else {
        const markerElement = playerMarker.getElement();
        if (markerElement) {
            const rotDiv = markerElement.querySelector('div');
            if (rotDiv) {
                rotDiv.style.transform = `rotate(${heading}deg)`;
            }
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
    
    if (heatmapVisible) {
        await loadHeatmap();
        heatmapLayer.addTo(map);
        
        // Starte Auto-Refresh der Heatmap (alle 30 Sekunden)
        if (heatmapUpdateInterval) {
            clearInterval(heatmapUpdateInterval);
        }
        heatmapUpdateInterval = setInterval(async () => {
            if (heatmapVisible) {
                await loadHeatmap();
                console.log('🔥 Heatmap aktualisiert');
            }
        }, 30000); // 30 Sekunden
    } else {
        map.removeLayer(heatmapLayer);
        
        // Stoppe Auto-Refresh
        if (heatmapUpdateInterval) {
            clearInterval(heatmapUpdateInterval);
            heatmapUpdateInterval = null;
        }
    }
}

async function loadHeatmap() {
    try {
        const heatmaps = await apiRequest('/claims/heatmap/all?limit=5');
        
        heatmapLayer.clearLayers();
        
        if (heatmaps && heatmaps.length > 0) {
            heatmaps.forEach(heatmap => {
                if (heatmap.points && heatmap.points.length > 0) {
                    const points = heatmap.points.map(p => [p.latitude, p.longitude, p.intensity]);
                    const heat = L.heatLayer(points, {
                        radius: 25,
                        blur: 35,
                        maxZoom: 17,
                        minOpacity: 0.4
                    });
                    heatmapLayer.addLayer(heat);
                }
            });
        }
        
        // Ensure heatmap is on top
        if (map.hasLayer(heatmapLayer)) {
            heatmapLayer.bringToFront();
        }
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
    const menu = document.createElement('div');
    menu.className = 'layer-menu';
    menu.innerHTML = `
        <h3>Kartenansicht & Overlays</h3>
        <div class="layer-section">
            <h4>Basiskarte</h4>
            ${Object.keys(window.mapLayers).map(name => `
                <label>
                    <input type="radio" name="baselayer" value="${name}" ${map.hasLayer(window.mapLayers[name]) ? 'checked' : ''}>
                    ${name}
                </label>
            `).join('')}
        </div>
        <div class="layer-section">
            <h4>Overlays</h4>
            <label>
                <input type="checkbox" id="overlay-heatmap" ${heatmapVisible ? 'checked' : ''}>
                Heatmap 🔥
            </label>
            <label>
                <input type="checkbox" id="overlay-tracks" ${trackLayers.size > (activeTrackId ? 1 : 0) ? 'checked' : ''}>
                Tracks 📊
            </label>
        </div>
        <button id="layer-close">Schließen</button>
    `;
    
    document.body.appendChild(menu);
    
    // Handle base layer changes
    menu.querySelectorAll('input[name="baselayer"]').forEach(input => {
        input.addEventListener('change', (e) => {
            if (e.target.checked) {
                map.eachLayer(layer => {
                    if (layer instanceof L.TileLayer) {
                        map.removeLayer(layer);
                    }
                });
                window.mapLayers[e.target.value].addTo(map);
            }
        });
    });
    
    // Handle heatmap overlay
    menu.querySelector('#overlay-heatmap').addEventListener('change', (e) => {
        if (e.target.checked) {
            toggleHeatmap();
        } else if (heatmapVisible) {
            toggleHeatmap();
        }
    });
    
    // Handle tracks overlay
    menu.querySelector('#overlay-tracks').addEventListener('change', (e) => {
        if (e.target.checked) {
            if (trackLayers.size === (activeTrackId ? 1 : 0)) {
                toggleTracksView();
            }
        } else {
            if (trackLayers.size > (activeTrackId ? 1 : 0)) {
                toggleTracksView();
            }
        }
    });
    
    // Close button
    menu.querySelector('#layer-close').addEventListener('click', () => {
        menu.remove();
    });
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
    
    soundManager.playSound('loot');
    showNotification('Loot Spawned!', `+${data.xp} XP nearby`, 'loot-event');
    
    spotMarkers.set(data.spot_id, marker);
}

// Create Spot Modal
function showCreateSpotModal() {
    if (!currentUser) {
        showMessage('Please login first', 'error');
        return;
    }
    
    // Check if user is creator or admin
    if (currentUser.role !== 'creator' && currentUser.role !== 'admin') {
        showMessage('Only creators and admins can create spots', 'error');
        return;
    }
    
    if (!currentPosition) {
        showMessage('Please enable GPS first', 'error');
        return;
    }
    
    const name = prompt('Spot name:');
    if (!name) return;
    
    const description = prompt('Spot description (optional):');
    const isLoot = confirm('Is this a loot spot?');
    
    createSpot({
        name: name,
        description: description || '',
        latitude: currentPosition.lat,
        longitude: currentPosition.lng,
        is_permanent: true,
        is_loot: isLoot
    });
}

async function createSpot(spotData) {
    try {
        const response = await apiRequest('/spots/', {
            method: 'POST',
            body: JSON.stringify(spotData),
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        showMessage(`Spot "${spotData.name}" created!`, 'success');
        loadNearbySpots();
    } catch (error) {
        console.error('Create spot error:', error);
        showMessage('Failed to create spot', 'error');
    }
}

// WakeLock - Keep screen on
async function requestWakeLock() {
    if (!('wakeLock' in navigator)) {
        console.log('WakeLock API not supported');
        return;
    }
    
    try {
        wakeLock = await navigator.wakeLock.request('screen');
        console.log('WakeLock acquired');
        
        wakeLock.addEventListener('release', () => {
            console.log('WakeLock released');
        });
    } catch (err) {
        console.error('WakeLock error:', err);
    }
}

async function releaseWakeLock() {
    if (wakeLock !== null) {
        await wakeLock.release();
        wakeLock = null;
        console.log('WakeLock manually released');
    }
}

function toggleWakeLock() {
    wakeLockEnabled = !wakeLockEnabled;
    const btn = document.getElementById('btn-wakelock');
    
    if (wakeLockEnabled) {
        btn.classList.add('active');
        requestWakeLock();
        showNotification('Display', 'Display bleibt an', 'success');
    } else {
        btn.classList.remove('active');
        releaseWakeLock();
        showNotification('Display', 'Display kann ausgehen', 'info');
    }
}

// Re-request wakelock when page becomes visible again
document.addEventListener('visibilitychange', async () => {
    if (wakeLockEnabled && document.visibilityState === 'visible') {
        await requestWakeLock();
    }
});

// Track Management Functions
async function loadAllTracks() {
    try {
        const tracks = await apiRequest('/tracks/');
        displayTracks(tracks);
    } catch (error) {
        console.error('Failed to load tracks:', error);
    }
}

async function loadTrackPoints(trackId) {
    try {
        const track = await apiRequest(`/tracks/${trackId}`);
        return track.points.map(p => [p.latitude, p.longitude]);
    } catch (error) {
        console.error('Failed to load track points:', error);
        return [];
    }
}

function displayTracks(tracks) {
    // Clear old tracks (except active)
    for (const [id, layer] of trackLayers.entries()) {
        if (id !== 'active') {
            trackingLayer.removeLayer(layer);
            trackLayers.delete(id);
        }
    }
    
    // Display each track
    tracks.forEach(async (track) => {
        const points = await loadTrackPoints(track.id);
        if (points.length > 1) {
            const polyline = L.polyline(points, {
                color: track.id === activeTrackId ? '#667eea' : '#888',
                weight: 2,
                opacity: 0.6
            });
            
            // Add click handler to show track info
            polyline.bindPopup(`
                <strong>${track.name}</strong><br>
                Started: ${new Date(track.started_at).toLocaleString()}<br>
                ${track.ended_at ? 'Ended: ' + new Date(track.ended_at).toLocaleString() : 'Active'}
            `);
            
            trackingLayer.addLayer(polyline);
            trackLayers.set(track.id, polyline);
        }
    });
}

function toggleTracksView() {
    const hasOldTracks = trackLayers.size > (activeTrackId ? 1 : 0);
    
    if (hasOldTracks) {
        // Hide all old tracks
        for (const [id, layer] of trackLayers.entries()) {
            if (id !== 'active') {
                trackingLayer.removeLayer(layer);
                trackLayers.delete(id);
            }
        }
        showNotification('Tracks', 'Alte Tracks ausgeblendet', 'info');
    } else {
        // Load and show all tracks
        loadAllTracks();
        showNotification('Tracks', 'Lade alle Tracks...', 'info');
    }
}

// Settings Functions
function showSettings() {
    const settingsModal = document.getElementById('settings-modal');
    settingsModal.classList.remove('hidden');
    
    // Update current settings in UI
    document.getElementById('setting-sound-toggle').checked = soundManager.soundsEnabled;
    document.getElementById('setting-volume-slider').value = soundManager.volume * 100;
    document.getElementById('volume-value').textContent = Math.round(soundManager.volume * 100) + '%';
}

function closeSettings() {
    const settingsModal = document.getElementById('settings-modal');
    settingsModal.classList.add('hidden');
}

function toggleSound() {
    const enabled = soundManager.toggle();
    soundManager.playSound('log'); // Play sound to confirm
    showNotification('Sound', enabled ? '🔊 Aktiviert' : '🔇 Deaktiviert', 'info');
}

function changeVolume() {
    const slider = document.getElementById('setting-volume-slider');
    const volume = slider.value / 100;
    soundManager.setVolume(volume);
    document.getElementById('volume-value').textContent = slider.value + '%';
}
