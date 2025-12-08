// Claim GPS Game - Frontend JavaScript
// Configuration
const API_BASE = window.location.origin + '/api';
const WS_BASE = (window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host + '/ws';

// Auto-log cooldown tracking to prevent spam in console
let autoLogCooldownUntil = 0;
// Track spots already being logged to prevent duplicate requests
const spotsBeingLogged = new Set();
// Track last auto-log time per spot to prevent rapid re-triggering
const lastAutoLogTime = new Map();

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
        this.unlocked = false; // NEW: Track if unlock button was pressed
        this.setupGlobalListeners();
        // Version tag for debugging
        if (window.debugLog) window.debugLog('SoundManager init v1765059200');
        console.log('SoundManager init v1765059200');
        // Do NOT auto-create AudioContext on load (iOS blocks it). Create lazily on first gesture or play.
        // Do NOT setup global listeners - only manual unlock button
    }

    setupGlobalListeners() {
        // Setup global listeners for aggressive auto-unlock on ANY user interaction
        // iOS requires multiple unlock attempts, so we trigger on EVERY click/touch
        const unlockAudio = () => {
            this.performUnlock();
        };
        
        // Listen for EVERY user interaction (not just first)
        document.addEventListener('click', unlockAudio, { passive: true });
        document.addEventListener('touchstart', unlockAudio, { passive: true });
    }

    performUnlock() {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        const ctx = new AudioContext({ latencyHint: 'interactive' });
        
        // Don't play beeps - just create context silently
        ctx.resume().catch(() => {});
        this.setUnlocked(ctx);
    }

    // Called by unlock button to mark audio as unlocked
    setUnlocked(ctx) {
        this.unlocked = true;
        this.audioContext = ctx;
        this.audioInitialized = true;
    }

    // Workaround: Use actual audio file to unlock iOS audio
    async autoUnlockOnLoad() {
        try {
            // Create a simple beep tone as base64-encoded WAV
            // This is a 1kHz sine wave, 100ms, mono, 16-bit, 44.1kHz
            const wavBase64 = 'UklGRiYAAABXQVZFZm10IBAAAAABAAEAQB8AAAB9AAACABAAZGF0YQIAAAAAAA==';
            const binaryString = atob(wavBase64);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) return;
            
            const ctx = new AudioContext({ latencyHint: 'interactive' });
            const audioBuffer = await ctx.decodeAudioData(bytes.buffer);
            
            // Play the buffer
            const source = ctx.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(ctx.destination);
            source.start(0);
            
            // Store context
            this.audioContext = ctx;
            this.unlocked = true;
            this.audioInitialized = true;
            
            console.log('🔊 AutoUnlock: Audio file played, context ready');
            if (window.debugLog) window.debugLog('🔊 AutoUnlock: Audio file played');
        } catch (e) {
            console.log('🔊 AutoUnlock with file failed:', e.message);
            // Fallback: try oscillator method
            try {
                const AudioContext = window.AudioContext || window.webkitAudioContext;
                if (AudioContext) {
                    const ctx = new AudioContext({ latencyHint: 'interactive' });
                    const now = ctx.currentTime;
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    gain.gain.setValueAtTime(0.00001, now);
                    gain.gain.exponentialRampToValueAtTime(0.000001, now + 0.01);
                    osc.frequency.value = 440;
                    osc.start(now);
                    osc.stop(now + 0.01);
                    
                    this.audioContext = ctx;
                    this.unlocked = true;
                    this.audioInitialized = true;
                    
                    console.log('🔊 AutoUnlock: Oscillator fallback used');
                    if (window.debugLog) window.debugLog('🔊 AutoUnlock: Oscillator fallback');
                }
            } catch (e2) {
                console.log('🔊 AutoUnlock completely failed:', e2.message);
            }
        }
    }

    initAudioContext(force = false) {
        try {
            if (!this.audioContext || force) {
                const AudioContext = window.AudioContext || window.webkitAudioContext;
                if (AudioContext) {
                    this.audioContext = new AudioContext({ latencyHint: 'interactive' });
                    this.audioInitialized = true;
                    console.log('AudioContext created, state:', this.audioContext.state);
                    if (window.debugLog) window.debugLog('🎵 AudioContext created, state: ' + this.audioContext.state);
                }
            }
        } catch (e) {
            console.warn('AudioContext not available:', e);
            if (window.debugLog) window.debugLog('🎵 AudioContext error: ' + e.message);
        }
    }

    async resumeContext() {
        if (!this.audioContext) return false;
        if (this.audioContext.state === 'suspended') {
            this.resumeAttempts++;
            if (window.debugLog) window.debugLog('⏸️ Resume attempt #' + this.resumeAttempts);
            try {
                await this.audioContext.resume();
                this.contextResumed = true;
                const st = this.audioContext.state;
                console.log('✓ AudioContext resumed (attempt', this.resumeAttempts + ') state:', st);
                if (window.debugLog) window.debugLog('✓ AudioContext resumed #' + this.resumeAttempts + ' state:' + st);
                // kick a silent buffer to fully unlock on iOS
                this.playUnlockTone();
                return st === 'running';
            } catch (err) {
                console.warn('Resume failed:', err);
                if (window.debugLog) window.debugLog('✗ Resume failed: ' + err.message);
                return false;
            }
        } else if (this.audioContext.state === 'running') {
            this.contextResumed = true;
            return true;
        }
        return false;
    }

    playHaptic(pattern) {
        // Vibration API fallback for iOS
        // Only try if user has already interacted (vibrate blocked otherwise)
        try {
            if (navigator.vibrate) {
                const result = navigator.vibrate(pattern);
                // Suppress logging for vibration since it often fails early in app lifecycle
                if (result) {
                    console.log('📳 Haptic triggered:', pattern);
                    if (window.debugLog) window.debugLog('📳 Haptic: ' + JSON.stringify(pattern));
                }
            } else {
                console.log('📳 Vibration API not available');
                if (window.debugLog) window.debugLog('📳 Vibration API not available');
            }
        } catch (e) {
            console.log('📳 Haptic error:', e);
            if (window.debugLog) window.debugLog('📳 Haptic error: ' + e.message);
        }
    }

    playUnlockTone() {
        if (!this.audioContext || this.audioContext.state !== 'running') return;
        try {
            const now = this.audioContext.currentTime;
            const osc = this.audioContext.createOscillator();
            const gain = this.audioContext.createGain();
            osc.connect(gain);
            gain.connect(this.audioContext.destination);
            gain.gain.setValueAtTime(0.0001, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
            osc.frequency.setValueAtTime(440, now);
            osc.start(now);
            osc.stop(now + 0.1);
            if (window.debugLog) window.debugLog('🔓 Unlock tone played');
        } catch (e) {
            if (window.debugLog) window.debugLog('🔓 Unlock tone failed: ' + e.message);
        }
    }

    async ensureContext(force) {
        if (!this.audioContext || force) {
            this.initAudioContext(true);
            if (window.debugLog) window.debugLog('🎵 initAudioContext invoked');
        }
        const resumed = await this.resumeContext();
        return resumed;
    }

    // Audio samples (Base64-encoded WAV files)
    audioSamples = {
        // LOG sound: Triumphales aufsteigendes Ding für Spot-Capture (E-G-C chord, ascending)
        log: 'UklGRiYAAABXQVZFZm10IBAAAAABAAEAQB8AAAB9AAACABAAZGF0YQIAAAAAAA=='
    };

    async playSound(type) {
        const msg = '🔊 playSound: ' + type + ' enabled:' + this.soundsEnabled + ' vol:' + this.volume;
        console.log(msg);
        if (window.debugLog) window.debugLog(msg);

        // Error sound can be played even if not fully unlocked (important for immediate feedback)
        // Other sounds require unlock
        if (!this.unlocked && type !== 'error') {
            if (window.debugLog) window.debugLog('🔊 Not unlocked yet - using haptics');
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
            }
            return;
        }
        
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

        // If context is dead/closed, recreate it
        if (!this.audioContext || this.audioContext.state === 'closed') {
            try {
                const AudioContext = window.AudioContext || window.webkitAudioContext;
                if (AudioContext) {
                    this.audioContext = new AudioContext({ latencyHint: 'interactive' });
                    if (window.debugLog) window.debugLog('🔊 AudioContext recreated');
                }
            } catch (e) {
                if (window.debugLog) window.debugLog('🔊 Recreate failed: ' + e.message);
                this.playHaptic([30]);
                return;
            }
        }

        const ctxState = this.audioContext.state;
        console.log('🔊 AudioContext state:', ctxState);
        if (window.debugLog) window.debugLog('🔊 AudioContext state: ' + ctxState);

        try {
            // Try to play sound
            const now = this.audioContext.currentTime;

            switch (type) {
                case 'log': // Triumphales aufsteigendes Ding
                    await this.playLogSound(now);
                    this.playHaptic([30, 30, 30]);
                    break;
                case 'loot': // Loot/Item sound
                    await this.playLootSound(now);
                    this.playHaptic([50, 50, 50]);
                    break;
                case 'levelup': // Ascending tones
                    await this.playLevelupSound(now);
                    this.playHaptic([100, 50, 100, 50, 100]);
                    break;
                case 'error': // Low buzz
                    await this.playErrorSound(now);
                    this.playHaptic([200]);
                    break;
            }
        } catch (e) {
            console.warn('Sound playback failed:', e);
            if (window.debugLog) window.debugLog('🔊 Playback error: ' + e.message);
            this.playHaptic([30]);
        }
    }

    // Play triumphales aufsteigendes Log-Sound (E-G-C chord progression)
    async playLogSound(now) {
        try {
            // Load and play Yum_CMaj.wav
            if (!this.logSoundBuffer) {
                console.log('🎵 Loading Yum_CMaj.wav from /sounds/Yum_CMaj.wav');
                const response = await fetch('/sounds/Yum_CMaj.wav');
                if (!response.ok) {
                    console.error(`🎵 Failed to load: HTTP ${response.status}`);
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                const arrayBuffer = await response.arrayBuffer();
                console.log('🎵 Decoding audio buffer...');
                this.logSoundBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
                console.log('🎵 Buffer loaded successfully, duration:', this.logSoundBuffer.duration);
            }
            
            const source = this.audioContext.createBufferSource();
            source.buffer = this.logSoundBuffer;
            
            const gain = this.audioContext.createGain();
            gain.gain.setValueAtTime(this.volume, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + this.logSoundBuffer.duration);
            
            source.connect(gain);
            gain.connect(this.audioContext.destination);
            console.log('🎵 Playing Yum_CMaj.wav');
            source.start(now);
        } catch (e) {
            console.warn('🎵 Failed to play Yum sound, falling back to oscillator:', e);
            // Fallback: Play E-G-C chord if file loading fails
            const frequencies = [330, 392, 523]; // E, G, C (triadic chord)
            const duration = 0.15;
            const startDelay = 0.05;
            
            for (let i = 0; i < frequencies.length; i++) {
                const osc = this.audioContext.createOscillator();
                const gain = this.audioContext.createGain();
                osc.connect(gain);
                gain.connect(this.audioContext.destination);
                
                const startTime = now + (i * startDelay);
                osc.frequency.value = frequencies[i];
                gain.gain.setValueAtTime(this.volume * 0.8, startTime);
                gain.gain.exponentialRampToValueAtTime(0.01, startTime + duration);
                
                osc.start(startTime);
                osc.stop(startTime + duration);
            }
        }
    }

    // Play error sound from WAV file
    async playErrorSound(now) {
        try {
            // Ensure we have an AudioContext (may not be initialized yet on first error)
            if (!this.audioContext || this.audioContext.state === 'closed') {
                const AudioContext = window.AudioContext || window.webkitAudioContext;
                this.audioContext = new AudioContext({ latencyHint: 'interactive' });
                this.audioContext.resume().catch(() => {});
            }
            
            // Load and play error sound
            if (!this.errorSoundBuffer) {
                console.log('🎵 Loading error sound from /sounds/Sound%20LD%20Bumpy%20Reconstruction_keyC%23min.wav');
                const response = await fetch('/sounds/Sound%20LD%20Bumpy%20Reconstruction_keyC%23min.wav');
                if (!response.ok) {
                    console.error(`🎵 Failed to load error sound: HTTP ${response.status}`);
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                const arrayBuffer = await response.arrayBuffer();
                console.log('🎵 Decoding error sound buffer...');
                this.errorSoundBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
                console.log('🎵 Error buffer loaded successfully, duration:', this.errorSoundBuffer.duration);
            }
            
            const source = this.audioContext.createBufferSource();
            source.buffer = this.errorSoundBuffer;
            
            const gain = this.audioContext.createGain();
            gain.gain.setValueAtTime(this.volume, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + this.errorSoundBuffer.duration);
            
            source.connect(gain);
            gain.connect(this.audioContext.destination);
            console.log('🎵 Playing error sound');
            source.start(now);
        } catch (e) {
            console.warn('🎵 Failed to play error sound:', e);
            // No fallback - just fail silently if WAV doesn't load
        }
    }

    // Play levelup sound from WAV file
    async playLevelupSound(now) {
        try {
            // Load and play levelup sound
            if (!this.levelupSoundBuffer) {
                console.log('🎵 Loading levelup sound from /sounds/TR%20727%20Beat%203_125bpm.wav');
                const response = await fetch('/sounds/TR%20727%20Beat%203_125bpm.wav');
                if (!response.ok) {
                    console.error(`🎵 Failed to load levelup sound: HTTP ${response.status}`);
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                const arrayBuffer = await response.arrayBuffer();
                console.log('🎵 Decoding levelup sound buffer...');
                this.levelupSoundBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
                console.log('🎵 Levelup buffer loaded successfully, duration:', this.levelupSoundBuffer.duration);
            }
            
            const source = this.audioContext.createBufferSource();
            source.buffer = this.levelupSoundBuffer;
            
            const gain = this.audioContext.createGain();
            gain.gain.setValueAtTime(this.volume, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + this.levelupSoundBuffer.duration);
            
            source.connect(gain);
            gain.connect(this.audioContext.destination);
            console.log('🎵 Playing levelup sound');
            source.start(now);
        } catch (e) {
            console.warn('🎵 Failed to play levelup sound:', e);
            // No fallback - just fail silently if WAV doesn't load
        }
    }

    // Play loot sound from WAV file
    async playLootSound(now) {
        try {
            // Load and play loot sound
            if (!this.lootSoundBuffer) {
                console.log('🎵 Loading loot sound from /sounds/DN_DSV_Vocal_Yeah_02_KeyBmin_56bpm.wav');
                const response = await fetch('/sounds/DN_DSV_Vocal_Yeah_02_KeyBmin_56bpm.wav');
                if (!response.ok) {
                    console.error(`🎵 Failed to load loot sound: HTTP ${response.status}`);
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                const arrayBuffer = await response.arrayBuffer();
                console.log('🎵 Decoding loot sound buffer...');
                this.lootSoundBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
                console.log('🎵 Loot buffer loaded successfully, duration:', this.lootSoundBuffer.duration);
            }
            
            const source = this.audioContext.createBufferSource();
            source.buffer = this.lootSoundBuffer;
            
            const gain = this.audioContext.createGain();
            gain.gain.setValueAtTime(this.volume, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + this.lootSoundBuffer.duration);
            
            source.connect(gain);
            gain.connect(this.audioContext.destination);
            console.log('🎵 Playing loot sound');
            source.start(now);
        } catch (e) {
            console.warn('🎵 Failed to play loot sound:', e);
            // No fallback - just fail silently if WAV doesn't load
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
// Expose globally for debug/HTML button handlers
window.soundManager = soundManager;

// Heatmap color palette for different players
const HEATMAP_COLORS = [
    { user: 'Player1', gradient: {0.4: 'red', 0.65: 'orange', 1.0: 'yellow'} },
    { user: 'Player2', gradient: {0.4: 'blue', 0.65: 'cyan', 1.0: 'lime'} },
    { user: 'Player3', gradient: {0.4: 'purple', 0.65: 'magenta', 1.0: 'pink'} },
    { user: 'Player4', gradient: {0.4: 'green', 0.65: 'lightgreen', 1.0: 'yellow'} },
    { user: 'Player5', gradient: {0.4: 'brown', 0.65: 'orange', 1.0: 'gold'} }
];

// State
let map, playerMarker, trackingLayer, heatmapLayer;
let currentPosition = null;
let lastSpotReloadPosition = null; // Track last position when spots were reloaded
let spotReloadTimeout = null; // Debounce timeout for spot reloading
let lastGPSUpdateTime = null; // Track last GPS update for tracking pause detection
let followMode = false;
let trackingActive = false;
let compassEnabled = false;
let heatmapVisible = true;  // Start with heatmap enabled
let authToken = null;
let ws = null;
let currentUser = null;
let activeTrackId = null;
let wakeLock = null;
let wakeLockEnabled = false; // Initial aus
let heatmapUpdateInterval = null; // Interval für Heatmap-Refresh
let currentLevel = 0; // Track for level-up detection
let activeHeatmaps = new Set(); // Track which player heatmaps are visible
let heatmapLayers = new Map(); // Map of userId -> heatmapLayer

// Map markers storage
const spotMarkers = new Map();
const playerMarkers = new Map();
const trackLayers = new Map(); // Store track polylines
let activeTrackPoints = []; // Current track points for live drawing

// Version information
function getVersionInfo() {
    // Get version from data attribute if injected during build, otherwise use timestamp
    const versionElement = document.getElementById('version-hash');
    const commitHash = versionElement?.dataset.commit || new Date().toISOString().split('T')[0];
    return commitHash.substring(0, 8);
}

function getVersionTimestamp() {
    // Get timestamp from data attribute if available
    const versionElement = document.getElementById('version-hash');
    const timestamp = versionElement?.dataset.timestamp;
    return timestamp || new Date().toLocaleString('de-DE');
}

function initVersionBadge() {
    const timestampDisplay = document.getElementById('timestamp-display');
    const toggleDebugBtn = document.getElementById('toggle-debug');
    
    console.log('initVersionBadge called');
    console.log('timestampDisplay:', timestampDisplay);
    console.log('toggleDebugBtn:', toggleDebugBtn);
    
    if (timestampDisplay && toggleDebugBtn) {
        let commit = toggleDebugBtn.getAttribute('data-commit');
        let timestamp = toggleDebugBtn.getAttribute('data-timestamp');
        
        console.log('commit attribute:', commit);
        console.log('timestamp attribute:', timestamp);
        
        // Fallback if not injected
        if (!commit) {
            commit = new Date().toISOString().split('T')[0];
        }
        if (!timestamp) {
            timestamp = new Date().toLocaleString('de-DE');
        }
        
        if (commit && timestamp) {
            // Format: commit hash + timestamp
            // Example: 0def80fd • 07.12.2025 19:32:27
            const displayText = `${commit.substring(0, 8)} • ${timestamp}`;
            console.log('displayText:', displayText);
            timestampDisplay.textContent = displayText;
            timestampDisplay.title = `Commit: ${commit}\nDeployed: ${timestamp}`;
            
            if (window.debugLog) {
                window.debugLog(`🔖 Commit: ${commit}`);
                window.debugLog(`📅 Deployed: ${timestamp}`);
            }
        }
    } else {
        console.error('timestampDisplay or toggleDebugBtn not found');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);

function init() {
    // Lock screen orientation to portrait (if supported)
    lockOrientationToPortrait();
    
    // Initialize version badge
    initVersionBadge();
    
    // Check for existing auth
    try {
        authToken = localStorage.getItem('claim_token');
    } catch (e) {
        console.warn('Storage blocked:', e);
        authToken = null;
    }
    
    if (!authToken) {
        showLoginModal();
    } else {
        hideLoginModal();
        initializeApp();
    }
    
    // Setup event listeners
    setupEventListeners();
}

function lockOrientationToPortrait() {
    // Try to lock orientation using Screen Orientation API
    if (screen.orientation && screen.orientation.lock) {
        screen.orientation.lock('portrait').catch(err => {
            console.log('Screen orientation lock not supported:', err.message);
        });
    }
    
    // Check orientation on load
    checkOrientation();
    
    // Listen for orientation changes (iOS and Android)
    window.addEventListener('orientationchange', checkOrientation);
    window.addEventListener('resize', checkOrientation);
    
    // Also use matchMedia for more reliable detection
    const portraitQuery = window.matchMedia('(orientation: portrait)');
    portraitQuery.addEventListener('change', checkOrientation);
}

function checkOrientation() {
    // Check multiple ways to detect landscape
    const isLandscape = 
        (window.orientation === 90 || window.orientation === -90) || // iOS orientationchange
        (window.innerWidth > window.innerHeight) || // Dimension check
        (window.matchMedia && window.matchMedia('(orientation: landscape)').matches); // Media query
    
    if (isLandscape) {
        showRotationWarning();
    } else {
        hideRotationWarning();
    }
}

function showRotationWarning() {
    let warning = document.getElementById('rotation-warning');
    if (!warning) {
        warning = document.createElement('div');
        warning.id = 'rotation-warning';
        warning.style.cssText = `
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            height: 100% !important;
            background: rgba(0, 0, 0, 0.98) !important;
            color: white !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            z-index: 999999 !important;
            font-size: 18px !important;
            text-align: center !important;
            padding: 20px !important;
            pointer-events: auto !important;
        `;
        warning.innerHTML = `
            <div style="font-size: 100px; margin-bottom: 30px; animation: rotate 2s infinite;">📱</div>
            <div style="font-weight: bold; font-size: 24px; margin-bottom: 15px;">Bitte drehe dein Gerät</div>
            <div style="font-size: 16px; opacity: 0.8;">Diese App funktioniert nur im Hochformat</div>
        `;
        // Add CSS animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes rotate {
                0%, 100% { transform: rotate(0deg); }
                25% { transform: rotate(-15deg); }
                75% { transform: rotate(15deg); }
            }
        `;
        document.head.appendChild(style);
        document.body.appendChild(warning);
    }
    warning.style.display = 'flex';
    // Prevent any interaction with the app when in landscape
    document.body.style.overflow = 'hidden';
    document.body.style.pointerEvents = 'none';
    warning.style.pointerEvents = 'auto';
}

function hideRotationWarning() {
    const warning = document.getElementById('rotation-warning');
    if (warning) {
        warning.style.display = 'none';
    }
    // Re-enable interaction with the app
    document.body.style.pointerEvents = 'auto';
}

function setupEventListeners() {
    // Auth buttons
    const btnLogin = document.getElementById('btn-login');
    if (btnLogin) btnLogin.addEventListener('click', handleLogin);
    
    // Enter key support for login fields
    const loginUsername = document.getElementById('login-username');
    const loginPassword = document.getElementById('login-password');
    if (loginUsername) {
        loginUsername.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleLogin();
            }
        });
    }
    if (loginPassword) {
        loginPassword.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleLogin();
            }
        });
    }
    
    const btnRegister = document.getElementById('btn-register');
    if (btnRegister) btnRegister.addEventListener('click', handleRegister);
    const showRegister = document.getElementById('show-register');
    if (showRegister) showRegister.addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('login-form')?.classList.add('hidden');
        document.getElementById('register-form')?.classList.remove('hidden');
    });
    const showLogin = document.getElementById('show-login');
    if (showLogin) showLogin.addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('register-form')?.classList.add('hidden');
        document.getElementById('login-form')?.classList.remove('hidden');
    });
    
    // Logout button
    const logoutBtn = document.getElementById('btn-logout');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
    
    // Action buttons
    document.getElementById('btn-tracking')?.addEventListener('click', toggleTracking);
    document.getElementById('btn-follow')?.addEventListener('click', toggleFollow);
    document.getElementById('btn-compass')?.addEventListener('click', toggleCompass);
    document.getElementById('btn-layers')?.addEventListener('click', showLayerMenu);
    document.getElementById('btn-create-spot')?.addEventListener('click', toggleSpotCreationMode);
    document.getElementById('btn-wakelock')?.addEventListener('click', toggleWakeLock);
    document.getElementById('btn-settings')?.addEventListener('click', showSettings);
    document.getElementById('btn-inventory')?.addEventListener('click', showInventory);
    
    // Settings modal
    document.getElementById('btn-close-settings')?.addEventListener('click', closeSettings);
    document.getElementById('setting-sound-toggle')?.addEventListener('change', toggleSound);
    document.getElementById('setting-volume-slider')?.addEventListener('input', changeVolume);
    
    // Inventory modal
    document.getElementById('btn-close-inventory')?.addEventListener('click', closeInventory);
    
    // Stats toggle
    document.getElementById('stats-toggle')?.addEventListener('click', toggleStatsDetail);
}

// Authentication
async function handleLogin() {
    const username = document.getElementById('login-username').value.toLowerCase().trim();
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
        // Set token immediately and ensure it's available
        authToken = data.access_token;
        localStorage.setItem('claim_token', authToken);
        
        showMessage('Login successful!', 'success');
        
        // Give more time for token to be stored and available
        await new Promise(resolve => setTimeout(resolve, 500));
        
        hideLoginModal();
        
        // Make sure token is available before initializing
        if (!authToken) {
            console.error('Token not set after login');
            showMessage('Token initialization failed, please login again', 'error');
            showLoginModal();
            return;
        }
        
        // Initialize with retry logic
        let retries = 3;
        let lastError;
        while (retries > 0) {
            try {
                await initializeApp();
                break; // Success, exit retry loop
            } catch (error) {
                lastError = error;
                retries--;
                if (retries > 0) {
                    console.warn(`App initialization failed, retrying... (${retries} attempts left)`, error);
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
            }
        }
        
        if (retries === 0) {
            console.error('App initialization failed after retries:', lastError);
            showMessage('Failed to initialize app after login. Please refresh the page.', 'error');
            showLoginModal();
        }
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
    if (window.debugLog) window.debugLog('👋 Logging out...');
    localStorage.removeItem('claim_token');
    authToken = null;
    currentUser = null;
    
    // Stop tracking and reset state
    if (trackingActive) {
        trackingActive = false;
        document.getElementById('btn-tracking').classList.remove('active');
        if (window.debugLog) window.debugLog('🛑 Tracking stopped');
    }
    if (ws) {
        ws.close();
        ws = null;
        if (window.debugLog) window.debugLog('🌐 WebSocket closed');
    }
    
    // Stop heatmap refresh interval
    if (heatmapUpdateInterval) {
        clearInterval(heatmapUpdateInterval);
        heatmapUpdateInterval = null;
    }
    
    // Show logout message
    showNotification('Logout', 'Successfully logged out', 'success');
    if (window.debugLog) window.debugLog('✅ Logged out successfully');
    
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
        
        // Auto-unlock audio on iOS (workaround for audio device lock)
        if (soundManager) {
            await soundManager.autoUnlockOnLoad();
        }
        
        // Fetch current user
        const response = await apiRequest('/auth/me');
        currentUser = response;
        if (window.debugLog) window.debugLog(`👤 User loaded: ${currentUser.username} (${currentUser.role})`);
        
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
        if (window.debugLog) window.debugLog('🗺️ Map initialized');
        
        // Start GPS tracking
        startGPSTracking();
        if (window.debugLog) window.debugLog('📍 GPS tracking started');
        
        // Enable follow mode initially
        followMode = true;
        document.getElementById('btn-follow').classList.add('active');
        
        // Don't automatically start tracking - let user decide via button
        trackingActive = false;
        
        // Connect WebSocket
        connectWebSocket();
        if (window.debugLog) window.debugLog('🌐 WebSocket connecting...');
        
        // Cleanup expired loot before loading
        try {
            await apiRequest('/loot/cleanup', { method: 'POST' });
            if (window.debugLog) window.debugLog('🧹 Expired loot cleaned up');
        } catch (cleanupError) {
            console.error('Loot cleanup failed:', cleanupError);
        }
        
        // Load initial data
        loadStats();
        loadNearbySpots();
        trySpawnLoot(); // Try to spawn initial loot
        if (window.debugLog) window.debugLog('📊 Initial data loaded');
        
        // Load heatmap if visible
        if (heatmapVisible) {
            await loadHeatmap();
            heatmapLayer.addTo(map);
            if (window.debugLog) window.debugLog('🔥 Heatmap loaded');
        }
        
        // Start update loops
        setInterval(updateAutoLog, 1000); // Check auto-log every 1 second
        setInterval(loadStats, 30000); // Update stats every 30 seconds
        setInterval(trySpawnLoot, 120000); // Try spawn loot every 2 minutes
        if (window.debugLog) window.debugLog('⏱️ Update loops started (AutoLog: 1s, Stats: 30s, Loot: 2m)');
        
        // AGGRESSIVE: Periodically try to unlock audio on iOS (every 3 seconds for first 30 seconds)
        let unlockAttempts = 0;
        const unlockInterval = setInterval(() => {
            unlockAttempts++;
            if (unlockAttempts > 10) {
                clearInterval(unlockInterval); // Stop after 30 seconds (10 attempts × 3s)
                return;
            }
            if (window.soundManager) {
                window.soundManager.performUnlock();
            }
        }, 3000);
    } catch (error) {
        console.error('App initialization error:', error);
        localStorage.removeItem('claim_token');
        showLoginModal();
    }
}

// Map Initialization
function initMap() {
    // Check if map is already initialized
    if (map) {
        console.log('Map already initialized, skipping initMap()');
        if (window.debugLog) window.debugLog('🗺️ Map already initialized');
        return;
    }
    
    // Start with default location (will be updated when GPS position arrives)
    map = L.map('map', {
        zoomControl: true,
        attributionControl: false,
        touchZoom: true,
        doubleClickZoom: true,
        scrollWheelZoom: true,
        dragging: true,
        tap: false
    }).setView([51.505, -0.09], 17);
    
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
    
    // Reload spots when map is moved or zoomed (with debouncing)
    map.on('moveend', () => {
        if (spotReloadTimeout) clearTimeout(spotReloadTimeout);
        spotReloadTimeout = setTimeout(() => {
            if (window.debugLog) window.debugLog('🗺️ Map moved - reloading spots');
            loadNearbySpots();
        }, 500); // Wait 500ms after movement stops
    });
    
    map.on('zoomend', () => {
        if (spotReloadTimeout) clearTimeout(spotReloadTimeout);
        spotReloadTimeout = setTimeout(() => {
            if (window.debugLog) window.debugLog('🔍 Zoom changed - reloading spots');
            loadNearbySpots();
        }, 500); // Wait 500ms after zoom stops
    });
}

// Handle map click for spot creation
let spotCreationMode = false;

function handleMapClick(e) {
    // Auto-unlock on map tap
    if (window.soundManager) {
        window.soundManager.performUnlock();
    }
    
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
        if (window.debugLog) window.debugLog('❌ GPS: Geolocation not supported');
        showNotification('GPS Error', 'Geolocation not supported', 'error');
        return;
    }
    
    if (window.debugLog) window.debugLog('📍 GPS: Starting tracking');
    
    // Get initial position and center map
    // Use longer timeout for initial request (may need time to get first fix)
    navigator.geolocation.getCurrentPosition(
        (position) => {
            map.setView([position.coords.latitude, position.coords.longitude], 17);
            if (window.debugLog) window.debugLog(`📍 GPS: Initial fix - ${position.coords.latitude.toFixed(4)}, ${position.coords.longitude.toFixed(4)}`);
            console.log('Initial GPS position acquired');
        },
        (error) => {
            console.warn('Initial GPS error (code: ' + error.code + '):', error.message);
            if (window.debugLog) window.debugLog(`⚠️ GPS: Initial error (code ${error.code})`);
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
            
            // Update last GPS update timestamp
            lastGPSUpdateTime = Date.now();
            
            updatePlayerPosition();
            
            // Reload spots if player moved significantly (every 100 meters) AND in follow mode
            // (When not in follow mode, map movement triggers reload already)
            if (followMode && (!lastSpotReloadPosition || 
                map.distance(
                    [lastSpotReloadPosition.lat, lastSpotReloadPosition.lng],
                    [currentPosition.lat, currentPosition.lng]
                ) > 100)) {
                if (window.debugLog) window.debugLog('📍 Player moved significantly in follow mode - reloading spots');
                lastSpotReloadPosition = { lat: currentPosition.lat, lng: currentPosition.lng };
                loadNearbySpots();
            }
            
            if (followMode) {
                // Smooth pan instead of instant setView
                map.panTo([currentPosition.lat, currentPosition.lng], {
                    animate: true,
                    duration: 0.5, // 500ms smooth animation
                    easeLinearity: 0.25
                });
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
        // Smooth animation to new position
        playerMarker.setLatLng([currentPosition.lat, currentPosition.lng]);
        
        // Update rotation if compass is enabled
        if (compassEnabled && currentPosition.heading !== null) {
            const icon = playerMarker.getElement();
            if (icon) {
                const arrowDiv = icon.querySelector('div');
                if (arrowDiv) {
                    arrowDiv.style.transition = 'transform 0.3s ease-out';
                    arrowDiv.style.transform = `rotate(${currentPosition.heading}deg)`;
                }
            }
        }
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
            // Simple circle without arrow (compass not enabled)
            arrowSvg = `
                <svg width="28" height="28" viewBox="0 0 28 28" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="14" cy="14" r="12" fill="#667eea" stroke="white" stroke-width="1.5"/>
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
    
    if (window.debugLog) window.debugLog('🌐 WebSocket: Connecting...');
    
    ws = new WebSocket(`${WS_BASE}?token=${authToken}`);
    
    ws.onopen = () => {
        if (window.debugLog) window.debugLog('✅ WebSocket: Connected');
        console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
    };
    
    ws.onerror = (error) => {
        if (window.debugLog) window.debugLog('❌ WebSocket: Error');
        console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
        if (window.debugLog) window.debugLog('❌ WebSocket: Closed, reconnecting in 5s...');
        console.log('WebSocket closed, reconnecting...');
        setTimeout(connectWebSocket, 5000);
    };
}

function handleWebSocketMessage(message) {
    const { event_type, data } = message;
    if (window.debugLog) window.debugLog(`📨 WS: ${event_type}`);
    
    switch (event_type) {
        case 'connected':
            if (window.debugLog) window.debugLog(`✅ WS connected`);
            console.log('Connected:', data.message);
            break;
            
        case 'position_update':
            if (window.debugLog) window.debugLog(`👥 Player pos update`);
            updateOtherPlayerPosition(data);
            break;
            
        case 'log_event':
            if (window.debugLog) window.debugLog(`📝 Log: +${data.xp_gained}XP`);
            showLogNotification(data);
            break;
            
        case 'loot_spawn':
            if (window.debugLog) window.debugLog(`💎 Loot spawned: ${data.xp} XP available ${data.item_name ? '+ ' + data.item_name : ''}`);
            soundManager.playSound('collect');
            showNotification('💎 Loot Spawned!', `New loot nearby! (${data.xp} XP available)`, 'success');
            // Reload spots to show new loot
            loadNearbySpots();
            break;
            
        case 'claim_update':
            if (window.debugLog) window.debugLog(`🚩 Claim update`);
            updateClaimHeatmap();
            // Aktualisiere Heatmap wenn sichtbar
            if (heatmapVisible) {
                loadHeatmap();
            }
            break;
            
        case 'tracking_update':
            if (window.debugLog) window.debugLog(`📍 Tracking update`);
            console.log('Tracking update:', data);
            break;
    }
}

function updateOtherPlayerPosition(data) {
    const { user_id, username, latitude, longitude } = data;
    
    // Validate coordinates
    if (!latitude || !longitude || 
        isNaN(latitude) || isNaN(longitude) ||
        latitude < -90 || latitude > 90 ||
        longitude < -180 || longitude > 180) {
        console.error('Invalid player position:', data);
        return;
    }
    
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
        
        // Only log non-429 errors to console (rate limiting is expected and silent)
        if (response.status !== 429) {
            console.error(`API Error (${response.status}):`, errorDetail);
        }
        
        throw error;
    }
    
    return response.json();
}

// Data Loading
async function loadStats() {
    try {
        if (window.debugLog) window.debugLog('📊 Loading stats...');
        const stats = await apiRequest('/items/stats');
        
        // Check for level-up
        if (stats.level > currentLevel && currentLevel > 0) {
            if (window.debugLog) window.debugLog(`⬆️ LEVEL UP: ${currentLevel} → ${stats.level}`);
            // Only play sound if this is a real level-up (not on initial load)
            soundManager.playSound('levelup');
            showNotification('🎉 LEVEL UP!', `Du bist jetzt Level ${stats.level}!`, 'levelup');
            currentLevel = stats.level;
        } else {
            // First load - just set level without sound
            currentLevel = stats.level;
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
        
        if (window.debugLog) window.debugLog(`✅ Stats: L${stats.level} | ${stats.total_claim_points}pts | ${stats.total_logs}logs`);
    } catch (error) {
        if (window.debugLog) window.debugLog(`❌ Stats failed: ${error.message}`);
        console.error('Failed to load stats:', error);
    }
}

// Create dynamic popup content for spots with detailed info
function createSpotPopupContent(spot) {
    const container = document.createElement('div');
    container.style.minWidth = '200px';
    
    // Special handling for loot spots
    if (spot.is_loot) {
        container.innerHTML = `
            <div style="padding: 5px;">
                <b style="font-size: 14px; color: gold;">💎 ${spot.name}</b><br>
                ${spot.description ? `<small>${spot.description}</small><br>` : ''}
                <div style="font-size: 12px; margin: 8px 0;">
                    <strong>Belohnung:</strong> ${spot.loot_xp || 0} XP
                    ${spot.loot_item ? '<br>+ Item 🎁' : ''}
                </div>
                <button onclick="collectLoot(${spot.id})" 
                    style="width: 100%; padding: 8px; background: gold; color: black; 
                    border: none; border-radius: 4px; font-weight: bold; cursor: pointer;">
                    Einsammeln
                </button>
            </div>
        `;
        return container;
    }
    
    // Normal spot popup
    container.innerHTML = `
        <div style="padding: 5px;">
            <b style="font-size: 14px;">${spot.name}</b><br>
            ${spot.description ? `<small>${spot.description}</small><br>` : ''}
            <div id="spot-details-${spot.id}" style="font-size: 11px; margin: 5px 0;">Lädt...</div>
            <div style="margin-top: 5px; display: flex; gap: 5px;">
                <button onclick="logSpot(${spot.id})" style="flex: 1; padding: 5px 10px; font-size: 12px;">Log Spot</button>
                <button onclick="showSpotLogs(${spot.id})" style="flex: 1; padding: 5px 10px; font-size: 12px;">Logs</button>
            </div>
        </div>
    `;
    
    // Load details async
    loadSpotDetails(spot.id, container);
    return container;
}

// Load and display detailed spot info
async function loadSpotDetails(spotId, container) {
    try {
        const details = await apiRequest(
            `/spots/${spotId}/details?latitude=${currentPosition.lat}&longitude=${currentPosition.lng}`
        );
        
        const detailsDiv = document.getElementById(`spot-details-${spotId}`);
        if (!detailsDiv) return;
        
        // Format cooldown - show both auto and manual status
        let logStatusText = '';
        
        if (details.can_manual_log) {
            logStatusText += '✅ Manuelles Log: Bereit<br>';
        } else {
            const manMinutes = Math.floor(details.manual_cooldown_remaining / 60);
            const manSeconds = details.manual_cooldown_remaining % 60;
            logStatusText += `⏱️ Manuelles Log: ${manMinutes}m ${manSeconds}s<br>`;
        }
        
        if (details.can_auto_log) {
            logStatusText += '✅ Auto Log: Bereit';
        } else {
            const minutes = Math.floor(details.auto_cooldown_remaining / 60);
            const seconds = details.auto_cooldown_remaining % 60;
            logStatusText += `⏱️ Auto Log: ${minutes}m ${seconds}s`;
        }
        
        // Format distance
        const distanceText = details.distance_meters < 1000
            ? `${Math.round(details.distance_meters)}m`
            : `${(details.distance_meters / 1000).toFixed(1)}km`;
        
        // Format dominance
        let dominanceText = 'Noch nicht geclaimed';
        if (details.top_claimers.length > 0) {
            dominanceText = details.top_claimers
                .map((c, i) => `${i+1}. ${c.username} (${Math.round(c.claim_value)}pts)`)
                .join('<br>');
        }
        
        detailsDiv.innerHTML = `
            <strong>Entfernung:</strong> ${distanceText}<br>
            <strong>Status:</strong><br>
            <small style="display: block; margin-left: 10px; line-height: 1.6;">${logStatusText}</small>
            <strong style="display: block; margin-top: 5px;">Meine Punkte:</strong> ${Math.round(details.my_claim_value)}<br>
            <strong style="display: block; margin-top: 5px;">Top Claimer:</strong>
            <small>${dominanceText}</small>
        `;
    } catch (error) {
        const detailsDiv = document.getElementById(`spot-details-${spotId}`);
        if (detailsDiv) {
            detailsDiv.innerHTML = 'Fehler beim Laden der Details';
        }
    }
}

async function loadNearbySpots() {
    if (!map) {
        if (window.debugLog) window.debugLog('⏳ Spots: Waiting for map initialization...');
        return;
    }
    
    try {
        // Use map center instead of GPS position to show spots in visible area
        const center = map.getCenter();
        const lat = center.lat;
        const lng = center.lng;
        
        // Calculate radius based on zoom level (visible area)
        // At zoom 17: ~300m, zoom 15: ~1000m, zoom 13: ~5000m
        const zoom = map.getZoom();
        const radius = Math.min(5000, Math.max(300, Math.pow(2, 18 - zoom) * 100));
        
        if (window.debugLog) window.debugLog(`🗺️ Loading spots around map center (${lat.toFixed(6)}, ${lng.toFixed(6)}) with radius ${radius.toFixed(0)}m (zoom: ${zoom})...`);
        
        const spots = await apiRequest(
            `/spots/nearby?latitude=${lat}&longitude=${lng}&radius=${radius}`
        );
        
        if (window.debugLog) window.debugLog(`📦 API returned ${spots.length} spots`);
        
        // Clear existing markers
        spotMarkers.forEach(marker => marker.remove());
        spotMarkers.clear();
        
        // Count loot spots for debugging
        let lootCount = 0;
        
        // Add new markers
        spots.forEach(spot => {
            // Validate coordinates before creating marker
            if (!spot.latitude || !spot.longitude || 
                isNaN(spot.latitude) || isNaN(spot.longitude) ||
                spot.latitude < -90 || spot.latitude > 90 ||
                spot.longitude < -180 || spot.longitude > 180) {
                if (window.debugLog) window.debugLog(`⚠️ Invalid coordinates for spot ${spot.id}: lat=${spot.latitude}, lng=${spot.longitude}`);
                return; // Skip this spot
            }
            
            if (spot.is_loot) lootCount++;
            
            const marker = L.marker([spot.latitude, spot.longitude], {
                icon: L.divIcon({
                    className: spot.is_loot ? 'loot-marker' : 'spot-marker',
                    iconSize: [15, 15],
                    iconAnchor: [7, 7],  // Center the icon on the coordinate (half of iconSize)
                    popupAnchor: [0, -7]  // Position popup above the icon
                })
            }).addTo(map);
            
            // Bind popup with click handler to load details dynamically
            marker.bindPopup(() => {
                return createSpotPopupContent(spot);
            }, {
                autoPan: true,
                autoPanPadding: [50, 50],
                maxWidth: 250,
                autoClose: false,
                closeOnClick: false
            });
            
            spotMarkers.set(spot.id, marker);
        });
        
        if (window.debugLog) {
            if (spots.length > 0) {
                window.debugLog(`✅ Spots: ${spots.length} spots loaded (${lootCount} loot spots)`);
            } else {
                window.debugLog('⚠️ No spots in range (5000m radius)');
            }
        }
    } catch (error) {
        if (window.debugLog) window.debugLog(`❌ Failed to load spots: ${error.message}`);
        console.error('Failed to load spots:', error);
    }
}

// Auto-logging
async function updateAutoLog() {
    if (!currentPosition) return;
    
    const now = Date.now();
    
    spotMarkers.forEach((marker, spotId) => {
        // Skip if already logging this spot
        if (spotsBeingLogged.has(spotId)) {
            return;
        }
        
        // Skip if logged this spot recently (within 60 seconds)
        const lastLog = lastAutoLogTime.get(spotId);
        if (lastLog && now - lastLog < 60000) {
            return;
        }
        
        const spotPos = marker.getLatLng();
        const distance = map.distance(
            [currentPosition.lat, currentPosition.lng],
            [spotPos.lat, spotPos.lng]
        );
        
        // Auto-log at 20m
        if (distance <= 20) {
            if (window.debugLog) window.debugLog(`🎯 AutoLog triggered for spot ${spotId}: ${distance.toFixed(1)}m`);
            performAutoLog(spotId);
        }
    });
}

// Silent 429-aware wrapper for auto-logging requests
async function apiRequestSilent429(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    // Use raw fetch with silent error handling to prevent browser console spam
    const response = await fetch(url, {
        ...options,
        headers
    }).catch(err => {
        // Network errors - return dummy 429 to silence console
        return { ok: false, status: 429 };
    });
    
    if (!response.ok && response.status === 429) {
        // Return silently for 429
        return { status: 429 };
    }
    
    if (!response.ok) {
        // For other errors, use normal apiRequest error handling
        throw new Error(`API Error: ${response.statusText}`);
    }
    
    return response.json();
}

async function performAutoLog(spotId) {
    // Mark spot as being logged
    spotsBeingLogged.add(spotId);
    
    try {
        // Check if we're still in cooldown from server
        const now = Date.now();
        if (now < autoLogCooldownUntil) {
            // Skip request during cooldown to prevent console spam
            if (window.debugLog) window.debugLog(`⏳ AutoLog cooldown active for ${Math.round((autoLogCooldownUntil - now) / 1000)}s`);
            return;
        }
        
        if (window.debugLog) window.debugLog(`📤 AutoLog POST: spot ${spotId}`);
        
        const response = await apiRequestSilent429('/logs/', {
            method: 'POST',
            body: JSON.stringify({
                spot_id: spotId,
                latitude: currentPosition.lat,
                longitude: currentPosition.lng,
                is_auto: true
            })
        });
        
        // Check if we got rate limited (429)
        if (response.status === 429) {
            // Set cooldown for 5 minutes to prevent repeated requests
            autoLogCooldownUntil = now + (5 * 60 * 1000);
            if (window.debugLog) window.debugLog(`⚠️ Rate limited (429) - cooldown 5m`);
            return;
        }
        
        if (window.debugLog) window.debugLog(`✅ AutoLog success: +${response.xp_gained}XP, +${response.claim_points}Claims`);
        
        // Record successful log time
        lastAutoLogTime.set(spotId, now);
        
        soundManager.playSound('log');
        showNotification(
            'Auto Log!',
            `+${response.xp_gained} XP, +${response.claim_points} Claims`,
            'log-event'
        );
        
        loadStats();
        
        // Update heatmap after autolog
        updateClaimHeatmap();
    } finally {
        // Always remove from being logged set
        spotsBeingLogged.delete(spotId);
    }
}

window.logSpot = async function(spotId) {
    if (!currentPosition) return;
    
    // Close the popup first
    map.closePopup();
    
    // Show log dialog
    showLogDialog(spotId);
};

function showLogDialog(spotId) {
    // Create modal dialog
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    `;
    
    const dialog = document.createElement('div');
    dialog.style.cssText = `
        background: white;
        border-radius: 10px;
        padding: 20px;
        max-width: 400px;
        width: 90%;
        max-height: 80vh;
        overflow-y: auto;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    `;
    
    dialog.innerHTML = `
        <h2 style="margin-top: 0; color: #333;">Log Spot</h2>
        
        <div style="margin: 15px 0;">
            <label for="log-notes" style="display: block; margin-bottom: 5px; font-weight: bold;">Notes (optional):</label>
            <textarea id="log-notes" placeholder="Add notes about this spot..." 
                style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; 
                       font-family: Arial; min-height: 80px; box-sizing: border-box;"></textarea>
        </div>
        
        <div style="margin: 15px 0;">
            <label for="log-photo" style="display: block; margin-bottom: 5px; font-weight: bold;">Foto (optional):</label>
            <input type="file" id="log-photo" accept="image/*" 
                style="display: block; width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 5px;">
            <small style="color: #666; display: block; margin-top: 5px;">Max 5 MB</small>
        </div>
        
        <div style="margin-top: 20px; display: flex; gap: 10px;">
            <button id="log-cancel" style="flex: 1; padding: 10px; background: #ddd; border: none; border-radius: 5px; cursor: pointer;">Abbrechen</button>
            <button id="log-submit" style="flex: 1; padding: 10px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">Log Spot</button>
        </div>
    `;
    
    modal.appendChild(dialog);
    document.body.appendChild(modal);
    
    // Event handlers
    document.getElementById('log-cancel').onclick = () => {
        modal.remove();
    };
    
    document.getElementById('log-submit').onclick = async () => {
        const notes = document.getElementById('log-notes').value;
        const photoFile = document.getElementById('log-photo').files[0];
        
        // Disable button while uploading
        const submitBtn = document.getElementById('log-submit');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Lädt...';
        
        try {
            await submitLog(spotId, notes, photoFile);
            modal.remove();
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Log Spot';
        }
    };
    
    // Close on background click
    modal.onclick = (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    };
}

async function submitLog(spotId, notes, photoFile) {
    if (!currentPosition) return;
    
    try {
        let photoData = null;
        let photoMime = null;
        
        // Process photo if provided
        if (photoFile) {
            if (photoFile.size > 5 * 1024 * 1024) {
                showNotification('Fehler', 'Foto ist zu groß (max 5 MB)', 'error');
                return;
            }
            const uploadResult = await uploadPhoto(photoFile);
            photoData = uploadResult.photo_data;
            photoMime = uploadResult.mime_type;
        }
        
        // Send log with binary photo data
        const log = await apiRequest('/logs/', {
            method: 'POST',
            body: JSON.stringify({
                spot_id: spotId,
                latitude: currentPosition.lat,
                longitude: currentPosition.lng,
                is_auto: false,
                notes: notes || null,
                photo_data: photoData,
                photo_mime: photoMime
            })
        });
        
        soundManager.playSound('log');
        showNotification(
            'Logged!',
            `+${log.xp_gained} XP, +${log.claim_points} Claims`,
            'log-event'
        );
        
        loadStats();
        
        // Update heatmap after manual log
        updateClaimHeatmap();
    } catch (error) {
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
}

async function uploadPhoto(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE}/logs/upload`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`
        },
        body: formData
    });
    
    if (!response.ok) {
        throw new Error('Photo upload failed');
    }
    
    const data = await response.json();
    return { photo_data: data.photo_data, mime_type: data.mime_type };
}

// Loot Functions
window.collectLoot = async function(lootSpotId) {
    if (!currentPosition) return;
    
    map.closePopup();
    
    try {
        const result = await apiRequest('/loot/collect', {
            method: 'POST',
            body: JSON.stringify({
                loot_spot_id: lootSpotId,
                latitude: currentPosition.lat,
                longitude: currentPosition.lng
            })
        });
        
        if (result.success) {
            soundManager.playSound('collect');
            
            // Remove marker immediately from map
            const marker = spotMarkers.get(lootSpotId);
            if (marker) {
                map.removeLayer(marker);
                spotMarkers.delete(lootSpotId);
            }
            
            // Show rewards notification
            let message = `+${result.rewards.xp} XP`;
            if (result.rewards.items && result.rewards.items.length > 0) {
                result.rewards.items.forEach(item => {
                    message += `\n🎁 ${item.name}`;
                });
            }
            
            if (result.level_up) {
                message += `\n🎉 Level Up! Jetzt Level ${result.new_level}`;
                soundManager.playSound('levelup');
            }
            
            showNotification('💎 Loot Collected!', message, 'success');
            
            // Update stats
            loadStats();
            
            // Reload spots to remove collected loot
            await loadNearbySpots();
            
            // Try to spawn new loot
            await trySpawnLoot();
        }
    } catch (error) {
        showNotification('Error', error.message || 'Failed to collect loot', 'error');
    }
};

async function trySpawnLoot() {
    if (!currentPosition) {
        if (window.debugLog) window.debugLog('⏳ Loot: Waiting for GPS position...');
        return;
    }
    
    try {
        if (window.debugLog) window.debugLog(`💎 Trying to spawn loot at (${currentPosition.lat.toFixed(6)}, ${currentPosition.lng.toFixed(6)})...`);
        
        const spots = await apiRequest('/loot/spawn', {
            method: 'POST',
            body: JSON.stringify({
                latitude: currentPosition.lat,
                longitude: currentPosition.lng,
                radius_meters: 500
            })
        });
        
        if (spots && spots.length > 0) {
            if (window.debugLog) window.debugLog(`✅ Spawned ${spots.length} loot spot(s)`);
            await loadNearbySpots();
        } else {
            if (window.debugLog) window.debugLog('ℹ️ No loot spawned (max limit reached or cooldown active)');
        }
    } catch (error) {
        // Silently fail - loot spawning is not critical
        if (window.debugLog) window.debugLog(`❌ Loot spawn error: ${error.message}`);
        console.error('Loot spawn failed:', error);
    }
}

async function loadActiveLoot() {
    try {
        const lootSpots = await apiRequest('/loot/active');
        if (window.debugLog && lootSpots.length > 0) {
            window.debugLog(`💎 Active loot: ${lootSpots.length} spot(s)`);
        }
        return lootSpots;
    } catch (error) {
        console.error('Failed to load active loot:', error);
        return [];
    }
}

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
    
    // Check if GPS updates are recent (within last 10 seconds)
    const now = Date.now();
    const timeSinceLastUpdate = now - (lastGPSUpdateTime || 0);
    
    if (timeSinceLastUpdate > 10000) {
        // GPS updates paused (probably screen off or no signal)
        if (window.debugLog) window.debugLog('⏸️ Track recording paused - no recent GPS updates');
        return;
    }
    
    // Check if this point is too far from last point (indicates GPS jump/gap)
    if (activeTrackPoints.length > 0) {
        const lastPoint = activeTrackPoints[activeTrackPoints.length - 1];
        const distance = map.distance(lastPoint, [position.lat, position.lng]);
        
        // If distance is more than 500m, it's probably a GPS gap/jump
        if (distance > 500) {
            if (window.debugLog) window.debugLog(`⚠️ Track point skipped - jump detected (${distance.toFixed(0)}m)`);
            return;
        }
    }
    
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
            // Recreate marker immediately with current position and heading
            updatePlayerPosition();
        }
    } else {
        btn.classList.remove('active');
        // Recreate marker for non-compass mode (simple circle without arrow)
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
        
        // Starte Auto-Refresh der Heatmap (alle 30 Sekunden)
        if (heatmapUpdateInterval) {
            clearInterval(heatmapUpdateInterval);
        }
        heatmapUpdateInterval = setInterval(async () => {
            if (heatmapVisible) {
                await loadHeatmap();
                if (window.debugLog) window.debugLog('🔥 Heatmap aktualisiert');
            }
        }, 30000); // 30 Sekunden
    } else {
        // Remove all heatmap layers from map
        heatmapLayers.forEach((layer, userId) => {
            if (map.hasLayer(layer)) {
                map.removeLayer(layer);
            }
        });
        
        // Stoppe Auto-Refresh
        if (heatmapUpdateInterval) {
            clearInterval(heatmapUpdateInterval);
            heatmapUpdateInterval = null;
        }
    }
}

async function loadHeatmap() {
    try {
        const heatmaps = await apiRequest('/claims/heatmap/all?limit=10');
        
        // Clear old heatmap layers
        heatmapLayers.forEach((layer, userId) => {
            if (map.hasLayer(layer)) {
                map.removeLayer(layer);
            }
        });
        heatmapLayers.clear();
        
        if (heatmaps && heatmaps.length > 0) {
            heatmaps.forEach((heatmap, index) => {
                if (heatmap.points && heatmap.points.length > 0) {
                    const points = heatmap.points.map(p => [p.latitude, p.longitude, p.intensity]);
                    
                    // Get color for this heatmap (cycle through palette)
                    const colorIndex = index % HEATMAP_COLORS.length;
                    const colorConfig = HEATMAP_COLORS[colorIndex];
                    
                    // Create heatmap with specific color gradient
                    const heat = L.heatLayer(points, {
                        radius: 25,
                        blur: 35,
                        maxZoom: 17,
                        minOpacity: 0.4,
                        gradient: colorConfig.gradient
                    });
                    
                    // Store layer and always add to map if heatmap is visible
                    const userId = heatmap.user_id || `user_${index}`;
                    heatmapLayers.set(userId, heat);
                    
                    // Always show all heatmaps when heatmap layer is active
                    if (heatmapVisible) {
                        heat.addTo(map);
                    }
                }
            });
        }
        
        if (window.debugLog) window.debugLog(`🔥 Heatmap updated: ${heatmapLayers.size} players`);
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
                Heatmap 🔥 (alle Spieler)
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
            if (!heatmapVisible) {
                toggleHeatmap();
            }
        } else {
            if (heatmapVisible) {
                toggleHeatmap();
            }
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
    // Validate coordinates
    if (!data.latitude || !data.longitude || 
        isNaN(data.latitude) || isNaN(data.longitude) ||
        data.latitude < -90 || data.latitude > 90 ||
        data.longitude < -180 || data.longitude > 180) {
        console.error('Invalid loot spawn coordinates:', data);
        return;
    }
    
    const marker = L.marker([data.latitude, data.longitude], {
        icon: L.divIcon({
            className: 'loot-marker',
            iconSize: [20, 20]
        })
    }).addTo(map);
    
    marker.bindPopup(`
        <b>Loot Spot!</b><br>
        ${data.xp} XP available<br>
        ${data.item_name ? `Item: ${data.item_name}` : ''}<br>
        <button onclick="logSpot(${data.spot_id})">Collect</button>
    `);
    
    soundManager.playSound('loot');
    showNotification('Loot Spawned!', `${data.xp} XP available nearby`, 'loot-event');
    
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
    if (document.visibilityState === 'hidden') {
        if (window.debugLog) window.debugLog('🌙 Display off - GPS updates may pause');
    } else {
        if (window.debugLog) window.debugLog('☀️ Display on - GPS updates resumed');
    }
    
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
            const startedStr = new Date(track.started_at).toLocaleString('de-DE');
            const endedStr = track.ended_at ? new Date(track.ended_at).toLocaleString('de-DE') : 'Aktiv';
            
            polyline.bindPopup(`
                <strong>${track.name}</strong><br>
                Gestartet: ${startedStr}<br>
                ${track.ended_at ? 'Beendet: ' + endedStr : 'Status: Aktiv'}
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
    if (!settingsModal) return;
    settingsModal.classList.remove('hidden');
    
    // Update current settings in UI
    const soundToggle = document.getElementById('setting-sound-toggle');
    const volumeSlider = document.getElementById('setting-volume-slider');
    const volumeValue = document.getElementById('volume-value');
    
    if (soundToggle) soundToggle.checked = soundManager.soundsEnabled;
    if (volumeSlider) volumeSlider.value = soundManager.volume * 100;
    if (volumeValue) volumeValue.textContent = Math.round(soundManager.volume * 100) + '%';
}

function closeSettings() {
    const settingsModal = document.getElementById('settings-modal');
    if (settingsModal) settingsModal.classList.add('hidden');
}

// Inventory Functions
async function showInventory() {
    const inventoryModal = document.getElementById('inventory-modal');
    if (!inventoryModal) return;
    inventoryModal.classList.remove('hidden');
    
    const inventoryList = document.getElementById('inventory-list');
    if (!inventoryList) return;
    
    inventoryList.innerHTML = '<p style="text-align: center; color: #666;">Loading...</p>';
    
    try {
        const inventory = await apiRequest('/items/inventory');
        
        if (!inventory || inventory.length === 0) {
            inventoryList.innerHTML = '<p style="text-align: center; color: #666;">Dein Inventar ist leer.</p>';
            return;
        }
        
        // Group items by rarity
        const rarityColors = {
            common: '#9ca3af',
            rare: '#3b82f6',
            epic: '#a855f7',
            legendary: '#f59e0b'
        };
        
        inventoryList.innerHTML = inventory.map(inv => {
            const item = inv.item;
            const color = rarityColors[item.rarity] || '#666';
            
            return `
                <div style="
                    border: 2px solid ${color};
                    border-radius: 8px;
                    padding: 12px;
                    margin-bottom: 10px;
                    background: linear-gradient(135deg, white 0%, ${color}20 100%);
                ">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="flex: 1;">
                            <div style="font-weight: bold; font-size: 16px; color: ${color};">
                                ${item.icon_url || '📦'} ${item.name}
                            </div>
                            <div style="font-size: 12px; color: #666; margin-top: 4px; text-transform: uppercase;">
                                ${item.rarity}
                            </div>
                            <div style="font-size: 13px; margin-top: 8px; color: #444;">
                                ${item.description}
                            </div>
                            ${item.xp_boost || item.claim_boost || item.range_boost ? `
                                <div style="font-size: 12px; margin-top: 8px; color: #666;">
                                    ${item.xp_boost ? `✨ XP +${Math.round(item.xp_boost * 100)}%<br>` : ''}
                                    ${item.claim_boost ? `💎 Claim +${Math.round(item.claim_boost * 100)}%<br>` : ''}
                                    ${item.range_boost ? `📡 Range +${item.range_boost}m` : ''}
                                </div>
                            ` : ''}
                        </div>
                        <div style="text-align: right; margin-left: 10px;">
                            <div style="font-size: 20px; font-weight: bold; color: ${color};">
                                x${inv.quantity}
                            </div>
                            ${item.item_type === 'consumable' ? `
                                <button onclick="useInventoryItem(${item.id})" 
                                    style="
                                        margin-top: 8px;
                                        padding: 6px 12px;
                                        background: ${color};
                                        color: white;
                                        border: none;
                                        border-radius: 4px;
                                        cursor: pointer;
                                        font-size: 12px;
                                        font-weight: bold;
                                    ">
                                    Use
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        inventoryList.innerHTML = '<p style="text-align: center; color: red;">Fehler beim Laden des Inventars.</p>';
        console.error('Failed to load inventory:', error);
    }
}

function closeInventory() {
    const inventoryModal = document.getElementById('inventory-modal');
    if (inventoryModal) inventoryModal.classList.add('hidden');
}

window.useInventoryItem = async function(itemId) {
    try {
        const result = await apiRequest(`/items/${itemId}/use`, {
            method: 'POST'
        });
        
        if (result.success) {
            soundManager.playSound('collect');
            
            let message = `Used ${result.item_name}`;
            if (result.effects) {
                if (result.effects.xp_boost) message += `\n✨ XP +${Math.round(result.effects.xp_boost * 100)}%`;
                if (result.effects.claim_boost) message += `\n💎 Claim +${Math.round(result.effects.claim_boost * 100)}%`;
                if (result.effects.range_boost) message += `\n📡 Range +${result.effects.range_boost}m`;
            }
            
            showNotification('Item Used', message, 'success');
            
            // Refresh inventory
            await showInventory();
            loadStats();
        }
    } catch (error) {
        showNotification('Error', error.message || 'Failed to use item', 'error');
    }
};

function toggleSound() {
    const enabled = soundManager.toggle();
    soundManager.playSound('log'); // Play sound to confirm
    showNotification('Sound', enabled ? '🔊 Aktiviert' : '🔇 Deaktiviert', 'info');
}

function changeVolume() {
    const slider = document.getElementById('setting-volume-slider');
    const volumeValue = document.getElementById('volume-value');
    if (!slider || !volumeValue) return;
    const volume = slider.value / 100;
    soundManager.setVolume(volume);
    volumeValue.textContent = slider.value + '%';
}

// Show all logs for a spot with photos
window.showSpotLogs = async function(spotId) {
    try {
        const logs = await apiRequest(`/logs/spot/${spotId}`);
        
        // Close the spot popup
        map.closePopup();
        
        // Create modal dialog
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            overflow: auto;
        `;
        
        const dialog = document.createElement('div');
        dialog.style.cssText = `
            background: white;
            border-radius: 10px;
            padding: 20px;
            max-width: 500px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            margin: auto;
        `;
        
        if (logs.length === 0) {
            dialog.innerHTML = `
                <h2 style="margin-top: 0; color: #333;">Logs für diesen Spot</h2>
                <p style="color: #666;">Noch keine Logs vorhanden</p>
                <button id="logs-close" style="margin-top: 10px; padding: 10px 20px; background: #007AFF; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%;">Schließen</button>
            `;
        } else {
            let logsHtml = `<h2 style="margin-top: 0; color: #333;">Logs für diesen Spot (${logs.length})</h2>`;
            
            logs.forEach((log, index) => {
                // Format CET timestamp (backend already provides CET)
                const date = new Date(log.timestamp).toLocaleString('de-DE');
                const username = log.username || 'Unknown';
                
                // Auto-Logs anzeigen: kompakt ohne Details
                if (log.is_auto) {
                    logsHtml += `
                        <div style="border-left: 3px solid #FFB800; padding: 6px 10px; margin: 5px 0; background: #FFF9E6; font-size: 12px;">
                            <span style="background: #FFB800; color: white; padding: 1px 4px; border-radius: 2px; font-weight: bold; font-size: 10px;">AUTO</span>
                            <small style="color: #666; margin-left: 5px;">${date}</small>
                            <small style="display: block; color: #888; margin-top: 2px;">+${log.xp_gained} XP, +${log.claim_points} Claims</small>
                        </div>
                    `;
                } else {
                    // Manuelle Logs anzeigen: mit Details, Foto, Notizen
                    logsHtml += `
                        <div style="border: 1px solid #ddd; padding: 10px; margin: 10px 0; border-radius: 5px; background: #fff;">
                            <strong>${username}</strong> - <small style="color: #666;">${date}</small><br>
                            <small style="color: #888;">+${log.xp_gained} XP, +${log.claim_points} Claims</small>
                    `;
                    
                    if (log.notes) {
                        logsHtml += `<br><em style="color: #555;">📝 ${log.notes}</em>`;
                    }
                    
                    if (log.has_photo) {
                        logsHtml += `
                            <div style="margin-top: 8px; text-align: center;">
                                <img id="log-photo-${log.id}" 
                                     data-log-id="${log.id}"
                                     style="max-width: 100%; max-height: 150px; border-radius: 5px; cursor: pointer; object-fit: cover;"
                                     onclick="openPhotoModal(${log.id})">
                            </div>
                        `;
                    }
                    
                    logsHtml += `</div>`;
                }
            });
            
            logsHtml += `<button id="logs-close" style="margin-top: 10px; padding: 10px 20px; background: #007AFF; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%;">Schließen</button>`;
            dialog.innerHTML = logsHtml;
            
            // Load photo previews (nur für manuelle Logs)
            logs.forEach(log => {
                if (!log.is_auto && log.has_photo) {
                    const img = dialog.querySelector(`#log-photo-${log.id}`);
                    if (img) {
                        img.src = `/api/logs/${log.id}/photo?t=${Date.now()}`;
                    }
                }
            });
        }
        
        modal.appendChild(dialog);
        document.body.appendChild(modal);
        
        // Close button
        document.getElementById('logs-close').onclick = () => {
            modal.remove();
        };
        
        // Close on background click
        modal.onclick = (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        };
    } catch (error) {
        showNotification('Fehler', 'Logs konnten nicht geladen werden', 'error');
    }
};

// Open photo in fullscreen modal
window.openPhotoModal = function(logId) {
    const photoModal = document.createElement('div');
    photoModal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.9);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 2000;
    `;
    
    const img = document.createElement('img');
    img.src = `/api/logs/${logId}/photo?t=${Date.now()}`;
    img.style.cssText = `
        max-width: 95vw;
        max-height: 95vh;
        object-fit: contain;
    `;
    
    photoModal.appendChild(img);
    document.body.appendChild(photoModal);
    
    photoModal.onclick = () => {
        photoModal.remove();
    };
};

