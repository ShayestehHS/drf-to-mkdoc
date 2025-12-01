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

function applyFilters(skipUpdateOptions = false) {
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
        permissions: getPermissionsCheckboxValue(),
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

    // Update filter options based on visible cards (unless skipped)
    if (!skipUpdateOptions) {
        updateFilterOptions();
    }
}

function getValue(id) {
    const el = document.getElementById(id);
    return el ? el.value.trim().toLowerCase() : '';
}

function getPermissionsCheckboxValue() {
    const checkboxes = document.querySelectorAll('#permissions-checkbox-list input[type="checkbox"]:checked');
    const selected = Array.from(checkboxes)
        .map(cb => cb.value.trim().toLowerCase())
        .filter(val => val !== '');
    
    return selected.length > 0 ? selected.join(' ') : '';
}

function populateAppFilterOptions() {
    const select = document.getElementById('filter-app');
    if (!select) return;
    
    const allOption = select.querySelector('option[value=""]');
    select.innerHTML = '';
    if (allOption) {
        select.appendChild(allOption);
    } else {
        const opt = document.createElement('option');
        opt.value = '';
        opt.textContent = 'All';
        select.appendChild(opt);
    }
    
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

function updateAppFilterOptions() {
    const select = document.getElementById('filter-app');
    if (!select) return;
    
    const currentValue = select.value;
    const apps = new Set();

    // Only collect apps from visible cards
    document.querySelectorAll('.endpoint-card:not(.hidden)').forEach(card => {
        const app = card.dataset.app;
        if (app) apps.add(app);
    });

    // Remove all options except "All"
    const allOption = select.querySelector('option[value=""]');
    select.innerHTML = '';
    if (allOption) {
        select.appendChild(allOption);
    } else {
        const opt = document.createElement('option');
        opt.value = '';
        opt.textContent = 'All';
        select.appendChild(opt);
    }

    // Add options from visible cards
    Array.from(apps).sort().forEach(app => {
        const opt = document.createElement('option');
        opt.value = app;
        opt.textContent = app;
        select.appendChild(opt);
    });

    // Restore current selection if it's still valid
    if (currentValue && apps.has(currentValue)) {
        select.value = currentValue;
    } else if (currentValue && !apps.has(currentValue)) {
        // Current selection is no longer available, reset to "All"
        select.value = '';
        currentFilters.app = '';
    }
}

// Helper function to build a permission checkbox element
function buildPermissionCheckbox(fullPath, displayName, isChecked = false) {
    const label = document.createElement('label');
    label.className = 'permissions-checkbox-item';
    
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = fullPath;
    checkbox.dataset.fullPath = fullPath;
    checkbox.dataset.displayName = displayName;
    if (isChecked) checkbox.checked = true;
    
    const span = document.createElement('span');
    span.textContent = displayName;
    span.className = 'permissions-checkbox-label';
    
    label.appendChild(checkbox);
    label.appendChild(span);
    return label;
}

// Helper function to build "No Permissions" checkbox
function buildNoPermissionsCheckbox(isChecked = false) {
    return buildPermissionCheckbox('__no_permissions__', 'No Permissions', isChecked);
}

// Helper function to extract permissions from a card
function extractPermissionsFromCard(card) {
    let permissionsMap = null;
    if (card.dataset.permissionsNames) {
        try {
            permissionsMap = JSON.parse(card.dataset.permissionsNames);
        } catch (e) {
            console.debug('Failed to parse permissions_names', e);
        }
    }
    
    const perms = card.dataset.permissions;
    const result = { permissions: [], hasNoPermissions: false };
    
    if (perms && perms.trim() !== '') {
        perms.split(' ').forEach(perm => {
            if (perm) {
                let displayName = null;
                if (Array.isArray(permissionsMap)) {
                    const permData = permissionsMap.find(p => 
                        p.class_path && p.class_path.toLowerCase() === perm.toLowerCase()
                    );
                    if (permData?.display_name) displayName = permData.display_name;
                }
                if (!displayName) {
                    displayName = perm.includes('.') ? perm.split('.').pop() : perm;
                }
                result.permissions.push({ fullPath: perm, displayName });
            }
        });
    } else {
        result.hasNoPermissions = true;
    }
    return result;
}

// Helper function to setup permissions search handler
function setupPermissionsSearchHandler() {
    const searchInput = document.getElementById('filter-permissions-search');
    if (!searchInput) return;
    
    if (searchInput._permissionsSearchHandler) {
        searchInput.removeEventListener('input', searchInput._permissionsSearchHandler);
    }
    
    searchInput._permissionsSearchHandler = (e) => {
        const searchTerm = e.target.value.toLowerCase();
        document.querySelectorAll('.permissions-checkbox-item').forEach(item => {
            const checkbox = item.querySelector('input[type="checkbox"]');
            const displayName = (checkbox.dataset.displayName || '').toLowerCase();
            const fullPath = (checkbox.dataset.fullPath || checkbox.value).toLowerCase();
            const matches = displayName.includes(searchTerm) || fullPath.includes(searchTerm);
            item.style.display = matches ? '' : 'none';
        });
    };
    
    searchInput.addEventListener('input', searchInput._permissionsSearchHandler);
}

// Helper function to attach checkbox change listeners
function attachPermissionCheckboxListeners(checkboxList) {
    const debouncedApplyFilters = debounce(applyFilters, 250);
    checkboxList.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            updatePermissionsTriggerText();
            debouncedApplyFilters();
        });
    });
}

function populatePermissionsFilterOptions() {
    const checkboxList = document.getElementById('permissions-checkbox-list');
    if (!checkboxList) return;
    
    const permissions = new Map(); // Use Map to store both full path and display name
    let hasNoPermissions = false;
    
    document.querySelectorAll('.endpoint-card').forEach(card => {
        const extracted = extractPermissionsFromCard(card);
        extracted.permissions.forEach(({ fullPath, displayName }) => {
            permissions.set(fullPath, displayName);
        });
        if (extracted.hasNoPermissions) {
            hasNoPermissions = true;
        }
    });

    // Sort by display name for better UX
    const sortedPerms = Array.from(permissions.entries()).sort((a, b) => 
        a[1].localeCompare(b[1])
    );

    // Clear existing checkboxes
    checkboxList.innerHTML = '';

    // Add "No Permissions" option first if there are any cards with no permissions
    if (hasNoPermissions) {
        checkboxList.appendChild(buildNoPermissionsCheckbox());
    }

    // Add checkboxes
    sortedPerms.forEach(([fullPath, displayName]) => {
        checkboxList.appendChild(buildPermissionCheckbox(fullPath, displayName));
    });
    
    // Setup search functionality
    setupPermissionsSearchHandler();
    
    // Attach checkbox change listeners
    attachPermissionCheckboxListeners(checkboxList);
    
    // Setup dropdown toggle (only if not already set up)
    setupPermissionsDropdown();
    
    // Update trigger text
    updatePermissionsTriggerText();
}

// Store original permissions for restoration
let originalPermissionsData = null;

function storeOriginalPermissions() {
    if (originalPermissionsData) return; // Already stored
    
    const checkboxList = document.getElementById('permissions-checkbox-list');
    if (!checkboxList) return;
    
    originalPermissionsData = {
        permissions: new Map(),
        hasNoPermissions: false
    };
    
    document.querySelectorAll('.endpoint-card').forEach(card => {
        const extracted = extractPermissionsFromCard(card);
        extracted.permissions.forEach(({ fullPath, displayName }) => {
            originalPermissionsData.permissions.set(fullPath, displayName);
        });
        if (extracted.hasNoPermissions) {
            originalPermissionsData.hasNoPermissions = true;
        }
    });
}

function updatePermissionsFilterOptions() {
    const checkboxList = document.getElementById('permissions-checkbox-list');
    if (!checkboxList) return;
    
    // Get currently selected permissions
    const selectedPermissions = new Set();
    checkboxList.querySelectorAll('input[type="checkbox"]:checked').forEach(cb => {
        selectedPermissions.add(cb.value.toLowerCase());
    });
    
    const permissions = new Map(); // Use Map to store both full path and display name
    
    // Only collect permissions from visible cards
    document.querySelectorAll('.endpoint-card:not(.hidden)').forEach(card => {
        const extracted = extractPermissionsFromCard(card);
        extracted.permissions.forEach(({ fullPath, displayName }) => {
            permissions.set(fullPath.toLowerCase(), displayName);
        });
    });

    // Check if we need to show "No Permissions" option
    let hasNoPermissions = false;
    document.querySelectorAll('.endpoint-card:not(.hidden)').forEach(card => {
        const perms = card.dataset.permissions;
        if (!perms || perms.trim() === '') {
            hasNoPermissions = true;
        }
    });

    // Sort by display name for better UX
    const sortedPerms = Array.from(permissions.entries()).sort((a, b) => 
        a[1].localeCompare(b[1])
    );

    // Clear existing checkboxes
    checkboxList.innerHTML = '';

    // Add "No Permissions" option first if there are visible cards with no permissions
    if (hasNoPermissions) {
        checkboxList.appendChild(buildNoPermissionsCheckbox(selectedPermissions.has('__no_permissions__')));
    }

    // Add checkboxes
    sortedPerms.forEach(([fullPath, displayName]) => {
        checkboxList.appendChild(buildPermissionCheckbox(fullPath, displayName, selectedPermissions.has(fullPath)));
    });
    
    // Attach checkbox change listeners
    attachPermissionCheckboxListeners(checkboxList);
    
    // Update trigger text
    updatePermissionsTriggerText();
}

let permissionsDropdownSetup = false;

function setupPermissionsDropdown() {
    const trigger = document.getElementById('permissions-dropdown-trigger');
    const dropdown = document.getElementById('permissions-dropdown');
    
    if (!trigger || !dropdown) return;
    
    // Only setup once to avoid duplicate event listeners
    if (permissionsDropdownSetup) return;
    permissionsDropdownSetup = true;
    
    // Toggle dropdown on trigger click
    trigger.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('open');
        trigger.classList.toggle('open');
        
        // Focus search input when opened
        if (dropdown.classList.contains('open')) {
            const searchInput = document.getElementById('filter-permissions-search');
            if (searchInput) {
                setTimeout(() => searchInput.focus(), 100);
            }
        }
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!trigger.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.remove('open');
            trigger.classList.remove('open');
        }
    });
}

function updatePermissionsTriggerText() {
    const triggerText = document.getElementById('permissions-trigger-text');
    const checkboxes = document.querySelectorAll('#permissions-checkbox-list input[type="checkbox"]:checked');
    
    if (!triggerText) return;
    
    const selectedCount = checkboxes.length;
    if (selectedCount === 0) {
        triggerText.textContent = 'Select permissions...';
    } else if (selectedCount === 1) {
        const displayName = checkboxes[0].dataset.displayName || checkboxes[0].value;
        triggerText.textContent = displayName;
    } else {
        triggerText.textContent = `${selectedCount} permissions selected`;
    }
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
        const selectedPerms = f.permissions.split(' ').filter(p => p);
        if (selectedPerms.length > 0) {
            // Special case: "No Permissions" selected
            if (selectedPerms.includes('__no_permissions__')) {
                // If "No Permissions" is selected, show only endpoints with no permissions
                const cardPerms = (d.permissions || '').split(' ').filter(p => p);
                if (cardPerms.length > 0) return false;
            } else {
                // Multi-select: check if ALL selected permissions are present (AND logic)
                const cardPerms = (d.permissions || '').split(' ').filter(p => p);
                const hasAllPerms = selectedPerms.every(selected => cardPerms.includes(selected));
                if (!hasAllPerms) return false;
            }
        }
    }
    if (f.contentType && d.contentType !== f.contentType) return false;

    if (f.params && !d.params.includes(f.params)) return false;

    return true;
}

function updateFilterOptions() {
    // Update filter options based on currently visible cards
    updateAppFilterOptions();
    updatePermissionsFilterOptions();
    updateMethodFilterOptions();
}

function updateMethodFilterOptions() {
    const select = document.getElementById('filter-method');
    if (!select) return;
    
    const currentValue = select.value;
    const methods = new Set();

    // Only collect methods from visible cards
    document.querySelectorAll('.endpoint-card:not(.hidden)').forEach(card => {
        const method = card.dataset.method;
        if (method) methods.add(method);
    });

    // Get all existing options
    const allOption = select.querySelector('option[value=""]');
    const existingOptions = Array.from(select.options).map(opt => ({
        value: opt.value,
        text: opt.textContent
    }));

    // Hide/show options based on availability
    Array.from(select.options).forEach(opt => {
        if (opt.value === '') {
            // Always show "All" option
            opt.style.display = '';
        } else {
            // Show option only if it exists in visible cards
            opt.style.display = methods.has(opt.value) ? '' : 'none';
        }
    });

    // If current selection is no longer available, reset to "All"
    if (currentValue && !methods.has(currentValue)) {
        select.value = '';
        currentFilters.method = '';
    }
}

function clearFilters() {
    // First, ensure all cards are visible
    document.querySelectorAll('.endpoint-card').forEach(card => {
        card.classList.remove('hidden');
    });
    
    // Show all app sections
    document.querySelectorAll('.app-section').forEach(app => {
        app.style.display = '';
    });
    
    document.querySelectorAll('.filter-input, .filter-select').forEach(el => {
        if (el.multiple) {
            // Clear multi-select
            Array.from(el.options).forEach(opt => {
                opt.selected = false;
                opt.style.display = ''; // Show all options when clearing
            });
        } else if (el.id !== 'filter-permissions-search') {
            el.value = '';
        }
    });
    
    // Show all method options when clearing
    const methodSelect = document.getElementById('filter-method');
    if (methodSelect) {
        Array.from(methodSelect.options).forEach(opt => {
            opt.style.display = '';
        });
    }
    
    // Clear permissions checkboxes (but don't remove them yet)
    document.querySelectorAll('#permissions-checkbox-list input[type="checkbox"]').forEach(cb => {
        cb.checked = false;
    });
    
    // Clear permissions search and show all items
    const permissionsSearch = document.getElementById('filter-permissions-search');
    if (permissionsSearch) {
        permissionsSearch.value = '';
        document.querySelectorAll('.permissions-checkbox-item').forEach(item => {
            item.style.display = '';
        });
    }
    
    // Update trigger text
    updatePermissionsTriggerText();
    
    currentFilters = {
        method: '', path: '', models: '', auth: '', roles: '', contentType: '',
        params: '', schema: '', pagination: '', tags: '', app: '', ordering: '', search: '', permissions: ''
    };
    
    // Update URL params
    updateURLParams(currentFilters);
    
    // Update filter result stats
    const cards = document.querySelectorAll('.endpoint-card');
    document.querySelector('.filter-results').textContent =
        `Showing ${cards.length} of ${cards.length} endpoints`;
    
    // Hide empty state
    const emptyState = document.getElementById('empty-state');
    if (emptyState) {
        emptyState.style.display = 'none';
    }
    
    // Restore all filter options after clearing - this will show all options from all cards
    populateAppFilterOptions();
    
    // Use stored original permissions if available, otherwise populate from cards
    if (originalPermissionsData) {
        restorePermissionsFromStoredData();
    } else {
        populatePermissionsFilterOptions();
    }
}

function restorePermissionsFromStoredData() {
    const checkboxList = document.getElementById('permissions-checkbox-list');
    if (!checkboxList || !originalPermissionsData) return;
    
    // Sort by display name
    const sortedPerms = Array.from(originalPermissionsData.permissions.entries()).sort((a, b) => 
        a[1].localeCompare(b[1])
    );
    
    // Clear existing checkboxes
    checkboxList.innerHTML = '';
    
    // Add "No Permissions" option if needed
    if (originalPermissionsData.hasNoPermissions) {
        checkboxList.appendChild(buildNoPermissionsCheckbox());
    }
    
    // Add checkboxes
    sortedPerms.forEach(([fullPath, displayName]) => {
        checkboxList.appendChild(buildPermissionCheckbox(fullPath, displayName));
    });
    
    // Setup search functionality
    setupPermissionsSearchHandler();
    
    // Attach checkbox change listeners
    attachPermissionCheckboxListeners(checkboxList);
    
    // Update trigger text
    updatePermissionsTriggerText();
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
        if (k === 'permissions') {
            // Handle permissions checkboxes
            // Normalize to lowercase to match format from getPermissionsCheckboxValue()
            const selectedPerms = v.split(' ').filter(p => p).map(p => p.toLowerCase());
            document.querySelectorAll('#permissions-checkbox-list input[type="checkbox"]').forEach(cb => {
                cb.checked = selectedPerms.includes(cb.value.toLowerCase());
            });
            updatePermissionsTriggerText();
        } else {
            const input = document.getElementById(`filter-${k}`);
            if (input) input.value = v;
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    // Store original permissions data for restoration
    storeOriginalPermissions();
    
    populateAppFilterOptions();
    populatePermissionsFilterOptions();
    loadURLParams();
    document.querySelectorAll('.filter-input, .filter-select').forEach(input => {
        if (input.multiple) {
            input.addEventListener('change', debounce(applyFilters, 250));
        } else if (input.id !== 'filter-permissions-search') {
            // Don't add filter listener to search input (it's handled in populatePermissionsFilterOptions)
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


document.addEventListener('DOMContentLoaded', () => {
    const filterPanel = document.getElementById('filterSidebar');
    const leftSidebar = document.querySelector('.md-sidebar--primary');

    if (filterPanel && leftSidebar) {
        leftSidebar.innerHTML = ''; // Remove nav if not needed
        leftSidebar.appendChild(filterPanel);
        filterPanel.classList.remove('collapsed'); // Make sure it's visible
    }
});