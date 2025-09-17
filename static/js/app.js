// app.js - Main JavaScript for BankNifty Dispersion Trade Monitor
class DispersionTradeApp {
    constructor() {
        this.socket = null;
        this.currentData = {};
        this.historicalData = [];
        this.connectionStatus = 'disconnected';
        this.zerodhaConnected = false;
        this.chart = null;
        
        this.init();
    }
    
    init() {
        this.initializeSocket();
        this.bindEventHandlers();
        this.loadInitialData();
        this.initializeChart();
    }
    
    initializeSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.connectionStatus = 'connected';
            this.updateConnectionStatus('connected', 'Connected to server');
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.connectionStatus = 'disconnected';
            this.updateConnectionStatus('disconnected', 'Disconnected from server');
        });
        
        this.socket.on('data_update', (data) => {
            console.log('Data update received:', data);
            this.currentData = data;
            this.updateUI(data);
        });
        
        this.socket.on('connection_status', (status) => {
            console.log('Connection status:', status);
            this.zerodhaConnected = status.status === 'connected';
            this.updateConnectionStatus(status.status, status.message);
        });
        
        this.socket.on('alert', (alert) => {
            console.log('Alert received:', alert);
            this.showAlert(alert);
        });
    }
    
    bindEventHandlers() {
        // Settings form
        document.getElementById('settings-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.applySettings();
        });
        
        // Monitoring controls
        document.getElementById('start-monitoring-btn')?.addEventListener('click', () => {
            this.startMonitoring();
        });
        
        document.getElementById('stop-monitoring-btn')?.addEventListener('click', () => {
            this.stopMonitoring();
        });
        
        // Data refresh
        document.getElementById('refresh-btn')?.addEventListener('click', () => {
            this.refreshData();
        });
        
        // Export buttons
        document.querySelectorAll('.export-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const otmLevel = e.target.dataset.otmLevel || 'ATM';
                this.exportData(otmLevel);
            });
        });
        
        // Authentication buttons
        document.getElementById('refresh-totp-btn')?.addEventListener('click', () => {
            this.refreshTOTP();
        });
        
        document.getElementById('get-login-url-btn')?.addEventListener('click', () => {
            this.getLoginURL();
        });
        
        // Diagnostics
        document.getElementById('diagnostics-btn')?.addEventListener('click', () => {
            this.showConnectionDiagnostics();
        });
    }
    
    async loadInitialData() {
        try {
            const [dataResponse, statusResponse] = await Promise.all([
                fetch('/api/data'),
                fetch('/api/status')
            ]);
            
            if (dataResponse.ok) {
                const data = await dataResponse.json();
                this.currentData = data;
                this.updateUI(data);
            }
            
            if (statusResponse.ok) {
                const status = await statusResponse.json();
                this.zerodhaConnected = status.zerodha_connected;
                this.updateConnectionStatus(
                    status.zerodha_connected ? 'connected' : 'disconnected',
                    status.zerodha_connected ? 'Connected to Zerodha' : 'Not connected to Zerodha'
                );
            }
            
            // Load historical data
            await this.loadHistoricalData();
            
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showNotification('Error loading initial data', 'error');
        }
    }
    
    async loadHistoricalData() {
        try {
            const response = await fetch('/api/historical');
            if (response.ok) {
                const data = await response.json();
                this.historicalData = data;
                this.updateHistoricalChart();
            }
        } catch (error) {
            console.error('Error loading historical data:', error);
        }
    }
    
    updateUI(data) {
        // Update last updated timestamp
        this.updateElement('last-updated', new Date().toLocaleTimeString());
        
        // Update BankNifty details
        if (data.banknifty) {
            this.updateElement('bn-spot', this.formatCurrency(data.banknifty.spot));
            this.updateElement('bn-strike', this.formatCurrency(data.banknifty.atm_strike));
            this.updateElement('bn-expiry', data.expiry_date);
            this.updateElement('bn-days-to-expiry', data.days_to_expiry);
            
            const monitoringElement = document.getElementById('bn-monitoring');
            if (monitoringElement) {
                monitoringElement.textContent = data.monitoring_active ? 'Yes' : 'No';
                monitoringElement.className = data.monitoring_active ? 'badge bg-success' : 'badge bg-secondary';
            }
        }
        
        // Update net premium displays
        if (data.net_premium && typeof data.net_premium === 'object') {
            Object.keys(data.net_premium).forEach(level => {
                const premium = data.net_premium[level] || 0;
                const elementId = `net-premium-${level.toLowerCase()}`;
                const element = document.getElementById(elementId);
                
                if (element) {
                    element.textContent = this.formatCurrency(premium);
                    element.className = premium >= 0 ? 'premium-positive' : 'premium-negative';
                }
            });
            
            // Update main premium display (fallback)
            const mainElement = document.getElementById('net-premium');
            if (mainElement && data.net_premium.ATM !== undefined) {
                this.updateNetPremium(data.net_premium.ATM);
            }
        }
        
        // Update constituents table
        this.updateConstituentsTable(data);
        
        // Add to historical data for charting
        if (data.net_premium) {
            this.historicalData.push({
                time: new Date().toISOString(),
                premium: data.net_premium.ATM || 0,
                banknifty_spot: data.banknifty ? data.banknifty.spot : 0
            });
            
            // Keep only last 100 data points
            if (this.historicalData.length > 100) {
                this.historicalData.shift();
            }
            
            this.updateHistoricalChart();
        }
    }
    
    updateConstituentsTable(data) {
        const tableBody = document.getElementById('constituents-table');
        if (!tableBody || !data.constituents) return;
        
        let html = '';
        Object.entries(data.constituents).forEach(([symbol, details]) => {
            const atmData = details.otm_levels ? details.otm_levels.ATM : {};
            html += `
                <tr>
                    <td>${symbol}</td>
                    <td>${(details.weight * 100).toFixed(2)}%</td>
                    <td>${this.formatCurrency(details.spot || 0)}</td>
                    <td>${this.formatCurrency(details.atm_strike || 0)}</td>
                    <td>${this.formatCurrency(atmData.call_premium || 0)}</td>
                    <td>${this.formatCurrency(atmData.put_premium || 0)}</td>
                    <td>${this.formatCurrency(atmData.straddle_premium || 0)}</td>
                    <td>${details.lot_size || '-'}</td>
                    <td>${data.normalized_lots && data.normalized_lots[symbol] ? data.normalized_lots[symbol].lot_count : 1}</td>
                </tr>
            `;
        });
        
        tableBody.innerHTML = html;
    }
    
    updateNetPremium(premium) {
        const element = document.getElementById('net-premium');
        if (element) {
            element.textContent = this.formatCurrency(premium);
            element.className = premium >= 0 ? 'premium-positive' : 'premium-negative';
        }
    }
    
    updateConnectionStatus(status, message) {
        const statusElement = document.getElementById('connection-status');
        const messageElement = document.getElementById('connection-message');
        
        if (statusElement) {
            statusElement.textContent = status === 'connected' ? 'Connected' : 'Disconnected';
            statusElement.className = status === 'connected' ? 'badge bg-success' : 'badge bg-danger';
        }
        
        if (messageElement) {
            messageElement.textContent = message;
        }
    }
    
    async applySettings() {
        try {
            const formData = new FormData(document.getElementById('settings-form'));
            const settings = Object.fromEntries(formData.entries());
            
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    alert_threshold: parseFloat(settings.alert_threshold),
                    selected_otm_level: settings.otm_level,
                    auto_alerts_enabled: settings.auto_alerts === 'on'
                })
            });
            
            if (response.ok) {
                this.showNotification('Settings applied successfully!');
            } else {
                throw new Error('Failed to apply settings');
            }
        } catch (error) {
            console.error('Error applying settings:', error);
            this.showNotification('Error applying settings', 'error');
        }
    }
    
    async startMonitoring() {
        try {
            const response = await fetch('/api/start-monitoring', { method: 'POST' });
            const data = await response.json();
            
            if (data.status === 'success') {
                this.updateElement('monitoring-status', 'Active');
                this.toggleMonitoringButtons(true);
                this.showNotification(data.message);
            } else {
                this.showNotification(data.message, 'error');
            }
        } catch (error) {
            console.error('Error starting monitoring:', error);
            this.showNotification('Error starting monitoring', 'error');
        }
    }
    
    async stopMonitoring() {
        try {
            const response = await fetch('/api/stop-monitoring', { method: 'POST' });
            const data = await response.json();
            
            if (data.status === 'success') {
                this.updateElement('monitoring-status', 'Inactive');
                this.toggleMonitoringButtons(false);
                this.showNotification(data.message);
            } else {
                this.showNotification(data.message, 'error');
            }
        } catch (error) {
            console.error('Error stopping monitoring:', error);
            this.showNotification('Error stopping monitoring', 'error');
        }
    }
    
    toggleMonitoringButtons(isActive) {
        const startBtn = document.getElementById('start-monitoring-btn');
        const stopBtn = document.getElementById('stop-monitoring-btn');
        
        if (startBtn) startBtn.style.display = isActive ? 'none' : 'block';
        if (stopBtn) stopBtn.style.display = isActive ? 'block' : 'none';
    }
    
    async refreshData() {
        try {
            const response = await fetch('/api/data');
            if (response.ok) {
                const data = await response.json();
                this.currentData = data;
                this.updateUI(data);
                this.showNotification('Data refreshed successfully!');
            } else {
                throw new Error('Failed to refresh data');
            }
        } catch (error) {
            console.error('Error refreshing data:', error);
            this.showNotification('Error refreshing data', 'error');
        }
    }
    
    exportData(otmLevel = 'ATM') {
        if (!this.currentData || Object.keys(this.currentData).length === 0) {
            this.showNotification('No data available to export', 'error');
            return;
        }
        
        this.showNotification(`Preparing ${otmLevel} data for export...`);
        window.open(`/api/export/${otmLevel}`, '_blank');
        this.showNotification(`${otmLevel} data export initiated!`);
    }
    
    async refreshTOTP() {
        try {
            const response = await fetch('/api/totp');
            const data = await response.json();
            
            if (data.totp) {
                const totpElement = document.getElementById('current-totp');
                if (totpElement) totpElement.value = data.totp;
                this.showNotification('TOTP refreshed: ' + data.totp);
            } else {
                this.showNotification('Failed to get TOTP', 'error');
            }
        } catch (error) {
            console.error('TOTP fetch error:', error);
            this.showNotification('Error getting TOTP', 'error');
        }
    }
    
    async getLoginURL() {
        try {
            const response = await fetch('/api/login-url');
            const data = await response.json();
            
            if (data.login_url) {
                window.open(data.login_url, '_blank');
                this.showNotification('Login URL opened in new tab');
                
                if (data.current_totp) {
                    const totpElement = document.getElementById('current-totp');
                    if (totpElement) totpElement.value = data.current_totp;
                }
            } else {
                this.showNotification('Failed to get login URL', 'error');
            }
        } catch (error) {
            console.error('Error getting login URL:', error);
            this.showNotification('Error getting login URL', 'error');
        }
    }
    
    async showConnectionDiagnostics() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            let diagnosticsText = `Connection Diagnostics:\n\n`;
            diagnosticsText += `Status: ${data.zerodha_connected ? 'Connected' : 'Disconnected'}\n`;
            diagnosticsText += `Monitoring Active: ${data.monitoring_active ? 'Yes' : 'No'}\n`;
            diagnosticsText += `Days to Expiry: ${data.days_to_expiry}\n`;
            diagnosticsText += `Last Update: ${data.last_update || 'Never'}\n`;
            diagnosticsText += `Net Premium (ATM): ₹${data.net_premium ? data.net_premium.ATM || 0 : 0}\n`;
            
            if (data.last_heartbeat) {
                diagnosticsText += `Last Heartbeat: ${new Date(data.last_heartbeat).toLocaleString()}\n`;
                diagnosticsText += `Time Since Last Data: ${Math.floor(data.seconds_since_last_data || 0)}s\n`;
            } else {
                diagnosticsText += `Last Heartbeat: Never\n`;
            }
            
            alert(diagnosticsText);
        } catch (error) {
            console.error('Error fetching diagnostics:', error);
            this.showNotification('Failed to fetch connection diagnostics', 'error');
        }
    }
    
    initializeChart() {
        // Initialize Chart.js chart for historical data
        const ctx = document.getElementById('historical-chart');
        if (!ctx) return;
        
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Net Premium (ATM)',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Net Premium (₹)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    }
                }
            }
        });
    }
    
    updateHistoricalChart() {
        if (!this.chart || !this.historicalData.length) return;
        
        const labels = this.historicalData.map(d => new Date(d.time).toLocaleTimeString());
        const data = this.historicalData.map(d => d.premium);
        
        this.chart.data.labels = labels;
        this.chart.data.datasets[0].data = data;
        this.chart.update();
    }
    
    showAlert(alert) {
        // Create and show alert notification
        const alertHtml = `
            <div class="alert alert-warning alert-dismissible fade show" role="alert">
                <strong>${alert.otm_level} Alert!</strong> ${alert.message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        const alertContainer = document.getElementById('alerts-container');
        if (alertContainer) {
            alertContainer.insertAdjacentHTML('afterbegin', alertHtml);
        }
        
        // Also show as notification
        this.showNotification(alert.message, 'warning');
    }
    
    showNotification(message, type = 'info') {
        // Create toast notification
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : type === 'warning' ? 'warning' : 'primary'} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        const toastContainer = document.getElementById('toast-container');
        if (toastContainer) {
            toastContainer.insertAdjacentHTML('beforeend', toastHtml);
            const toastElement = toastContainer.lastElementChild;
            const toast = new bootstrap.Toast(toastElement);
            toast.show();
            
            // Remove toast element after it's hidden
            toastElement.addEventListener('hidden.bs.toast', () => {
                toastElement.remove();
            });
        }
    }
    
    // Utility functions
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    }
    
    formatCurrency(value) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 2
        }).format(value || 0).replace('₹', '₹');
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dispersionApp = new DispersionTradeApp();
});
