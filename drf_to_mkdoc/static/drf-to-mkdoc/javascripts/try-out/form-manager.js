// Form management functionality
const FormManager = {
    // Initialize form functionality
    init: function() {
        this.setupEventListeners();
        this.setupFormValidation();
        this.initializeRequestBody();
    },

    initializeRequestBody: function() {
        const requestExample = document.querySelector('.request-example');
        const requestBody = document.getElementById('requestBody');
        let example = null;
        if (requestExample && requestBody) {
            try {
                example = requestExample.getAttribute('data-example');
                if (example) {
                    // Remove markdown code block syntax if present
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
        
        headerItem.innerHTML = `
            <div class="header-inputs">
                <input type="text" 
                       class="modern-input name-input" 
                       placeholder="Header name"
                       list="headerSuggestions">
                <input type="text" 
                       class="modern-input value-input" 
                       placeholder="Header value">
                <button class="remove-btn" 
                        aria-label="Remove header">
                    <span class="icon">✕</span>
                </button>
            </div>
        `;
        
        // Attach the removal handler programmatically
        const removeBtn = headerItem.querySelector('.remove-btn');
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
            button.closest('.parameter-item, .header-item').remove();
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
        const headerInputs = document.querySelectorAll('#requestHeaders .kv-item');
        
        headerInputs.forEach(item => {
            const inputs = item.querySelectorAll('input');
            if (inputs.length === 2) {
                const name = inputs[0].value.trim();
                const value = inputs[1].value.trim();
                if (name && value) {
                    headers[name] = value;
                }
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
