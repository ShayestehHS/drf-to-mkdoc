// Settings Modal Management
const SettingsManager = {
    storageKey: 'drfToMkdocSettings',
    headersStorageKey: 'drfToMkdocHeaders', // Separate key for headers
    usePersistentHeaders: false, // Track whether user opted in to persistent storage
    _authInProgress: false, // Guard flag to prevent concurrent auth runs
    
    // Open settings modal
    openSettingsModal: function() {
        const modal = document.getElementById('settingsModal');
        if (!modal) return;
        
        // Show/hide auth section based on auto-auth status
        this.toggleAuthSection();
        
        // Load and populate current settings
        this.loadSettings();
        
        // Show modal
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
        
        // Focus on first input after modal transition
        const firstInput = modal.querySelector('#settingsHost');
        if (firstInput) {
            // Wait for CSS transition to complete before focusing
            modal.addEventListener('transitionend', () => firstInput.focus(), { once: true });
        }
    },
    
    // Toggle auth section visibility - show only when auto-auth is enabled
    toggleAuthSection: function() {
        const authSection = document.getElementById('authSection');
        if (!authSection) return;
        
        const authConfig = window.DRF_TO_MKDOC_AUTH_CONFIG;
        // Show auth section only when auto-auth is enabled
        if (authConfig && authConfig.enabled) {
            authSection.style.display = 'block';
        } else {
            authSection.style.display = 'none';
        }
        
        this.updateAuthEmoji(); // Update emoji based on stored header
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
    
    // Helper to load host and headers from storage
    _loadStoredSettings: function() {
        // Load host from localStorage (non-sensitive)
        let host = this.getDefaultHost();
        let usePersistentHeaders = false;
        
        try {
            const savedHost = localStorage.getItem(this.storageKey);
            if (savedHost) {
                const parsed = JSON.parse(savedHost);
                host = parsed.host || this.getDefaultHost();
                usePersistentHeaders = parsed.persistHeaders === true;
                this.usePersistentHeaders = usePersistentHeaders;
            }
        } catch (e) {
            console.warn('Failed to parse saved host settings:', e);
        }
        
        // Load headers from sessionStorage by default (sensitive)
        // Fall back to localStorage if persistHeaders was enabled
        let headers = {};
        try {
            const sessionHeaders = sessionStorage.getItem(this.headersStorageKey);
            if (sessionHeaders) {
                headers = JSON.parse(sessionHeaders);
            }
            
            // Also check localStorage if persistHeaders was enabled
            if (usePersistentHeaders) {
                const saved = localStorage.getItem(this.storageKey);
                if (saved) {
                    const parsed = JSON.parse(saved);
                    if (parsed.headers) {
                        // Merge: sessionStorage takes precedence, then localStorage
                        headers = { ...parsed.headers, ...headers };
                    }
                }
            }
        } catch (e) {
            console.warn('Failed to parse saved headers:', e);
        }
        
        return {
            host: host,
            headers: headers,
            usePersistentHeaders: usePersistentHeaders
        };
    },
    
    // Load settings from storage and populate UI
    loadSettings: function() {
        // Load stored settings using helper
        const settings = this._loadStoredSettings();
        
        // Populate host input
        const hostInput = document.getElementById('settingsHost');
        if (hostInput) {
            hostInput.value = settings.host;
        }
        
        // Populate persist headers checkbox
        const persistCheckbox = document.getElementById('persistHeaders');
        if (persistCheckbox) {
            persistCheckbox.checked = settings.usePersistentHeaders;
        }
        
        // Reset emoji; final state will be derived from current header inputs
        const authEmoji = document.getElementById('settingsAuthEmoji');
        if (authEmoji) {
            authEmoji.textContent = '🔒';
            authEmoji.classList.remove('success', 'unlocking');
            authEmoji.setAttribute('aria-label', 'Locked');
        }
        
        // Clear all header items
        const headerList = document.querySelector('#settingsHeaders .header-list');
        if (headerList) {
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
        
        // Now that header inputs reflect saved headers, sync the emoji state
        this.updateAuthEmoji();
        
        return settings;
    },
    
    // Save settings to storage
    saveSettings: function() {
        const hostInput = document.getElementById('settingsHost');
        const host = hostInput?.value.trim() || this.getDefaultHost();
        
        // Get persist headers preference
        const persistCheckbox = document.getElementById('persistHeaders');
        this.usePersistentHeaders = persistCheckbox?.checked === true;
        
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
        
        try {
            // Save host to localStorage (non-sensitive)
            const hostSettings = {
                host: host,
                persistHeaders: this.usePersistentHeaders
            };
            localStorage.setItem(this.storageKey, JSON.stringify(hostSettings));
            
            // Save headers based on user preference
            if (this.usePersistentHeaders) {
                // Save to localStorage (less secure, but user opted in)
                const allSettings = {
                    ...hostSettings,
                    headers: headers
                };
                localStorage.setItem(this.storageKey, JSON.stringify(allSettings));
                // Also save to sessionStorage for immediate use
                sessionStorage.setItem(this.headersStorageKey, JSON.stringify(headers));
            } else {
                // Save to sessionStorage only (more secure, cleared on tab close)
                sessionStorage.setItem(this.headersStorageKey, JSON.stringify(headers));
                // Remove headers from localStorage if they were there
                const existing = localStorage.getItem(this.storageKey);
                if (existing) {
                    try {
                        const parsed = JSON.parse(existing);
                        delete parsed.headers;
                        localStorage.setItem(this.storageKey, JSON.stringify({
                            ...parsed,
                            ...hostSettings
                        }));
                    } catch (e) {
                        // If parsing fails, just save host settings
                        localStorage.setItem(this.storageKey, JSON.stringify(hostSettings));
                    }
                }
            }
            
            // Close modal
            this.closeSettingsModal();
            
            // Show success feedback
            const storageType = this.usePersistentHeaders ? 'localStorage' : 'sessionStorage';
            this.showToast(`Settings saved (headers in ${storageType})`, 'success');
            
            // Reload settings in try-out form if it exists
            if (window.FormManager && typeof window.FormManager.loadSettings === 'function') {
                window.FormManager.loadSettings();
            }
        } catch (e) {
            console.error('Failed to save settings:', e);
            this.showToast('Failed to save settings', 'error');
        }
    },
    
    // Get saved settings (reads from both storage locations)
    getSettings: function() {
        // Use helper method to load settings
        const settings = this._loadStoredSettings();
        return {
            host: settings.host,
            headers: settings.headers
        };
    },
    
    // Test authentication
    testAuth: function() {
        const authButton = document.getElementById('settingsAuthTestButton');
        const authEmoji = document.getElementById('settingsAuthEmoji');
        
        if (!authButton || !authEmoji) {
            return;
        }
        
        // Guard against concurrent auth runs
        if (this._authInProgress) {
            this.showToast('Authentication already in progress', 'info');
            return;
        }
        
        this._authInProgress = true;
        
        // Use shared AuthHandler if available
        if (window.AuthHandler && typeof window.AuthHandler.handleAuth === 'function') {
            // Set loading state
            const buttonText = authButton.querySelector('.auth-card-button-text');
            const buttonLoader = authButton.querySelector('.auth-prompt-button-loader');
            authButton.disabled = true;
            authButton.classList.add('loading');
            if (buttonText) buttonText.textContent = 'Generating...';
            if (buttonLoader) buttonLoader.style.display = 'inline-block';
            authEmoji.textContent = '🔓';
            authEmoji.classList.add('unlocking');
            authEmoji.setAttribute('aria-label', 'Unlocking');
            
            try {
                window.AuthHandler.handleAuth({
                    onStart: () => {
                        // Loading state already set above
                    },
                    onSuccess: (result) => {
                        this._handleAuthTestResult(result, authButton, authEmoji);
                    },
                    onError: (error) => {
                        this._handleAuthTestError(error, authButton, authEmoji);
                    }
                });
            } catch (error) {
                // Ensure UI state and guard flag are reset on sync failures
                this._handleAuthTestError(error, authButton, authEmoji);
            }
        } else {
            // Fallback to legacy implementation
            this._testAuthLegacy(authButton, authEmoji);
        }
    },
    
    // Legacy test auth implementation
    _testAuthLegacy: function(authButton, authEmoji) {
        // Check if getAuthHeader function exists
        if (typeof window.getAuthHeader !== 'function') {
            this._authInProgress = false; // Clear flag on early return
            this.showToast('getAuthHeader function not found. Please configure it in your JavaScript.', 'error');
            return;
        }
        
        // Set loading state
        const buttonText = authButton.querySelector('.auth-card-button-text');
        const buttonLoader = authButton.querySelector('.auth-prompt-button-loader');
        authButton.disabled = true;
        authButton.classList.add('loading');
        if (buttonText) buttonText.textContent = 'Generating...';
        if (buttonLoader) buttonLoader.style.display = 'inline-block';
        authEmoji.textContent = '🔓';
        authEmoji.classList.add('unlocking');
        authEmoji.setAttribute('aria-label', 'Unlocking');
        
        // Set up timeout to prevent hanging
        const TIMEOUT_MS = 30000; // 30 seconds
        let timeoutId = null;
        let completed = false;
        
        const clearTimeoutAndComplete = () => {
            if (timeoutId) {
                clearTimeout(timeoutId);
                timeoutId = null;
            }
            completed = true;
        };
        
        const handleTimeout = () => {
            if (!completed) {
                clearTimeoutAndComplete();
                this._handleAuthTestError(new Error('Authentication timed out'), authButton, authEmoji);
            }
        };
        
        timeoutId = setTimeout(handleTimeout, TIMEOUT_MS);
        
        try {
            // Call auth function directly (credentials should be handled in the function)
            let authResult = window.getAuthHeader();
            
            // Check if result is null or undefined
            if (!authResult) {
                clearTimeoutAndComplete();
                throw new Error('getAuthHeader function returned null or undefined.');
            }
            
            // Handle async functions
            if (authResult && typeof authResult.then === 'function') {
                authResult.then(result => {
                    if (completed) return; // Timeout already handled
                    clearTimeoutAndComplete();
                    
                    // Validate async result
                    if (!result) {
                        this._handleAuthTestError(new Error('getAuthHeader function returned null or undefined.'), authButton, authEmoji);
                        return;
                    }
                    this._handleAuthTestResult(result, authButton, authEmoji);
                }).catch(error => {
                    if (completed) return; // Timeout already handled
                    clearTimeoutAndComplete();
                    this._handleAuthTestError(error, authButton, authEmoji);
                });
            } else {
                // Handle synchronous result
                clearTimeoutAndComplete();
                this._handleAuthTestResult(authResult, authButton, authEmoji);
            }
        } catch (error) {
            if (!completed) {
                clearTimeoutAndComplete();
                this._handleAuthTestError(error, authButton, authEmoji);
            }
        }
    },
    
    // Handle auth test result
    _handleAuthTestResult: function(result, authButton, authEmoji) {
        const buttonText = authButton.querySelector('.auth-card-button-text');
        const buttonLoader = authButton.querySelector('.auth-prompt-button-loader');
        
        // Strict validation: result must be an object with both headerName and headerValue as non-empty strings
        if (result && 
            typeof result === 'object' && 
            result.headerName && 
            typeof result.headerName === 'string' && 
            result.headerName.trim() &&
            result.headerValue && 
            typeof result.headerValue === 'string' && 
            result.headerValue.trim()) {
            
            // Check if header already exists in headers section
            const headerItems = document.querySelectorAll('#settingsHeaders .header-item');
            let existingHeaderItem = null;
            
            headerItems.forEach(item => {
                const nameInput = item.querySelector('.name-input');
                const existingName = nameInput && typeof nameInput.value === 'string'
                    ? nameInput.value.trim().toLowerCase()
                    : '';
                const targetName = typeof result.headerName === 'string'
                    ? result.headerName.trim().toLowerCase()
                    : '';
                if (existingName && existingName === targetName) {
                    existingHeaderItem = item;
                }
            });
            
            if (existingHeaderItem) {
                // Update existing header
                const valueInput = existingHeaderItem.querySelector('.value-input');
                if (valueInput) {
                    valueInput.value = result.headerValue.trim();
                }
            } else {
                // Add new header to headers section
                this.addHeaderField(result.headerName.trim(), result.headerValue.trim());
            }
            
            // Update emoji state
            this.updateAuthEmoji();
            
            authEmoji.textContent = '✅';
            authEmoji.classList.remove('unlocking');
            authEmoji.classList.add('success');
            authEmoji.setAttribute('aria-label', 'Authenticated');
            authButton.disabled = false;
            authButton.classList.remove('loading');
            if (buttonText) buttonText.textContent = 'Header Added';
            if (buttonLoader) buttonLoader.style.display = 'none';
            this.showToast('Authorization header added successfully!', 'success');
            
            // Reset after 3 seconds
            setTimeout(() => {
                authEmoji.textContent = '🔓';
                authEmoji.classList.remove('success');
                authEmoji.setAttribute('aria-label', 'Unlocked');
                if (buttonText) buttonText.textContent = 'Get Header';
                this.updateAuthEmoji(); // Update emoji based on current headers
            }, 3000);
            
            // Clear auth in progress flag
            this._authInProgress = false;
        } else {
            // Invalid result - show error
            this._handleAuthTestError(
                new Error('Invalid auth result format. Expected: { headerName: string, headerValue: string }'),
                authButton, 
                authEmoji
            );
        }
    },
    
    // Handle auth test error
    _handleAuthTestError: function(error, authButton, authEmoji) {
        const buttonText = authButton.querySelector('.auth-card-button-text');
        const buttonLoader = authButton.querySelector('.auth-prompt-button-loader');
        
        // Sanitize error before logging (always sanitize, even if AuthHandler is absent)
        let sanitizedError;
        if (window.AuthHandler && typeof window.AuthHandler.sanitizeError === 'function') {
            sanitizedError = window.AuthHandler.sanitizeError(error);
        } else {
            // Inline sanitization when AuthHandler is not available
            const message = error?.message || String(error || 'Unknown error');
            sanitizedError = message
                .replace(/Bearer\s+[\w-]+/gi, 'Bearer [REDACTED]')
                .replace(/token[=:]\s*[\w-]+/gi, 'token=[REDACTED]')
                .replace(/password[=:]\s*[^\s]+/gi, 'password=[REDACTED]')
                .replace(/api[_-]?key[=:]\s*[\w-]+/gi, 'api_key=[REDACTED]');
        }
        console.error('Auth test failed:', sanitizedError);
        
        authEmoji.textContent = '🔒';
        authEmoji.classList.remove('unlocking', 'success');
        authEmoji.setAttribute('aria-label', 'Locked');
        authButton.disabled = false;
        authButton.classList.remove('loading');
        if (buttonText) buttonText.textContent = 'Try Again';
        if (buttonLoader) buttonLoader.style.display = 'none';
        this.showToast('Authentication test failed: ' + sanitizedError, 'error');
        
        // Reset after 3 seconds
        setTimeout(() => {
            if (buttonText) buttonText.textContent = 'Get Header';
            this.updateAuthEmoji();
        }, 3000);
        
        // Clear auth in progress flag
        this._authInProgress = false;
    },
    
    // Update auth emoji based on stored header or function availability
    updateAuthEmoji: function() {
        const authEmoji = document.getElementById('settingsAuthEmoji');
        if (!authEmoji) return;
        
        // Check if there's an authorization header in the headers section
        const headerItems = document.querySelectorAll('#settingsHeaders .header-item');
        let hasAuthHeader = false;
        
        headerItems.forEach(item => {
            const nameInput = item.querySelector('.name-input');
            const valueInput = item.querySelector('.value-input');
            const normalizedHeader = nameInput && typeof nameInput.value === 'string'
                ? nameInput.value.trim().toLowerCase()
                : null;
            if (normalizedHeader === 'authorization' && 
                valueInput && valueInput.value.trim()) {
                hasAuthHeader = true;
            }
        });
        
        // Update emoji based on whether header exists
        if (hasAuthHeader) {
            authEmoji.textContent = '🔓'; // Unlocked if header exists
            authEmoji.classList.remove('success', 'unlocking');
            authEmoji.setAttribute('aria-label', 'Unlocked');
        } else if (typeof window.getAuthHeader === 'function') {
            authEmoji.textContent = '🔒'; // Locked if function exists but no header yet
            authEmoji.classList.remove('success', 'unlocking');
            authEmoji.setAttribute('aria-label', 'Locked');
        } else {
            authEmoji.textContent = '🔒'; // Locked if no function
            authEmoji.classList.remove('success', 'unlocking');
            authEmoji.setAttribute('aria-label', 'Locked');
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
    
    // Create header item element (using DOM creation to prevent XSS)
    createHeaderItem: function(name = '', value = '') {
        const headerItem = document.createElement('div');
        headerItem.className = 'header-item';
        
        // Create header-inputs container
        const headerInputs = document.createElement('div');
        headerInputs.className = 'header-inputs';
        
        // Create name input
        const nameInput = document.createElement('input');
        nameInput.type = 'text';
        nameInput.className = 'modern-input name-input';
        nameInput.placeholder = 'Header name';
        nameInput.setAttribute('list', 'settingsHeaderSuggestions');
        nameInput.value = name;
        nameInput.addEventListener('input', () => {
            // Keep auth indicator in sync with header name edits
            if (window.SettingsManager && typeof window.SettingsManager.updateAuthEmoji === 'function') {
                window.SettingsManager.updateAuthEmoji();
            }
        });
        
        // Create value input
        const valueInput = document.createElement('input');
        valueInput.type = 'text';
        valueInput.className = 'modern-input value-input';
        valueInput.placeholder = 'Header value';
        valueInput.value = value;
        valueInput.addEventListener('input', () => {
            // Keep auth indicator in sync with header value edits
            if (window.SettingsManager && typeof window.SettingsManager.updateAuthEmoji === 'function') {
                window.SettingsManager.updateAuthEmoji();
            }
        });
        
        // Create remove button
        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-btn';
        removeBtn.setAttribute('aria-label', 'Remove header');
        
        // Create icon span
        const iconSpan = document.createElement('span');
        iconSpan.className = 'icon';
        iconSpan.textContent = '✕';
        
        // Append icon to button
        removeBtn.appendChild(iconSpan);
        
        // Attach click handler with addEventListener
        removeBtn.addEventListener('click', () => {
            SettingsManager.removeHeaderField(removeBtn);
        });
        
        // Append inputs and button to header-inputs
        headerInputs.appendChild(nameInput);
        headerInputs.appendChild(valueInput);
        headerInputs.appendChild(removeBtn);
        
        // Append header-inputs to header-item
        headerItem.appendChild(headerInputs);
        
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
            
            // After any removal/clear, recompute auth emoji state
            this.updateAuthEmoji();
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
            
            // Close modal on Escape key (with stored handler to prevent duplicates)
            if (!this._onKeydown) {
                this._onKeydown = function(e) {
                    if (e.key === 'Escape' && modal && modal.classList.contains('show')) {
                        SettingsManager.closeSettingsModal();
                    }
                }.bind(this);
                document.addEventListener('keydown', this._onKeydown);
            }
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
