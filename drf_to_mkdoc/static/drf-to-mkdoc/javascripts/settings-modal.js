// Settings Modal Management
const SettingsManager = {
    storageKey: 'drfToMkdocSettings',
    
    // Open settings modal
    openSettingsModal: function() {
        const modal = document.getElementById('settingsModal');
        if (!modal) return;
        
        // Load and populate current settings
        this.loadSettings();
        
        // Show modal
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
        
        // Focus on first input
        const firstInput = modal.querySelector('#settingsHost');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    },
    
    // Close settings modal
    closeSettingsModal: function() {
        const modal = document.getElementById('settingsModal');
        if (!modal) return;
        
        modal.classList.remove('show');
        document.body.style.overflow = '';
    },
    
    // Get current browser host
    getDefaultHost: function() {
        return window.location.origin;
    },
    
    // Load settings from localStorage
    loadSettings: function() {
        const saved = localStorage.getItem(this.storageKey);
        let settings = {
            host: this.getDefaultHost(),
            headers: {}
        };
        
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                settings = {
                    host: parsed.host || this.getDefaultHost(),
                    headers: parsed.headers || {}
                };
            } catch (e) {
                console.warn('Failed to parse saved settings:', e);
            }
        }
        
        // Populate host input
        const hostInput = document.getElementById('settingsHost');
        if (hostInput) {
            hostInput.value = settings.host;
        }
        
        // Clear existing header items (except first empty one)
        const headerList = document.querySelector('#settingsHeaders .header-list');
        if (headerList) {
            const firstItem = headerList.querySelector('.header-item');
            headerList.innerHTML = '';
            
            // Add saved headers or one empty item
            const headerEntries = Object.entries(settings.headers);
            if (headerEntries.length > 0) {
                headerEntries.forEach(([name, value]) => {
                    const headerItem = this.createHeaderItem(name, value);
                    headerList.appendChild(headerItem);
                });
            } else {
                // Add one empty header item
                headerList.appendChild(this.createHeaderItem('', ''));
            }
        }
        
        return settings;
    },
    
    // Save settings to localStorage
    saveSettings: function() {
        const hostInput = document.getElementById('settingsHost');
        const host = hostInput?.value.trim() || this.getDefaultHost();
        
        // Collect headers
        const headers = {};
        const headerItems = document.querySelectorAll('#settingsHeaders .header-item');
        headerItems.forEach(item => {
            const nameInput = item.querySelector('.name-input');
            const valueInput = item.querySelector('.value-input');
            const name = nameInput?.value.trim();
            const value = valueInput?.value.trim();
            
            if (name && value) {
                headers[name] = value;
            }
        });
        
        // Save to localStorage
        const settings = {
            host: host,
            headers: headers
        };
        
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(settings));
            
            // Close modal
            this.closeSettingsModal();
            
            // Show success feedback (optional)
            this.showToast('Settings saved successfully', 'success');
            
            // Reload settings in try-out form if it exists
            if (window.FormManager && typeof window.FormManager.loadSettings === 'function') {
                window.FormManager.loadSettings();
            }
        } catch (e) {
            console.error('Failed to save settings:', e);
            this.showToast('Failed to save settings', 'error');
        }
    },
    
    // Get saved settings
    getSettings: function() {
        const saved = localStorage.getItem(this.storageKey);
        if (!saved) {
            return {
                host: this.getDefaultHost(),
                headers: {}
            };
        }
        
        try {
            const parsed = JSON.parse(saved);
            return {
                host: parsed.host || this.getDefaultHost(),
                headers: parsed.headers || {}
            };
        } catch (e) {
            console.warn('Failed to parse saved settings:', e);
            return {
                host: this.getDefaultHost(),
                headers: {}
            };
        }
    },
    
    // Add header field
    addHeaderField: function(name = '', value = '') {
        const headerList = document.querySelector('#settingsHeaders .header-list');
        if (!headerList) return;
        
        const headerItem = this.createHeaderItem(name, value);
        headerList.appendChild(headerItem);
        
        // Focus on the first input
        const nameInput = headerItem.querySelector('.name-input');
        if (nameInput) {
            nameInput.focus();
        }
    },
    
    // Create header item element
    createHeaderItem: function(name = '', value = '') {
        const headerItem = document.createElement('div');
        headerItem.className = 'header-item';
        
        headerItem.innerHTML = `
            <div class="header-inputs">
                <input type="text" 
                       class="modern-input name-input" 
                       placeholder="Header name"
                       value="${name}"
                       list="settingsHeaderSuggestions">
                <input type="text" 
                       class="modern-input value-input" 
                       placeholder="Header value"
                       value="${value}">
                <button class="remove-btn" 
                        onclick="SettingsManager.removeHeaderField(this)"
                        aria-label="Remove header">
                    <span class="icon">✕</span>
                </button>
            </div>
        `;
        
        return headerItem;
    },
    
    // Remove header field
    removeHeaderField: function(button) {
        const headerItem = button.closest('.header-item');
        if (headerItem) {
            const headerList = document.querySelector('#settingsHeaders .header-list');
            const remainingItems = headerList?.querySelectorAll('.header-item') || [];
            
            // Don't allow removing if it's the last item
            if (remainingItems.length > 1) {
                headerItem.remove();
            } else {
                // If it's the last item, just clear the inputs
                const nameInput = headerItem.querySelector('.name-input');
                const valueInput = headerItem.querySelector('.value-input');
                if (nameInput) nameInput.value = '';
                if (valueInput) valueInput.value = '';
            }
        }
    },
    
    // Show toast notification
    showToast: function(message, type = 'success') {
        // Create or get toast element
        let toast = document.getElementById('settingsToast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'settingsToast';
            toast.className = 'settings-toast';
            document.body.appendChild(toast);
        }
        
        toast.textContent = message;
        toast.className = `settings-toast toast-${type}`;
        toast.classList.add('show');
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    },
    
    // Initialize
    init: function() {
        // Close modal on overlay click
        const modal = document.getElementById('settingsModal');
        if (modal) {
            const overlay = modal.querySelector('.modal-overlay');
            if (overlay) {
                overlay.addEventListener('click', (e) => {
                    if (e.target === overlay) {
                        this.closeSettingsModal();
                    }
                });
            }
            
            // Close modal on Escape key
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && modal.classList.contains('show')) {
                    this.closeSettingsModal();
                }
            });
        }
    }
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    SettingsManager.init();
});

// Global functions for onclick handlers
window.openSettingsModal = () => SettingsManager.openSettingsModal();
window.closeSettingsModal = () => SettingsManager.closeSettingsModal();

// Export for global access
window.SettingsManager = SettingsManager;
