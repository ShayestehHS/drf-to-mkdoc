let currentFilters = {
    method: '',
    path: '',
    models: '',
    auth: '',
    roles: '',
    contentType: '',
    params: '',
    schema: '',
    pagination: '',
    tags: '',
    app: '',
    ordering: '',
    search: '',
    permissions: ''
};

function applyFilters() {
    // Read all filters
    currentFilters = {
        method: getValue('filter-method'),
        path: getValue('filter-path'),
        models: getValue('filter-models'),
        auth: getValue('filter-auth'),
        roles: getValue('filter-roles'),
        contentType: getValue('filter-content-type'),
        params: getValue('filter-params'),
        schema: getValue('filter-schema'),
        pagination: getValue('filter-pagination'),
        tags: getValue('filter-tags'),
        app: getValue('filter-app'),
        ordering: getValue('filter-ordering'),
        search: getValue('filter-search'),
        permissions: getMultiSelectValue('filter-permissions'),
    };

    updateURLParams(currentFilters);

    const cards = document.querySelectorAll('.endpoint-card');
    let visibleCount = 0;

    cards.forEach(card => {
        const visible = matchesFilters(card);
        card.classList.toggle('hidden', !visible);
        if (visible) visibleCount++;
    });

    // Collapse viewset sections with no visible cards
    document.querySelectorAll('.viewset-section').forEach(section => {
        const visibleCards = section.querySelectorAll('.endpoint-card:not(.hidden)');
        section.style.display = visibleCards.length === 0 ? 'none' : '';
    });

    // Collapse app sections with no visible cards
    document.querySelectorAll('.app-section').forEach(app => {
        const visibleCards = app.querySelectorAll('.endpoint-card:not(.hidden)');
        app.style.display = visibleCards.length === 0 ? 'none' : '';
    });

    // Show/hide empty state
    const emptyState = document.getElementById('empty-state');
    if (emptyState) {
        emptyState.style.display = visibleCount === 0 ? 'block' : 'none';
    }

    // Update filter result stats
    document.querySelector('.filter-results').textContent =
        `Showing ${visibleCount} of ${cards.length} endpoints`;
}

function getValue(id) {
    const el = document.getElementById(id);
    return el ? el.value.trim().toLowerCase() : '';
}

function getMultiSelectValue(id) {
    const el = document.getElementById(id);
    if (!el) return '';
    
    const selected = Array.from(el.selectedOptions)
        .map(opt => opt.value.trim().toLowerCase())
        .filter(val => val !== '');
    
    return selected.length > 0 ? selected.join(' ') : '';
}

function populateAppFilterOptions() {
    const select = document.getElementById('filter-app');
    const apps = new Set();

    document.querySelectorAll('.endpoint-card').forEach(card => {
        const app = card.dataset.app;
        if (app) apps.add(app);
    });

    // Convert to sorted array and add as options
    Array.from(apps).sort().forEach(app => {
        const opt = document.createElement('option');
        opt.value = app;
        opt.textContent = app;
        select.appendChild(opt);
    });
}

function populatePermissionsFilterOptions() {
    const select = document.getElementById('filter-permissions');
    if (!select) return;
    
    const permissions = new Set();

    document.querySelectorAll('.endpoint-card').forEach(card => {
        const perms = card.dataset.permissions;
        if (perms) {
            perms.split(' ').forEach(perm => {
                if (perm) permissions.add(perm);
            });
        }
    });

    // Convert to sorted array and add as options
    Array.from(permissions).sort().forEach(perm => {
        const opt = document.createElement('option');
        opt.value = perm;
        // Extract display name (class name without module path)
        const displayName = perm.includes('.') ? perm.split('.').pop() : perm;
        opt.textContent = displayName;
        select.appendChild(opt);
    });
}

function matchesFilters(card) {
    const d = card.dataset;
    const f = currentFilters;

    if (f.method && d.method !== f.method) return false;
    if (f.path && !d.path.includes(f.path)) return false;
    if (f.app && d.app !== f.app) return false;
    if (f.auth && d.auth !== f.auth) return false;
    if (f.pagination && d.pagination !== f.pagination) return false;
    if (f.search && d.search !== f.search) return false;
    if (f.ordering && d.ordering !== f.ordering) return false;
    if (f.models && !d.models.includes(f.models)) return false;
    if (f.roles && !d.roles.includes(f.roles)) return false;
    if (f.tags && !d.tags.includes(f.tags)) return false;
    if (f.permissions) {
        // Multi-select: check if any selected permission matches
        const selectedPerms = f.permissions.split(' ').filter(p => p);
        if (selectedPerms.length > 0) {
            const cardPerms = (d.permissions || '').split(' ').filter(p => p);
            const hasMatch = selectedPerms.some(selected => cardPerms.includes(selected));
            if (!hasMatch) return false;
        }
    }
    if (f.contentType && d.contentType !== f.contentType) return false;

    if (f.params && !d.params.includes(f.params)) return false;

    return true;
}

function clearFilters() {
    document.querySelectorAll('.filter-input, .filter-select').forEach(el => {
        if (el.multiple) {
            // Clear multi-select
            Array.from(el.options).forEach(opt => opt.selected = false);
        } else {
            el.value = '';
        }
    });
    currentFilters = {
        method: '', path: '', models: '', auth: '', roles: '', contentType: '',
        params: '', schema: '', pagination: '', tags: '', app: '', ordering: '', search: '', permissions: ''
    };
    applyFilters();
    updateURLParams(currentFilters);
}


function updateURLParams(filters) {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => {
        if (v) params.set(k, v);
    });
    history.replaceState(null, '', '?' + params.toString());
}

function loadURLParams() {
    const params = new URLSearchParams(location.search);
    params.forEach((v, k) => {
        const input = document.getElementById(`filter-${k}`);
        if (input) input.value = v;
    });
}

document.addEventListener('DOMContentLoaded', () => {
    populateAppFilterOptions();
    populatePermissionsFilterOptions();
    loadURLParams();
    document.querySelectorAll('.filter-input, .filter-select').forEach(input => {
        if (input.multiple) {
            input.addEventListener('change', debounce(applyFilters, 250));
        } else {
            input.addEventListener('input', debounce(applyFilters, 250));
        }
    });
    applyFilters();
});

function debounce(func, delay) {
    let timeout;
    return function () {
        clearTimeout(timeout);
        timeout = setTimeout(func, delay);
    };
}



document.addEventListener('DOMContentLoaded', function() {
    // Example filter implementation
    const container = document.getElementById('fullscreen-container');
    
    // Check if container exists before proceeding
    if (!container) {
        return;
    }

    // Add filter controls
    const filterControls = document.createElement('div');
    filterControls.className = 'filter-controls';
    filterControls.innerHTML = `
        <select id="filter-select">
            <option value="none">No Filter</option>
            <option value="grayscale">Grayscale</option>
            <option value="sepia">Sepia</option>
            <option value="blur">Blur</option>
        </select>
    `;
    container.prepend(filterControls);

    // Apply filter based on selection
    document.getElementById('filter-select').addEventListener('change', function(e) {
        container.style.filter = e.target.value === 'none' ? '' : e.target.value + '(100%)';
    });

    // Your custom filter logic here
    // Example: Apply initial filter if needed
    // container.style.filter = 'grayscale(50%)';
});

document.addEventListener('DOMContentLoaded', () => {
    const filterPanel = document.getElementById('filterSidebar');
    const leftSidebar = document.querySelector('.md-sidebar--primary');

    if (filterPanel && leftSidebar) {
        leftSidebar.innerHTML = ''; // Remove nav if not needed
        leftSidebar.appendChild(filterPanel);
        filterPanel.classList.remove('collapsed'); // Make sure it's visible
    }
});