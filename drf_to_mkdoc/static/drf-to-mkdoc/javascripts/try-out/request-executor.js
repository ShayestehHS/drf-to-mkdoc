// Request execution functionality
const RequestExecutor = {
    async executeRequest() {
        const executeBtn = document.getElementById('executeBtn');
        if (!executeBtn) return;

        // Validate required parameters
        const emptyParams = FormManager.validateRequiredParams();
        if (emptyParams.length > 0) {
            // Switch to parameters tab if we're on a different tab
            const activeTab = document.querySelector('.try-out-form .tab.active');
            if (activeTab && activeTab.getAttribute('data-tab') !== 'parameters') {
                const parametersTab = document.querySelector('.try-out-form .tab[data-tab="parameters"]');
                if (parametersTab) {
                    TabManager.switchTab(parametersTab);
                }
            }
            
            this.showValidationError(`Please fill in the required parameters: ${emptyParams.join(', ')}`);
            return;
        }

        // Show loading state
        this.setLoadingState(executeBtn, true);

        try {
            const startTime = Date.now();
            const url = FormManager.buildRequestUrl();
            const headers = FormManager.getRequestHeaders();
            const body = FormManager.getRequestBody();
            const method = document.querySelector('.try-out-form')?.getAttribute('data-method') || 'GET';

            const requestOptions = {
                method: method.toUpperCase(),
                headers: headers
            };

            // Add body for non-GET requests
            if (body && !['GET', 'HEAD'].includes(method.toUpperCase())) {
                if (typeof body === 'string') {
                    requestOptions.body = body;
                } else {
                    requestOptions.body = JSON.stringify(body);
                    if (!headers['Content-Type']) {
                        requestOptions.headers['Content-Type'] = 'application/json';
                    }
                }
            }

            const response = await fetch(url, requestOptions);
            const responseTime = Date.now() - startTime;
            const responseText = await response.text();

            ModalManager.showResponseModal(response.status, responseText, responseTime);

        } catch (error) {
            let errorMessage = error.message || 'Unknown error occurred';
            ModalManager.showResponseModal('Error', errorMessage);
        } finally {
            this.setLoadingState(executeBtn, false);
        }
    },

    setLoadingState(button, loading) {
        button.disabled = loading;
        button.innerHTML = '';
        
        if (loading) {
            const spinner = document.createElement('div');
            spinner.className = 'spinner';
            const text = document.createTextNode(' Sending...');
            button.appendChild(spinner);
            button.appendChild(text);
        } else {
            const playIcon = document.createElement('span');
            playIcon.textContent = '▶';
            const text = document.createTextNode(' Execute Request');
            button.appendChild(playIcon);
            button.appendChild(text);
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

// Global function for onclick handlers
window.executeRequest = () => RequestExecutor.executeRequest();

// Export for global access
window.RequestExecutor = RequestExecutor;
