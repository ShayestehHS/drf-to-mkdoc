// Tab management functionality
const TabManager = {
    init: function() {
        // Initialize try-out form tabs
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
        
        // Initialize example tabs
        document.querySelectorAll('.example-tabs .example-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                this.switchExampleTab(tab);
            });
            
            // Add keyboard support
            tab.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.switchExampleTab(tab);
                }
            });
        });
        
        // Initialize response subtabs
        document.querySelectorAll('.response-subtabs .response-subtab').forEach(tab => {
            tab.addEventListener('click', () => {
                this.switchResponseSubtab(tab);
            });
            
            // Add keyboard support
            tab.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.switchResponseSubtab(tab);
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
        
        // If headers tab is opened, ensure auth prompt is visible if needed
        if (contentId === 'headersTab' || contentId === 'headers') {
            if (window.FormManager && typeof window.FormManager.showAuthPrompt === 'function') {
                // Reset state first, then show prompt
                if (typeof window.FormManager.resetAuthPromptState === 'function') {
                    window.FormManager.resetAuthPromptState();
                }
                setTimeout(() => {
                    window.FormManager.showAuthPrompt();
                }, 100);
            }
        }
        
        // Debug logging
        console.log('Tab switched to:', contentId, 'Content element:', content);
    },
    
    switchExampleTab: function(activeTab) {
        const tabContainer = activeTab.closest('.example-tabs');
        if (!tabContainer) return;
        
        const container = tabContainer.closest('.example-tabs-container');
        if (!container) return;

        // Remove active class from all tabs in this container
        tabContainer.querySelectorAll('.example-tab').forEach(t => {
            t.classList.remove('active');
            t.setAttribute('aria-selected', 'false');
        });

        // Remove active class from all tab content
        container.querySelectorAll('.example-tab-content').forEach(c => {
            c.classList.remove('active');
        });

        // Add active class to clicked tab and its content
        activeTab.classList.add('active');
        activeTab.setAttribute('aria-selected', 'true');
        
        // Show corresponding content
        const contentId = activeTab.getAttribute('aria-controls');
        if (contentId) {
            const content = document.getElementById(contentId);
            if (content) {
                content.classList.add('active');
                // Reset subtabs to show JSON first when switching examples
                const subtabsContainer = content.querySelector('.response-subtabs-container');
                if (subtabsContainer) {
                    const firstSubtab = subtabsContainer.querySelector('.response-subtab');
                    if (firstSubtab) {
                        this.switchResponseSubtab(firstSubtab);
                    }
                }
            }
        }
    },
    
    switchResponseSubtab: function(activeTab) {
        const tabContainer = activeTab.closest('.response-subtabs');
        if (!tabContainer) return;
        
        const container = tabContainer.closest('.response-subtabs-container');
        if (!container) return;

        // Remove active class from all subtabs in this container
        tabContainer.querySelectorAll('.response-subtab').forEach(t => {
            t.classList.remove('active');
            t.setAttribute('aria-selected', 'false');
        });

        // Remove active class from all subtab content
        container.querySelectorAll('.response-subtab-content').forEach(c => {
            c.classList.remove('active');
        });

        // Add active class to clicked subtab and its content
        activeTab.classList.add('active');
        activeTab.setAttribute('aria-selected', 'true');
        
        // Show corresponding content
        const contentId = activeTab.getAttribute('aria-controls');
        if (contentId) {
            const content = document.getElementById(contentId);
            if (content) {
                content.classList.add('active');
            }
        }
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
