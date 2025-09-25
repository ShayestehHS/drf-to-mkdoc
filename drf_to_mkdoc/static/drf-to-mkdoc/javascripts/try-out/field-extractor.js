// Field extractor for documentation content
document.addEventListener('DOMContentLoaded', function() {
    // Extract filter fields and pagination fields from documentation
    const FieldExtractor = {
        init: function() {
            // Extract fields from documentation
            const fields = this.extractFieldsFromDocumentation();
            
            // Make fields available for suggestions
            if (fields && (fields.filter_fields.length > 0 || fields.pagination_fields.length > 0)) {
                window.queryParametersData = window.queryParametersData || {};
                
                // Add filter fields
                if (fields.filter_fields.length > 0) {
                    window.queryParametersData.filter_fields = fields.filter_fields;
                }
                
                // Add pagination fields
                if (fields.pagination_fields.length > 0) {
                    window.queryParametersData.pagination_fields = fields.pagination_fields;
                }
                
                // Initialize suggestions if TryOutSuggestions is available
                if (window.TryOutSuggestions) {
                    window.TryOutSuggestions.init();
                }
            }
        },
        
        extractFieldsFromDocumentation: function() {
            const result = {
                filter_fields: [],
                pagination_fields: []
            };
            
            // Look for filter fields section
            const filterFieldsHeading = document.querySelector('h3#filter-fields');
            if (filterFieldsHeading) {
                const filterFieldsList = filterFieldsHeading.nextElementSibling;
                if (filterFieldsList && filterFieldsList.tagName === 'UL') {
                    const filterFields = Array.from(filterFieldsList.querySelectorAll('li code'))
                        .map(code => code.textContent.trim());
                    
                    if (filterFields.length > 0) {
                        result.filter_fields = filterFields;
                    }
                }
            }
            
            // Look for pagination fields section
            const paginationFieldsHeading = document.querySelector('h3#pagination-fields');
            if (paginationFieldsHeading) {
                const paginationFieldsList = paginationFieldsHeading.nextElementSibling;
                if (paginationFieldsList && paginationFieldsList.tagName === 'UL') {
                    const paginationFields = Array.from(paginationFieldsList.querySelectorAll('li code'))
                        .map(code => code.textContent.trim());
                    
                    if (paginationFields.length > 0) {
                        result.pagination_fields = paginationFields;
                    }
                }
            }
            
            return result;
        },
        
        formatDocumentation: function() {
            // Format filter fields section
            this.formatSection('filter-fields', 'Filter Fields');
            
            // Format pagination fields section
            this.formatSection('pagination-fields', 'Pagination Fields');
        },
        
        formatSection: function(sectionId, title) {
            const heading = document.querySelector(`h3#${sectionId}`);
            if (!heading) return;
            
            const list = heading.nextElementSibling;
            if (!list || list.tagName !== 'UL') return;
            
            // Create a new container div
            const container = document.createElement('div');
            container.className = 'api-parameters-section';
            container.id = `${sectionId}-container`;
            
            // Create a new heading
            const newHeading = document.createElement('h3');
            newHeading.id = sectionId;
            newHeading.innerHTML = heading.innerHTML;
            
            // Create a new list container
            const listContainer = document.createElement('div');
            listContainer.className = 'parameters-list';
            
            // Create a description paragraph
            const description = document.createElement('p');
            description.className = 'parameters-description';
            
            if (sectionId === 'filter-fields') {
                description.textContent = 'These fields can be used to filter the API results. Add them as query parameters to your request.';
            } else if (sectionId === 'pagination-fields') {
                description.textContent = 'These fields control pagination of the API results.';
            }
            
            // Process the list items to enhance them
            const enhancedList = this.enhanceParametersList(list);
            
            // Move the list into the container
            listContainer.appendChild(enhancedList);
            
            // Add elements to the container
            container.appendChild(newHeading);
            container.appendChild(description);
            container.appendChild(listContainer);
            
            // Replace the old elements with the new container
            heading.parentNode.insertBefore(container, heading);
            list.parentNode.removeChild(list);
            heading.parentNode.removeChild(heading);
            
            // Add try-it buttons
            this.addTryItButtons(container, sectionId);
        },
        
        enhanceParametersList: function(list) {
            // Clone the list
            const enhancedList = list.cloneNode(true);
            
            // Process each list item
            Array.from(enhancedList.querySelectorAll('li')).forEach(li => {
                const code = li.querySelector('code');
                if (code) {
                    // Create a button to try this parameter
                    const tryButton = document.createElement('button');
                    tryButton.className = 'try-param-btn';
                    tryButton.textContent = 'Try it';
                    tryButton.dataset.param = code.textContent.trim();
                    tryButton.addEventListener('click', (e) => {
                        e.preventDefault();
                        this.addParameterToTryOut(e.target.dataset.param);
                    });
                    
                    li.appendChild(tryButton);
                }
            });
            
            return enhancedList;
        },
        
        addTryItButtons: function(container, sectionId) {
            // Create a button to try all parameters in this section
            const tryAllButton = document.createElement('button');
            tryAllButton.className = 'try-all-params-btn';
            tryAllButton.textContent = 'Try All Parameters';
            
            tryAllButton.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Get all parameters in this section
                const params = Array.from(container.querySelectorAll('code'))
                    .map(code => code.textContent.trim());
                
                // Add all parameters to try-out form
                params.forEach(param => this.addParameterToTryOut(param));
            });
            
            // Add the button to the container
            container.appendChild(tryAllButton);
        },
        
        addParameterToTryOut: function(paramName) {
            // Find the try-out modal or form
            const tryOutModal = document.getElementById('tryOutModal');
            if (!tryOutModal) return;
            
            // Show the modal if it's not already visible
            if (tryOutModal.style.display !== 'flex') {
                if (window.ModalManager && window.ModalManager.openTryOut) {
                    window.ModalManager.openTryOut();
                } else {
                    tryOutModal.style.display = 'flex';
                }
            }
            
            // Add the parameter to the query parameters
            if (window.TryOutSidebar && window.TryOutSidebar.addQueryParam) {
                window.TryOutSidebar.addQueryParam(paramName);
            } else if (window.FormManager && window.FormManager.addQueryParam) {
                window.FormManager.addQueryParam(paramName);
            }
        }
    };
    
    // Initialize field extractor
    FieldExtractor.init();
    
    // Format documentation sections
    FieldExtractor.formatDocumentation();
});
