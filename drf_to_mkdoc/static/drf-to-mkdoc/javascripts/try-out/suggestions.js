// Query parameter suggestions functionality
const TryOutSuggestions = {
    init: function() {
        this.suggestions = this.getAvailableSuggestions();
        this.updateDatalist();
        
        // Re-initialize when window.queryParametersData changes
        if (window.MutationObserver) {
            this.setupDataObserver();
        }
    },
    
    setupDataObserver: function() {
        // Check for changes in queryParametersData every second
        setInterval(() => {
            if (window.queryParametersData && window.queryParametersData._lastUpdate !== this._lastDataUpdate) {
                this._lastDataUpdate = window.queryParametersData._lastUpdate;
                this.suggestions = this.getAvailableSuggestions();
                this.updateDatalist();
            }
        }, 1000);
    },

    setupAutocomplete: function() {
        // Using native datalist, just make sure all inputs are properly initialized
        this.setupExistingInputs();
        
        // Setup for the add button to mark new inputs as initialized
        const addBtn = document.querySelector('.add-btn');
        if (addBtn) {
            addBtn.addEventListener('click', () => {
                // Wait for DOM to update
                setTimeout(() => {
                    this.setupExistingInputs();
                }, 10);
            });
        }
    },
    
    updateDatalist: function() {
        // Update the datalist with our suggestions
        const datalist = document.getElementById('paramSuggestions');
        if (datalist && this.suggestions.length > 0) {
            // Clear existing options
            datalist.innerHTML = '';
            
            // Add new options from our suggestions - without descriptions
            this.suggestions.forEach(suggestion => {
                const option = document.createElement('option');
                option.value = suggestion.name;
                // No description text as per requirement
                datalist.appendChild(option);
            });
        }
    },

    setupExistingInputs: function() {
        // Find all parameter name inputs
        const paramInputs = document.querySelectorAll('#queryParams .name-input');
        paramInputs.forEach(input => {
            // Skip if already initialized
            if (input.dataset.autocompleteInitialized) return;
            
            // Mark as initialized
            input.dataset.autocompleteInitialized = 'true';
            
            // We're using the native datalist for autocomplete
            // No need for custom suggestions dropdown
        });
    },

    getAvailableSuggestions: function() {
        // Get query parameters only from window.queryParametersData
        const suggestions = [];
        
        if (window.queryParametersData) {
            const data = window.queryParametersData;
            
            // Add filter fields
            if (data.filter_fields && data.filter_fields.length > 0) {
                suggestions.push(...data.filter_fields.map(field => ({
                    name: field
                })));
            }
            
            // Add search fields - only add the 'search' key, not individual fields
            // The 'search' key will be added via special_keys
            
            // Add ordering fields - only add the 'ordering' key, not individual fields
            // The 'ordering' key will be added via special_keys
            
            // Add special keys
            if (data.special_keys && data.special_keys.length > 0) {
                suggestions.push(...data.special_keys.map(key => ({
                    name: key
                })));
            }
            
            // Add pagination fields
            if (data.pagination_fields && data.pagination_fields.length > 0) {
                suggestions.push(...data.pagination_fields.map(field => ({
                    name: field
                })));
            }
        }
        
        return suggestions;
    },
    
    selectSuggestion: function(input, suggestion) {
        // Set input value
        input.value = suggestion;
        
        // Focus on value input
        const valueInput = input.nextElementSibling;
        if (valueInput) {
            valueInput.focus();
        }
    },
};

// Export for global access
window.TryOutSuggestions = TryOutSuggestions;
