"""Utilities for handling authentication in auto-auth feature."""
import re
from pathlib import Path
from typing import List, Optional

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings


def _is_likely_inline_js(content: str) -> bool:
    """
    Heuristically determine if content is inline JavaScript.
    
    Args:
        content: The content to check
        
    Returns:
        True if content appears to be inline JavaScript, False otherwise
    """
    # Check for JS function patterns
    js_patterns = [
        r'\bfunction\s+\w+\s*\(',
        r'\bfunction\s*\(',
        r'\w+\s*=>\s*[{(]',
        r'\bconst\s+\w+\s*=\s*function',
        r'\bconst\s+\w+\s*=\s*\(',
        r'\blet\s+\w+\s*=\s*function',
        r'\bvar\s+\w+\s*=\s*function',
    ]
    return any(re.search(pattern, content) for pattern in js_patterns)


def load_auth_function_js() -> Optional[str]:
    """
    Load the JavaScript auth function from settings.
    
    Returns:
        JavaScript code string if available, None otherwise.
        
    The function can be:
    - Direct JavaScript code (if it matches JS patterns)
    - Path to a JavaScript file (relative to project root or absolute)
    
    Security:
    - Paths are validated to ensure they're within the project root
    - Only .js and .javascript file extensions are allowed
    - Path traversal attempts are blocked
    """
    auth_function_js = drf_to_mkdoc_settings.AUTH_FUNCTION_JS
    if not auth_function_js:
        return None
    
    # Detect inline JS first (before any file operations)
    if _is_likely_inline_js(auth_function_js):
        return auth_function_js
    
    auth_path_value = Path(auth_function_js)
    candidate_paths: List[Path] = []
    current_dir = Path.cwd()
    project_root = None

    # Find project root
    for parent in [current_dir, *current_dir.parents]:
        if (parent / "manage.py").exists() or (parent / "pyproject.toml").exists():
            project_root = parent
            break

    if auth_path_value.is_absolute():
        candidate_paths.append(auth_path_value)
    else:
        if project_root:
            candidate_paths.append(project_root / auth_function_js)
        candidate_paths.append(current_dir / auth_function_js)

    seen_paths = set()
    for candidate in candidate_paths:
        try:
            resolved_candidate = candidate.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
            
        # Validate the resolved path is within allowed directories
        if project_root:
            try:
                # Check if resolved path is relative to project root
                resolved_candidate.relative_to(project_root.resolve())
            except ValueError:
                # Path is outside project root - skip it
                continue
        
        if resolved_candidate in seen_paths:
            continue
        seen_paths.add(resolved_candidate)

        if resolved_candidate.exists() and resolved_candidate.is_file():
            # Additional validation: check file extension
            if resolved_candidate.suffix.lower() not in ['.js', '.javascript']:
                continue
                
            try:
                with resolved_candidate.open("r", encoding="utf-8") as file_obj:
                    return file_obj.read()
            except (OSError, UnicodeDecodeError):
                continue

    return None


def get_auth_config() -> dict:
    """
    Get authentication configuration for templates.
    
    Returns:
        Dictionary with auth configuration including:
        - enable_auto_auth: bool
        - auth_function_js: str or None
    """
    enable_auto_auth = drf_to_mkdoc_settings.ENABLE_AUTO_AUTH
    auth_function_js = None
    
    if enable_auto_auth:
        auth_function_js = load_auth_function_js()
    
    return {
        "enable_auto_auth": enable_auto_auth,
        "auth_function_js": auth_function_js,
    }

