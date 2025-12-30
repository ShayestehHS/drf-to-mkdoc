/**
 * Query Parameters Expandable Tables
 * Handles expand/collapse functionality for query parameter tables
 */

(function() {
    'use strict';

    /**
     * Initialize query parameters functionality
     */
    function initQueryParameters() {
        // Handle section header toggles
        const sectionHeaders = document.querySelectorAll('.query-params-header');
        sectionHeaders.forEach(header => {
            header.addEventListener('click', function() {
                const isExpanded = this.getAttribute('aria-expanded') === 'true';
                const contentId = this.getAttribute('aria-controls');
                const content = document.getElementById(contentId);
                
                if (content) {
                    if (isExpanded) {
                        // Collapse
                        this.setAttribute('aria-expanded', 'false');
                        collapseContent(content);
                    } else {
                        // Expand
                        this.setAttribute('aria-expanded', 'true');
                        expandContent(content);
                    }
                }
            });

            // Keyboard support
            header.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.click();
                }
            });
        });

        // Initialize tabs - ensure first tab is active
        initializeTabs();

        // Handle tab switching
        const tabs = document.querySelectorAll('.query-params-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                switchQueryParamsTab(this);
            });

            // Keyboard support for tabs
            tab.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.click();
                } else if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                    e.preventDefault();
                    navigateTabs(this, e.key === 'ArrowRight');
                }
            });
        });

    }

    /**
     * Initialize tabs - activate first tab if none is active
     */
    function initializeTabs() {
        const tabContainers = document.querySelectorAll('.query-params-content');
        tabContainers.forEach(container => {
            const tabs = container.querySelectorAll('.query-params-tab');
            const activeTab = container.querySelector('.query-params-tab.active');
            
            // If no tab is active, activate the first one
            if (!activeTab && tabs.length > 0) {
                switchQueryParamsTab(tabs[0]);
            }
        });
    }

    /**
     * Expand content section
     */
    function expandContent(content) {
        // Set max-height to actual height for smooth animation
        content.style.maxHeight = content.scrollHeight + 'px';
        
        // Trigger reflow to ensure animation
        content.offsetHeight;
        
        // Add expanded class for additional styling if needed
        content.classList.add('expanded');
        
        // Re-initialize tabs inside expanded content (for schema sub-tabs, etc.)
        // This ensures tabs are clickable after the section expands
        if (window.TabManager && typeof window.TabManager.init === 'function') {
            // Use setTimeout to ensure DOM is ready after expansion animation
            setTimeout(() => {
                window.TabManager.init();
            }, 150);
        }
    }

    /**
     * Collapse content section
     */
    function collapseContent(content) {
        // Set max-height to current height
        content.style.maxHeight = content.scrollHeight + 'px';
        
        // Trigger reflow
        content.offsetHeight;
        
        // Animate to 0
        requestAnimationFrame(() => {
            content.style.maxHeight = '0';
            content.classList.remove('expanded');
        });
    }


    /**
     * Switch query parameters tab
     */
    function switchQueryParamsTab(activeTab) {
        const tabContainer = activeTab.closest('.query-params-content');
        if (!tabContainer) return;

        // Remove active class from all tabs in this container
        tabContainer.querySelectorAll('.query-params-tab').forEach(t => {
            t.classList.remove('active');
            t.setAttribute('aria-selected', 'false');
        });

        // Remove active class from all tab content
        tabContainer.querySelectorAll('.query-params-tab-content').forEach(c => {
            c.classList.remove('active');
        });

        // Add active class to clicked tab and its content
        activeTab.classList.add('active');
        activeTab.setAttribute('aria-selected', 'true');
        
        // Show corresponding content
        const contentId = activeTab.getAttribute('aria-controls') || activeTab.getAttribute('data-tab');
        if (contentId) {
            const content = document.getElementById(contentId);
            if (content) {
                content.classList.add('active');
            }
        }
    }

    /**
     * Navigate between tabs with arrow keys
     */
    function navigateTabs(currentTab, forward) {
        const tabs = Array.from(currentTab.closest('.query-params-tabs').querySelectorAll('.query-params-tab'));
        const currentIndex = tabs.indexOf(currentTab);
        let nextIndex;
        
        if (forward) {
            nextIndex = (currentIndex + 1) % tabs.length;
        } else {
            nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
        }
        
        tabs[nextIndex].focus();
        switchQueryParamsTab(tabs[nextIndex]);
    }

    /**
     * Handle window resize to recalculate heights
     */
    function handleResize() {
        const expandedContents = document.querySelectorAll('.query-params-content.expanded');
        expandedContents.forEach(content => {
            if (content.style.maxHeight && content.style.maxHeight !== '0') {
                content.style.maxHeight = content.scrollHeight + 'px';
            }
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initQueryParameters);
    } else {
        initQueryParameters();
    }

    // Handle window resize
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(handleResize, 250);
    });

})();

