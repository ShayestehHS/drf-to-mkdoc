document.addEventListener('DOMContentLoaded', function() {
    // Initialize tabs functionality
    const tabs = document.querySelectorAll('.er-tab');
    const contents = document.querySelectorAll('.er-content');
    
    // Set the first tab as active by default
    if (tabs.length > 0 && contents.length > 0) {
        tabs[0].classList.add('active');
        contents[0].classList.add('active');
    }
    
    // Add click event listeners to tabs
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Remove active class from all tabs and contents
            tabs.forEach(t => t.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding content
            this.classList.add('active');
            const targetId = this.getAttribute('data-target');
            const targetContent = document.getElementById(targetId);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });
});

