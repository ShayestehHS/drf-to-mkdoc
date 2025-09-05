"""Path manipulation utilities."""

import re
from asyncio.log import logger
from typing import Any

from django.utils.module_loading import import_string

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings


def substitute_path_params(path: str, parameters: list[dict[str, Any]]) -> str:
    django_path = convert_to_django_path(path, parameters)

    django_path = re.compile(r"\{[^}]+\}").sub("1", django_path)
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
    If PATH_PARAM_SUBSTITUTE_FUNCTION is set, use that function instead.
    """
    function = None
    func_path = drf_to_mkdoc_settings.PATH_PARAM_SUBSTITUTE_FUNCTION

    if func_path:
        try:
            function = import_string(func_path)
        except ImportError:
            logger.warning("PATH_PARAM_SUBSTITUTE_FUNCTION is not a valid import path")

    # If custom function exists and returns a valid value, use it
    PATH_PARAM_SUBSTITUTE_MAPPING = drf_to_mkdoc_settings.PATH_PARAM_SUBSTITUTE_MAPPING
    if callable(function):
        try:
            result = function(path, parameters)
            if result and isinstance(result, dict):
                PATH_PARAM_SUBSTITUTE_MAPPING.update(result)
        except Exception as e:
            logger.exception("Error in custom path substitutor: %s", e)

    # Default Django path conversion
    def replacement(match):
        param_name = match.group(1)
        custom_param_type = PATH_PARAM_SUBSTITUTE_MAPPING.get(param_name)
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
