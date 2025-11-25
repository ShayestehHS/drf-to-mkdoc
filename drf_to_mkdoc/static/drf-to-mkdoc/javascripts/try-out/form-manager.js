// Form management functionality
const FormManager = {
    _authButtonHandler: null, // Store handler reference for cleanup
    
    // Initialize form functionality
    init: function() {
        this.setupEventListeners();
        this.setupFormValidation();
        this.initializeRequestBody();
        this.loadSettings();
    },
    
    // Cleanup method to remove event listeners
    cleanup: function() {
        if (this._authButtonHandler) {
            const authButton = document.getElementById('authPromptButton');
            if (authButton) {
                authButton.removeEventListener('click', this._authButtonHandler);
                delete authButton.dataset.handlerAttached;
            }
            this._authButtonHandler = null;
        }
    },
    
    // Load settings and pre-fill form
    loadSettings: function() {
        // Get saved settings if available - try SettingsManager first, then storage as fallback
        let settings = { host: null, headers: {} };
        
        if (window.SettingsManager) {
            settings = window.SettingsManager.getSettings();
        } else {
            // Fallback: read from storage (host from localStorage, headers from sessionStorage)
            try {
                // Get host from localStorage
                const savedHost = localStorage.getItem('drfToMkdocSettings');
                if (savedHost) {
                    const parsed = JSON.parse(savedHost);
                    settings.host = parsed.host || null;
                }
                
                // Get headers from sessionStorage (secure by default)
                const savedHeaders = sessionStorage.getItem('drfToMkdocHeaders');
                if (savedHeaders) {
                    settings.headers = JSON.parse(savedHeaders);
                } else {
                    // Fallback: check localStorage if persistHeaders was enabled
                    if (savedHost) {
                        const parsed = JSON.parse(savedHost);
                        if (parsed.persistHeaders === true && parsed.headers) {
                            settings.headers = parsed.headers;
                        }
                    }
                }
            } catch (e) {
                console.warn('Failed to parse settings from storage:', e);
            }
        }
        
        // Set host in baseUrl input
        const baseUrlInput = document.getElementById('baseUrl');
        if (baseUrlInput) {
            // Priority: settings.host > browser origin > localhost:8000
            if (settings.host && settings.host.trim()) {
                let hostValue = settings.host.trim();
                // Ensure host has protocol (add https:// if missing for secure default)
                if (!hostValue.match(/^https?:\/\//)) {
                    hostValue = 'https://' + hostValue;
                }
                baseUrlInput.value = hostValue;
            } else {
                const browserOrigin = window.location.origin;
                if (browserOrigin) {
                    baseUrlInput.value = browserOrigin;
                } else {
                    baseUrlInput.value = 'http://localhost:8000';
                }
            }
        }
        
        // Add headers from settings - update existing ones or add new ones
        if (settings.headers && Object.keys(settings.headers).length > 0) {
            const headerList = document.querySelector('#requestHeaders .header-list');
            if (headerList) {
                // Create a map of existing headers by name (case-insensitive)
                const existingHeadersMap = new Map();
                headerList.querySelectorAll('.header-item').forEach(item => {
                    const nameInput = item.querySelector('.name-input');
                    const valueInput = item.querySelector('.value-input');
                    if (nameInput && nameInput.value.trim()) {
                        const headerName = nameInput.value.trim();
                        existingHeadersMap.set(headerName.toLowerCase(), {
                            item: item,
                            nameInput: nameInput,
                            valueInput: valueInput
                        });
                    }
                });
                
                // Process headers from settings
                Object.entries(settings.headers).forEach(([name, value]) => {
                    if (!name.trim() || !value || !String(value).trim()) {
                        return; // Skip empty names or values
                    }
                    
                    const normalizedName = name.trim().toLowerCase();
                    const headerValue = String(value).trim();
                    
                    // Check if header already exists (case-insensitive)
                    const existing = existingHeadersMap.get(normalizedName);
                    
                    if (existing) {
                        // Update existing header value
                        if (existing.valueInput) {
                            existing.valueInput.value = headerValue;
                        }
                    } else {
                        // Add new header item
                        const headerItem = this.createHeaderItem();
                        const nameInput = headerItem.querySelector('.name-input');
                        const valueInput = headerItem.querySelector('.value-input');
                        if (nameInput) nameInput.value = name.trim();
                        if (valueInput) valueInput.value = headerValue;
                        headerList.appendChild(headerItem);
                    }
                });
            }
        }
        
        // Show auth prompt if enabled and endpoint requires auth
        this.showAuthPrompt();
    },
    
    // Reset auth prompt to initial state
    resetAuthPromptState: function() {
        const authPromptContainer = document.getElementById('authPromptContainer');
        if (!authPromptContainer) {
            return;
        }
        
        const authPrompt = authPromptContainer.querySelector('.auth-prompt');
        const authButton = document.getElementById('authPromptButton');
        const authEmoji = document.getElementById('authPromptEmoji');
        
        // Reset all visual states
        if (authPrompt) {
            authPrompt.classList.remove('success', 'error', 'fade-out');
        }
        
        if (authButton) {
            authButton.disabled = false;
            authButton.classList.remove('loading');
            const buttonText = authButton.querySelector('.auth-prompt-button-text');
            if (buttonText) {
                buttonText.textContent = 'Get Authorization Header';
            }
            const buttonLoader = authButton.querySelector('.auth-prompt-button-loader');
            if (buttonLoader) {
                buttonLoader.style.display = 'none';
            }
        }
        
        if (authEmoji) {
            authEmoji.textContent = '🔒';
            authEmoji.classList.remove('unlocking', 'success');
            authEmoji.setAttribute('aria-label', 'Locked');
        }
        
        // Reset title and description
        const titleElement = authPrompt?.querySelector('.auth-prompt-title');
        const descriptionText = authPrompt?.querySelector('.auth-prompt-description');
        if (titleElement) {
            titleElement.textContent = 'Authentication Required';
        }
        if (descriptionText) {
            descriptionText.textContent = 'This endpoint requires authentication. Click the button below to automatically generate and add the authorization header.';
        }
    },
    
    // Show authentication prompt if needed
    showAuthPrompt: function() {
        // Always reset state first to ensure clean display
        this.resetAuthPromptState();
        
        const authConfig = window.DRF_TO_MKDOC_AUTH_CONFIG;
        if (!authConfig || !authConfig.enabled) {
            const authPromptContainer = document.getElementById('authPromptContainer');
            if (authPromptContainer) {
                authPromptContainer.style.display = 'none';
            }
            return;
        }
        
        // Check if endpoint requires authentication
        const tryOutForm = document.querySelector('.try-out-form');
        const authRequired = authConfig.authRequired || 
            (tryOutForm && tryOutForm.dataset.auth === 'true');
        
        if (!authRequired) {
            const authPromptContainer = document.getElementById('authPromptContainer');
            if (authPromptContainer) {
                authPromptContainer.style.display = 'none';
            }
            return;
        }
        
        // Check if getAuthHeader function exists
        if (typeof window.getAuthHeader !== 'function') {
            console.warn('Auto-auth enabled but getAuthHeader function not found');
            const authPromptContainer = document.getElementById('authPromptContainer');
            if (authPromptContainer) {
                authPromptContainer.style.display = 'none';
            }
            return;
        }
        
        // Check if auth header already exists
        const headerList = document.querySelector('#requestHeaders .header-list');
        if (headerList) {
            const existingHeaders = headerList.querySelectorAll('.header-item');
            let hasAuthHeader = false;
            
            existingHeaders.forEach(item => {
                const nameInput = item.querySelector('.name-input');
                const normalizedHeader =
                    nameInput && typeof nameInput.value === 'string'
                        ? nameInput.value.trim().toLowerCase()
                        : null;
                if (normalizedHeader === 'authorization') {
                    const valueInput = item.querySelector('.value-input');
                    if (valueInput && valueInput.value.trim()) {
                        hasAuthHeader = true;
                    }
                }
            });
            
            // If header already exists with a value, don't show prompt
            if (hasAuthHeader) {
                const authPromptContainer = document.getElementById('authPromptContainer');
                if (authPromptContainer) {
                    authPromptContainer.style.display = 'none';
                }
                return;
            }
        }
        
        // Show the auth prompt
        const authPromptContainer = document.getElementById('authPromptContainer');
        if (authPromptContainer) {
            authPromptContainer.style.display = 'block';
            
            // Set up button click handler (store reference for cleanup)
            const authButton = document.getElementById('authPromptButton');
            if (authButton && !authButton.dataset.handlerAttached) {
                this._authButtonHandler = () => this.handleAuthButtonClick();
                authButton.addEventListener('click', this._authButtonHandler);
                authButton.dataset.handlerAttached = 'true';
            }
        }
    },
    
    // Handle auth button click
    handleAuthButtonClick: function() {
        const authButton = document.getElementById('authPromptButton');
        const authPrompt = document.querySelector('.auth-prompt');
        const authEmoji = document.getElementById('authPromptEmoji');
        
        if (!authButton || !authPrompt) {
            return;
        }
        
        // Use shared AuthHandler if available, otherwise fall back to old implementation
        if (window.AuthHandler && typeof window.AuthHandler.handleAuth === 'function') {
            // Set loading state and change emoji to unlocking
            authButton.disabled = true;
            authButton.classList.add('loading');
            authPrompt.classList.remove('success', 'error');
            
            if (authEmoji) {
                authEmoji.textContent = '🔓';
                authEmoji.classList.add('unlocking');
                authEmoji.setAttribute('aria-label', 'Unlocking');
            }
            
            const buttonText = authButton.querySelector('.auth-prompt-button-text');
            const buttonLoader = authButton.querySelector('.auth-prompt-button-loader');
            if (buttonText) buttonText.textContent = 'Generating...';
            if (buttonLoader) buttonLoader.style.display = 'inline-block';
            
            try {
                window.AuthHandler.handleAuth({
                    onStart: () => {
                        // Already set loading state above
                    },
                    onSuccess: (result) => {
                        this._handleAuthResult(result, authButton, authPrompt);
                    },
                    onError: (error) => {
                        this._handleAuthError(error, authButton, authPrompt);
                    }
                });
            } catch (error) {
                // Ensure UI state is reset on sync failures
                this._handleAuthError(error, authButton, authPrompt);
            }
        } else {
            // Fallback to old implementation if AuthHandler not available
            this._handleAuthButtonClickLegacy(authButton, authPrompt, authEmoji);
        }
    },
    
    // Legacy implementation (kept for backward compatibility)
    _handleAuthButtonClickLegacy: function(authButton, authPrompt, authEmoji) {
        // Set loading state and change emoji to unlocking
        authButton.disabled = true;
        authButton.classList.add('loading');
        authPrompt.classList.remove('success', 'error');
        
        if (authEmoji) {
            authEmoji.textContent = '🔓';
            authEmoji.classList.add('unlocking');
        }
        
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
                this._handleAuthError(new Error('Authentication timed out'), authButton, authPrompt);
            }
        };
        
        timeoutId = setTimeout(handleTimeout, TIMEOUT_MS);
        
        try {
            // Check if getAuthHeader function exists
            if (typeof window.getAuthHeader !== 'function') {
                clearTimeoutAndComplete();
                throw new Error('getAuthHeader function is not defined. Please configure it in your JavaScript settings.');
            }
            
            // Call the auth function directly (credentials should be handled in the function)
            let authResult = window.getAuthHeader();
            
            // Check if result is null or undefined
            if (!authResult) {
                clearTimeoutAndComplete();
                throw new Error('getAuthHeader function returned null or undefined.');
            }
            
            // Handle async functions (if result is a Promise)
            if (authResult && typeof authResult.then === 'function') {
                // It's a Promise, wait for it
                authResult.then(result => {
                    if (completed) return; // Timeout already handled
                    clearTimeoutAndComplete();
                    
                    // Validate async result
                    if (!result) {
                        this._handleAuthError(new Error('getAuthHeader function returned null or undefined.'), authButton, authPrompt);
                        return;
                    }
                    this._handleAuthResult(result, authButton, authPrompt);
                }).catch(error => {
                    if (completed) return; // Timeout already handled
                    clearTimeoutAndComplete();
                    this._handleAuthError(error, authButton, authPrompt);
                });
                return; // Exit early, result will be handled asynchronously
            }
            
            // Handle synchronous result
            clearTimeoutAndComplete();
            this._handleAuthResult(authResult, authButton, authPrompt);
        } catch (error) {
            if (!completed) {
                clearTimeoutAndComplete();
                this._handleAuthError(error, authButton, authPrompt);
            }
        }
    },
    
    // Handle auth result
    _handleAuthResult: function(result, authButton, authPrompt) {
        const authEmoji = document.getElementById('authPromptEmoji');
        const buttonText = authButton.querySelector('.auth-prompt-button-text');
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
            // Add header to form
            this._addAuthHeaderToForm(result.headerName, result.headerValue);
            
            // Change emoji to success
            if (authEmoji) {
                authEmoji.textContent = '✅';
                authEmoji.classList.remove('unlocking');
                authEmoji.classList.add('success');
                authEmoji.setAttribute('aria-label', 'Authenticated');
            }
            
            // Show success state
            authPrompt.classList.add('success');
            
            // Reset button state after a delay
            if (buttonText) buttonText.textContent = 'Header Added';
            if (buttonLoader) buttonLoader.style.display = 'none';
            
            setTimeout(() => {
                authButton.disabled = false;
                authButton.classList.remove('loading');
                
                // Fade out the prompt after success
                setTimeout(() => {
                    const authPromptContainer = document.getElementById('authPromptContainer');
                    if (authPromptContainer) {
                        authPromptContainer.classList.add('fade-out');
                        setTimeout(() => {
                            authPromptContainer.style.display = 'none';
                            authPromptContainer.classList.remove('fade-out');
                            // Reset emoji for next time
                            if (authEmoji) {
                                authEmoji.textContent = '🔒';
                                authEmoji.classList.remove('success', 'unlocking');
                                authEmoji.setAttribute('aria-label', 'Locked');
                            }
                        }, 300);
                    }
                }, 1500);
            }, 500);
        } else {
            // Invalid result - show error
            this._handleAuthError(
                new Error('Invalid auth result format. Expected: { headerName: string, headerValue: string }'),
                authButton, 
                authPrompt
            );
        }
    },
    
    // Handle auth error
    _handleAuthError: function(error, authButton, authPrompt) {
        const authEmoji = document.getElementById('authPromptEmoji');
        const buttonText = authButton.querySelector('.auth-prompt-button-text');
        const buttonLoader = authButton.querySelector('.auth-prompt-button-loader');
        
        // Sanitize error before logging
        const sanitizedError = window.AuthHandler 
            ? window.AuthHandler.sanitizeError(error)
            : (error?.message || String(error));
        console.error('Failed to get auth header:', sanitizedError);
        
        // Reset emoji back to locked
        if (authEmoji) {
            authEmoji.textContent = '🔒';
            authEmoji.classList.remove('unlocking', 'success');
            authEmoji.setAttribute('aria-label', 'Locked');
        }
        
        // Update button text and hide loader
        if (buttonText) buttonText.textContent = 'Try Again';
        if (buttonLoader) buttonLoader.style.display = 'none';
        
        // Show error state
        authPrompt.classList.add('error');
        authPrompt.classList.remove('success');
        
        // Reset button state
        setTimeout(() => {
            authButton.disabled = false;
            authButton.classList.remove('loading');
            authPrompt.classList.remove('error');
        }, 2000);
    },
    
    // Legacy method for backward compatibility (called from request-executor)
    // Now async to properly handle Promise-based auth functions
    addAutoAuthHeader: async function() {
        // This is now handled by the prompt, but we keep it for compatibility
        // It will be called before request execution to ensure header is present
        const authConfig = window.DRF_TO_MKDOC_AUTH_CONFIG;
        if (!authConfig || !authConfig.enabled) {
            return;
        }
        
        const tryOutForm = document.querySelector('.try-out-form');
        const authRequired = authConfig.authRequired || 
            (tryOutForm && tryOutForm.dataset.auth === 'true');
        
        if (!authRequired) {
            return;
        }
        
        // Check if header already exists
        const headerList = document.querySelector('#requestHeaders .header-list');
        if (headerList) {
            const existingHeaders = headerList.querySelectorAll('.header-item');
            let hasAuthHeader = false;
            
            existingHeaders.forEach(item => {
                const nameInput = item.querySelector('.name-input');
                const normalizedHeader =
                    nameInput && typeof nameInput.value === 'string'
                        ? nameInput.value.trim().toLowerCase()
                        : null;
                if (normalizedHeader === 'authorization') {
                    hasAuthHeader = true;
                }
            });
            
            // If header doesn't exist, try to add it (user might have clicked the prompt)
            if (!hasAuthHeader && typeof window.getAuthHeader === 'function') {
                try {
                    let authResult = window.getAuthHeader();
                    if (authResult && typeof authResult.then === 'function') {
                        // Wait for Promise to resolve
                        authResult = await authResult;
                    }
                    
                    if (authResult && authResult.headerName && authResult.headerValue) {
                        this._addAuthHeaderToForm(authResult.headerName, authResult.headerValue);
                    }
                } catch (error) {
                    // Sanitize error before logging
                    const sanitizedError = window.AuthHandler 
                        ? window.AuthHandler.sanitizeError(error)
                        : (error?.message || 'Unknown error');
                    console.error('Failed to add auth header:', sanitizedError);
                }
            }
        }
    },
    
    // Helper function to add auth header to form
    _addAuthHeaderToForm: function(headerName, headerValue) {
        const headerList = document.querySelector('#requestHeaders .header-list');
        if (!headerList) {
            return;
        }
        
        // Check if header already exists (case-insensitive)
        const existingHeaders = headerList.querySelectorAll('.header-item');
        let headerExists = false;
        
        const normalizedTargetName =
            typeof headerName === 'string' ? headerName.trim().toLowerCase() : '';
        const sanitizedHeaderName =
            typeof headerName === 'string' ? headerName.trim() : headerName;

        existingHeaders.forEach(item => {
            const nameInput = item.querySelector('.name-input');
            const normalizedExisting =
                nameInput && typeof nameInput.value === 'string'
                    ? nameInput.value.trim().toLowerCase()
                    : null;
            if (normalizedExisting === normalizedTargetName) {
                // Update existing header
                const valueInput = item.querySelector('.value-input');
                if (valueInput) {
                    valueInput.value = headerValue;
                }
                headerExists = true;
            }
        });
        
        if (!headerExists) {
            // Add new header
            const headerItem = this.createHeaderItem();
            const nameInput = headerItem.querySelector('.name-input');
            const valueInput = headerItem.querySelector('.value-input');
            if (nameInput && sanitizedHeaderName) {
                nameInput.value = sanitizedHeaderName;
            }
            if (valueInput) valueInput.value = headerValue;
            headerList.appendChild(headerItem);
        }
    },

    initializeRequestBody: function() {
        // Get all request examples (support multiple examples)
        const requestExamples = document.querySelectorAll('.request-example');
        const requestBody = document.getElementById('requestBody');
        
        // Use the first example (index 0) if multiple exist
        const requestExample = requestExamples.length > 0 ? requestExamples[0] : null;
        
        if (requestExample && requestBody) {
            let example = null;
            try {
                example = requestExample.getAttribute('data-example');
                if (example) {
                    // Remove markdown code block syntax if present (for backward compatibility)
                    example = example.replace(/^```json\n/, '').replace(/```$/, '');
                    // Remove any leading/trailing whitespace
                    example = example.trim();
                    
                    // Try to parse and format the JSON
                    const formattedJson = JSON.stringify(JSON.parse(example), null, 2);
                    requestBody.value = formattedJson;
                    
                    // Validate the JSON after setting it
                    if (window.RequestExecutor) {
                        window.RequestExecutor.validateJson();
                    }
                }
            } catch (e) {
                console.warn('Failed to parse request example:', e);
                // If parsing fails, try to at least show the raw example
                if (example) {
                    requestBody.value = example;
                }
            }
        }
    },

    setupEventListeners: function() {
        // Form reset functionality
        const resetButtons = document.querySelectorAll('[data-action="reset"], .secondary-btn, .secondary-button');
        resetButtons.forEach(btn => {
            if (btn.textContent.toLowerCase().includes('reset')) {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.resetForm();
                });
            }
        });

        // Parameter filtering
        const searchInput = document.querySelector('.parameter-search');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce((e) => {
                this.filterParameters(e.target.value);
            }, 300));
        }

        // Copy URL functionality
        const copyBtn = document.querySelector('.copy-btn');
        if (copyBtn) {
            copyBtn.addEventListener('click', () => this.copyToClipboard());
        }

        // JSON validation on input
        const editor = document.getElementById('requestBody');
        if (editor) {
            editor.addEventListener('input', this.debounce(() => {
                if (window.RequestExecutor) {
                    window.RequestExecutor.validateJson();
                }
            }, 500));
        }

        // Format and validate buttons
        const formatBtn = document.querySelector('.format-btn');
        const validateBtn = document.querySelector('.validate-btn');
        
        if (formatBtn) {
            formatBtn.addEventListener('click', () => {
                if (window.RequestExecutor) {
                    window.RequestExecutor.formatJson();
                }
            });
        }
        if (validateBtn) {
            validateBtn.addEventListener('click', () => {
                if (window.RequestExecutor) {
                    window.RequestExecutor.validateJson();
                }
            });
        }
    },

    setupFormValidation: function() {
        // Add validation to required inputs
        const requiredInputs = document.querySelectorAll('input[required]');
        requiredInputs.forEach(input => {
            input.addEventListener('blur', () => {
                if (window.RequestExecutor) {
                    window.RequestExecutor.validateInput(input);
                }
            });
            input.addEventListener('input', () => this.clearValidationError(input));
        });
    },

    clearValidationError: function(input) {
        input.classList.remove('error');
        const validationMessage = input.parentElement.querySelector('.validation-message');
        if (validationMessage) {
            validationMessage.textContent = '';
            validationMessage.style.display = 'none';
        }
    },

    // Debounce utility function
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    addQueryParam: function(paramName) {
        const container = document.querySelector('#queryParams .parameter-list');
        if (!container) return;

        const paramItem = this.createParameterItem();
        container.appendChild(paramItem);
        
        // If a parameter name was provided, set it
        const nameInput = paramItem.querySelector('.name-input');
        if (nameInput && paramName) {
            nameInput.value = paramName;
            
            // Focus on the value input instead
            const valueInput = paramItem.querySelector('.value-input');
            if (valueInput) {
                valueInput.focus();
            }
        } else if (nameInput) {
            // Otherwise focus on the name input
            nameInput.focus();
        }

        // Setup suggestions for new input if available
        if (window.TryOutSuggestions) {
            setTimeout(() => {
                window.TryOutSuggestions.setupExistingInputs();
            }, 10);
        }
        
        return paramItem;
    },

    createParameterItem: function() {
        const paramItem = document.createElement('div');
        paramItem.className = 'parameter-item';
        
        paramItem.innerHTML = `
            <div class="parameter-inputs">
                <input type="text" 
                       class="modern-input name-input" 
                       placeholder="Parameter name"
                       list="paramSuggestions">
                <input type="text" 
                       class="modern-input value-input" 
                       placeholder="Value">
                <button class="remove-btn" 
                        onclick="FormManager.removeKvItem(this)"
                        aria-label="Remove parameter">
                    <span class="icon">✕</span>
                </button>
            </div>
        `;
        
        return paramItem;
    },

    addHeader: function() {
        const container = document.querySelector('#requestHeaders .header-list');
        if (!container) return;

        const headerItem = this.createHeaderItem();
        container.appendChild(headerItem);
        
        // Focus on the first input
        const firstInput = headerItem.querySelector('.name-input');
        if (firstInput) {
            firstInput.focus();
        }
    },

    createHeaderItem: function() {
        const headerItem = document.createElement('div');
        headerItem.className = 'header-item';
        
        const headerInputs = document.createElement('div');
        headerInputs.className = 'header-inputs';
        
        const nameInput = document.createElement('input');
        nameInput.type = 'text';
        nameInput.className = 'modern-input name-input';
        nameInput.placeholder = 'Header name';
        nameInput.setAttribute('list', 'headerSuggestions');
        
        const valueInput = document.createElement('input');
        valueInput.type = 'text';
        valueInput.className = 'modern-input value-input';
        valueInput.placeholder = 'Header value';
        
        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-btn';
        removeBtn.setAttribute('aria-label', 'Remove header');
        
        const iconSpan = document.createElement('span');
        iconSpan.className = 'icon';
        iconSpan.textContent = '✕';
        
        removeBtn.appendChild(iconSpan);
        
        headerInputs.appendChild(nameInput);
        headerInputs.appendChild(valueInput);
        headerInputs.appendChild(removeBtn);
        
        headerItem.appendChild(headerInputs);
        
        removeBtn.addEventListener('click', (e) => FormManager.removeKvItem(e.currentTarget));
        
        return headerItem;
    },

    createKvItem: function(namePlaceholder, valuePlaceholder, removable = true) {
        const kvItem = document.createElement('div');
        kvItem.className = 'kv-item';

        const nameInput = document.createElement('input');
        nameInput.type = 'text';
        nameInput.placeholder = namePlaceholder;

        const valueInput = document.createElement('input');
        valueInput.type = 'text';
        valueInput.placeholder = valuePlaceholder;

        kvItem.appendChild(nameInput);
        kvItem.appendChild(valueInput);

        if (removable) {
            const removeBtn = document.createElement('button');
            removeBtn.className = 'remove-btn';
            removeBtn.textContent = '✕';
            removeBtn.addEventListener('click', () => this.removeKvItem(removeBtn));
            kvItem.appendChild(removeBtn);
        }

        return kvItem;
    },

    removeKvItem: function(button) {
        if (button && button.closest('.parameter-item, .header-item')) {
            const item = button.closest('.parameter-item, .header-item');
            const isHeaderItem = item.classList.contains('header-item');
            
            // Check if we're removing an authorization header
            let wasAuthHeader = false;
            if (isHeaderItem) {
                const nameInput = item.querySelector('.name-input');
                const normalizedHeader =
                    nameInput && typeof nameInput.value === 'string'
                        ? nameInput.value.trim().toLowerCase()
                        : null;
                if (normalizedHeader === 'authorization') {
                    wasAuthHeader = true;
                }
            }
            
            // Remove the item
            item.remove();
            
            // If auth header was removed, show the prompt again
            if (wasAuthHeader) {
                setTimeout(() => {
                    this.showAuthPrompt();
                }, 100);
            }
        }
    },

    validateRequiredParams: function() {
        const requiredInputs = document.querySelectorAll('#pathParams input[required]');
        const errors = [];

        requiredInputs.forEach(input => {
            const errorElement = input.parentElement.querySelector('.error-message');
            
            if (!input.value.trim()) {
                const paramName = input.getAttribute('data-param');
                errors.push(paramName);
                input.classList.add('error');
                
                if (errorElement) {
                    errorElement.textContent = `${paramName} is required`;
                    errorElement.classList.add('show');
                }
                
                // Remove error on input
                input.addEventListener('input', () => {
                    input.classList.remove('error');
                    if (errorElement) {
                        errorElement.classList.remove('show');
                    }
                }, { once: true });
            } else {
                input.classList.remove('error');
                if (errorElement) {
                    errorElement.classList.remove('show');
                }
            }
        });

        return errors;
    },

    addSuggestion: function(input, suggestion) {
        input.value = suggestion;
        input.focus();
    },

    buildRequestUrl: function() {
        const baseUrl = document.getElementById('baseUrl').value.trim();
        const pathDisplay = document.querySelector('.path-display').textContent.trim();
        
        let url = baseUrl + pathDisplay;
        
        // Replace path parameters
        const pathParams = document.querySelectorAll('#pathParams input');
        pathParams.forEach(input => {
            const paramName = input.getAttribute('data-param');
            const paramValue = input.value.trim();
            if (paramName && paramValue) {
                url = url.replace(`{${paramName}}`, encodeURIComponent(paramValue));
            }
        });
        
        // Add query parameters
        const queryParams = [];
        const queryInputs = document.querySelectorAll('#queryParams .kv-item');
        queryInputs.forEach(item => {
            const inputs = item.querySelectorAll('input');
            if (inputs.length === 2) {
                const name = inputs[0].value.trim();
                const value = inputs[1].value.trim();
                if (name && value) {
                    queryParams.push(`${encodeURIComponent(name)}=${encodeURIComponent(value)}`);
                }
            }
        });
        
        if (queryParams.length > 0) {
            url += '?' + queryParams.join('&');
        }
        
        return url;
    },

    getRequestHeaders: function() {
        const headers = {};
        const headerItems = document.querySelectorAll('#requestHeaders .header-item');
        
        headerItems.forEach(item => {
            const nameInput = item.querySelector('.name-input');
            const valueInput = item.querySelector('.value-input');
            if (!nameInput || !valueInput) {
                return;
            }
            
            const name = nameInput.value.trim();
            const value = valueInput.value.trim();
            if (name && value) {
                headers[name] = value;
            }
        });
        
        return headers;
    },

    getRequestBody: function() {
        const bodyTextarea = document.getElementById('requestBody');
        if (bodyTextarea && bodyTextarea.value.trim()) {
            try {
                return JSON.parse(bodyTextarea.value);
            } catch (e) {
                return bodyTextarea.value;
            }
        }
        return null;
    },

    // Form reset functionality
    resetForm: function() {
        const form = document.querySelector('.try-out-form');
        if (form) {
            // Reset text inputs except base URL
            form.querySelectorAll('input[type="text"], textarea').forEach(input => {
                if (!input.id || input.id !== 'baseUrl') {
                    input.value = '';
                }
            });

            // Reset validation states
            form.querySelectorAll('.error').forEach(el => {
                el.classList.remove('error');
            });

            form.querySelectorAll('.validation-message').forEach(msg => {
                msg.textContent = '';
                msg.style.display = 'none';
            });

            // Reset JSON editor
            const editor = document.getElementById('requestBody');
            if (editor) {
                editor.value = '';
            }

            // Reset validation status
            const status = document.querySelector('.validation-status');
            if (status) {
                status.textContent = '';
                status.className = 'validation-status';
            }

            // Reset auth prompt state
            this.resetAuthPromptState();
            
            // Show auth prompt again if needed (after reset, headers are cleared)
            setTimeout(() => {
                this.showAuthPrompt();
            }, 100);

            // Reset to first tab
            const firstTab = document.querySelector('.tab');
            if (firstTab && window.TabManager) {
                window.TabManager.switchTab(firstTab);
            }

            // Clear any error messages
            if (window.RequestExecutor) {
                window.RequestExecutor.clearValidationErrors();
            }
        }
    },

    // Parameter filtering
    filterParameters: function(query) {
        const items = document.querySelectorAll('.parameter-item');
        query = query.toLowerCase();

        items.forEach(item => {
            const nameInput = item.querySelector('.name-input');
            const name = nameInput?.value.toLowerCase() || '';

            if (name.includes(query) || query === '') {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    },

    // Copy URL to clipboard
    copyToClipboard: function() {
        const baseUrl = document.getElementById('baseUrl')?.value || '';
        const pathDisplay = document.querySelector('.path-display')?.textContent || '';
        const url = baseUrl + pathDisplay;

        navigator.clipboard.writeText(url).then(() => {
            // Show copy success in the URL preview
            const copyBtn = document.querySelector('.copy-btn');
            if (copyBtn) {
                const originalText = copyBtn.innerHTML;
                copyBtn.innerHTML = '<span class="icon">✓</span>';
                setTimeout(() => {
                    copyBtn.innerHTML = originalText;
                }, 2000);
            }
        }).catch(() => {
            console.error('Failed to copy URL');
        });
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    FormManager.init();
});

// Global functions for backward compatibility
window.resetForm = () => FormManager.resetForm();
window.filterParameters = (query) => FormManager.filterParameters(query);
window.copyToClipboard = () => FormManager.copyToClipboard();

// Export for global access
window.FormManager = FormManager;
