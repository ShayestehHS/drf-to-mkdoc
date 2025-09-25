// Main try-out functionality - combines all components
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    if (window.TabManager) {
        TabManager.init();
    }
    
    if (window.FormManager) {
        FormManager.init();
    }
    
    if (window.TryOutSuggestions) {
        TryOutSuggestions.init();
    }
    
    // Initialize modal functionality
    if (window.ModalManager) {
        // Modal is already initialized through its own file
        console.log('Try-out modal functionality loaded');
    }
    
    // Initialize request executor
    if (window.RequestExecutor) {
        console.log('Try-out request executor loaded');
    }
    
    console.log('Try-out functionality fully initialized');
});

// Legacy compatibility - maintain old interface
window.TryOutSidebar = {
    openTryOut: () => window.ModalManager?.openTryOut(),
    closeTryOut: () => window.ModalManager?.closeTryOut(),
    closeResponseModal: () => window.ModalManager?.closeResponseModal(),
    showResponseModal: (status, responseText, responseTime) => window.ModalManager?.showResponseModal(status, responseText, responseTime),
    addQueryParam: () => window.FormManager?.addQueryParam(),
    addHeader: () => window.FormManager?.addHeader(),
    removeKvItem: (button) => window.FormManager?.removeKvItem(button),
    validateRequiredParams: () => window.FormManager?.validateRequiredParams()
};

// Additional global functions for HTML onclick handlers
window.TryOutForm = {
    resetForm: () => window.FormManager?.resetForm(),
    sendRequest: () => window.RequestExecutor?.executeRequest()
};

// Global proxy functions for template onclick handlers
window.resetForm = () => window.TryOutForm?.resetForm?.();
window.executeRequest = () => window.TryOutForm?.sendRequest?.();
