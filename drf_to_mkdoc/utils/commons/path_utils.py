"""Path manipulation utilities."""

import logging
import re
from typing import Any

from django.utils.module_loading import import_string

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings

logger = logging.getLogger(__name__)


def substitute_path_params(path: str, parameters: list[dict[str, Any]]) -> str:
    django_path = convert_to_django_path(path, parameters)

    django_path = re.sub(r"\{[^}]+\}", "1", django_path)
    django_path = re.sub(r"<int:[^>]+>", "1", django_path)
    django_path = re.sub(r"<uuid:[^>]+>", "12345678-1234-5678-9abc-123456789012", django_path)
    django_path = re.sub(r"<float:[^>]+>", "1.0", django_path)
    django_path = re.sub(r"<(?:string|str):[^>]+>", "dummy", django_path)
    django_path = re.sub(r"<path:[^>]+>", "dummy/path", django_path)
    django_path = re.sub(r"<[^:>]+>", "dummy", django_path)  # Catch remaining simple params

    return django_path  # noqa: RET504


def convert_to_django_path(path: str, parameters: list[dict[str, Any]]) -> str:
    """
    Convert a path with {param} to a Django-style path with <type:param>.
    If PATH_PARAM_SUBSTITUTE_FUNCTION is set, call it and merge its returned mapping.
    """
    function = None
    func_path = drf_to_mkdoc_settings.PATH_PARAM_SUBSTITUTE_FUNCTION

    if func_path:
        try:
            function = import_string(func_path)
        except ImportError:
            logger.warning("Invalid PATH_PARAM_SUBSTITUTE_FUNCTION import path: %r", func_path)

    # If custom function exists and returns a valid value, use it
    mapping = dict(drf_to_mkdoc_settings.PATH_PARAM_SUBSTITUTE_MAPPING or {})
    if callable(function):
        try:
            result = function(path, parameters)
            if result and isinstance(result, dict):
                mapping.update(result)
        except Exception:
            logger.exception("Error in custom path substitutor %r for path %r", func_path, path)

    # Default Django path conversion
    def replacement(match):
        param_name = match.group(1)
        custom_param_type = mapping.get(param_name)
        if custom_param_type and custom_param_type in ("int", "uuid", "str"):
            converter = custom_param_type
        else:
            param_info = next((p for p in parameters if p.get("name") == param_name), {})
            param_type = param_info.get("schema", {}).get("type")
            param_format = param_info.get("schema", {}).get("format")

            if param_type == "integer":
                converter = "int"
            elif param_type == "string" and param_format == "uuid":
                converter = "uuid"
            else:
                converter = "str"

        return f"<{converter}:{param_name}>"

    return re.sub(r"{(\w+)}", replacement, path)


def create_safe_filename(path: str, method: str) -> str:
    """Create a safe filename from path and method"""
    safe_path = re.sub(r"[^a-zA-Z0-9_-]", "_", path.strip("/"))
    return f"{method.lower()}_{safe_path}.md"


def camel_case_to_readable(name: str) -> str:
    """
    Convert camelCase or all-lowercase class name to readable format.
    
    Args:
        name: Class name (e.g., "IsAuthenticated", "deleteserverpermission")
    
    Returns:
        Readable format (e.g., "Is Authenticated", "Delete Server Permission")
    """
    if not name:
        return name
    
    import re
    
    # First, handle camelCase by adding spaces before capital letters
    result = re.sub(r'([A-Z])', r' \1', name)
    
    # If the string is all lowercase (no spaces added), try to split intelligently
    if result == name and name == name.lower():
        # Common permission word patterns (sorted by length, longest first for greedy matching)
        common_words = [
            'authenticated', 'permission', 'anonymous', 'instance', 'resource',
            'delete', 'create', 'update', 'server', 'team', 'user', 'admin', 'staff',
            'object', 'model', 'action', 'access', 'manage', 'remove', 'change',
            'read', 'view', 'list', 'edit', 'grant', 'revoke',
            'get', 'post', 'put', 'has', 'can', 'is', 'add', 'deny', 'allow'
        ]
        
        # Try to find and split by these words
        remaining = name.lower()
        found_words = []
        
        while remaining:
            matched = False
            # Try to match from longest to shortest words
            for word in common_words:
                if remaining.startswith(word):
                    found_words.append(word)
                    remaining = remaining[len(word):]
                    matched = True
                    break
            
            if not matched:
                # If no word matches, try to find the next word boundary
                next_match = None
                next_match_index = len(remaining)
                
                for word in common_words:
                    index = remaining.find(word)
                    if 0 < index < next_match_index:
                        next_match = word
                        next_match_index = index
                
                if next_match and next_match_index > 0:
                    # Found a word later in the string, take everything before it as a word
                    before_word = remaining[:next_match_index]
                    if before_word:
                        found_words.append(before_word)
                    remaining = remaining[next_match_index:]
                else:
                    # No more matches, take the rest as one word
                    if remaining:
                        found_words.append(remaining)
                    break
        
        # Capitalize first letter of each word
        result = ' '.join(word.capitalize() for word in found_words)
    else:
        # Handle camelCase: capitalize first letter and clean up
        words = [w for w in result.split() if w]
        result = ' '.join(word[0].upper() + word[1:].lower() if len(word) > 1 else word.upper() for word in words)
    
    return result.strip()


def get_permission_url(permission_class_path: str) -> str:
    """
    Generate URL path for permission detail page.
    
    Args:
        permission_class_path: Full path to permission class (e.g., "rest_framework.permissions.IsAuthenticated")
    
    Returns:
        URL path (e.g., "permissions/rest_framework/permissions/IsAuthenticated/")
    """
    # Replace dots with slashes for URL path, but keep the full path structure
    # This ensures unique URLs for each permission class and creates a directory structure
    safe_path = permission_class_path.replace(".", "/")
    return f"permissions/{safe_path}/"
