document.addEventListener('DOMContentLoaded', function() {
    // Initialize zoom controls for each diagram
    const diagrams = document.querySelectorAll('.er-diagram');
    
    diagrams.forEach(diagram => {
        // Initial scale and transform values
        let scale = 1;
        let translateX = 0;
        let translateY = 0;
        let isDragging = false;
        let startX, startY;
        let lastTranslateX = 0;
        let lastTranslateY = 0;
        
        // Get the diagram's mermaid SVG element
        const mermaidSvg = diagram.querySelector('svg');
        if (!mermaidSvg) return;
        
        // Create zoom controls if they don't exist
        if (!diagram.querySelector('.er-zoom-controls')) {
            const zoomControls = document.createElement('div');
            zoomControls.className = 'er-zoom-controls';
            zoomControls.innerHTML = `
                <button class="er-zoom-btn er-zoom-in" title="Zoom In">+</button>
                <button class="er-zoom-btn er-zoom-out" title="Zoom Out">-</button>
                <button class="er-zoom-btn er-zoom-reset" title="Reset Zoom">100%</button>
            `;
            diagram.appendChild(zoomControls);
            
            // Add event listeners to zoom buttons
            const zoomIn = zoomControls.querySelector('.er-zoom-in');
            const zoomOut = zoomControls.querySelector('.er-zoom-out');
            const zoomReset = zoomControls.querySelector('.er-zoom-reset');
            
            zoomIn.addEventListener('click', function() {
                scale = Math.min(scale * 1.2, 5); // Max zoom: 5x
                updateTransform();
            });
            
            zoomOut.addEventListener('click', function() {
                scale = Math.max(scale / 1.2, 0.5); // Min zoom: 0.5x
                updateTransform();
            });
            
            zoomReset.addEventListener('click', function() {
                scale = 1;
                translateX = 0;
                translateY = 0;
                updateTransform();
            });
        }
        
        // Enable dragging for panning
        mermaidSvg.addEventListener('mousedown', function(e) {
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            lastTranslateX = translateX;
            lastTranslateY = translateY;
            mermaidSvg.style.cursor = 'grabbing';
        });
        
        document.addEventListener('mousemove', function(e) {
            if (!isDragging) return;
            
            translateX = lastTranslateX + (e.clientX - startX) / scale;
            translateY = lastTranslateY + (e.clientY - startY) / scale;
            updateTransform();
        });
        
        document.addEventListener('mouseup', function() {
            isDragging = false;
            mermaidSvg.style.cursor = 'grab';
        });
        
        // Handle wheel events for zooming
        diagram.addEventListener('wheel', function(e) {
            e.preventDefault();
            
            // Get mouse position relative to the diagram
            const rect = diagram.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            
            // Calculate zoom direction
            const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
            
            // Calculate new scale (with limits)
            const newScale = Math.min(Math.max(scale * zoomFactor, 0.5), 5);
            
            // Calculate new translate values to zoom toward mouse position
            if (scale !== newScale) {
                const scaleRatio = newScale / scale;
                translateX = mouseX / scale - scaleRatio * (mouseX / scale - translateX);
                translateY = mouseY / scale - scaleRatio * (mouseY / scale - translateY);
                scale = newScale;
                updateTransform();
            }
        }, { passive: false });
        
        // Function to update transform
        function updateTransform() {
            mermaidSvg.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
            mermaidSvg.style.transformOrigin = '0 0';
            
            // Update zoom reset button text
            const zoomReset = diagram.querySelector('.er-zoom-reset');
            if (zoomReset) {
                zoomReset.textContent = `${Math.round(scale * 100)}%`;
            }
        }
        
        // Initialize cursor style
        mermaidSvg.style.cursor = 'grab';
        
        // Initialize transform
        updateTransform();
    });
});

