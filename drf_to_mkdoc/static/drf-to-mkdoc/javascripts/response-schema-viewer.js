/**
 * Schema Tree Viewer
 * Simple wrapper to render schema trees
 */

(function() {
    'use strict';

    /**
     * Initialize all schema tree viewers on the page
     */
    function initSchemaTreeViewers() {
        const schemaContainers = document.querySelectorAll('.schema-tree-viewer-container');
        
        schemaContainers.forEach(container => {
            const schemaTreeData = container.getAttribute('data-schema-tree');
            
            if (!schemaTreeData) {
                container.innerHTML = '<div class="schema-view-empty">No schema available</div>';
                return;
            }
            
            let schemaTree = null;
            
            try {
                schemaTree = JSON.parse(schemaTreeData);
            } catch (e) {
                console.error('Error parsing schema tree data:', e);
                container.innerHTML = '<div class="schema-view-empty">Error loading schema</div>';
                return;
            }
            
            if (schemaTree && window.ResponseSchemaTree) {
                const treeView = document.createElement('div');
                treeView.className = 'response-schema-tree-view';
                container.appendChild(treeView);
                
                const treeInstance = new window.ResponseSchemaTree(
                    treeView,
                    schemaTree,
                    { expandedByDefault: false, showValidation: true }
                );
                treeInstance.render();
            } else {
                container.innerHTML = '<div class="schema-view-empty">No schema available</div>';
            }
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSchemaTreeViewers);
    } else {
        initSchemaTreeViewers();
    }

})();

