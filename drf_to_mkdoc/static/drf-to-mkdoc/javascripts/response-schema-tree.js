/**
 * Response Schema Tree Component
 * Renders an interactive hierarchical tree view of response schema structures
 */

(function() {
    'use strict';

    class ResponseSchemaTree {
        constructor(container, schemaTree, options = {}) {
            this.container = container;
            this.schemaTree = schemaTree;
            this.options = {
                expandedByDefault: options.expandedByDefault === true, // Default to false (collapsed)
                showValidation: options.showValidation !== false,
                ...options
            };
            this.expandedNodes = new Set();
            this.maxDepth = 0;
            
            // Calculate maximum depth before rendering
            if (this.schemaTree) {
                this.maxDepth = this.calculateMaxDepth(this.schemaTree, 0);
            }
        }

        /**
         * Calculate the maximum depth of the tree recursively
         */
        calculateMaxDepth(node, currentDepth) {
            if (!node) return currentDepth;
            
            let maxDepth = currentDepth;
            
            // Check children
            if (node.children && node.children.length > 0) {
                for (const child of node.children) {
                    const childDepth = this.calculateMaxDepth(child, currentDepth + 1);
                    maxDepth = Math.max(maxDepth, childDepth);
                }
            }
            
            // Check array items
            if (node.type === 'array' && node.items) {
                const itemsDepth = this.calculateMaxDepth(node.items, currentDepth + 1);
                maxDepth = Math.max(maxDepth, itemsDepth);
            }
            
            return maxDepth;
        }

        /**
         * Render the tree structure
         */
        render() {
            if (!this.schemaTree) {
                this.container.innerHTML = '<div class="schema-tree-empty">No schema available</div>';
                return;
            }

            this.container.innerHTML = '';
            const treeWrapper = document.createElement('div');
            treeWrapper.className = 'schema-tree-wrapper';
            
            // Add toolbar
            const toolbar = this.createToolbar();
            treeWrapper.appendChild(toolbar);
            
            // Render tree
            const treeContainer = document.createElement('div');
            treeContainer.className = 'schema-tree-container';
            this.renderNode(treeContainer, this.schemaTree, 0, true);
            treeWrapper.appendChild(treeContainer);
            
            this.container.appendChild(treeWrapper);
            
            // Initialize expanded state - only expand first level by default
            if (this.options.expandedByDefault) {
                // Only expand root level and first level children
                const rootNodes = this.container.querySelectorAll('.schema-tree-node[data-depth="0"]');
                rootNodes.forEach(rootNode => {
                    const firstLevelChildren = rootNode.querySelectorAll('.schema-tree-node[data-depth="1"]');
                    if (firstLevelChildren.length > 0) {
                        this.toggleNode(rootNode);
                    }
                });
            }
        }

        /**
         * Create toolbar with expand/collapse controls
         */
        createToolbar() {
            const toolbar = document.createElement('div');
            toolbar.className = 'schema-tree-toolbar';
            
            const expandBtn = document.createElement('button');
            expandBtn.className = 'schema-tree-toolbar-btn';
            expandBtn.textContent = 'Expand All';
            expandBtn.setAttribute('aria-label', 'Expand all nodes');
            expandBtn.addEventListener('click', () => this.expandAll());
            
            const collapseBtn = document.createElement('button');
            collapseBtn.className = 'schema-tree-toolbar-btn';
            collapseBtn.textContent = 'Collapse All';
            collapseBtn.setAttribute('aria-label', 'Collapse all nodes');
            collapseBtn.addEventListener('click', () => this.collapseAll());
            
            toolbar.appendChild(expandBtn);
            toolbar.appendChild(collapseBtn);
            
            return toolbar;
        }

        /**
         * Render a single node in the tree
         */
        renderNode(parent, node, depth, isRoot = false) {
            if (!node) return;

            const nodeElement = document.createElement('div');
            nodeElement.className = 'schema-tree-node';
            nodeElement.setAttribute('data-depth', depth);
            nodeElement.setAttribute('data-node-id', this.generateNodeId());
            
            if (!isRoot) {
                nodeElement.classList.add('schema-tree-node-nested');
                
                // Calculate darkness ratio based on depth and max depth
                // Apply progressive background darkness for visual separation
                if (this.maxDepth > 0) {
                    const darknessRatio = depth / this.maxDepth;
                    nodeElement.setAttribute('data-darkness-ratio', darknessRatio.toFixed(3));
                    
                    // Calculate background color based on darkness ratio
                    // Light mode: Start with #f8fafc (very light) and darken progressively
                    // Dark mode: Start with #1e293b (dark) and get darker progressively
                    // Max darkness at max depth is now 90% (much darker)
                    const maxDarkness = 0.9;
                    const adjustedRatio = darknessRatio * maxDarkness;
                    
                    // Light mode: RGB values that get darker
                    // Base: rgb(248, 250, 252) -> darker: rgb(241, 245, 249) -> darkest: rgb(203, 213, 225)
                    const lightBase = { r: 248, g: 250, b: 252 };
                    const lightDark = { r: 203, g: 213, b: 225 };
                    const lightR = Math.round(lightBase.r - (lightBase.r - lightDark.r) * adjustedRatio);
                    const lightG = Math.round(lightBase.g - (lightBase.g - lightDark.g) * adjustedRatio);
                    const lightB = Math.round(lightBase.b - (lightBase.b - lightDark.b) * adjustedRatio);
                    
                    // Dark mode: RGB values that get darker
                    // Base: rgb(30, 41, 59) -> darker: rgb(15, 23, 42) -> darkest: rgb(0, 0, 0) (almost black)
                    const darkBase = { r: 30, g: 41, b: 59 };
                    const darkDark = { r: 0, g: 0, b: 0 };
                    const darkR = Math.round(darkBase.r - (darkBase.r - darkDark.r) * adjustedRatio);
                    const darkG = Math.round(darkBase.g - (darkBase.g - darkDark.g) * adjustedRatio);
                    const darkB = Math.round(darkBase.b - (darkBase.b - darkDark.b) * adjustedRatio);
                    
                    // Set CSS custom properties for the node
                    nodeElement.style.setProperty('--depth-bg-light', `rgb(${lightR}, ${lightG}, ${lightB})`);
                    nodeElement.style.setProperty('--depth-bg-dark', `rgb(${darkR}, ${darkG}, ${darkB})`);
                }
            }

            const hasChildren = node.children && node.children.length > 0;
            const isExpandable = hasChildren || (node.type === 'array' && node.items);
            
            if (isExpandable) {
                nodeElement.classList.add('schema-tree-node-expandable');
            }

            // Node content
            const content = document.createElement('div');
            content.className = 'schema-tree-node-content';
            
            // Indentation spacer (handled by CSS data-depth attribute)
            const spacer = document.createElement('div');
            spacer.className = 'schema-tree-spacer';
            content.appendChild(spacer);
            
            // Expand/collapse button
            if (isExpandable) {
                const toggleBtn = document.createElement('button');
                toggleBtn.className = 'schema-tree-toggle';
                toggleBtn.setAttribute('aria-label', 'Toggle node');
                toggleBtn.setAttribute('aria-expanded', 'false');
                toggleBtn.innerHTML = '<span class="schema-tree-toggle-icon">▶</span>';
                toggleBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.toggleNode(nodeElement);
                });
                content.appendChild(toggleBtn);
            } else {
                const spacer = document.createElement('div');
                spacer.className = 'schema-tree-toggle-spacer';
                content.appendChild(spacer);
            }
            
            // Field name (if not root and not an array item)
            // Array items don't have a field name - they represent the structure of items in the array
            if (!isRoot && node.name && !node.isArrayItem) {
                const nameSpan = document.createElement('span');
                nameSpan.className = 'schema-tree-field-name';
                nameSpan.textContent = node.name;
                
                // Add tooltip for description if available
                if (node.description) {
                    nameSpan.setAttribute('title', node.description);
                    nameSpan.classList.add('schema-tree-field-with-tooltip');
                }
                
                content.appendChild(nameSpan);
            } else if (!isRoot && node.isArrayItem) {
                // For array items, show a structural indicator instead of a field name
                const indicatorSpan = document.createElement('span');
                indicatorSpan.className = 'schema-tree-array-indicator';
                indicatorSpan.textContent = '[array item]';
                
                // Add tooltip for description if available
                if (node.description) {
                    indicatorSpan.setAttribute('title', node.description);
                    indicatorSpan.classList.add('schema-tree-field-with-tooltip');
                }
                
                content.appendChild(indicatorSpan);
            }
            
            // Type badge
            const typeBadge = this.createTypeBadge(node);
            content.appendChild(typeBadge);
            
            // Required/Optional badge
            if (!isRoot && node.required !== undefined) {
                const reqBadge = document.createElement('span');
                reqBadge.className = node.required ? 'schema-tree-badge-required' : 'schema-tree-badge-optional';
                reqBadge.textContent = node.required ? 'Required' : 'Optional';
                content.appendChild(reqBadge);
            }
            
            // Read-only badge
            if (node.readOnly) {
                const roBadge = document.createElement('span');
                roBadge.className = 'schema-tree-badge-readonly';
                roBadge.textContent = 'readOnly';
                content.appendChild(roBadge);
            }
            
            // Description (hidden by default, shown in tooltip on hover)
            // We don't show description inline anymore, only in tooltip
            
            // Validation rules
            if (this.options.showValidation && node.validation && Object.keys(node.validation).length > 0) {
                const validationDiv = this.createValidationDisplay(node.validation);
                content.appendChild(validationDiv);
            }
            
            nodeElement.appendChild(content);
            
            // Children container
            if (isExpandable) {
                const childrenContainer = document.createElement('div');
                childrenContainer.className = 'schema-tree-children';
                childrenContainer.style.display = 'none';
                
                if (hasChildren) {
                    // Sort children: non-expandable (leaf nodes) first, expandable (collapsible) last
                    const sortedChildren = [...node.children].sort((a, b) => {
                        const aHasChildren = (a.children && a.children.length > 0) || (a.type === 'array' && a.items);
                        const bHasChildren = (b.children && b.children.length > 0) || (b.type === 'array' && b.items);
                        
                        // If both are expandable or both are not, maintain original order
                        if (aHasChildren === bHasChildren) {
                            return 0;
                        }
                        // Non-expandable (false) comes before expandable (true)
                        return aHasChildren ? 1 : -1;
                    });
                    
                    sortedChildren.forEach(child => {
                        this.renderNode(childrenContainer, child, depth + 1, false);
                    });
                } else if (node.type === 'array' && node.items) {
                    // Render array items - don't show "items" as a field name
                    // Mark it as an array item node so it renders differently
                    const itemsNode = { ...node.items, isArrayItem: true };
                    this.renderNode(childrenContainer, itemsNode, depth + 1, false);
                }
                
                nodeElement.appendChild(childrenContainer);
            }
            
            parent.appendChild(nodeElement);
        }

        /**
         * Create type badge element
         */
        createTypeBadge(node) {
            const badge = document.createElement('span');
            badge.className = 'schema-tree-type-badge';
            
            let typeText = node.type || 'unknown';
            if (node.type === 'array') {
                typeText = `array[${node.itemsType || 'string'}]`;
            } else if (node.ref) {
                typeText = node.ref;
                badge.classList.add('schema-tree-type-ref');
            }
            
            badge.textContent = typeText;
            badge.setAttribute('data-type', node.type);
            
            return badge;
        }

        /**
         * Create validation display element
         */
        createValidationDisplay(validation) {
            const container = document.createElement('div');
            container.className = 'schema-tree-validation';
            
            const rules = [];
            
            if (validation.enum) {
                rules.push(`enum: [${validation.enum.slice(0, 3).join(', ')}${validation.enum.length > 3 ? '...' : ''}]`);
            }
            if (validation.minLength !== undefined) {
                rules.push(`minLength: ${validation.minLength}`);
            }
            if (validation.maxLength !== undefined) {
                rules.push(`maxLength: ${validation.maxLength}`);
            }
            if (validation.minimum !== undefined) {
                rules.push(`min: ${validation.minimum}`);
            }
            if (validation.maximum !== undefined) {
                rules.push(`max: ${validation.maximum}`);
            }
            if (validation.minItems !== undefined) {
                rules.push(`minItems: ${validation.minItems}`);
            }
            if (validation.maxItems !== undefined) {
                rules.push(`maxItems: ${validation.maxItems}`);
            }
            if (validation.pattern) {
                rules.push(`pattern: ${validation.pattern}`);
            }
            if (validation.format) {
                rules.push(`format: ${validation.format}`);
            }
            
            if (rules.length > 0) {
                const validationText = document.createElement('span');
                validationText.className = 'schema-tree-validation-text';
                validationText.textContent = rules.join(' | ');
                container.appendChild(validationText);
            }
            
            return container;
        }

        /**
         * Toggle node expansion
         */
        toggleNode(nodeElement) {
            const childrenContainer = nodeElement.querySelector('.schema-tree-children');
            const toggleBtn = nodeElement.querySelector('.schema-tree-toggle');
            
            if (!childrenContainer || !toggleBtn) return;
            
            const isExpanded = childrenContainer.style.display !== 'none';
            const nodeId = nodeElement.getAttribute('data-node-id');
            
            if (isExpanded) {
                childrenContainer.style.display = 'none';
                toggleBtn.setAttribute('aria-expanded', 'false');
                const icon = toggleBtn.querySelector('.schema-tree-toggle-icon');
                icon.textContent = '▶';
                icon.classList.remove('expanded');
                this.expandedNodes.delete(nodeId);
            } else {
                childrenContainer.style.display = 'block';
                toggleBtn.setAttribute('aria-expanded', 'true');
                const icon = toggleBtn.querySelector('.schema-tree-toggle-icon');
                icon.textContent = '▶';
                icon.classList.add('expanded');
                this.expandedNodes.add(nodeId);
            }
        }

        /**
         * Expand all nodes
         */
        expandAll() {
            const allNodes = this.container.querySelectorAll('.schema-tree-node-expandable');
            allNodes.forEach(node => {
                const childrenContainer = node.querySelector('.schema-tree-children');
                const toggleBtn = node.querySelector('.schema-tree-toggle');
                
                if (childrenContainer && toggleBtn) {
                    childrenContainer.style.display = 'block';
                    toggleBtn.setAttribute('aria-expanded', 'true');
                    const icon = toggleBtn.querySelector('.schema-tree-toggle-icon');
                    icon.textContent = '▶';
                    icon.classList.add('expanded');
                    
                    const nodeId = node.getAttribute('data-node-id');
                    this.expandedNodes.add(nodeId);
                }
            });
        }

        /**
         * Collapse all nodes
         */
        collapseAll() {
            const allNodes = this.container.querySelectorAll('.schema-tree-node-expandable');
            allNodes.forEach(node => {
                const childrenContainer = node.querySelector('.schema-tree-children');
                const toggleBtn = node.querySelector('.schema-tree-toggle');
                
                if (childrenContainer && toggleBtn) {
                    childrenContainer.style.display = 'none';
                    toggleBtn.setAttribute('aria-expanded', 'false');
                    const icon = toggleBtn.querySelector('.schema-tree-toggle-icon');
                    icon.textContent = '▶';
                    icon.classList.remove('expanded');
                    
                    const nodeId = node.getAttribute('data-node-id');
                    this.expandedNodes.delete(nodeId);
                }
            });
        }

        /**
         * Generate unique node ID
         */
        generateNodeId() {
            return `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        }
    }

    // Export to global scope
    window.ResponseSchemaTree = ResponseSchemaTree;

})();

