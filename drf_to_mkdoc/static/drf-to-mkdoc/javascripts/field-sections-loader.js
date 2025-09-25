// Loader script for field sections functionality
document.addEventListener('DOMContentLoaded', function() {
    // Load CSS
    function loadCSS(url) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = url;
        document.head.appendChild(link);
    }
    
    // Load JavaScript
    function loadScript(url, callback) {
        const script = document.createElement('script');
        script.src = url;
        script.onload = callback || function() {};
        document.body.appendChild(script);
    }
    
    // Base URL for static files
    const baseUrl = document.querySelector('meta[name="static-url"]')?.getAttribute('content') || '';
    
    // Load CSS file
    loadCSS(baseUrl + '/static/drf-to-mkdoc/stylesheets/field-sections.css');
    
    // Load field extractor script
    loadScript(baseUrl + '/static/drf-to-mkdoc/javascripts/try-out/field-extractor.js');
    
    console.log('Field sections functionality loaded');
});
