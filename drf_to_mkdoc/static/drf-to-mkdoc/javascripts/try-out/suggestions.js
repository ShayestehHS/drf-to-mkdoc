// Query parameter suggestions functionality
const TryOutSuggestions = {
    init: function() {
        this.suggestions = this.getAvailableSuggestions();
        this.setupAutocomplete();
    },

    setupAutocomplete: function() {
        // Setup event listeners for all query parameter inputs
        document.addEventListener('click', (e) => {
            // Hide all suggestion dropdowns when clicking outside
            if (!e.target.matches('#queryParams input')) {
                this.hideAllSuggestions();
            }
        });

        // Initial setup for existing inputs
        this.setupExistingInputs();

        // Setup for the add button to attach listeners to new inputs
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

    setupExistingInputs: function() {
        // Find all parameter name inputs
        const paramInputs = document.querySelectorAll('#queryParams .name-input');
        paramInputs.forEach(input => {
            // Skip if already initialized
            if (input.dataset.autocompleteInitialized) return;
            
            // Mark as initialized
            input.dataset.autocompleteInitialized = 'true';
            
            // Create suggestions container for this input
            const suggestionsContainer = document.createElement('div');
            suggestionsContainer.className = 'suggestions-dropdown';
            suggestionsContainer.id = 'suggestions-' + Math.random().toString(36).substr(2, 9);
            
            // Find the parameter inputs container
            const container = input.closest('.parameter-inputs');
            if (container) {
                container.style.position = 'relative';
                container.appendChild(suggestionsContainer);
            }
            
            // Store reference to container
            input.dataset.suggestionsContainer = suggestionsContainer.id;
            
            // Add event listeners
            input.addEventListener('focus', () => this.showSuggestions(input));
            input.addEventListener('input', () => this.filterSuggestions(input));
            input.addEventListener('keydown', (e) => this.handleKeyNavigation(e, input));
            input.addEventListener('blur', () => {
                setTimeout(() => {
                    const container = document.getElementById(input.dataset.suggestionsContainer);
                    if (container) {
                        container.classList.remove('show');
                    }
                }, 150);
            });
        });
    },

    getAvailableSuggestions: function() {
        // Try to load from script tag first
        try {
            const dataScript = document.querySelector('script[type="application/json"][data-query-params]');
            if (dataScript) {
                const data = JSON.parse(dataScript.textContent);
                return data.map(param => ({
                    name: param.name,
                    description: param.description || ''
                }));
            }
        } catch (e) {
            console.warn('Could not load query parameters data');
        }

        // Try to get query parameters from the page context
        const suggestions = [];
        if (window.queryParametersData) {
            const data = window.queryParametersData;
            
            // Add filter fields
            if (data.filter_fields && data.filter_fields.length > 0) {
                suggestions.push(...data.filter_fields.map(field => ({
                    name: field,
                    description: 'Filter by ' + field
                })));
            }
            
            // Add search if available
            if (data.search_fields && data.search_fields.length > 0) {
                suggestions.push({ name: 'search', description: 'Search term' });
            }
            
            // Add ordering if available
            if (data.ordering_fields && data.ordering_fields.length > 0) {
                suggestions.push({ name: 'ordering', description: 'Field to order results by' });
            }
            
            // Add pagination
            if (data.pagination_fields && data.pagination_fields.length > 0) {
                suggestions.push(...data.pagination_fields.map(field => ({
                    name: field,
                    description: 'Pagination parameter'
                })));
            }
        }
        
        // Default common parameters for Django REST framework
        if (suggestions.length === 0) {
            return [
                { name: 'page', description: 'Page number for pagination' },
                { name: 'page_size', description: 'Number of items per page' },
                { name: 'limit', description: 'Limit number of results' },
                { name: 'offset', description: 'Offset for pagination' },
                { name: 'ordering', description: 'Field to order results by' },
                { name: 'search', description: 'Search term' },
                { name: 'format', description: 'Response format (json, xml, etc.)' },
                { name: 'fields', description: 'Comma-separated list of fields to include' },
                { name: 'expand', description: 'Related fields to expand' },
                { name: 'filter', description: 'Filter results' }
            ];
        }
        
        return suggestions;
    },

    showSuggestions: function(input) {
        const container = document.getElementById(input.dataset.suggestionsContainer);
        if (!container) return;
        
        // Clear existing suggestions
        container.innerHTML = '';
        
        // Filter suggestions based on input value
        const inputValue = input.value.toLowerCase();
        const filteredSuggestions = this.suggestions.filter(suggestion => 
            suggestion.name.toLowerCase().includes(inputValue) ||
            suggestion.description.toLowerCase().includes(inputValue)
        );
        
        if (filteredSuggestions.length === 0) {
            container.classList.remove('show');
            return;
        }
        
        // Add suggestions to container
        filteredSuggestions.forEach((suggestion, index) => {
            const suggestionElement = document.createElement('div');
            suggestionElement.className = 'suggestion-item';
            suggestionElement.dataset.index = index;
            suggestionElement.dataset.name = suggestion.name;
            suggestionElement.innerHTML = `
                <div class="suggestion-name">${suggestion.name}</div>
                <div class="suggestion-description">${suggestion.description}</div>
            `;
            suggestionElement.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectSuggestion(input, suggestion.name);
            });
            container.appendChild(suggestionElement);
        });
        
        // Show suggestions
        container.classList.add('show');
    },
    
    filterSuggestions: function(input) {
        // Just re-show suggestions with current filter
        this.showSuggestions(input);
    },
    
    hideAllSuggestions: function() {
        document.querySelectorAll('.param-suggestions').forEach(container => {
            container.classList.remove('show');
        });
    },
    
    selectSuggestion: function(input, suggestion) {
        // Set input value
        input.value = suggestion;
        
        // Hide suggestions
        const container = document.getElementById(input.dataset.suggestionsContainer);
        if (container) {
            container.classList.remove('show');
        }
        
        // Focus on value input
        const valueInput = input.nextElementSibling;
        if (valueInput) {
            valueInput.focus();
        }
    },
    
    handleKeyNavigation: function(event, input) {
        const container = document.getElementById(input.dataset.suggestionsContainer);
        if (!container || !container.classList.contains('show')) return;
        
        const suggestions = container.querySelectorAll('.param-suggestion');
        if (suggestions.length === 0) return;
        
        // Find currently selected suggestion
        const selectedIndex = Array.from(suggestions).findIndex(el => el.classList.contains('highlighted'));
        
        switch (event.key) {
            case 'ArrowDown':
                event.preventDefault();
                this.navigateSuggestion(suggestions, selectedIndex, 1);
                break;
                
            case 'ArrowUp':
                event.preventDefault();
                this.navigateSuggestion(suggestions, selectedIndex, -1);
                break;
                
            case 'Enter':
                event.preventDefault();
                if (selectedIndex >= 0) {
                    this.selectSuggestion(input, suggestions[selectedIndex].textContent);
                } else if (suggestions.length > 0) {
                    this.selectSuggestion(input, suggestions[0].textContent);
                }
                break;
                
            case 'Escape':
                event.preventDefault();
                container.classList.remove('show');
                break;
        }
    },
    
    navigateSuggestion: function(suggestions, currentIndex, direction) {
        // Remove current selection
        if (currentIndex >= 0) {
            suggestions[currentIndex].classList.remove('highlighted');
        }
        
        // Calculate new index
        let newIndex;
        if (currentIndex < 0) {
            newIndex = direction > 0 ? 0 : suggestions.length - 1;
        } else {
            newIndex = (currentIndex + direction + suggestions.length) % suggestions.length;
        }
        
        // Select new suggestion
        suggestions[newIndex].classList.add('highlighted');
        suggestions[newIndex].scrollIntoView({ block: 'nearest' });
    }
};

// Export for global access
window.TryOutSuggestions = TryOutSuggestions;
