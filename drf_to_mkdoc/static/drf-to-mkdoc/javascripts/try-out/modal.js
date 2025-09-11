// Modal management functionality
const ModalManager = {
    openTryOut: function() {
        const modal = document.getElementById('tryOutModal');
        if (modal) {
            modal.classList.add('show');
            modal.style.display = 'flex';
            document.body.classList.add('modal-open');
            
            // Focus management
            const firstInput = modal.querySelector('input, button');
            if (firstInput) {
                firstInput.focus();
            }
        }
    },

    closeTryOut: function() {
        const modal = document.getElementById('tryOutModal');
        if (modal) {
            modal.classList.remove('show');
            modal.style.display = 'none';
            document.body.classList.remove('modal-open');
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

// Keyboard navigation
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        ModalManager.closeTryOut();
        ModalManager.closeResponseModal();
    }
});

// Export for global access
window.ModalManager = ModalManager;
