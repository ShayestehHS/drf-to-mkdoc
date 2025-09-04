document.addEventListener('DOMContentLoaded', function() {
    // Get endpoint information from the page
    const getEndpointInfo = () => {
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
            // Create a temporary element to decode HTML entities
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = path;
            path = tempDiv.textContent || tempDiv.innerText || path;
            
            // Remove any non-printable characters or replace problematic ones
            path = path.replace(/[^\x20-\x7E]/g, ''); // Remove non-ASCII printable characters
            path = path.replace(/¶/g, ''); // Specifically remove paragraph symbols
            path = path.trim();
        }
        
        return {
            method: method,
            path: path || '/api/endpoint',
            pathParams: path ? extractPathParams(path) : []
        };
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

    // Create the try-out panel HTML
    const createTryOutPanel = (endpointInfo) => {
        // Create path parameters HTML
        let pathParamsHtml = '';
        if (endpointInfo.pathParams.length > 0) {
            pathParamsHtml = `
                <div class="form-group">
                    <label class="form-label">Path Parameters</label>
                    <div class="kv-container" id="pathParams">
                        ${endpointInfo.pathParams.map(param => `
                            <div class="kv-item">
                                <label class="param-label">${param}</label>
                                <input type="text" placeholder="Enter ${param} value" data-param="${param}" required>
                            </div>
                        `).join('')}
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
                            ${Array.from(document.querySelectorAll('ul li code')).map(code => {
                                const paramName = code.textContent.trim();
                                return paramName ? `<option value="${paramName}">` : '';
                            }).join('')}
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
                // Clear existing sidebar content
                leftSidebar.innerHTML = '';
                
                // Create and append the try-out panel
                const panelContainer = document.createElement('div');
                panelContainer.innerHTML = tryOutPanel;
                leftSidebar.appendChild(panelContainer);
            
                // Add response modal to body
                const modal = document.createElement('div');
                modal.innerHTML = `
                    <div class="response-modal" id="responseModal" style="display: none;">
                        <div class="modal-overlay" onclick="closeResponseModal()"></div>
                        <div class="modal-content">
                            <div class="modal-header">
                                <h3>API Response</h3>
                                <button class="modal-close" onclick="closeResponseModal()">✕</button>
                            </div>
                            <div class="modal-body">
                                <div class="response-header">
                                    <span>Status: </span>
                                    <span class="status-badge" id="modalStatusBadge"></span>
                                </div>
                                <div class="response-body" id="modalResponseBody"></div>
                            </div>
                        </div>
                    </div>
                `;
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
        fab.innerHTML = `
            <div class="mobile-try-out-fab" onclick="openMobileTryOut()">
                <span>🚀</span>
            </div>
        `;
        document.body.appendChild(fab);
        
        // Create mobile modal
        const mobileModal = document.createElement('div');
        mobileModal.innerHTML = `
            <div class="mobile-try-out-modal" id="mobileTryOutModal" style="display: none;">
                <div class="mobile-modal-overlay" onclick="closeMobileTryOut()"></div>
                <div class="mobile-modal-content">
                    <div class="mobile-modal-header">
                        <h3>🚀 Try It Out</h3>
                        <button class="mobile-modal-close" onclick="closeMobileTryOut()">✕</button>
                    </div>
                    <div class="mobile-modal-body">
                        <div class="try-out-sidebar mobile-try-out">
                            ${tryOutPanel.replace(/<div class="try-out-sidebar">|<\/div>$/g, '').trim()}
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(mobileModal);
        
        // Add response modal for mobile
        const responseModal = document.createElement('div');
        responseModal.innerHTML = `
            <div class="response-modal" id="responseModal" style="display: none;">
                <div class="modal-overlay" onclick="closeResponseModal()"></div>
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>API Response</h3>
                        <button class="modal-close" onclick="closeResponseModal()">✕</button>
                    </div>
                    <div class="modal-body">
                        <div class="response-header">
                            <span>Status: </span>
                            <span class="status-badge" id="modalStatusBadge"></span>
                        </div>
                        <div class="response-body" id="modalResponseBody"></div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(responseModal);
        
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

// Global mobile functions
function openMobileTryOut() {
    const modal = document.getElementById('mobileTryOutModal');
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
}

function closeMobileTryOut() {
    const modal = document.getElementById('mobileTryOutModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// Global functions for the try-out panel
function addQueryParam() {
    const container = document.getElementById('queryParams');
    if (!container) return;
    
    const kvItem = document.createElement('div');
    kvItem.className = 'kv-item';
    kvItem.innerHTML = `
        <input type="text" placeholder="Parameter name" list="queryParamSuggestions">
        <input type="text" placeholder="Parameter value">
        <button class="remove-btn" onclick="removeKvItem(this)">✕</button>
    `;
    container.appendChild(kvItem);
}

function addHeader() {
    const container = document.getElementById('requestHeaders');
    if (!container) return;
    
    const kvItem = document.createElement('div');
    kvItem.className = 'kv-item';
    kvItem.innerHTML = `
        <input type="text" placeholder="Header name" list="headerSuggestions">
        <input type="text" placeholder="Header value">
        <button class="remove-btn" onclick="removeKvItem(this)">✕</button>
    `;
    container.appendChild(kvItem);
}

function removeKvItem(button) {
    if (button && button.parentElement) {
        button.parentElement.remove();
        updateUrlFromParams();
    }
}

function updateUrlFromParams() {
    // This function is no longer needed since we don't show the full URL
}

function closeResponseModal() {
    const modal = document.getElementById('responseModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function showResponseModal(status, responseText) {
    const modal = document.getElementById('responseModal');
    const statusBadge = document.getElementById('modalStatusBadge');
    const responseBody = document.getElementById('modalResponseBody');
    
    if (modal && statusBadge && responseBody) {
        statusBadge.textContent = status;
        statusBadge.className = `status-badge status-${Math.floor(status / 100) * 100}`;
        
        try {
            const jsonResponse = JSON.parse(responseText);
            responseBody.textContent = JSON.stringify(jsonResponse, null, 2);
        } catch (e) {
            responseBody.textContent = responseText;
        }
        
        modal.style.display = 'block';
    }
}

function validateRequiredParams() {
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

async function executeRequest() {
    const executeBtn = document.getElementById('executeBtn');
    if (!executeBtn) return;
    
    // Validate required parameters
    const emptyParams = validateRequiredParams();
    if (emptyParams.length > 0) {
        alert(`Please fill in the required parameters: ${emptyParams.join(', ')}`);
        return;
    }
    
    // Update button state
    executeBtn.disabled = true;
    executeBtn.innerHTML = '<div class="spinner"></div> Sending...';
    
    try {
        // Get base URL and construct full URL
        const baseUrl = document.getElementById('baseUrl').value.trim() || window.location.origin;
        
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
            // Create a temporary element to decode HTML entities
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = path;
            path = tempDiv.textContent || tempDiv.innerText || path;
            
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
                    // Replace both {paramName} and any remaining placeholders
                    url = url.replace(`{${paramName}}`, paramValue);
                    url = url.replace(new RegExp(`\\{${paramName}\\}`, 'g'), paramValue);
                    console.log(`URL after replacing {${paramName}}: ${beforeReplace} -> ${url}`);
                } else if (paramName) {
                    // If no value provided, remove the parameter placeholder to avoid issues
                    url = url.replace(`{${paramName}}`, '');
                    console.log(`Removed empty param {${paramName}}`);
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
        showResponseModal(response.status, responseText);
        
    } catch (error) {
        // Show error in modal
        showResponseModal('Error', `Error: ${error.message}`);
    } finally {
        // Reset button
        executeBtn.disabled = false;
        executeBtn.innerHTML = '<span>▶</span> Execute Request';
    }
}
