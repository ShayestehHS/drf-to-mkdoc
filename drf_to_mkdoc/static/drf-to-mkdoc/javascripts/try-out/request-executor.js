// Request execution functionality
const RequestExecutor = {
    // Show validation error in the appropriate section
    showValidationError: function(message, section) {
        let errorContainer;
        
        if (section === 'json') {
            // Show error in JSON validation status
            errorContainer = document.querySelector('.validation-status');
            if (errorContainer) {
                errorContainer.textContent = '✗ ' + message;
                errorContainer.className = 'validation-status invalid';
            }
        } else if (section === 'parameters') {
            // Show error in parameters section
            const parametersTab = document.querySelector('[data-tab="parameters"]');
                if (parametersTab) {
                window.TabManager?.switchTab(parametersTab);
            }
            
            // Create or update error message
            errorContainer = document.querySelector('#parametersError');
            if (!errorContainer) {
                errorContainer = document.createElement('div');
                errorContainer.id = 'parametersError';
                errorContainer.className = 'error-message';
                const parametersSection = document.querySelector('#parametersTab .form-section');
                if (parametersSection) {
                    parametersSection.insertBefore(errorContainer, parametersSection.firstChild);
                }
            }
            errorContainer.textContent = message;
            errorContainer.style.display = 'block';
        }
    },

    // Clear validation errors
    clearValidationErrors: function() {
        // Clear JSON validation status
        const jsonStatus = document.querySelector('.validation-status');
        if (jsonStatus) {
            jsonStatus.textContent = '';
            jsonStatus.className = 'validation-status';
        }

        // Clear parameters error
        const paramsError = document.querySelector('#parametersError');
        if (paramsError) {
            paramsError.style.display = 'none';
        }

        // Clear all input validation states
        document.querySelectorAll('.error').forEach(el => {
            el.classList.remove('error');
        });
        document.querySelectorAll('.validation-message').forEach(msg => {
            msg.style.display = 'none';
        });
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

        // Add default headers if not already set
        if (!headers['Accept']) {
            headers['Accept'] = '*/*';
        }
        if (!headers['User-Agent']) {
            headers['User-Agent'] = navigator.userAgent;
        }
        if (!headers['Accept-Language']) {
            headers['Accept-Language'] = navigator.language || 'en-US,en;q=0.9';
        }
        if (!headers['Accept-Encoding']) {
            headers['Accept-Encoding'] = 'gzip, deflate, br';
        }
        if (!headers['Connection']) {
            headers['Connection'] = 'keep-alive';
        }
        if (!headers['Cache-Control']) {
            headers['Cache-Control'] = 'no-cache';
        }

        // Add cookies if available
        if (document.cookie) {
            headers['Cookie'] = document.cookie;
        }

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
        const requiredInputs = document.querySelectorAll('#pathParams input[required]');
        let emptyFields = [];
        
        requiredInputs.forEach(input => {
            if (!input.value.trim()) {
                const paramName = input.dataset.param || 'parameter';
                emptyFields.push(paramName);
                this.validateInput(input);
            }
        });

        if (emptyFields.length > 0) {
            this.showValidationError(`Please fill in required fields: ${emptyFields.join(', ')}`, 'parameters');
            return;
        }

        // Show loading state
        this.setLoadingState(executeBtn, true);

        const startTime = Date.now();
        
        try {
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

            // Convert response headers to object
            const responseHeaders = {};
            response.headers.forEach((value, key) => {
                // Handle multiple headers with the same name (like Set-Cookie)
                if (responseHeaders[key]) {
                    if (Array.isArray(responseHeaders[key])) {
                        responseHeaders[key].push(value);
                    } else {
                        responseHeaders[key] = [responseHeaders[key], value];
                    }
                } else {
                    responseHeaders[key] = value;
                }
            });

            ModalManager.showResponseModal(response.status, responseText, responseTime, responseHeaders, requestData.headers);

        } catch (error) {
            console.error('Request failed:', error);
            const requestData = this.buildRequestData();
            const errorTime = Date.now() - startTime;
            ModalManager.showResponseModal('Error', error.message || 'Unknown error occurred', errorTime, null, requestData.headers);
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
            this.showValidationError('Invalid JSON format', 'json');
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

    // This method is now handled by the main showValidationError method above
};

// Global functions for onclick handlers and backward compatibility
window.executeRequest = () => RequestExecutor.executeRequest();
window.formatJson = () => RequestExecutor.formatJson();
window.validateJson = () => RequestExecutor.validateJson();

// Export for global access
window.RequestExecutor = RequestExecutor;
