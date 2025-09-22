// Request execution functionality
const RequestExecutor = {
    // Toast notification system
    showToast: function(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 10);
        
        // Remove toast
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    // Form validation
    validateInput: function(input) {
        const isValid = input.value.trim() !== '';
        const validationMessage = input.parentElement.querySelector('.validation-message');
        
        if (!isValid) {
            input.classList.add('error');
            if (validationMessage) {
                validationMessage.textContent = 'This field is required';
                validationMessage.style.display = 'block';
            }
        } else {
            input.classList.remove('error');
            if (validationMessage) {
                validationMessage.textContent = '';
                validationMessage.style.display = 'none';
            }
        }
        
        return isValid;
    },

    // Build complete request data
    buildRequestData: function() {
        const baseUrl = document.getElementById('baseUrl')?.value || '';
        const pathDisplay = document.querySelector('.path-display')?.textContent || '';
        
        // Build full URL
        let fullUrl = baseUrl + pathDisplay;
        
        // Replace path parameters
        const pathParams = {};
        document.querySelectorAll('#pathParams input').forEach(input => {
            const param = input.dataset.param;
            if (param && input.value) {
                pathParams[param] = input.value;
                fullUrl = fullUrl.replace(`{${param}}`, encodeURIComponent(input.value));
            }
        });

        // Collect query parameters
        const queryParams = {};
        document.querySelectorAll('#queryParams .parameter-item').forEach(item => {
            const nameInput = item.querySelector('.name-input');
            const valueInput = item.querySelector('.value-input');
            if (nameInput?.value && valueInput?.value) {
                queryParams[nameInput.value] = valueInput.value;
            }
        });

        // Add query parameters to URL
        if (Object.keys(queryParams).length > 0) {
            const queryString = new URLSearchParams(queryParams).toString();
            fullUrl += (fullUrl.includes('?') ? '&' : '?') + queryString;
        }

        // Collect headers
        const headers = {};
        document.querySelectorAll('#requestHeaders .header-item').forEach(item => {
            const nameInput = item.querySelector('.name-input');
            const valueInput = item.querySelector('.value-input');
            if (nameInput?.value && valueInput?.value) {
                headers[nameInput.value] = valueInput.value;
            }
        });

        // Get request body
        const bodyEditor = document.getElementById('requestBody');
        let body = null;
        if (bodyEditor?.value.trim()) {
            try {
                body = JSON.parse(bodyEditor.value);
            } catch (e) {
                body = bodyEditor.value;
            }
        }

        // Get method
        const methodBadge = document.querySelector('.method-badge');
        const method = methodBadge?.dataset.method || 'GET';

        return {
            url: fullUrl,
            method,
            headers,
            body,
            pathParams,
            queryParams
        };
    },
    async executeRequest() {
        const executeBtn = document.querySelector('[data-action="send"], .primary-button, .primary-btn, #executeBtn');
        if (!executeBtn) {
            console.warn('Execute button not found');
            return;
        }

        // Validate required fields
        const requiredInputs = document.querySelectorAll('input[required]');
        let isValid = true;
        
        requiredInputs.forEach(input => {
            if (!this.validateInput(input)) {
                isValid = false;
            }
        });

        if (!isValid) {
            this.showToast('Please fill in all required fields', 'error');
            return;
        }

        // Show loading state
        this.setLoadingState(executeBtn, true);

        try {
            const startTime = Date.now();
            const requestData = this.buildRequestData();
            
            const requestOptions = {
                method: requestData.method.toUpperCase(),
                headers: requestData.headers
            };

            // Add body for non-GET requests
            if (requestData.body && !['GET', 'HEAD'].includes(requestData.method.toUpperCase())) {
                if (typeof requestData.body === 'string') {
                    requestOptions.body = requestData.body;
                } else {
                    requestOptions.body = JSON.stringify(requestData.body);
                    if (!requestData.headers['Content-Type']) {
                        requestOptions.headers['Content-Type'] = 'application/json';
                    }
                }
            }

            // Show response section
            const responseSection = document.querySelector('.response-section');
            if (responseSection) {
                responseSection.hidden = false;
            }

            const response = await fetch(requestData.url, requestOptions);
            const responseTime = Date.now() - startTime;
            const responseText = await response.text();

            ModalManager.showResponseModal(response.status, responseText, responseTime);
            this.showToast('Request executed successfully');

        } catch (error) {
            console.error('Request failed:', error);
            this.showToast('Request failed: ' + error.message, 'error');
            ModalManager.showResponseModal('Error', error.message || 'Unknown error occurred');
        } finally {
            this.setLoadingState(executeBtn, false);
        }
    },

    setLoadingState(button, loading) {
        button.disabled = loading;
        
        if (loading) {
            button.classList.add('loading');
            const spinner = button.querySelector('.loading-spinner');
            if (spinner) {
                spinner.style.display = 'inline-block';
            }
        } else {
            button.classList.remove('loading');
            const spinner = button.querySelector('.loading-spinner');
            if (spinner) {
                spinner.style.display = 'none';
            }
        }
    },

    // JSON formatting and validation
    formatJson: function() {
        const editor = document.getElementById('requestBody');
        if (!editor) return;

        try {
            const formatted = JSON.stringify(JSON.parse(editor.value), null, 2);
            editor.value = formatted;
            this.validateJson();
        } catch (e) {
            this.showToast('Invalid JSON format', 'error');
        }
    },

    validateJson: function() {
        const editor = document.getElementById('requestBody');
        const status = document.querySelector('.validation-status');
        
        if (!editor || !status) return true;

        if (!editor.value.trim()) {
            status.textContent = '';
            status.className = 'validation-status';
            return true;
        }

        try {
            JSON.parse(editor.value);
            status.textContent = '✓ Valid JSON';
            status.className = 'validation-status valid';
            return true;
        } catch (e) {
            status.textContent = '✗ ' + e.message;
            status.className = 'validation-status invalid';
            return false;
        }
    },

    showValidationError(message) {
        // Create or update validation error display
        let errorDiv = document.getElementById('validation-error');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'validation-error';
            errorDiv.className = 'error-message show';
            
            const executeBtn = document.getElementById('executeBtn');
            if (executeBtn) {
                executeBtn.parentNode.insertBefore(errorDiv, executeBtn);
            }
        }
        
        errorDiv.textContent = message;
        errorDiv.classList.add('show');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorDiv.classList.remove('show');
        }, 5000);
    }
};

// Global functions for onclick handlers and backward compatibility
window.executeRequest = () => RequestExecutor.executeRequest();
window.formatJson = () => RequestExecutor.formatJson();
window.validateJson = () => RequestExecutor.validateJson();

// Export for global access
window.RequestExecutor = RequestExecutor;
