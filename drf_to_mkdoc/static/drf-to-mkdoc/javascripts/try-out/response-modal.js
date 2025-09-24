// Response modal functionality
const ResponseModalManager = {
    init: function() {
        // Tab switching
        const tabs = document.querySelectorAll('.response-tabs .tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab));
        });

        // Initialize syntax highlighting
        this.initializePrism();
    },

    switchTab: function(tab) {
        if (!tab) return;
        
        // Remove active class from all tabs and content
        document.querySelectorAll('.response-tabs .tab').forEach(t => {
            if (t && t.classList) {
                t.classList.remove('active');
                t.setAttribute('aria-selected', 'false');
            }
        });
        document.querySelectorAll('.tab-content').forEach(c => {
            if (c && c.classList) {
                c.classList.remove('active');
            }
        });

        // Add active class to clicked tab and its content
        if (tab.classList) {
            tab.classList.add('active');
            tab.setAttribute('aria-selected', 'true');
        }
        const contentId = tab.getAttribute('aria-controls');
        const contentElement = document.getElementById(contentId);
        if (contentElement && contentElement.classList) {
            contentElement.classList.add('active');
        }
    },

    copyResponse: function() {
        const responseBody = document.getElementById('modalResponseBody');
        if (!responseBody) return;
        
        const responseText = responseBody.textContent;
        if (navigator.clipboard) {
            navigator.clipboard.writeText(responseText).then(() => {
                this.showToast('Response copied to clipboard');
            }).catch(() => {
                this.showToast('Failed to copy response');
            });
        } else {
            this.showToast('Clipboard not supported');
        }
    },

    downloadResponse: function() {
        const responseBody = document.getElementById('modalResponseBody');
        if (!responseBody) return;
        
        const responseText = responseBody.textContent;
        const blob = new Blob([responseText], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'response.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        this.showToast('Response downloaded');
    },

    formatResponse: function() {
        try {
            const responseBody = document.getElementById('modalResponseBody');
            if (!responseBody) return;
            
            const content = responseBody.textContent;
            if (!content.trim()) return;
            
            try {
                const parsed = JSON.parse(content);
                responseBody.textContent = JSON.stringify(parsed, null, 2);
            } catch (e) {
                // If not JSON, just return as is
                console.log('Response is not valid JSON, skipping formatting');
            }
        } catch (error) {
            console.error('Error formatting response:', error);
        }
    },

    collapseAll: function() {
        const responseBody = document.getElementById('modalResponseBody');
        if (!responseBody) return;
        
        // Simple collapse - replace newlines with spaces for basic collapse
        const content = responseBody.textContent;
        if (content) {
            responseBody.textContent = content.replace(/\n\s*/g, ' ').trim();
        }
    },

    expandAll: function() {
        const responseBody = document.getElementById('modalResponseBody');
        if (!responseBody) return;
        
        const content = responseBody.textContent;
        if (!content.trim()) return;
        
        try {
            // Try to format as JSON first
            const parsed = JSON.parse(content);
            responseBody.textContent = JSON.stringify(parsed, null, 2);
        } catch (e) {
            // If not JSON, just restore original formatting
            responseBody.textContent = content;
        }
    },

    showToast: function(message) {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #333;
            color: white;
            padding: 12px 20px;
            border-radius: 4px;
            z-index: 10000;
            font-size: 14px;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        
        // Show toast
        setTimeout(() => {
            toast.style.opacity = '1';
        }, 10);
        
        // Hide toast after 3 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 3000);
    },

    initializePrism: function() {
        // Basic syntax highlighting placeholder
        // This would integrate with Prism.js if available
        console.log('Syntax highlighting initialized');
    }
};

// Export for global access
window.ResponseModalManager = ResponseModalManager;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    ResponseModalManager.init();
});
