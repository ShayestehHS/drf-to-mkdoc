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
        // Close modal when clicking overlay
        const overlay = document.querySelector('.modal-overlay');
        if (overlay) {
            overlay.addEventListener('click', () => this.closeTryOut());
        }

        // Close modal with close button
        const closeButtons = document.querySelectorAll('.modal-close');
        closeButtons.forEach(btn => {
            btn.addEventListener('click', () => this.closeTryOut());
        });
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
        const modal = document.getElementById('tryOutModal');
        if (modal) {
            modal.classList.remove('show');
            modal.style.display = 'none';
            document.body.classList.remove('modal-open');
            
            // Hide response section
            const responseSection = document.querySelector('.response-section');
            if (responseSection) {
                responseSection.hidden = true;
            }
        }
    },

    openResponseModal: function() {
        const modal = document.getElementById('responseModal');
        if (modal) {
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

    closeResponseModal: function() {
        const modal = document.getElementById('responseModal');
        if (modal) {
            modal.classList.remove('show');
            modal.style.display = 'none';
        }
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
                statusBadge.textContent = String(status);
                const code = Number(status);
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
        // Only close if not already handled by modal's keyboard trap
        const modal = document.getElementById('tryOutModal');
        const responseModal = document.getElementById('responseModal');
        
        if (modal && !modal.contains(document.activeElement)) {
            ModalManager.closeTryOut();
        }
        if (responseModal && !responseModal.contains(document.activeElement)) {
            ModalManager.closeResponseModal();
        }
    }
});

// Export for global access
window.ModalManager = ModalManager;

// Create TryOutSidebar alias for backward compatibility
window.TryOutSidebar = {
    closeResponseModal: function() {
        ModalManager.closeResponseModal();
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
