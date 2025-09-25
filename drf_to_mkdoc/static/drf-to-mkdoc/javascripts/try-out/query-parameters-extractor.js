// Query parameters extractor
document.addEventListener('DOMContentLoaded', function() {
    const QueryParametersExtractor = {
        init: function() {
            // Extract parameters from the query-parameters-data script tag
            const parameters = this.extractParameters();
            
            // Make parameters available for suggestions
            if (parameters) {
                window.queryParametersData = parameters;
                
                // Initialize suggestions if TryOutSuggestions is available
                if (window.TryOutSuggestions) {
                    window.TryOutSuggestions.init();
                }
            }
        },
        
        extractParameters: function() {
            // Try to get parameters from the script tag
            const dataScript = document.getElementById('query-parameters-data');
            if (!dataScript) {
                return null;
            }
            
            try {
                const data = JSON.parse(dataScript.textContent);
                
                // Add special keys
                this.addSpecialKeys(data);
                
                return data;
            } catch (e) {
                console.error('Failed to parse query parameters data:', e);
                return null;
            }
        },
        
        addSpecialKeys: function(data) {
            // Add special keys for common query parameter types
            
            // Add special keys for each parameter type
            if (data) {
                // Special keys for search fields
                if (data.search_fields && data.search_fields.length > 0) {
                    if (!data.special_keys) {
                        data.special_keys = [];
                    }
                    if (!data.special_keys.includes('search')) {
                        data.special_keys.push('search');
                    }
                }
                
                // Special keys for ordering fields
                if (data.ordering_fields && data.ordering_fields.length > 0) {
                    if (!data.special_keys) {
                        data.special_keys = [];
                    }
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
