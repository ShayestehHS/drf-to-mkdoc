// Form management functionality
const FormManager = {
    addQueryParam: function() {
        const container = document.getElementById('queryParams');
        if (!container) return;

        const kvItem = this.createKvItem('Parameter name', 'Parameter value', true);
        container.appendChild(kvItem);
        
        // Focus on the first input
        const firstInput = kvItem.querySelector('input');
        if (firstInput) {
            firstInput.focus();
        }
    },

    addHeader: function() {
        const container = document.getElementById('requestHeaders');
        if (!container) return;

        const kvItem = this.createKvItem('Header name', 'Header value', true);
        container.appendChild(kvItem);
        
        // Focus on the first input
        const firstInput = kvItem.querySelector('input');
        if (firstInput) {
            firstInput.focus();
        }
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
        if (button && button.parentElement) {
            button.parentElement.remove();
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
    }
};

// Export for global access
window.FormManager = FormManager;
