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
    if (!el) return '';
    // Don't lowercase path filter to preserve regex patterns
    if (id === 'filter-path') {
        return el.value.trim();
    }
    return el.value.trim().toLowerCase();
}

function getPermissionsCheckboxValue() {
    const checkboxes = document.querySelectorAll('#permissions-checkbox-list input[type="checkbox"]:checked');
    const selected = Array.from(checkboxes)
        .map(cb => cb.value.trim().toLowerCase())
        .filter(val => val !== '');
    
    return selected.length > 0 ? selected.join(' ') : '';
}

/**
 * Ensures a select element has an "All" option, clearing all other options.
 * @param {HTMLSelectElement} select - The select element to update
 */
function ensureAllOption(select) {
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
}

function populateAppFilterOptions() {
    const select = document.getElementById('filter-app');
    if (!select) return;
    
    ensureAllOption(select);
    
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

function updateAppFilterOptions(visibleCards = null) {
    const select = document.getElementById('filter-app');
    if (!select) return;
    
    const currentValue = select.value;
    const apps = new Set();

    // Use provided cards or query if not provided
    const cards = visibleCards || document.querySelectorAll('.endpoint-card:not(.hidden)');
    cards.forEach(card => {
        const app = card.dataset.app;
        if (app) apps.add(app);
    });

    // Remove all options except "All"
    ensureAllOption(select);

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

/**
 * Builds a permission checkbox element with label.
 * @param {string} fullPath - The full permission class path
 * @param {string} displayName - The human-readable display name
 * @param {boolean} [isChecked=false] - Whether the checkbox should be checked
 * @returns {HTMLLabelElement} The constructed checkbox label element
 */
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

/**
 * Builds a "No Permissions" checkbox element.
 * @param {boolean} [isChecked=false] - Whether the checkbox should be checked
 * @returns {HTMLLabelElement} The constructed checkbox label element
 */
function buildNoPermissionsCheckbox(isChecked = false) {
    return buildPermissionCheckbox('__no_permissions__', 'No Permissions', isChecked);
}

/**
 * Extracts permissions data from an endpoint card element.
 * @param {HTMLElement} card - The endpoint card element
 * @returns {{permissions: Array<{fullPath: string, displayName: string}>, hasNoPermissions: boolean}} Object containing extracted permissions and no-permissions flag
 */
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

/**
 * Sets up the search handler for the permissions filter.
 * Removes any existing handler before attaching a new one to prevent duplicates.
 */
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

/**
 * Attaches change event listeners to all permission checkboxes.
 * @param {HTMLElement} checkboxList - The container element holding the checkboxes
 */
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

function updatePermissionsFilterOptions(visibleCards = null) {
    const checkboxList = document.getElementById('permissions-checkbox-list');
    if (!checkboxList) return;
    
    // Get currently selected permissions
    const selectedPermissions = new Set();
    checkboxList.querySelectorAll('input[type="checkbox"]:checked').forEach(cb => {
        selectedPermissions.add(cb.value.toLowerCase());
    });
    
    const permissions = new Map(); // Use Map to store both full path and display name
    
    // Use provided cards or query if not provided
    const cards = visibleCards || document.querySelectorAll('.endpoint-card:not(.hidden)');
    let hasNoPermissions = false;
    
    cards.forEach(card => {
        const extracted = extractPermissionsFromCard(card);
        extracted.permissions.forEach(({ fullPath, displayName }) => {
            permissions.set(fullPath.toLowerCase(), displayName);
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

/**
 * Converts a wildcard pattern (with * and ?) to a regex pattern.
 * @param {string} pattern - The wildcard pattern
 * @returns {string} The regex pattern
 */
function wildcardToRegex(pattern) {
    // First, escape special regex characters except * and ?
    // We need to escape: . + ^ $ { } ( ) | [ ] \
    let regexPattern = pattern.replace(/[.+^${}()|[\]\\]/g, '\\$&');
    // Now convert * to .* (any characters) - but we need to unescape * first if it was escaped
    // Actually, since * is not in the escape list above, it won't be escaped
    regexPattern = regexPattern.replace(/\*/g, '.*');
    // Convert ? to . (single character) - same, ? won't be escaped
    regexPattern = regexPattern.replace(/\?/g, '.');
    return regexPattern;
}

/**
 * Checks if a pattern looks like a wildcard pattern (contains * or ?).
 * @param {string} pattern - The pattern to check
 * @returns {boolean} True if it looks like a wildcard pattern
 */
function isWildcardPattern(pattern) {
    // Check if pattern contains * or ? that aren't part of complex regex
    if (!/[*?]/.test(pattern)) return false;
    // If it starts with / or has ^ at start or $ at end, it's likely a regex pattern
    if (pattern.startsWith('/') || pattern.startsWith('^') || pattern.endsWith('$')) return false;
    // If it contains .* (regex equivalent of *), it's likely already a regex pattern
    if (pattern.includes('.*')) return false;
    return true;
}

/**
 * Matches a path against a filter pattern, supporting regex, wildcard, and simple text matching.
 * Supports:
 * - Regex patterns (e.g., /ldap.*user/i)
 * - Wildcard patterns (e.g., ldap*user -> matches ldap followed by any chars then user)
 * - Simple text matching (case-insensitive substring)
 * @param {string} path - The path to match against
 * @param {string} filterPattern - The filter pattern (can be regex, wildcard, or simple text)
 * @returns {boolean} True if the path matches the filter pattern
 */
/**
 * Validates a regex pattern for potential ReDoS vulnerabilities.
 * @param {string} pattern - The regex pattern to validate
 * @returns {boolean} True if the pattern appears safe, false if potentially dangerous
 */
function isSafeRegexPattern(pattern) {
    // Limit pattern length to prevent extremely long patterns
    if (pattern.length > 1000) {
        return false;
    }
    
    // Check for nested quantifiers that can cause exponential backtracking
    // Patterns like (a+)+, (a*)*, (a?)?, etc. are dangerous
    const dangerousPatterns = [
        /\([^)]*\+[^)]*\)\+/,  // (a+)+
        /\([^)]*\*[^)]*\)\*/,  // (a*)*
        /\([^)]*\?[^)]*\)\?/,  // (a?)?
        /\([^)]*\+[^)]*\)\*/,  // (a+)*
        /\([^)]*\*[^)]*\)\+/,  // (a*)+
    ];
    
    for (const dangerousPattern of dangerousPatterns) {
        if (dangerousPattern.test(pattern)) {
            return false;
        }
    }
    
    return true;
}

/**
 * Executes a regex test with timeout protection against ReDoS attacks.
 * 
 * NOTE: This function cannot actually interrupt a synchronous regex execution.
 * It only detects if execution took too long after completion. For true protection,
 * consider using a Web Worker or a safe-regex library.
 * 
 * @param {RegExp} regex - The regex to test
 * @param {string} text - The text to test against
 * @param {number} timeoutMs - Maximum execution time in milliseconds (default: 100ms)
 * @returns {boolean|null} True if match, false if no match, null if timeout/error
 */
function regexTestWithTimeout(regex, text, timeoutMs = 100) {
    // Since regex.test() is synchronous and cannot be interrupted,
    // we can only detect slow execution after the fact.
    // This provides limited protection but is better than nothing.
    const startTime = Date.now();
    let result = false;
    
    try {
        result = regex.test(text);
    } catch (e) {
        // Regex execution error
        console.warn(`Regex execution error: ${e.message}`);
        return null;
    }
    
    const elapsed = Date.now() - startTime;
    if (elapsed > timeoutMs) {
        console.warn(
            `⚠️ ReDoS Warning: Regex test took ${elapsed}ms (limit: ${timeoutMs}ms). ` +
            `Pattern may be vulnerable to catastrophic backtracking. ` +
            `Consider using a simpler pattern or substring matching instead.`
        );
        return null;
    }
    
    return result;
}

function matchesPathFilter(path, filterPattern) {
    if (!filterPattern) return true;
    
    // Convert wildcard patterns to regex
    let regexPattern = filterPattern;
    const isWildcard = isWildcardPattern(filterPattern);
    if (isWildcard) {
        regexPattern = wildcardToRegex(filterPattern);
    }
    
    // Validate pattern for ReDoS before attempting to compile
    if (!isSafeRegexPattern(regexPattern)) {
        // Unsafe pattern detected, fall back to simple text matching
        console.warn(`Unsafe regex pattern detected, using substring matching: ${filterPattern}`);
        return path.toLowerCase().includes(filterPattern.toLowerCase());
    }
    
    // Try regex matching first
    try {
        const regex = new RegExp(regexPattern, 'i'); // Case-insensitive regex
        
        // Use timeout-protected regex test
        const matchResult = regexTestWithTimeout(regex, path, 100);
        if (matchResult === true) {
            return true;
        } else if (matchResult === false) {
            // Valid regex that doesn't match - return false immediately
            // Don't fall back to substring matching as this changes semantics
            return false;
        } else if (matchResult === null) {
            // Timeout or error occurred, fall back to substring matching
            console.warn(`Regex test failed or timed out, falling back to substring matching for: ${filterPattern}`);
            return path.toLowerCase().includes(filterPattern.toLowerCase());
        }
    } catch (e) {
        // Invalid regex compilation, log and fall through to simple text matching
        console.warn(`Invalid regex pattern "${filterPattern}": ${e.message}. Falling back to substring matching.`);
    }
    
    // Fall back to case-insensitive simple text matching
    // (only reached if regex compilation failed or matchResult was null)
    return path.toLowerCase().includes(filterPattern.toLowerCase());
}

function matchesFilters(card) {
    const d = card.dataset;
    const f = currentFilters;

    if (f.method && d.method !== f.method) return false;
    if (f.path && !matchesPathFilter(d.path, f.path)) return false;
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
    // Batch DOM query for better performance
    const visibleCards = document.querySelectorAll('.endpoint-card:not(.hidden)');
    updateAppFilterOptions(visibleCards);
    updatePermissionsFilterOptions(visibleCards);
    updateMethodFilterOptions(visibleCards);
}

function updateMethodFilterOptions(visibleCards = null) {
    const select = document.getElementById('filter-method');
    if (!select) return;
    
    const currentValue = select.value;
    const methods = new Set();

    // Use provided cards or query if not provided
    const cards = visibleCards || document.querySelectorAll('.endpoint-card:not(.hidden)');
    cards.forEach(card => {
        const method = card.dataset.method;
        if (method) methods.add(method);
    });

    ensureAllOption(select);
    
    // Add methods from visible cards
    Array.from(methods).sort().forEach(method => {
        const opt = document.createElement('option');
        opt.value = method;
        opt.textContent = method.toUpperCase();
        select.appendChild(opt);
    });

    // If current selection is no longer available, reset to "All"
    if (currentValue && !methods.has(currentValue)) {
        select.value = '';
        currentFilters.method = '';
    } else if (currentValue && methods.has(currentValue)) {
        select.value = currentValue;
    }
}

/**
 * Resets card visibility to show all cards and sections.
 */
function resetCardVisibility() {
    document.querySelectorAll('.endpoint-card').forEach(card => {
        card.classList.remove('hidden');
    });
    document.querySelectorAll('.app-section').forEach(app => {
        app.style.display = '';
    });
}

/**
 * Resets all filter input values to their default state.
 */
function resetFilterInputs() {
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
}

/**
 * Resets permissions filter state (checkboxes and search).
 */
function resetPermissionsState() {
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
}

/**
 * Updates UI elements after clearing filters (stats, empty state).
 */
function updateUIAfterClear() {
    // Update filter result stats
    const cards = document.querySelectorAll('.endpoint-card');
    document.querySelector('.filter-results').textContent =
        `Showing ${cards.length} of ${cards.length} endpoints`;
    
    // Hide empty state
    const emptyState = document.getElementById('empty-state');
    if (emptyState) {
        emptyState.style.display = 'none';
    }
}

/**
 * Restores filter options to their initial state after clearing.
 */
function restoreFilterOptions() {
    // Restore all filter options after clearing - this will show all options from all cards
    populateAppFilterOptions();
    
    // Use stored original permissions if available, otherwise populate from cards
    if (originalPermissionsData) {
        restorePermissionsFromStoredData();
    } else {
        populatePermissionsFilterOptions();
    }
}

function clearFilters() {
    resetCardVisibility();
    resetFilterInputs();
    resetPermissionsState();
    
    // Reset filter state
    currentFilters = {
        method: '', path: '', models: '', auth: '', roles: '', contentType: '',
        params: '', schema: '', pagination: '', tags: '', app: '', ordering: '', search: '', permissions: ''
    };
    
    // Update URL params
    updateURLParams(currentFilters);
    
    updateUIAfterClear();
    restoreFilterOptions();
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
    
    // Move filter panel to left sidebar
    const filterPanel = document.getElementById('filterSidebar');
    const leftSidebar = document.querySelector('.md-sidebar--primary');
    
    if (filterPanel && leftSidebar) {
        leftSidebar.innerHTML = ''; // Remove nav if not needed
        leftSidebar.appendChild(filterPanel);
        filterPanel.classList.remove('collapsed'); // Make sure it's visible
    }
});

function debounce(func, delay) {
    let timeout;
    return function () {
        clearTimeout(timeout);
        timeout = setTimeout(func, delay);
    };
}

// Copy endpoint path to clipboard
function copyEndpointPath(event, button) {
    // Prevent navigation when clicking the copy button
    event.preventDefault();
    event.stopPropagation();
    
    // Find the endpoint path element (sibling of the button)
    const endpointCard = button.closest('.endpoint-card');
    if (!endpointCard) return;
    
    const endpointPathElement = endpointCard.querySelector('.endpoint-path');
    if (!endpointPathElement) return;
    
    // Get the path text from the endpoint-path-text element
    const pathTextElement = endpointPathElement.querySelector('.endpoint-path-text');
    const endpointPath = pathTextElement ? pathTextElement.textContent.trim() : endpointPathElement.textContent.trim();
    
    // Check if Clipboard API is available (requires secure context - HTTPS or localhost)
    if (navigator.clipboard && navigator.clipboard.writeText) {
        // Use modern Clipboard API
        navigator.clipboard.writeText(endpointPath).then(() => {
            // Show success feedback
            const originalIcon = button.innerHTML;
            button.classList.add('copied');
            button.innerHTML = '<span class="copy-icon">✓</span>';
            
            // Reset after 1 second
            setTimeout(() => {
                button.classList.remove('copied');
                button.innerHTML = originalIcon;
            }, 1000);
        }).catch((err) => {
            console.error('Failed to copy endpoint path:', err);
            // Fallback to execCommand
            fallbackCopyToClipboard(endpointPath, button);
        });
    } else {
        // Clipboard API not available (insecure context), use fallback
        fallbackCopyToClipboard(endpointPath, button);
    }
}

/**
 * Fallback copy method using document.execCommand for insecure contexts.
 * @param {string} text - Text to copy
 * @param {HTMLElement} button - Button element for feedback
 */
function fallbackCopyToClipboard(text, button) {
    // Create a temporary textarea element
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.left = '-999999px';
    textarea.style.top = '-999999px';
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    
    try {
        // Use deprecated but widely supported execCommand
        const successful = document.execCommand('copy');
        if (successful) {
            // Show success feedback
            const originalIcon = button.innerHTML;
            button.classList.add('copied');
            button.innerHTML = '<span class="copy-icon">✓</span>';
            
            // Reset after 1 second
            setTimeout(() => {
                button.classList.remove('copied');
                button.innerHTML = originalIcon;
            }, 1000);
        } else {
            throw new Error('execCommand copy failed');
        }
    } catch (err) {
        console.error('Fallback copy failed:', err);
        // Show error feedback with user-friendly message
        const originalIcon = button.innerHTML;
        button.innerHTML = '<span class="copy-icon" title="Copy requires HTTPS or use localhost">✕</span>';
        setTimeout(() => {
            button.innerHTML = originalIcon;
        }, 2000);
    } finally {
        // Clean up
        document.body.removeChild(textarea);
    }
}

// Make function globally available
window.copyEndpointPath = copyEndpointPath;