// Modal management functionality
const ModalManager = {
    init: function() {
        this.setupKeyboardTraps();
        this.setupEventListeners();
    },

    setupKeyboardTraps: function() {
        const modal = document.getElementById('tryOutModal');
        if (!modal) return;
        
        // Trap focus within modal when open
        modal.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                // Check if response modal is open first
                const responseModal = document.getElementById('responseModal');
                if (responseModal && responseModal.classList.contains('show')) {
                    // Don't close tryOutModal if response modal is open
                    return;
                }
                this.closeTryOut();
            }
            
            if (e.key === 'Tab') {
                const focusableElements = modal.querySelectorAll(
                    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
                );
                const firstFocusable = focusableElements[0];
                const lastFocusable = focusableElements[focusableElements.length - 1];
                
                if (e.shiftKey) {
                    if (document.activeElement === firstFocusable) {
                        lastFocusable.focus();
                        e.preventDefault();
                    }
                } else {
                    if (document.activeElement === lastFocusable) {
                        firstFocusable.focus();
                        e.preventDefault();
                    }
                }
            }
        });
    },

    setupEventListeners: function() {
        // Close modal when clicking overlay - only for tryOutModal
        const modal = document.getElementById('tryOutModal');
        if (modal) {
            const overlay = modal.querySelector('.modal-overlay');
            if (overlay) {
                overlay.addEventListener('click', (e) => {
                    // Don't close if clicking inside the response modal
                    const responseModal = document.getElementById('responseModal');
                    if (responseModal && responseModal.contains(e.target)) {
                        return;
                    }
                    // Only close if clicking the overlay itself, not child elements
                    if (e.target === overlay) {
                        this.closeTryOut();
                    }
                });
            }

            // Close modal with close button - only buttons inside tryOutModal (not response modal)
            const closeButtons = modal.querySelectorAll('.modal-close');
            closeButtons.forEach(btn => {
                // Skip buttons that are inside the response modal
                const responseModal = document.getElementById('responseModal');
                if (responseModal && responseModal.contains(btn)) {
                    return;
                }
                btn.addEventListener('click', (e) => {
                    e.stopPropagation(); // Prevent event bubbling
                    this.closeTryOut();
                });
            });
        }
    },
    openTryOut: function() {
        const modal = document.getElementById('tryOutModal');
        if (modal) {
            modal.classList.add('show');
            modal.style.display = 'flex';
            document.body.classList.add('modal-open');
            
            // Focus management
            setTimeout(() => {
                const firstInput = modal.querySelector('input, button');
                if (firstInput) {
                    firstInput.focus();
                }
            }, 100);
            
            // Reinitialize components for dynamic content
            setTimeout(() => {
                if (window.FormManager) {
                    window.FormManager.init();
                }
                if (window.TryOutSuggestions) {
                    window.TryOutSuggestions.init();
                }
            }, 150);
        }
    },

    closeTryOut: function() {
        // Don't close if response modal is open
        const responseModal = document.getElementById('responseModal');
        if (responseModal && responseModal.classList.contains('show')) {
            return;
        }
        
        const modal = document.getElementById('tryOutModal');
        if (modal) {
            modal.classList.remove('show');
            modal.style.display = 'none';
            document.body.classList.remove('modal-open');
            
            // Hide response section
            const responseSection = modal.querySelector('.response-section');
            if (responseSection) {
                responseSection.hidden = true;
            }
            
            // Reset auth prompt state when modal closes
            if (window.FormManager && typeof window.FormManager.resetAuthPromptState === 'function') {
                window.FormManager.resetAuthPromptState();
            }
            
            // Cleanup event listeners to prevent memory leaks
            if (window.FormManager && typeof window.FormManager.cleanup === 'function') {
                window.FormManager.cleanup();
            }
            
            // Reset auth handler state
            if (window.AuthHandler && typeof window.AuthHandler.reset === 'function') {
                window.AuthHandler.reset();
            }
        }
    },

    openResponseModal: function() {
        const modal = document.getElementById('responseModal');
        if (modal) {
            // Show the response section container if it exists
            const responseSection = modal.closest('.response-section');
            if (responseSection) {
                responseSection.hidden = false;
            }
            
            modal.classList.add('show');
            modal.style.display = 'flex';
            
            // Reinitialize tabs for response modal
            setTimeout(() => {
                if (window.TabManager) {
                    window.TabManager.init();
                }
            }, 100);
        }
    },

    closeResponseModal: function(event) {
        // Prevent event from bubbling to tryOutModal handlers
        if (event) {
            event.stopPropagation();
        }
        const modal = document.getElementById('responseModal');
        if (modal) {
            modal.classList.remove('show');
            modal.style.display = 'none';
            
            // Also hide the response section container if it exists
            // The response modal is nested inside .response-section in the try-out modal
            const responseSection = modal.closest('.response-section');
            if (responseSection) {
                responseSection.hidden = true;
            }
        }
    },

    getStatusText: function(statusCode) {
        const statusMap = {
            // 1xx Informational
            100: 'Continue',
            101: 'Switching Protocols',
            102: 'Processing',
            103: 'Early Hints',
            
            // 2xx Success
            200: 'OK',
            201: 'Created',
            202: 'Accepted',
            203: 'Non-Authoritative Information',
            204: 'No Content',
            205: 'Reset Content',
            206: 'Partial Content',
            207: 'Multi-Status',
            208: 'Already Reported',
            226: 'IM Used',
            
            // 3xx Redirection
            300: 'Multiple Choices',
            301: 'Moved Permanently',
            302: 'Found',
            303: 'See Other',
            304: 'Not Modified',
            305: 'Use Proxy',
            307: 'Temporary Redirect',
            308: 'Permanent Redirect',
            
            // 4xx Client Error
            400: 'Bad Request',
            401: 'Unauthorized',
            402: 'Payment Required',
            403: 'Forbidden',
            404: 'Not Found',
            405: 'Method Not Allowed',
            406: 'Not Acceptable',
            407: 'Proxy Authentication Required',
            408: 'Request Timeout',
            409: 'Conflict',
            410: 'Gone',
            411: 'Length Required',
            412: 'Precondition Failed',
            413: 'Payload Too Large',
            414: 'URI Too Long',
            415: 'Unsupported Media Type',
            416: 'Range Not Satisfiable',
            417: 'Expectation Failed',
            418: 'I\'m a teapot',
            421: 'Misdirected Request',
            422: 'Unprocessable Entity',
            423: 'Locked',
            424: 'Failed Dependency',
            425: 'Too Early',
            426: 'Upgrade Required',
            428: 'Precondition Required',
            429: 'Too Many Requests',
            431: 'Request Header Fields Too Large',
            451: 'Unavailable For Legal Reasons',
            
            // 5xx Server Error
            500: 'Internal Server Error',
            501: 'Not Implemented',
            502: 'Bad Gateway',
            503: 'Service Unavailable',
            504: 'Gateway Timeout',
            505: 'HTTP Version Not Supported',
            506: 'Variant Also Negotiates',
            507: 'Insufficient Storage',
            508: 'Loop Detected',
            510: 'Not Extended',
            511: 'Network Authentication Required'
        };
        
        return statusMap[statusCode] || 'Unknown Status';
    },

    showResponseModal: function(status, responseText, responseTime, responseHeaders, requestHeaders) {
        const modal = document.getElementById('responseModal');
        const statusBadge = document.getElementById('modalStatusBadge');
        const responseBody = document.getElementById('modalResponseBody');
        const responseInfo = document.getElementById('responseInfo');
        const headersList = document.getElementById('responseHeadersList');
        const timeElement = document.getElementById('responseTime');
        const sizeElement = document.getElementById('responseSize');

        if (modal && statusBadge && responseBody) {
            // Update time and size stats
            if (timeElement && responseTime !== null && responseTime !== undefined) {
                timeElement.textContent = `${responseTime} ms`;
            }
            
            if (sizeElement && responseText) {
                const sizeInBytes = new Blob([responseText]).size;
                const formattedSize = this.formatSize(sizeInBytes);
                sizeElement.textContent = formattedSize;
            }

            // Handle error status
            if (status === 'Error') {
                statusBadge.textContent = 'Error';
                statusBadge.className = 'status-badge status-error';
                responseBody.textContent = responseText;
                if (responseInfo) {
                    responseInfo.textContent = 'Request failed';
                }
            } else {
                // Handle regular response
                const code = Number(status);
                const statusText = Number.isFinite(code) ? this.getStatusText(code) : '';
                if (statusText && statusText !== 'Unknown Status') {
                    statusBadge.textContent = `${status} ${statusText}`;
                } else {
                    statusBadge.textContent = String(status);
                }
                statusBadge.className = 'status-badge' + (Number.isFinite(code) ? ` status-${Math.floor(code/100)}xx` : '');

                try {
                    const jsonResponse = JSON.parse(responseText);
                    
                    // Show formatted JSON response
                    responseBody.textContent = JSON.stringify(jsonResponse, null, 2);
                } catch (e) {
                    // Handle non-JSON response
                    if (code >= 400) {
                        responseBody.innerHTML = `<div class="error-message">
                            <div class="error-title">Error Response</div>
                            <pre class="error-content">${responseText}</pre>
                        </div>`;
                    } else {
                        responseBody.innerHTML = `<pre class="error-content">${responseText}</pre>`;
                    }
                }

                if (responseInfo) {
                    responseInfo.textContent = '';
                }
            }

            // Display headers
            if (headersList) {
                this.displayHeaders(headersList, responseHeaders, requestHeaders);
            }

            this.openResponseModal();
        }
    },

    displayHeaders: function(headersList, responseHeaders, requestHeaders) {
        headersList.innerHTML = '';

        // Create response headers section
        if (responseHeaders && Object.keys(responseHeaders).length > 0) {
            const responseSection = document.createElement('div');
            responseSection.className = 'headers-section';
            
            const responseTitle = document.createElement('h4');
            responseTitle.textContent = `Response Headers (${Object.keys(responseHeaders).length})`;
            responseTitle.className = 'headers-title';
            responseSection.appendChild(responseTitle);

            const responseList = document.createElement('div');
            responseList.className = 'headers-grid';
            
            // Sort headers alphabetically
            const sortedResponseHeaders = Object.entries(responseHeaders).sort(([a], [b]) => a.toLowerCase().localeCompare(b.toLowerCase()));
            
            sortedResponseHeaders.forEach(([key, value]) => {
                const headerItem = document.createElement('div');
                headerItem.className = 'header-item';
                
                const headerKey = document.createElement('div');
                headerKey.className = 'header-key';
                headerKey.textContent = key;
                
                const headerValue = document.createElement('div');
                headerValue.className = 'header-value';
                
                // Special formatting for cookies
                if (key.toLowerCase() === 'set-cookie') {
                    const cookieList = document.createElement('div');
                    cookieList.className = 'cookie-list';
                    
                    // Handle multiple Set-Cookie headers
                    const cookies = Array.isArray(value) ? value : [value];
                    cookies.forEach(cookie => {
                        const cookieItem = document.createElement('div');
                        cookieItem.className = 'cookie-item';
                        cookieItem.textContent = cookie;
                        cookieList.appendChild(cookieItem);
                    });
                    
                    headerValue.appendChild(cookieList);
                } else {
                    headerValue.textContent = value;
                }
                
                headerItem.appendChild(headerKey);
                headerItem.appendChild(headerValue);
                responseList.appendChild(headerItem);
            });
            
            responseSection.appendChild(responseList);
            headersList.appendChild(responseSection);
        }

        // Create request headers section
        if (requestHeaders && Object.keys(requestHeaders).length > 0) {
            const requestSection = document.createElement('div');
            requestSection.className = 'headers-section';
            
            const requestTitle = document.createElement('h4');
            requestTitle.textContent = `Request Headers (${Object.keys(requestHeaders).length})`;
            requestTitle.className = 'headers-title';
            requestSection.appendChild(requestTitle);

            const requestList = document.createElement('div');
            requestList.className = 'headers-grid';
            
            // Sort headers alphabetically
            const sortedRequestHeaders = Object.entries(requestHeaders).sort(([a], [b]) => a.toLowerCase().localeCompare(b.toLowerCase()));
            
            sortedRequestHeaders.forEach(([key, value]) => {
                const headerItem = document.createElement('div');
                headerItem.className = 'header-item';
                
                const headerKey = document.createElement('div');
                headerKey.className = 'header-key';
                headerKey.textContent = key;
                
                const headerValue = document.createElement('div');
                headerValue.className = 'header-value';
                
                // Special formatting for cookies
                if (key.toLowerCase() === 'cookie') {
                    const cookieList = document.createElement('div');
                    cookieList.className = 'cookie-list';
                    
                    // Split cookies by semicolon and display each on a new line
                    const cookies = value.split(';').map(c => c.trim()).filter(c => c);
                    cookies.forEach(cookie => {
                        const cookieItem = document.createElement('div');
                        cookieItem.className = 'cookie-item';
                        cookieItem.textContent = cookie;
                        cookieList.appendChild(cookieItem);
                    });
                    
                    headerValue.appendChild(cookieList);
                } else {
                    headerValue.textContent = value;
                }
                
                headerItem.appendChild(headerKey);
                headerItem.appendChild(headerValue);
                requestList.appendChild(headerItem);
            });
            
            requestSection.appendChild(requestList);
            headersList.appendChild(requestSection);
        }

        // Show message if no headers
        if ((!responseHeaders || Object.keys(responseHeaders).length === 0) && 
            (!requestHeaders || Object.keys(requestHeaders).length === 0)) {
            const noHeadersMsg = document.createElement('div');
            noHeadersMsg.className = 'no-headers-message';
            noHeadersMsg.textContent = 'No headers available';
            headersList.appendChild(noHeadersMsg);
        }
    },

    formatSize: function(bytes) {
        if (bytes === 0) return '0 B';
        
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
};

// Initialize modal functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    ModalManager.init();
});

// Global keyboard navigation
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const responseModal = document.getElementById('responseModal');
        const tryOutModal = document.getElementById('tryOutModal');
        
        // If response modal is open, close it first (it's on top)
        if (responseModal && responseModal.classList.contains('show')) {
            ModalManager.closeResponseModal();
            e.stopPropagation(); // Prevent closing tryOutModal
        } else if (tryOutModal && tryOutModal.classList.contains('show')) {
            // Only close tryOutModal if response modal is not open
            ModalManager.closeTryOut();
        }
    }
});

// Export for global access
window.ModalManager = ModalManager;

// Create TryOutSidebar alias for backward compatibility
window.TryOutSidebar = {
    closeResponseModal: function(event) {
        ModalManager.closeResponseModal(event);
    },
    
    closeTryOut: function() {
        ModalManager.closeTryOut();
    },
    
    addQueryParam: function(paramName) {
        if (window.FormManager && window.FormManager.addQueryParam) {
            return window.FormManager.addQueryParam(paramName);
        }
    },
    
    removeKvItem: function(button) {
        if (window.FormManager && window.FormManager.removeKvItem) {
            return window.FormManager.removeKvItem(button);
        }
    }
};
