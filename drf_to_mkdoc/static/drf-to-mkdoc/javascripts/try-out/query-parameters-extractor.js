// Query parameters extractor
document.addEventListener('DOMContentLoaded', function() {
    const QueryParametersExtractor = {
        init: function() {
            // Extract parameters directly from HTML content
            const parameters = this.extractParametersFromHTML();
            
            // Make parameters available for suggestions
            if (parameters) {
                window.queryParametersData = parameters;
                
                // Initialize suggestions if TryOutSuggestions is available
                if (window.TryOutSuggestions) {
                    window.TryOutSuggestions.init();
                }
            }
        },
        
        extractParametersFromHTML: function() {
            const data = {
                filter_fields: [],
                search_fields: [],
                ordering_fields: [],
                pagination_fields: [],
                special_keys: []
            };
            
            // Extract filter fields
            this.extractFieldsFromSection('filter-fields', data.filter_fields);
            
            // Extract search fields
            this.extractFieldsFromSection('search-fields', data.search_fields);
            
            // Extract ordering fields
            this.extractFieldsFromSection('ordering-fields', data.ordering_fields);
            
            // Extract pagination fields
            this.extractFieldsFromSection('pagination-fields', data.pagination_fields);
            
            // Add special keys
            this.addSpecialKeys(data);
            
            return data;
        },
        
        extractFieldsFromSection: function(sectionId, targetArray) {
            const heading = document.querySelector(`h3#${sectionId}`);
            if (!heading) return;
            
            // Find the next UL element after the heading
            let currentElement = heading.nextElementSibling;
            while (currentElement && currentElement.tagName !== 'UL') {
                currentElement = currentElement.nextElementSibling;
            }
            
            if (!currentElement || currentElement.tagName !== 'UL') return;
            
            // Extract field names from code elements
            const codeElements = currentElement.querySelectorAll('code');
            codeElements.forEach(code => {
                const fieldName = code.textContent.trim();
                if (fieldName && !targetArray.includes(fieldName)) {
                    targetArray.push(fieldName);
                }
            });
        },
        
        addSpecialKeys: function(data) {
            // Add special keys for common query parameter types
            
            // Add special keys for each parameter type
            if (data) {
                // Special keys for search fields
                if (data.search_fields && data.search_fields.length > 0) {
                    if (!data.special_keys.includes('search')) {
                        data.special_keys.push('search');
                    }
                }
                
                // Special keys for ordering fields
                if (data.ordering_fields && data.ordering_fields.length > 0) {
                    if (!data.special_keys.includes('ordering')) {
                        data.special_keys.push('ordering');
                    }
                }
            }
            
            return data;
        }
    };
    
    // Initialize extractor
    QueryParametersExtractor.init();
});
