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
        }
    },

    closeResponseModal: function() {
        const modal = document.getElementById('responseModal');
        if (modal) {
            modal.classList.remove('show');
            modal.style.display = 'none';
        }
    },

    showResponseModal: function(status, responseText, responseTime) {
        const modal = document.getElementById('responseModal');
        const statusBadge = document.getElementById('modalStatusBadge');
        const responseBody = document.getElementById('modalResponseBody');
        const responseInfo = document.getElementById('responseInfo');

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

            if (responseInfo && responseTime) {
                responseInfo.textContent = `Response time: ${responseTime}ms`;
            }

            this.openResponseModal();
        }
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
