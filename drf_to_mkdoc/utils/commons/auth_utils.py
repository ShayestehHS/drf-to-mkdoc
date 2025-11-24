"""Utilities for handling authentication in auto-auth feature."""
from pathlib import Path
from typing import List, Optional

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
    
    auth_path_value = Path(auth_function_js)
    candidate_paths: List[Path] = []

    if auth_path_value.is_absolute():
        candidate_paths.append(auth_path_value)
    else:
        current_dir = Path.cwd()
        project_root = None

        for parent in [current_dir, *current_dir.parents]:
            if (parent / "manage.py").exists() or (parent / "pyproject.toml").exists():
                project_root = parent
                break

        if project_root:
            candidate_paths.append(project_root / auth_function_js)
        candidate_paths.append(current_dir / auth_function_js)

    seen_paths = set()
    for candidate in candidate_paths:
        resolved_candidate = candidate.resolve()
        if resolved_candidate in seen_paths:
            continue
        seen_paths.add(resolved_candidate)

        if resolved_candidate.exists() and resolved_candidate.is_file():
            try:
                with resolved_candidate.open("r", encoding="utf-8") as file_obj:
                    return file_obj.read()
            except (OSError, UnicodeDecodeError):
                return None

    # Fall back to treating the value as inline JS only if no file was found/read
    if "function" in auth_function_js or "=>" in auth_function_js:
        return auth_function_js

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

