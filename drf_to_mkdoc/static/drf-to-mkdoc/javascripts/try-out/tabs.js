// Tab management functionality
const TabManager = {
    init: function() {
        document.querySelectorAll('.try-out-form .tab').forEach(tab => {
            tab.addEventListener('click', () => {
                this.switchTab(tab);
            });
        });
    },

    switchTab: function(activeTab) {
        // Remove active class from all tabs and contents
        document.querySelectorAll('.try-out-form .tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.try-out-form .tab-content').forEach(c => c.classList.remove('active'));

        // Add active class to clicked tab
        activeTab.classList.add('active');
        
        // Show corresponding content
        const tabName = activeTab.getAttribute('data-tab');
        const content = document.getElementById(tabName + 'Tab');
        if (content) {
            content.classList.add('active');
        }
    }
};

// Initialize tabs when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    TabManager.init();
});

// Export for global access
window.TabManager = TabManager;
