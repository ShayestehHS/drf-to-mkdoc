document.addEventListener('DOMContentLoaded', function() {
    // Get endpoint information from the page
    const getEndpointInfo = () => {
        let { path = '', method = 'GET' } = (window.__getTryOutEndpointInfo && window.__getTryOutEndpointInfo()) || {};
        
        // First, try to find the method badge and code element in the same paragraph
        const methodBadge = document.querySelector('.method-badge');
        if (methodBadge) {
            method = methodBadge.textContent.trim();
            
            // Look for a code element in the same parent or nearby
            const parent = methodBadge.closest('p, div, section');
            if (parent) {
                const codeElement = parent.querySelector('code');
                if (codeElement) {
                    path = codeElement.textContent.trim();
                }
            }
        }
        
        // Fallback: try to find in title
        if (!path) {
            const title = document.querySelector('h1');
            if (title) {
                const titleText = title.textContent.trim();
                const pathMatch = titleText.match(/[A-Z]+\s+(.+)/);
                if (pathMatch) {
                    path = pathMatch[1];
                }
            }
        }
        
        // Additional fallback - look for code blocks with paths
        if (!path) {
            const codeBlocks = document.querySelectorAll('code');
            for (const code of codeBlocks) {
                const text = code.textContent.trim();
                if (text.startsWith('/') && !text.includes('http')) {
                    path = text;
                    break;
                }
            }
        }
        
        // Clean up the path to handle HTML entities and special characters
        if (path) {
            // Use DOMParser to safely decode HTML entities
            const parser = new DOMParser();
            const doc = parser.parseFromString(`<div>${path}</div>`, 'text/html');
            const tempDiv = doc.querySelector('div');
            path = tempDiv ? (tempDiv.textContent || tempDiv.innerText || path) : path;
            
            // Remove any non-printable characters or replace problematic ones
            path = path.replace(/[^\x20-\x7E]/g, ''); // Remove non-ASCII printable characters
            path = path.replace(/¶/g, ''); // Specifically remove paragraph symbols
            path = path.trim();
        }
        
        const info = {
            method: method,
            path: path || '/api/endpoint',
            pathParams: path ? extractPathParams(path) : []
        };
        // expose for global functions
        window.__getTryOutEndpointInfo = () => info;
        return info;
    };
    
    // Extract path parameters from URL
    const extractPathParams = (path) => {
        const matches = path.match(/\{([^}]+)\}/g) || [];
        return matches.map(param => param.slice(1, -1)); // Remove { }
    };
    
    // Standard header suggestions
    const standardHeaders = [
        'Accept', 'Accept-Encoding', 'Accept-Language', 'Authorization', 
        'Cache-Control', 'Content-Type', 'Cookie', 'User-Agent',
        'X-API-Key', 'X-Requested-With', 'X-CSRF-Token'
    ];

    // HTML escaping function to prevent XSS
    const escapeHtml = (s='') => s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    
    // Create the try-out panel HTML
    const createTryOutPanel = (endpointInfo) => {
        // Create path parameters HTML
        let pathParamsHtml = '';
        if (endpointInfo.pathParams.length > 0) {
            pathParamsHtml = `
                <div class="form-group">
                    <label class="form-label">Path Parameters</label>
                    <div class="kv-container" id="pathParams">
                        ${endpointInfo.pathParams.map(p => {
                            const param = escapeHtml(p);
                            return `
                            <div class="kv-item">
                                <label class="param-label">${param}</label>
                                <input type="text" placeholder="Enter ${param} value" data-param="${param}" required>
                            </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        }
        
        // Create the panel HTML
        return `
            <div class="try-out-sidebar">
                <div class="form-group">
                    <label class="form-label">Base URL</label>
                    <input type="text" class="form-input" id="baseUrl" value="${window.location.origin}" placeholder="https://api.example.com">
                </div>

                <div class="tabs">
                    <button class="tab active" data-tab="parameters">Parameters</button>
                    <button class="tab" data-tab="headers">Headers</button>
                    <button class="tab" data-tab="body" style="${['POST', 'PUT', 'PATCH'].includes(endpointInfo.method) ? '' : 'display: none;'}">Body</button>
                </div>

                <div class="tab-content active" id="parametersTab">
                    ${pathParamsHtml}

                    <div class="form-group">
                        <label class="form-label">Query Parameters</label>
                        <div class="kv-container" id="queryParams">
                            <div class="kv-item">
                                <input type="text" placeholder="Parameter name" list="queryParamSuggestions">
                                <input type="text" placeholder="Parameter value">
                                <button class="remove-btn" onclick="removeKvItem(this)">✕</button>
                            </div>
                        </div>
                        <datalist id="queryParamSuggestions">
                            ${(() => {
                                const suggestions = new Set();
                                
                                // Find query parameters section by looking for h2 with id="query-parameters"
                                const queryParamsHeading = document.querySelector('h2[id="query-parameters"]');
                                if (queryParamsHeading) {
                                    // Look for the next ul element after this heading
                                    let nextElement = queryParamsHeading.nextElementSibling;
                                    while (nextElement && nextElement.tagName !== 'UL') {
                                        nextElement = nextElement.nextElementSibling;
                                    }
                                    if (nextElement) {
                                        const queryParamElements = nextElement.querySelectorAll('li code');
                                        queryParamElements.forEach(code => {
                                            const name = (code.textContent || '').trim();
                                            if (name) {
                                                suggestions.add(name);
                                            }
                                        });
                                    }
                                }
                                
                                // Find search parameters section by looking for h3 with id="search-parameters"
                                const searchParamsHeading = document.querySelector('h3[id="search-parameters"]');
                                if (searchParamsHeading) {
                                    // Look for the next ul element after this heading
                                    let nextElement = searchParamsHeading.nextElementSibling;
                                    while (nextElement && nextElement.tagName !== 'UL') {
                                        nextElement = nextElement.nextElementSibling;
                                    }
                                    if (nextElement) {
                                        const searchParamItems = nextElement.querySelectorAll('li code');
                                        if (searchParamItems.length > 0) {
                                            suggestions.add('search');
                                        }
                                        // Also add the actual search parameter names
                                        searchParamItems.forEach(code => {
                                            const name = (code.textContent || '').trim();
                                            if (name) {
                                                suggestions.add(name);
                                            }
                                        });
                                    }
                                }
                                
                                // Fallback: if no specific sections found, look for any ul li code elements
                                if (suggestions.size === 0) {
                                    const fallbackElements = document.querySelectorAll('ul li code');
                                    fallbackElements.forEach(code => {
                                        const name = (code.textContent || '').trim();
                                        if (name) {
                                            suggestions.add(name);
                                        }
                                    });
                                }
                                
                                return Array.from(suggestions).map(name => `<option value="${escapeHtml(name)}">`).join('');
                            })()}
                        </datalist>
                        <button class="add-btn" onclick="addQueryParam()">
                            <span>+</span> Add Parameter
                        </button>
                    </div>
                </div>

                <div class="tab-content" id="headersTab">
                    <div class="form-group">
                        <label class="form-label">Request Headers</label>
                        <div class="kv-container" id="requestHeaders">
                            <div class="kv-item">
                                <input type="text" value="Content-Type" list="headerSuggestions">
                                <input type="text" value="application/json">
                                <button class="remove-btn" onclick="removeKvItem(this)">✕</button>
                            </div>
                            <div class="kv-item">
                                <input type="text" value="Authorization" list="headerSuggestions">
                                <input type="text" placeholder="Bearer your-token">
                                <button class="remove-btn" onclick="removeKvItem(this)">✕</button>
                            </div>
                        </div>
                        <datalist id="headerSuggestions">
                            ${standardHeaders.map(header => `<option value="${header}">`).join('')}
                        </datalist>
                        <button class="add-btn" onclick="addHeader()">
                            <span>+</span> Add Header
                        </button>
                    </div>
                </div>

                <div class="tab-content" id="bodyTab">
                    <div class="form-group">
                        <label class="form-label">Request Body</label>
                        <textarea class="form-input textarea" id="requestBody" placeholder="Enter JSON payload here..."></textarea>
                    </div>
                </div>

                <button class="execute-btn" id="executeBtn" onclick="executeRequest()">
                    <span>▶</span> Execute Request
                </button>
            </div>
        `;
    };
    
    // Check if mobile/tablet view
    const isMobile = () => window.innerWidth <= 480;
    const isTablet = () => window.innerWidth > 480 && window.innerWidth <= 1220; // Increased tablet breakpoint to match MkDocs
    
    // Add the try-out panel to the sidebar or create mobile version
    const addTryOutToSidebar = () => {
        const endpointInfo = getEndpointInfo();
        const tryOutPanel = createTryOutPanel(endpointInfo);
        
        if (isMobile()) {
            // Create mobile floating button and modal
            createMobileTryOut(tryOutPanel);
        } else if (isTablet()) {
            // Tablet: Create mobile interface but don't interfere with hamburger
            createMobileTryOut(tryOutPanel);
        } else {
            // Desktop: Add to sidebar
            const leftSidebar = document.querySelector('.md-sidebar--primary');
            if (leftSidebar) {
                const panelContainer = document.createElement('div');
                panelContainer.className = 'try-out-container';
                
                const parser = new DOMParser();
                const doc = parser.parseFromString(tryOutPanel, 'text/html');
                const elements = doc.body.children;
                while (elements.length > 0) {
                    panelContainer.appendChild(elements[0]);
                }
                leftSidebar.prepend(panelContainer);
            
                // Add response modal to body
                const modal = document.createElement('div');
                modal.id = 'responseModal';
                modal.style.display = 'none';
                modal.setAttribute('role', 'dialog');
                modal.setAttribute('aria-modal', 'true');
                modal.setAttribute('aria-label', 'API Response');
                
                const modalOverlay = document.createElement('div');
                modalOverlay.className = 'modal-overlay';
                modalOverlay.addEventListener('click', () => TryOutSidebar.closeResponseModal());
                
                const modalContent = document.createElement('div');
                modalContent.className = 'modal-content';
                
                const modalHeader = document.createElement('div');
                modalHeader.className = 'modal-header';
                
                const modalTitle = document.createElement('h3');
                modalTitle.textContent = 'API Response';
                
                const modalClose = document.createElement('button');
                modalClose.className = 'modal-close';
                modalClose.setAttribute('aria-label', 'Close');
                modalClose.textContent = '✕';
                modalClose.addEventListener('click', () => TryOutSidebar.closeResponseModal());
                
                modalHeader.appendChild(modalTitle);
                modalHeader.appendChild(modalClose);
                
                const modalBody = document.createElement('div');
                modalBody.className = 'modal-body';
                
                const responseHeader = document.createElement('div');
                responseHeader.className = 'response-header';
                
                const statusLabel = document.createElement('span');
                statusLabel.textContent = 'Status: ';
                
                const statusBadge = document.createElement('span');
                statusBadge.className = 'status-badge';
                statusBadge.id = 'modalStatusBadge';
                
                responseHeader.appendChild(statusLabel);
                responseHeader.appendChild(statusBadge);
                
                const responseBody = document.createElement('div');
                responseBody.className = 'response-body';
                responseBody.id = 'modalResponseBody';
                
                modalBody.appendChild(responseHeader);
                modalBody.appendChild(responseBody);
                
                modalContent.appendChild(modalHeader);
                modalContent.appendChild(modalBody);
                
                modal.appendChild(modalOverlay);
                modal.appendChild(modalContent);
                
                document.body.appendChild(modal);
                
                // Initialize tabs
                initTabs();
            }
        }
    };
    
    // Create mobile try-out interface
    const createMobileTryOut = (tryOutPanel) => {
        // Create floating action button
        const fab = document.createElement('div');
        fab.className = 'mobile-try-out-fab';
        fab.setAttribute('role', 'button');
        fab.setAttribute('tabindex', '0');
        fab.setAttribute('aria-label', 'Open Try It Out');
        fab.addEventListener('click', () => TryOutSidebar.openMobileTryOut());
        
        const fabIcon = document.createElement('span');
        fabIcon.textContent = '🚀';
        fab.appendChild(fabIcon);
        
        document.body.appendChild(fab);
        
        // Create mobile modal
        const mobileModal = document.createElement('div');
        mobileModal.className = 'mobile-try-out-modal';
        mobileModal.id = 'mobileTryOutModal';
        mobileModal.style.display = 'none';
        
        const mobileOverlay = document.createElement('div');
        mobileOverlay.className = 'mobile-modal-overlay';
        mobileOverlay.addEventListener('click', () => TryOutSidebar.closeMobileTryOut());
        
        const mobileContent = document.createElement('div');
        mobileContent.className = 'mobile-modal-content';
        
        const mobileHeader = document.createElement('div');
        mobileHeader.className = 'mobile-modal-header';
        
        const mobileTitle = document.createElement('h3');
        mobileTitle.textContent = '🚀 Try It Out';
        
        const mobileClose = document.createElement('button');
        mobileClose.className = 'mobile-modal-close';
        mobileClose.setAttribute('aria-label', 'Close');
        mobileClose.textContent = '✕';
        mobileClose.addEventListener('click', () => TryOutSidebar.closeMobileTryOut());
        
        mobileHeader.appendChild(mobileTitle);
        mobileHeader.appendChild(mobileClose);
        
        const mobileBody = document.createElement('div');
        mobileBody.className = 'mobile-modal-body';
        mobileBody.id = 'mobileTryOutBody';
        
        mobileContent.appendChild(mobileHeader);
        mobileContent.appendChild(mobileBody);
        
        mobileModal.appendChild(mobileOverlay);
        mobileModal.appendChild(mobileContent);
        
        document.body.appendChild(mobileModal);
        
        // Mount panel content into mobile body
        const parser = new DOMParser();
        const doc = parser.parseFromString(tryOutPanel, 'text/html');
        const panelEl = doc.querySelector('.try-out-sidebar');
        if (panelEl) {
            panelEl.classList.add('mobile-try-out');
            document.getElementById('mobileTryOutBody').appendChild(panelEl);
        }
        
        // Add response modal for mobile
        let responseModal = document.getElementById('responseModal');
        if (!responseModal) {
            responseModal = document.createElement('div');
            responseModal.id = 'responseModal';
            responseModal.style.display = 'none';
            responseModal.setAttribute('role', 'dialog');
            responseModal.setAttribute('aria-modal', 'true');
            responseModal.setAttribute('aria-label', 'API Response');
            
            const modalOverlay = document.createElement('div');
            modalOverlay.className = 'modal-overlay';
            modalOverlay.addEventListener('click', () => TryOutSidebar.closeResponseModal());
            
            const modalContent = document.createElement('div');
            modalContent.className = 'modal-content';
            
            const modalHeader = document.createElement('div');
            modalHeader.className = 'modal-header';
            
            const modalTitle = document.createElement('h3');
            modalTitle.textContent = 'API Response';
            
            const modalClose = document.createElement('button');
            modalClose.className = 'modal-close';
            modalClose.setAttribute('aria-label', 'Close');
            modalClose.textContent = '✕';
            modalClose.addEventListener('click', () => TryOutSidebar.closeResponseModal());
            
            modalHeader.appendChild(modalTitle);
            modalHeader.appendChild(modalClose);
            
            const modalBody = document.createElement('div');
            modalBody.className = 'modal-body';
            
            const responseHeader = document.createElement('div');
            responseHeader.className = 'response-header';
            
            const statusLabel = document.createElement('span');
            statusLabel.textContent = 'Status: ';
            
            const statusBadge = document.createElement('span');
            statusBadge.className = 'status-badge';
            statusBadge.id = 'modalStatusBadge';
            
            responseHeader.appendChild(statusLabel);
            responseHeader.appendChild(statusBadge);
            
            const responseBody = document.createElement('div');
            responseBody.className = 'response-body';
            responseBody.id = 'modalResponseBody';
            
            modalBody.appendChild(responseHeader);
            modalBody.appendChild(responseBody);
            
            modalContent.appendChild(modalHeader);
            modalContent.appendChild(modalBody);
            
            responseModal.appendChild(modalOverlay);
            responseModal.appendChild(modalContent);
            
            document.body.appendChild(responseModal);
        }
        
        // Initialize tabs for mobile
        setTimeout(() => initTabs(), 100);
    };
    
    // Initialize tabs
    const initTabs = () => {
        document.querySelectorAll('.try-out-sidebar .tab').forEach(tab => {
            tab.addEventListener('click', () => {
                // Remove active class from all tabs and contents
                document.querySelectorAll('.try-out-sidebar .tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.try-out-sidebar .tab-content').forEach(c => c.classList.remove('active'));
                
                // Add active class to clicked tab and corresponding content
                tab.classList.add('active');
                const tabName = tab.getAttribute('data-tab');
                document.getElementById(tabName + 'Tab').classList.add('active');
            });
        });
    };
    
    // Add try-out panel to sidebar
    addTryOutToSidebar();
    
    // Handle window resize
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            // Re-initialize on resize to handle mobile/desktop transitions
            const currentMobile = window.innerWidth <= 480;
            const currentTablet = window.innerWidth > 480 && window.innerWidth <= 1220;
            const fab = document.querySelector('.mobile-try-out-fab');
            const sidebar = document.querySelector('.md-sidebar--primary .try-out-sidebar');
            
            if ((currentMobile || currentTablet) && sidebar && !fab) {
                // Switched to mobile/tablet, need to create mobile interface
                location.reload(); // Simple solution to reinitialize
            } else if (!currentMobile && !currentTablet && fab && !sidebar) {
                // Switched to desktop, need to create sidebar interface
                location.reload(); // Simple solution to reinitialize
            }
        }, 250);
    });
});

// Create namespace to avoid global pollution
window.TryOutSidebar = {
    openMobileTryOut: function() {
        const modal = document.getElementById('mobileTryOutModal');
        if (modal) {
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';
        }
    },

    closeMobileTryOut: function() {
        const modal = document.getElementById('mobileTryOutModal');
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }
    },

    addQueryParam: function() {
        const container = document.getElementById('queryParams');
        if (!container) return;
        
        const kvItem = document.createElement('div');
        kvItem.className = 'kv-item';
        
        const nameInput = document.createElement('input');
        nameInput.type = 'text';
        nameInput.placeholder = 'Parameter name';
        nameInput.setAttribute('list', 'queryParamSuggestions');
        
        const valueInput = document.createElement('input');
        valueInput.type = 'text';
        valueInput.placeholder = 'Parameter value';
        
        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-btn';
        removeBtn.textContent = '✕';
        removeBtn.addEventListener('click', () => TryOutSidebar.removeKvItem(removeBtn));
        
        kvItem.appendChild(nameInput);
        kvItem.appendChild(valueInput);
        kvItem.appendChild(removeBtn);
        container.appendChild(kvItem);
    },

    addHeader: function() {
        const container = document.getElementById('requestHeaders');
        if (!container) return;
        
        const kvItem = document.createElement('div');
        kvItem.className = 'kv-item';
        
        const nameInput = document.createElement('input');
        nameInput.type = 'text';
        nameInput.placeholder = 'Header name';
        nameInput.setAttribute('list', 'headerSuggestions');
        
        const valueInput = document.createElement('input');
        valueInput.type = 'text';
        valueInput.placeholder = 'Header value';
        
        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-btn';
        removeBtn.textContent = '✕';
        removeBtn.addEventListener('click', () => TryOutSidebar.removeKvItem(removeBtn));
        
        kvItem.appendChild(nameInput);
        kvItem.appendChild(valueInput);
        kvItem.appendChild(removeBtn);
        container.appendChild(kvItem);
    },

    removeKvItem: function(button) {
        if (button && button.parentElement) {
            button.parentElement.remove();
            TryOutSidebar.updateUrlFromParams();
        }
    },

    updateUrlFromParams: function() {
        // This function is no longer needed since we don't show the full URL
    },

    closeResponseModal: function() {
        const modal = document.getElementById('responseModal');
        if (modal) {
            modal.style.display = 'none';
        }
    },

    showResponseModal: function(status, responseText) {
        const modal = document.getElementById('responseModal');
        const statusBadge = document.getElementById('modalStatusBadge');
        const responseBody = document.getElementById('modalResponseBody');
        
        if (modal && statusBadge && responseBody) {
            statusBadge.textContent = String(status);
            const code = Number(status);
            statusBadge.className = 'status-badge' + (Number.isFinite(code) ? ` status-${Math.floor(code/100)*100}` : '');
            
            try {
                const jsonResponse = JSON.parse(responseText);
                responseBody.textContent = JSON.stringify(jsonResponse, null, 2);
            } catch (e) {
                responseBody.textContent = responseText;
            }
            
            modal.style.display = 'block';
        }
    },

    validateRequiredParams: function() {
        const requiredInputs = document.querySelectorAll('#pathParams input[required]');
        const emptyParams = [];
        
        requiredInputs.forEach(input => {
            if (!input.value.trim()) {
                const paramName = input.getAttribute('data-param');
                emptyParams.push(paramName);
                input.classList.add('error');
                input.addEventListener('input', () => input.classList.remove('error'), { once: true });
            }
        });
        
        return emptyParams;
    }
};

// Legacy global functions for backward compatibility (deprecated)
function openMobileTryOut() { TryOutSidebar.openMobileTryOut(); }
function closeMobileTryOut() { TryOutSidebar.closeMobileTryOut(); }
function addQueryParam() { TryOutSidebar.addQueryParam(); }
function addHeader() { TryOutSidebar.addHeader(); }
function removeKvItem(button) { TryOutSidebar.removeKvItem(button); }
function updateUrlFromParams() { TryOutSidebar.updateUrlFromParams(); }
function closeResponseModal() { TryOutSidebar.closeResponseModal(); }
function showResponseModal(status, responseText) { TryOutSidebar.showResponseModal(status, responseText); }
function validateRequiredParams() { return TryOutSidebar.validateRequiredParams(); }

async function executeRequest() {
    const executeBtn = document.getElementById('executeBtn');
    if (!executeBtn) return;
    
    // Validate required parameters
    const emptyParams = TryOutSidebar.validateRequiredParams();
    if (emptyParams.length > 0) {
        alert(`Please fill in the required parameters: ${emptyParams.join(', ')}`);
        return;
    }
    
    // Update button state
    executeBtn.disabled = true;
    executeBtn.textContent = '';
    const spinner = document.createElement('div');
    spinner.className = 'spinner';
    const text = document.createTextNode(' Sending...');
    executeBtn.appendChild(spinner);
    executeBtn.appendChild(text);
    
    try {
        // Get base URL and construct full URL
        // Validate and normalize the Base URL, restricting scheme to http/https
        const baseInput = (document.getElementById('baseUrl').value || '').trim() || window.location.origin;
        let base;
        try {
            base = new URL(baseInput, window.location.origin);
        } catch (_) {
            throw new Error('Invalid Base URL');
        }
        if (!/^https?:$/.test(base.protocol)) {
            throw new Error('Base URL must use http or https');
        }
        const baseUrl = base.href;
        // Get endpoint info from the current page
        let path = '';
        let method = 'GET';
        
        // First, try to find the method badge and code element in the same paragraph
        const methodBadge = document.querySelector('.method-badge');
        if (methodBadge) {
            method = methodBadge.textContent.trim();
            
            // Look for a code element in the same parent or nearby
            const parent = methodBadge.closest('p, div, section');
            if (parent) {
                const codeElement = parent.querySelector('code');
                if (codeElement) {
                    path = codeElement.textContent.trim();
                }
            }
        }
        
        // Fallback: try to find in title
        if (!path) {
            const title = document.querySelector('h1');
            if (title) {
                const titleText = title.textContent.trim();
                const pathMatch = titleText.match(/([A-Z]+)\s+(.+)/);
                if (pathMatch) {
                    method = pathMatch[1];
                    path = pathMatch[2];
                }
            }
        }
        
        // Additional fallback - look for code blocks with paths
        if (!path) {
            const codeBlocks = document.querySelectorAll('code');
            for (const code of codeBlocks) {
                const text = code.textContent.trim();
                if (text.startsWith('/') && !text.includes('http')) {
                    path = text;
                    break;
                }
            }
        }
        
        // Clean up the path to handle HTML entities and special characters
        if (path) {
            // Use DOMParser to safely decode HTML entities
            const parser = new DOMParser();
            const doc = parser.parseFromString(`<div>${path}</div>`, 'text/html');
            const tempDiv = doc.querySelector('div');
            path = tempDiv ? (tempDiv.textContent || tempDiv.innerText || path) : path;
            
            // Remove any non-printable characters or replace problematic ones
            path = path.replace(/[^\x20-\x7E]/g, ''); // Remove non-ASCII printable characters
            path = path.replace(/¶/g, ''); // Specifically remove paragraph symbols
            path = path.trim();
        }
        
        console.log('Extracted path:', path);
        console.log('Extracted method:', method);
        
        // Ensure baseUrl doesn't end with slash and path starts with slash
        let cleanBaseUrl = baseUrl.replace(/\/$/, '');
        let cleanPath = path || '/api/endpoint';
        if (!cleanPath.startsWith('/')) {
            cleanPath = '/' + cleanPath;
        }
        
        let url = cleanBaseUrl + cleanPath;
        console.log('Initial URL:', url);
        
        // Replace path parameters
        const pathParams = document.querySelectorAll('#pathParams .kv-item');
        console.log('Found path params:', pathParams.length);
        
        pathParams.forEach((item, index) => {
            const label = item.querySelector('.param-label');
            const input = item.querySelector('input');
            if (label && input) {
                const paramName = label.textContent.trim();
                const paramValue = input.value.trim();
                console.log(`Param ${index}: ${paramName} = ${paramValue}`);
                
                if (paramName && paramValue) {
                    const beforeReplace = url;
                    const escaped = paramName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                    url = url.replace(new RegExp(`\\{${escaped}\\}`, 'g'), paramValue);
                    console.log(`URL after replacing {${paramName}}: ${beforeReplace} -> ${url}`);
                } else if (paramName && !paramValue) {
                    // This should not happen as validation should catch empty required params
                    console.warn(`Empty value for required parameter: ${paramName}`);
                    throw new Error(`Required parameter '${paramName}' has no value`);
                }
            }
        });
        
        // Clean up any remaining unreplaced parameters or malformed URLs
        const beforeCleanup = url;
        
        // Remove double slashes but preserve protocol slashes
        url = url.replace(/([^:])\/+/g, '$1/'); // Remove double slashes except after protocol
        url = url.replace(/\{[^}]*\}/g, ''); // Remove any remaining parameter placeholders
        
        // Don't remove trailing slash as it might be part of the endpoint
        
        console.log('Final URL:', beforeCleanup, '->', url);
        
        // Add query parameters
        const queryParams = {};
        document.querySelectorAll('#queryParams .kv-item').forEach(item => {
            const inputs = item.querySelectorAll('input');
            if (inputs.length >= 2) {
                const key = inputs[0].value.trim();
                const value = inputs[1].value.trim();
                if (key && value) {
                    queryParams[key] = value;
                }
            }
        });
        
        if (Object.keys(queryParams).length > 0) {
            const queryString = new URLSearchParams(queryParams).toString();
            url += (url.includes('?') ? '&' : '?') + queryString;
        }
        
        // Get headers
        const headers = {};
        document.querySelectorAll('#requestHeaders .kv-item').forEach(item => {
            const inputs = item.querySelectorAll('input');
            if (inputs.length >= 2) {
                const key = inputs[0].value.trim();
                const value = inputs[1].value.trim();
                if (key && value) {
                    headers[key] = value;
                }
            }
        });
        
        // Prepare request options
        const requestOptions = {
            method: method,
            headers: headers
        };
        
        // Add request body for POST, PUT, PATCH
        if (['POST', 'PUT', 'PATCH'].includes(method)) {
            const bodyInput = document.getElementById('requestBody');
            if (bodyInput && bodyInput.value.trim()) {
                try {
                    // Validate JSON
                    JSON.parse(bodyInput.value);
                    requestOptions.body = bodyInput.value;
                    if (!headers['Content-Type']) {
                        requestOptions.headers['Content-Type'] = 'application/json';
                    }
                } catch (e) {
                    throw new Error('Invalid JSON in request body');
                }
            }
        }
        
        // Send the request
        const response = await fetch(url, requestOptions);
        const responseText = await response.text();
        
        // Show response in modal
        TryOutSidebar.showResponseModal(response.status, responseText);
        
    } catch (error) {
        // Enhanced error handling with specific error types
        let errorMessage = 'Unknown error occurred';
        let errorType = 'Error';
        
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            errorType = 'Network Error';
            errorMessage = 'Failed to connect to the server. Please check your internet connection and try again.';
        } else if (error.name === 'SyntaxError' && error.message.includes('JSON')) {
            errorType = 'JSON Parse Error';
            errorMessage = 'Invalid JSON in request body. Please check your input and try again.';
        } else if (error.message.includes('CORS')) {
            errorType = 'CORS Error';
            errorMessage = 'Cross-origin request blocked. The server may not allow requests from this domain.';
        } else if (error.message) {
            errorMessage = error.message;
        }
        
        TryOutSidebar.showResponseModal(errorType, errorMessage);
    } finally {
        // Reset button
        executeBtn.disabled = false;
        executeBtn.textContent = '';
        const playIcon = document.createElement('span');
        playIcon.textContent = '▶';
        const text = document.createTextNode(' Execute Request');
        executeBtn.appendChild(playIcon);
        executeBtn.appendChild(text);
    }
}
