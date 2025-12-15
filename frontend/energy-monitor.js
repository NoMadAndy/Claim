// Energy Monitoring Module for Claim GPS Game
// Handles battery monitoring, energy consumption tracking, and optimization

class EnergyMonitor {
    // Configuration constants
    static METRIC_THROTTLE_INTERVAL = 60000; // Milliseconds between metric recordings per type (1 minute)
    static WEBSOCKET_UPDATE_INTERVAL_SAVING = 10000; // WebSocket update interval in energy saving mode (10 seconds)
    static WEBSOCKET_UPDATE_INTERVAL_NORMAL = 3000; // WebSocket update interval in normal mode (3 seconds)
    static BATTERY_UPDATE_INTERVAL = 30000; // Battery UI update interval (30 seconds)
    static STATS_UPDATE_INTERVAL = 300000; // Energy stats update interval (5 minutes)
    
    // Detect if running on iPhone/iOS
    static isIPhone() {
        // Modern detection using userAgentData when available
        if (navigator.userAgentData) {
            return navigator.userAgentData.mobile || 
                   navigator.userAgentData.platform === 'iOS';
        }
        
        // Fallback to userAgent check (works but can be spoofed)
        // Check for iPhone/iPad/iPod
        const isIOS = /iPhone|iPad|iPod/.test(navigator.userAgent) || 
                      // Check for iPad on iOS 13+ which reports as Mac
                      (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
        return isIOS;
    }
    
    constructor() {
        this.battery = null;
        this.batterySupported = 'getBattery' in navigator;
        this.isIPhone = EnergyMonitor.isIPhone();
        this.energySettings = null;
        this.metricsQueue = [];
        this.lastMetricTime = {};
        this.updateInterval = null;
        this.statsUpdateInterval = null;
        
        // Activity counters
        this.activityCounters = {
            gps: 0,
            network: 0,
            websocket: 0,
            tracking: 0
        };
        
        // Energy saving state
        this.energySavingEnabled = false;
        this.originalSettings = {};
    }

    async init() {
        console.log('🔋 Initializing Energy Monitor...');
        
        if (this.isIPhone) {
            console.log('📱 Running on iPhone/iOS - Battery API not available due to platform limitations');
        }
        
        // Initialize Battery Status API
        if (this.batterySupported) {
            try {
                this.battery = await navigator.getBattery();
                this.setupBatteryListeners();
                console.log('✅ Battery API connected');
            } catch (error) {
                console.warn('⚠️ Battery API not available:', error);
                this.batterySupported = false;
            }
        } else {
            console.warn('⚠️ Battery API not supported in this browser (this is normal on iOS/iPhone)');
        }
        
        // Update battery UI (will show "N/A" if battery API not available)
        this.updateBatteryUI();
        
        // Load energy settings from backend
        await this.loadEnergySettings();
        
        // Setup UI handlers
        this.setupUI();
        
        // Start monitoring
        this.startMonitoring();
        
        // Check if we should auto-enable energy saving
        this.checkAutoEnableEnergySaving();
        
        // If energy tab is already open, load stats immediately
        const energyTab = document.getElementById('energy-tab');
        if (this._isElementVisible(energyTab)) {
            console.log('📊 Energy tab is already open, loading stats...');
            this.updateEnergyStats();
        }
    }

    setupBatteryListeners() {
        if (!this.battery) return;
        
        // Listen for battery level changes
        this.battery.addEventListener('levelchange', () => {
            this.updateBatteryUI();
            this.checkAutoEnableEnergySaving();
        });
        
        // Listen for charging changes
        this.battery.addEventListener('chargingchange', () => {
            this.updateBatteryUI();
            
            // Disable energy saving when charging
            if (this.battery.charging && this.energySavingEnabled) {
                console.log('🔌 Device is charging, disabling energy saving mode');
                this.toggleEnergySaving(false);
            }
        });
        
        // Update UI immediately
        this.updateBatteryUI();
    }

    updateBatteryUI() {
        if (!this.battery) {
            // Show "not available" state with iPhone-specific message
            document.getElementById('battery-level').textContent = 'N/A';
            document.getElementById('battery-fill').style.width = '0%';
            const statusMsg = this.isIPhone 
                ? 'Not available on iPhone/iOS' 
                : 'Battery info not available';
            document.getElementById('charging-status').textContent = statusMsg;
            document.getElementById('time-remaining').textContent = '';
            return;
        }
        
        const level = Math.round(this.battery.level * 100);
        const charging = this.battery.charging;
        
        // Update battery level display
        document.getElementById('battery-level').textContent = `${level}%`;
        document.getElementById('battery-fill').style.width = `${level}%`;
        
        // Change color based on level
        const batteryFill = document.getElementById('battery-fill');
        if (level > 50) {
            batteryFill.style.background = 'linear-gradient(90deg, #22c55e, #16a34a)';
        } else if (level > 20) {
            batteryFill.style.background = 'linear-gradient(90deg, #f59e0b, #d97706)';
        } else {
            batteryFill.style.background = 'linear-gradient(90deg, #ef4444, #dc2626)';
        }
        
        // Update charging status
        document.getElementById('charging-status').textContent = charging ? '⚡ Charging' : 'Not charging';
        
        // Update time remaining estimate
        this.updateTimeRemaining();
    }

    async updateTimeRemaining() {
        try {
            const response = await fetch(`${API_BASE}/energy/stats`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    level: this.battery ? this.battery.level * 100 : null,
                    charging: this.battery ? this.battery.charging : false
                })
            });
            
            if (response.ok) {
                const stats = await response.json();
                
                if (stats.estimated_time_remaining_hours && !this.battery?.charging) {
                    const hours = Math.floor(stats.estimated_time_remaining_hours);
                    const minutes = Math.round((stats.estimated_time_remaining_hours - hours) * 60);
                    document.getElementById('time-remaining').textContent = 
                        `~${hours}h ${minutes}m remaining`;
                } else if (this.battery?.charging) {
                    document.getElementById('time-remaining').textContent = 'Charging...';
                } else {
                    document.getElementById('time-remaining').textContent = 'Collecting data...';
                }
            }
        } catch (error) {
            console.error('Failed to update time remaining:', error);
            document.getElementById('time-remaining').textContent = 'N/A';
        }
    }

    async loadEnergySettings() {
        try {
            const response = await fetch(`${API_BASE}/energy/settings`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            if (response.ok) {
                this.energySettings = await response.json();
                this.applySettingsToUI();
                console.log('✅ Energy settings loaded');
            }
        } catch (error) {
            console.error('Failed to load energy settings:', error);
        }
    }

    applySettingsToUI() {
        if (!this.energySettings) return;
        
        document.getElementById('energy-saving-toggle').checked = this.energySettings.energy_saving_enabled;
        document.getElementById('auto-enable-battery').value = this.energySettings.auto_enable_at_battery;
        document.getElementById('batch-network-requests').checked = this.energySettings.batch_network_requests;
        document.getElementById('reduce-heatmap-updates').checked = this.energySettings.reduce_heatmap_updates;
        document.getElementById('reduce-tracking-accuracy').checked = this.energySettings.reduce_tracking_accuracy;
        
        // Apply energy saving if enabled
        if (this.energySettings.energy_saving_enabled) {
            this.toggleEnergySaving(true);
        }
    }

    setupUI() {
        // Hide Battery Status section on iPhone (Battery API not available)
        if (this.isIPhone || !this.batterySupported) {
            const batteryStatus = document.getElementById('battery-status');
            if (batteryStatus) {
                // Add a notice instead of hiding completely
                const notice = document.createElement('div');
                notice.className = 'ios-notice';
                notice.innerHTML = '📱 <strong>iPhone/iOS Note:</strong> Battery Status API is not available on iOS devices due to platform restrictions. Basic energy optimization features are still available below.';
                batteryStatus.parentNode.insertBefore(notice, batteryStatus);
                batteryStatus.style.display = 'none';
            }
            
            // Hide auto-enable battery level setting (requires Battery API)
            const autoEnableContainer = document.getElementById('auto-enable-battery')?.parentElement;
            if (autoEnableContainer) {
                autoEnableContainer.style.display = 'none';
            }
        }
        
        // Energy saving toggle
        document.getElementById('energy-saving-toggle')?.addEventListener('change', (e) => {
            this.toggleEnergySaving(e.target.checked);
        });
        
        // Save settings button
        document.getElementById('save-energy-settings')?.addEventListener('click', () => {
            this.saveEnergySettings();
        });
        
        // Update energy tab when it's opened
        const energyTabBtn = document.querySelector('[data-tab="energy"]');
        if (energyTabBtn) {
            energyTabBtn.addEventListener('click', () => {
                this.updateEnergyStats();
            });
        }
    }

    async toggleEnergySaving(enabled) {
        this.energySavingEnabled = enabled;
        
        if (enabled) {
            console.log('💡 Energy saving mode ENABLED');
            this.applyEnergySavingOptimizations();
        } else {
            console.log('💡 Energy saving mode DISABLED');
            this.restoreNormalMode();
        }
        
        // Update backend
        try {
            await fetch(`${API_BASE}/energy/settings`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    energy_saving_enabled: enabled
                })
            });
        } catch (error) {
            console.error('Failed to update energy saving setting:', error);
        }
    }

    applyEnergySavingOptimizations() {
        // Store original settings
        if (window.gpsWatchId) {
            this.originalSettings.gpsUpdateInterval = 1000;
        }
        
        // Reduce GPS update frequency
        if (window.gpsWatchId && navigator.geolocation) {
            navigator.geolocation.clearWatch(window.gpsWatchId);
            
            window.gpsWatchId = navigator.geolocation.watchPosition(
                window.handleLocationUpdate,
                window.handleLocationError,
                {
                    enableHighAccuracy: false, // Use lower accuracy
                    maximumAge: 10000,
                    timeout: 15000
                }
            );
            console.log('📍 GPS update frequency reduced');
        }
        
        // Reduce WebSocket update frequency
        if (window.positionUpdateInterval) {
            clearInterval(window.positionUpdateInterval);
            window.positionUpdateInterval = setInterval(() => {
                if (window.currentPosition) {
                    window.sendPositionUpdate(window.currentPosition);
                }
            }, EnergyMonitor.WEBSOCKET_UPDATE_INTERVAL_SAVING);
            console.log('🔌 WebSocket update frequency reduced');
        }
        
        // Show notification
        if (window.showNotification) {
            window.showNotification('💡 Energy saving mode enabled', 'success');
        }
    }

    restoreNormalMode() {
        // Restore GPS to normal frequency
        if (window.gpsWatchId && navigator.geolocation) {
            navigator.geolocation.clearWatch(window.gpsWatchId);
            
            window.gpsWatchId = navigator.geolocation.watchPosition(
                window.handleLocationUpdate,
                window.handleLocationError,
                {
                    enableHighAccuracy: true,
                    maximumAge: 5000,
                    timeout: 10000
                }
            );
            console.log('📍 GPS restored to normal frequency');
        }
        
        // Restore WebSocket update frequency
        if (window.positionUpdateInterval) {
            clearInterval(window.positionUpdateInterval);
            window.positionUpdateInterval = setInterval(() => {
                if (window.currentPosition) {
                    window.sendPositionUpdate(window.currentPosition);
                }
            }, EnergyMonitor.WEBSOCKET_UPDATE_INTERVAL_NORMAL);
            console.log('🔌 WebSocket restored to normal frequency');
        }
        
        // Show notification
        if (window.showNotification) {
            window.showNotification('Energy saving mode disabled', 'info');
        }
    }

    checkAutoEnableEnergySaving() {
        if (!this.battery || !this.energySettings) return;
        
        const level = this.battery.level * 100;
        const threshold = this.energySettings.auto_enable_at_battery;
        
        if (level <= threshold && !this.battery.charging && !this.energySavingEnabled) {
            console.log(`🔋 Battery at ${level}%, auto-enabling energy saving mode`);
            document.getElementById('energy-saving-toggle').checked = true;
            this.toggleEnergySaving(true);
            
            if (window.showNotification) {
                window.showNotification(
                    `⚠️ Battery low (${Math.round(level)}%), energy saving enabled`,
                    'warning'
                );
            }
        }
    }

    async saveEnergySettings() {
        const settings = {
            auto_enable_at_battery: parseFloat(document.getElementById('auto-enable-battery').value),
            batch_network_requests: document.getElementById('batch-network-requests').checked,
            reduce_heatmap_updates: document.getElementById('reduce-heatmap-updates').checked,
            reduce_tracking_accuracy: document.getElementById('reduce-tracking-accuracy').checked
        };
        
        try {
            const response = await fetch(`${API_BASE}/energy/settings`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(settings)
            });
            
            if (response.ok) {
                this.energySettings = await response.json();
                if (window.showNotification) {
                    window.showNotification('✅ Energy settings saved', 'success');
                }
            }
        } catch (error) {
            console.error('Failed to save energy settings:', error);
            if (window.showNotification) {
                window.showNotification('❌ Failed to save settings', 'error');
            }
        }
    }

    async updateEnergyStats() {
        try {
            const response = await fetch(`${API_BASE}/energy/stats`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    level: this.battery ? this.battery.level * 100 : null,
                    charging: this.battery ? this.battery.charging : false
                })
            });
            
            if (response.ok) {
                const stats = await response.json();
                console.log('📊 Energy stats received:', stats);
                this.displayEnergyStats(stats);
            } else {
                console.error('Failed to fetch energy stats:', response.status, response.statusText);
                // Display error message to user
                const consumersDiv = document.getElementById('energy-consumers');
                const suggestionsDiv = document.getElementById('optimization-suggestions');
                if (consumersDiv) {
                    consumersDiv.innerHTML = this._createErrorMessage('⚠️ Unable to load energy data. Please try again later.');
                }
                if (suggestionsDiv) {
                    suggestionsDiv.innerHTML = this._createErrorMessage('⚠️ Unable to load optimization tips. Please try again later.');
                }
            }
        } catch (error) {
            console.error('Failed to update energy stats:', error);
            // Display error message to user
            const consumersDiv = document.getElementById('energy-consumers');
            const suggestionsDiv = document.getElementById('optimization-suggestions');
            if (consumersDiv) {
                consumersDiv.innerHTML = this._createErrorMessage('⚠️ Unable to load energy data. Please check your connection.');
            }
            if (suggestionsDiv) {
                suggestionsDiv.innerHTML = this._createErrorMessage('⚠️ Unable to load optimization tips. Please check your connection.');
            }
        }
    }

    // Helper method to create error message HTML
    // Note: message should be a safe, developer-controlled string
    _createErrorMessage(message) {
        const p = document.createElement('p');
        p.style.textAlign = 'center';
        p.style.color = '#f59e0b';
        p.style.fontSize = '13px';
        p.style.padding = '8px 0';
        p.textContent = message;
        return p.outerHTML;
    }
    
    // Helper method to check if element is visible
    _isElementVisible(element) {
        if (!element) return false;
        return element.style.display !== 'none' && !element.classList.contains('hidden');
    }

    displayEnergyStats(stats) {
        console.log('📊 Displaying energy stats:', {
            top_consumers_count: stats.top_consumers?.length || 0,
            suggestions_count: stats.optimization_suggestions?.length || 0
        });
        
        // Display top consumers
        const consumersDiv = document.getElementById('energy-consumers');
        if (consumersDiv) {
            if (stats.top_consumers && stats.top_consumers.length > 0) {
                const html = stats.top_consumers.map(consumer => {
                    const icon = this.getConsumerIcon(consumer.type);
                    const percentage = Math.round(consumer.percentage);
                    return `
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 13px;">${icon} ${consumer.type}</span>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <div style="width: 80px; height: 8px; background: rgba(0,0,0,0.2); border-radius: 4px; overflow: hidden;">
                                    <div style="width: ${percentage}%; height: 100%; background: #667eea;"></div>
                                </div>
                                <span style="min-width: 35px; text-align: right; font-size: 13px;">${percentage}%</span>
                            </div>
                        </div>
                    `;
                }).join('');
                consumersDiv.innerHTML = html;
            } else {
                consumersDiv.innerHTML = '<p style="text-align: center; color: #aaa; font-size: 13px; padding: 8px 0;">🔄 Collecting energy data... Use the app to generate metrics.</p>';
            }
        }
        
        // Display optimization suggestions
        const suggestionsDiv = document.getElementById('optimization-suggestions');
        if (suggestionsDiv) {
            if (stats.optimization_suggestions && stats.optimization_suggestions.length > 0) {
                const html = stats.optimization_suggestions.map(suggestion => {
                    return `<div style="padding: 6px 8px; background: rgba(255,255,255,0.05); border-radius: 4px; margin-bottom: 6px; font-size: 12px; line-height: 1.4;">${suggestion}</div>`;
                }).join('');
                suggestionsDiv.innerHTML = html;
            } else {
                suggestionsDiv.innerHTML = '<p style="text-align: center; color: #aaa; font-size: 13px; padding: 8px 0;">✅ No specific suggestions - app is running efficiently.</p>';
            }
        }
    }

    getConsumerIcon(type) {
        const icons = {
            gps: '📍',
            network: '🌐',
            websocket: '🔌',
            tracking: '🚶',
            sensors: '📱',
            ui: '🎨',
            other: '⚙️'
        };
        return icons[type] || '⚙️';
    }

    // Record energy metrics
    async recordMetric(type, data = {}) {
        // Don't record too frequently (throttle to configured interval per type)
        const now = Date.now();
        if (this.lastMetricTime[type] && now - this.lastMetricTime[type] < EnergyMonitor.METRIC_THROTTLE_INTERVAL) {
            return;
        }
        this.lastMetricTime[type] = now;
        
        const metric = {
            consumption_type: type,
            battery_level: this.battery ? this.battery.level * 100 : null,
            is_charging: this.battery ? this.battery.charging : false,
            ...data
        };
        
        try {
            await fetch(`${API_BASE}/energy/metrics`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(metric)
            });
        } catch (error) {
            console.error('Failed to record energy metric:', error);
        }
    }

    // Track GPS updates
    trackGPSUpdate() {
        this.activityCounters.gps++;
        
        // Record metric every 10 GPS updates
        if (this.activityCounters.gps % 10 === 0) {
            this.recordMetric('gps', {
                gps_updates_count: 10,
                activity_duration_seconds: 60,
                estimated_battery_drain: 0.5
            });
        }
    }

    // Track network requests
    trackNetworkRequest() {
        this.activityCounters.network++;
        
        // Record metric every 20 network requests
        if (this.activityCounters.network % 20 === 0) {
            this.recordMetric('network', {
                network_requests_count: 20,
                estimated_battery_drain: 0.3
            });
        }
    }

    // Track WebSocket messages
    trackWebSocketMessage() {
        this.activityCounters.websocket++;
        
        // Record metric every 50 WebSocket messages
        if (this.activityCounters.websocket % 50 === 0) {
            this.recordMetric('websocket', {
                websocket_messages_count: 50,
                estimated_battery_drain: 0.2
            });
        }
    }

    // Track tracking activity
    trackTrackingActivity(durationSeconds) {
        this.recordMetric('tracking', {
            activity_duration_seconds: durationSeconds,
            estimated_battery_drain: durationSeconds * 0.01
        });
    }

    startMonitoring() {
        // Update battery UI at configured interval
        this.updateInterval = setInterval(() => {
            this.updateBatteryUI();
        }, EnergyMonitor.BATTERY_UPDATE_INTERVAL);
        
        // Update stats at configured interval
        this.statsUpdateInterval = setInterval(() => {
            const energyTab = document.getElementById('energy-tab');
            if (this._isElementVisible(energyTab)) {
                this.updateEnergyStats();
            }
        }, EnergyMonitor.STATS_UPDATE_INTERVAL);
    }

    cleanup() {
        if (this.updateInterval) clearInterval(this.updateInterval);
        if (this.statsUpdateInterval) clearInterval(this.statsUpdateInterval);
    }
}

// Export for global use
window.EnergyMonitor = EnergyMonitor;
