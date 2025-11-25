/**
 * Shared authentication handler for auto-auth feature.
 * Provides centralized auth logic to prevent duplication and ensure consistency.
 * 
 * Security features:
 * - Race condition protection
 * - Timeout handling for async functions
 * - Input validation
 * - Error sanitization
 */

const AuthHandler = {
    _authInProgress: false,
    _timeoutMs: 30000, // 30 seconds default timeout
    
    /**
     * Handle authentication with callbacks for UI updates.
     * 
     * @param {Object} callbacks - Callback functions
     * @param {Function} callbacks.onStart - Called when auth starts
     * @param {Function} callbacks.onSuccess - Called on success with result object
     * @param {Function} callbacks.onError - Called on error with error object
     * @returns {Promise<Object>} Result object with success flag and result/error
     */
    async handleAuth(callbacks = {}) {
        // Prevent race conditions
        if (this._authInProgress) {
            const error = new Error('Authentication already in progress');
            callbacks.onError?.(error);
            return { success: false, error };
        }
        
        this._authInProgress = true;
        callbacks.onStart?.();
        
        try {
            // Check if getAuthHeader function exists
            if (typeof window.getAuthHeader !== 'function') {
                throw new Error('getAuthHeader function not defined. Please configure it in your JavaScript settings.');
            }
            
            // Call the auth function
            let result = window.getAuthHeader();
            
            // Handle async functions (Promises)
            if (result && typeof result.then === 'function') {
                result = await this._withTimeout(result, this._timeoutMs);
            }
            
            // Validate result
            if (!result) {
                throw new Error('getAuthHeader function returned null or undefined.');
            }
            
            // Validate result structure
            this._validateAuthResult(result);
            
            // Success
            callbacks.onSuccess?.(result);
            return { success: true, result };
            
        } catch (error) {
            callbacks.onError?.(error);
            return { success: false, error };
        } finally {
            this._authInProgress = false;
        }
    },
    
    /**
     * Validate auth result structure.
     * 
     * @param {*} result - The result to validate
     * @throws {Error} If validation fails
     */
    _validateAuthResult(result) {
        if (typeof result !== 'object' || result === null) {
            throw new Error('Result must be an object');
        }
        if (typeof result.headerName !== 'string' || !result.headerName.trim()) {
            throw new Error('headerName must be a non-empty string');
        }
        if (typeof result.headerValue !== 'string' || !result.headerValue.trim()) {
            throw new Error('headerValue must be a non-empty string');
        }
        
        // Validate header name format (RFC 7230)
        const headerNameRegex = /^[!#$%&'*+\-.0-9A-Z^_`a-z|~]+$/;
        if (!headerNameRegex.test(result.headerName.trim())) {
            throw new Error('Invalid header name format');
        }
        
        // Validate header value format (RFC 7230: visible ASCII + tab, no bare CR/LF)
        const headerValueRegex = /^[\t\x20-\x7E]*$/;
        if (!headerValueRegex.test(result.headerValue)) {
            throw new Error('Invalid header value: contains non-printable characters');
        }
        
        // Validate input lengths
        this._validateHeaderInput(result.headerName, result.headerValue);
    },
    
    /**
     * Validate header name and value lengths.
     * 
     * @param {string} name - Header name
     * @param {string} value - Header value
     * @throws {Error} If validation fails
     */
    _validateHeaderInput(name, value) {
        const MAX_HEADER_NAME_LENGTH = 256;
        const MAX_HEADER_VALUE_LENGTH = 8192;
        
        if (name.length > MAX_HEADER_NAME_LENGTH) {
            throw new Error(`Header name too long (max ${MAX_HEADER_NAME_LENGTH} chars)`);
        }
        if (value.length > MAX_HEADER_VALUE_LENGTH) {
            throw new Error(`Header value too long (max ${MAX_HEADER_VALUE_LENGTH} chars)`);
        }
    },
    
    /**
     * Wrap a promise with a timeout.
     * 
     * @param {Promise} promise - The promise to wrap
     * @param {number} timeoutMs - Timeout in milliseconds
     * @returns {Promise} Promise that rejects on timeout
     */
    _withTimeout(promise, timeoutMs) {
        return Promise.race([
            promise,
            new Promise((_, reject) => 
                setTimeout(() => reject(new Error('Authentication function timed out')), timeoutMs)
            )
        ]);
    },
    
    /**
     * Sanitize error messages to prevent leaking sensitive data.
     * 
     * @param {Error|*} error - The error to sanitize
     * @returns {string} Sanitized error message
     */
    sanitizeError(error) {
        if (!error) return 'Unknown error';
        const message = error.message || String(error);
        // Remove potential tokens/credentials from error messages
        return message
            .replace(/Bearer\s+[\w-]+/gi, 'Bearer [REDACTED]')
            .replace(/token[=:]\s*[\w-]+/gi, 'token=[REDACTED]')
            .replace(/password[=:]\s*[^\s]+/gi, 'password=[REDACTED]')
            .replace(/api[_-]?key[=:]\s*[\w-]+/gi, 'api_key=[REDACTED]');
    },
    
    /**
     * Check if authentication is currently in progress.
     * 
     * @returns {boolean} True if auth is in progress
     */
    isInProgress() {
        return this._authInProgress;
    },
    
    /**
     * Reset the auth state (useful for cleanup).
     */
    reset() {
        this._authInProgress = false;
    }
};

// Export for global access
window.AuthHandler = AuthHandler;

