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
        const paramInputs = document.querySelectorAll('#queryParams .kv-item input:first-child');
        paramInputs.forEach(input => {
            // Skip if already initialized
            if (input.dataset.autocompleteInitialized) return;
            
            // Mark as initialized
            input.dataset.autocompleteInitialized = 'true';
            
            // Create suggestions container for this input
            const suggestionsContainer = document.createElement('div');
            suggestionsContainer.className = 'param-suggestions';
            suggestionsContainer.id = 'suggestions-' + Math.random().toString(36).substr(2, 9);
            input.parentNode.style.position = 'relative';
            input.parentNode.appendChild(suggestionsContainer);
            
            // Store reference to container
            input.dataset.suggestionsContainer = suggestionsContainer.id;
            
            // Add event listeners
            input.addEventListener('focus', () => this.showSuggestions(input));
            input.addEventListener('input', () => this.filterSuggestions(input));
            input.addEventListener('keydown', (e) => this.handleKeyNavigation(e, input));
        });
    },

    getAvailableSuggestions: function() {
        const suggestions = [];
        
        // Try to get query parameters from the page context
        if (window.queryParametersData) {
            const data = window.queryParametersData;
            
            // Add filter fields
            if (data.filter_fields && data.filter_fields.length > 0) {
                suggestions.push(...data.filter_fields);
            }
            
            // Add search if available
            if (data.search_fields && data.search_fields.length > 0) {
                suggestions.push('search');
            }
            
            // Add ordering if available
            if (data.ordering_fields && data.ordering_fields.length > 0) {
                suggestions.push('ordering');
            }
            
            // Add pagination
            if (data.pagination_fields && data.pagination_fields.length > 0) {
                suggestions.push(...data.pagination_fields);
            }
        }
        
        // Default common parameters
        if (suggestions.length === 0) {
            suggestions.push('search', 'ordering', 'page', 'page_size');
        }
        
        // Remove duplicates and return
        return [...new Set(suggestions)];
    },

    showSuggestions: function(input) {
        const container = document.getElementById(input.dataset.suggestionsContainer);
        if (!container) return;
        
        // Clear existing suggestions
        container.innerHTML = '';
        
        // Filter suggestions based on input value
        const inputValue = input.value.toLowerCase();
        const filteredSuggestions = this.suggestions.filter(suggestion => 
            suggestion.toLowerCase().includes(inputValue)
        );
        
        if (filteredSuggestions.length === 0) {
            container.classList.remove('show');
            return;
        }
        
        // Add suggestions to container
        filteredSuggestions.forEach(suggestion => {
            const suggestionElement = document.createElement('div');
            suggestionElement.className = 'param-suggestion';
            suggestionElement.textContent = suggestion;
            suggestionElement.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectSuggestion(input, suggestion);
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
        const selectedIndex = Array.from(suggestions).findIndex(el => el.classList.contains('selected'));
        
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
            suggestions[currentIndex].classList.remove('selected');
        }
        
        // Calculate new index
        let newIndex;
        if (currentIndex < 0) {
            newIndex = direction > 0 ? 0 : suggestions.length - 1;
        } else {
            newIndex = (currentIndex + direction + suggestions.length) % suggestions.length;
        }
        
        // Select new suggestion
        suggestions[newIndex].classList.add('selected');
        suggestions[newIndex].scrollIntoView({ block: 'nearest' });
    }
};

// Export for global access
window.TryOutSuggestions = TryOutSuggestions;
