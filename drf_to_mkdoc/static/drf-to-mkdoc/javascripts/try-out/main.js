// Main try-out functionality - combines all components
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tabs
    TabManager.init();
    
    // Initialize suggestions if available
    if (window.TryOutSuggestions) {
        TryOutSuggestions.init();
    }
});

// Legacy compatibility - maintain old interface
window.TryOutSidebar = {
    openTryOut: () => ModalManager.openTryOut(),
    closeTryOut: () => ModalManager.closeTryOut(),
    closeResponseModal: () => ModalManager.closeResponseModal(),
    showResponseModal: (status, responseText, responseTime) => ModalManager.showResponseModal(status, responseText, responseTime),
    addQueryParam: () => FormManager.addQueryParam(),
    addHeader: () => FormManager.addHeader(),
    removeKvItem: (button) => FormManager.removeKvItem(button),
    validateRequiredParams: () => FormManager.validateRequiredParams()
};
