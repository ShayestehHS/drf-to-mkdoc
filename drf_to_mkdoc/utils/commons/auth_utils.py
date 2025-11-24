"""Utilities for handling authentication in auto-auth feature."""
import os
from pathlib import Path
from typing import Optional

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings


def load_auth_function_js() -> Optional[str]:
    """
    Load the JavaScript auth function from settings.
    
    Returns:
        JavaScript code string if available, None otherwise.
        
    The function can be:
    - Direct JavaScript code (if it contains 'function' or '=>')
    - Path to a JavaScript file (relative to project root or absolute)
    """
    auth_function_js = drf_to_mkdoc_settings.AUTH_FUNCTION_JS
    if not auth_function_js:
        return None
    
    # Check if it's JavaScript code (contains function definition)
    if "function" in auth_function_js or "=>" in auth_function_js:
        return auth_function_js
    
    # Otherwise, treat as file path
    auth_path = Path(auth_function_js)
    
    # If relative path, try relative to project root
    if not auth_path.is_absolute():
        # Try to find the project root (where manage.py or pyproject.toml is)
        current_dir = Path.cwd()
        project_root = None
        
        # Look for common project root indicators
        for parent in [current_dir] + list(current_dir.parents):
            if (parent / "manage.py").exists() or (parent / "pyproject.toml").exists():
                project_root = parent
                break
        
        if project_root:
            auth_path = project_root / auth_function_js
        else:
            auth_path = current_dir / auth_function_js
    
    # Read the file
    if auth_path.exists() and auth_path.is_file():
        try:
            with auth_path.open("r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None
    
    return None


def get_auth_config() -> dict:
    """
    Get authentication configuration for templates.
    
    Returns:
        Dictionary with auth configuration including:
        - enable_auto_auth: bool
        - auth_function_js: str or None
        - auth_username: str or None
    """
    enable_auto_auth = drf_to_mkdoc_settings.ENABLE_AUTO_AUTH
    auth_function_js = None
    
    if enable_auto_auth:
        auth_function_js = load_auth_function_js()
    
    return {
        "enable_auto_auth": enable_auto_auth,
        "auth_function_js": auth_function_js,
        "auth_username": drf_to_mkdoc_settings.AUTH_USERNAME,
    }

