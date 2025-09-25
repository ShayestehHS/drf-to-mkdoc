// Tab management functionality
const TabManager = {
    init: function() {
        document.querySelectorAll('.try-out-form .tab, .smart-tabs .tab, .response-tabs .tab').forEach(tab => {
            tab.addEventListener('click', () => {
                this.switchTab(tab);
            });
            
            // Add keyboard support
            tab.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.switchTab(tab);
                }
            });
        });
    },

    switchTab: function(activeTab) {
        const tabContainer = activeTab.closest('.smart-tabs, .response-tabs, .try-out-form');
        if (!tabContainer) return;

        // Remove active class from all tabs in this container
        tabContainer.querySelectorAll('.tab').forEach(t => {
            t.classList.remove('active');
            t.setAttribute('aria-selected', 'false');
        });

        // Remove active class from all tab content
        const contentContainer = tabContainer.parentElement || document;
        contentContainer.querySelectorAll('.tab-content').forEach(c => {
            c.classList.remove('active');
        });

        // Add active class to clicked tab and its content
        activeTab.classList.add('active');
        activeTab.setAttribute('aria-selected', 'true');
        
        // Show corresponding content
        const contentId = activeTab.getAttribute('aria-controls') || activeTab.getAttribute('data-tab');
        let content;
        
        if (contentId) {
            content = document.getElementById(contentId) || document.getElementById(contentId + 'Tab');
            if (content) {
                content.classList.add('active');
            }
        }
        
        // Debug logging
        console.log('Tab switched to:', contentId, 'Content element:', content);
    }
};

// Initialize tabs when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    TabManager.init();

    // Also initialize when modal is shown (for dynamic content)
    const modal = document.getElementById('tryOutModal');
    if (modal) {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    if (modal.classList.contains('show')) {
                        // Re-initialize tabs when modal is shown
                        setTimeout(() => TabManager.init(), 100);
                    }
                }
            });
        });
        observer.observe(modal, { attributes: true });
    }
});

// Export for global access
window.TabManager = TabManager;
