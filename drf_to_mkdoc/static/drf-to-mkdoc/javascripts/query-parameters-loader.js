// Query parameters loader script
document.addEventListener('DOMContentLoaded', function() {
    // Load JavaScript
    function loadScript(url, callback) {
        const script = document.createElement('script');
        script.src = url;
        script.onload = callback || function() {};
        document.body.appendChild(script);
    }
    
    // Base URL for static files
    const baseUrl = document.querySelector('meta[name="static-url"]')?.getAttribute('content') || '';
    
    // Load query parameters extractor script
    loadScript(baseUrl + '/static/drf-to-mkdoc/javascripts/try-out/query-parameters-extractor.js');
});
