// Energy Monitoring Module for Claim GPS Game
// Handles battery monitoring, energy consumption tracking, and optimization

class EnergyMonitor {
    constructor() {
        this.battery = null;
        this.batterySupported = 'getBattery' in navigator;
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
        
        // Initialize Battery Status API
        if (this.batterySupported) {
            try {
                this.battery = await navigator.getBattery();
                this.setupBatteryListeners();
                console.log('✅ Battery API connected');
            } catch (error) {
                console.warn('Battery API not available:', error);
                this.batterySupported = false;
            }
        } else {
            console.warn('Battery API not supported in this browser');
        }
        
        // Load energy settings from backend
        await this.loadEnergySettings();
        
        // Setup UI handlers
        this.setupUI();
        
        // Start monitoring
        this.startMonitoring();
        
        // Check if we should auto-enable energy saving
        this.checkAutoEnableEnergySaving();
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
            // Show "not available" state
            document.getElementById('battery-level').textContent = 'N/A';
            document.getElementById('battery-fill').style.width = '0%';
            document.getElementById('charging-status').textContent = 'Battery info not available';
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
                    document.getElementById('time-remaining').textContent = 'Calculating...';
                }
            }
        } catch (error) {
            console.error('Failed to update time remaining:', error);
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
            }, 10000); // Increase from default to 10 seconds
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
            }, 3000); // Restore to default 3 seconds
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
                this.displayEnergyStats(stats);
            }
        } catch (error) {
            console.error('Failed to update energy stats:', error);
        }
    }

    displayEnergyStats(stats) {
        // Display top consumers
        const consumersDiv = document.getElementById('energy-consumers');
        if (stats.top_consumers && stats.top_consumers.length > 0) {
            const html = stats.top_consumers.map(consumer => {
                const icon = this.getConsumerIcon(consumer.type);
                const percentage = Math.round(consumer.percentage);
                return `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <span>${icon} ${consumer.type}</span>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div style="width: 100px; height: 10px; background: rgba(0,0,0,0.2); border-radius: 5px; overflow: hidden;">
                                <div style="width: ${percentage}%; height: 100%; background: #667eea;"></div>
                            </div>
                            <span style="min-width: 40px; text-align: right;">${percentage}%</span>
                        </div>
                    </div>
                `;
            }).join('');
            consumersDiv.innerHTML = html;
        } else {
            consumersDiv.innerHTML = '<p style="text-align: center; color: #aaa;">No data yet. Keep using the app to collect energy metrics.</p>';
        }
        
        // Display optimization suggestions
        const suggestionsDiv = document.getElementById('optimization-suggestions');
        if (stats.optimization_suggestions && stats.optimization_suggestions.length > 0) {
            const html = stats.optimization_suggestions.map(suggestion => {
                return `<div style="padding: 8px; background: rgba(255,255,255,0.05); border-radius: 4px; margin-bottom: 8px; font-size: 13px;">${suggestion}</div>`;
            }).join('');
            suggestionsDiv.innerHTML = html;
        } else {
            suggestionsDiv.innerHTML = '<p style="text-align: center; color: #aaa;">No suggestions at this time.</p>';
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
        // Don't record too frequently (max once per minute per type)
        const now = Date.now();
        if (this.lastMetricTime[type] && now - this.lastMetricTime[type] < 60000) {
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
        // Update battery UI every 30 seconds
        this.updateInterval = setInterval(() => {
            this.updateBatteryUI();
        }, 30000);
        
        // Update stats every 5 minutes
        this.statsUpdateInterval = setInterval(() => {
            const energyTab = document.getElementById('energy-tab');
            if (energyTab && !energyTab.classList.contains('hidden') && energyTab.style.display !== 'none') {
                this.updateEnergyStats();
            }
        }, 300000);
    }

    cleanup() {
        if (this.updateInterval) clearInterval(this.updateInterval);
        if (this.statsUpdateInterval) clearInterval(this.statsUpdateInterval);
    }
}

// Export for global use
window.EnergyMonitor = EnergyMonitor;
