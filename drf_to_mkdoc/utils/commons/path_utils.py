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

    # Handle camelCase: insert space before uppercase letters
    # This catches transitions from lowercase to uppercase
    result = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)

    # Handle sequences of capitals followed by lowercase (e.g., "XMLParser" -> "XML Parser")
    result = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', result)

    # If still no spaces (all lowercase), insert spaces before common suffixes/patterns
    if ' ' not in result:
        # Insert space before common word boundaries using lookahead
        # This handles patterns like: "deleteserver" -> "delete server"
        result = re.sub(r'([a-z])([A-Z]|permission|server|user|admin|team)', r'\1 \2', result, flags=re.IGNORECASE)

    # Title case each word
    result = ' '.join(word.capitalize() for word in result.split())

    return result.strip()

def get_permission_url(permission_class_path: str, relative_from_endpoint: bool = True) -> str:
    """
    Generate URL path for permission detail page.
    
    Args:
        permission_class_path: Full path to permission class (e.g., "rest_framework.permissions.IsAuthenticated")
        relative_from_endpoint: If True, returns relative path from endpoint pages (with ../../../ prefix).
                                If False, returns base path without prefix (for file paths).
    
    Returns:
        URL path (e.g., "../../../permissions/rest_framework/permissions/IsAuthenticated/" or
                 "permissions/rest_framework/permissions/IsAuthenticated/")
    """
    # Replace dots with slashes for URL path, but keep the full path structure
    # This ensures unique URLs for each permission class and creates a directory structure
    safe_path = permission_class_path.replace(".", "/")
    base_path = f"permissions/{safe_path}/"
    
    # Endpoint pages are at endpoints/{app}/{viewset}/{file}.md (3 directory levels deep)
    # Permission pages are at permissions/{path}/index.md (at docs root level)
    # To go from endpoints/{app}/{viewset}/file.md to permissions/{path}/index.md:
    #   ../ goes up to {viewset}/
    #   ../../ goes up to {app}/
    #   ../../../ goes up to endpoints/
    #   ../../../permissions/ reaches the permissions directory at docs root
    # This hardcoded depth assumes the fixed structure: endpoints/{app}/{viewset}/{file}.md
    if relative_from_endpoint:
        return f"../../../{base_path}"
    return base_path
