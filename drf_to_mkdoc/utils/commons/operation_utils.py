"""Operation ID and viewset utilities."""

import logging
from functools import lru_cache
from typing import Any

from django.urls import Resolver404, resolve

from drf_to_mkdoc.utils.commons.path_utils import substitute_path_params
from drf_to_mkdoc.utils.commons.schema_utils import get_schema

logger = logging.getLogger(__name__)


@lru_cache
def get_operation_id_path_map() -> dict[str, tuple[str, list[dict[str, Any]]]]:
    schema = get_schema()
    paths = schema.get("paths", {})
    mapping = {}

    for path, actions in paths.items():
        for http_method_name, action_data in actions.items():
            if http_method_name.lower() == "parameters" or not isinstance(action_data, dict):
                # Skip path-level parameters entries (e.g., "parameters": [...] in OpenAPI schema)
                continue
            operation_id = action_data.get("operationId")
            if operation_id:
                mapping[operation_id] = (path, action_data.get("parameters", []))

    return mapping


def extract_viewset_from_operation_id(operation_id: str):
    """Extract the ViewSet class from an OpenAPI operation ID."""
    operation_map = get_operation_id_path_map()
    entry = operation_map.get(operation_id)
    if not entry:
        raise ValueError(f"Unknown operationId: {operation_id!r}")
    path, parameters = entry

    resolved_path = substitute_path_params(path, parameters)
    try:
        match = resolve(resolved_path)
        view_func = match.func
        if hasattr(view_func, "view_class"):
            # For generic class-based views
            return view_func.view_class

        if hasattr(view_func, "cls"):
            # For viewsets
            return view_func.cls

    except Resolver404:
        logger.exception(
            "Failed to resolve path. schema_path=%s tried_path=%s",
            path,
            resolved_path,
        )
    else:
        return view_func


def extract_viewset_name_from_operation_id(operation_id: str):
    view_cls = extract_viewset_from_operation_id(operation_id)
    return view_cls.__name__ if hasattr(view_cls, "__name__") else str(view_cls)


def extract_app_from_operation_id(operation_id: str) -> str:
    view = extract_viewset_from_operation_id(operation_id)

    if isinstance(view, type):
        module = view.__module__
    elif hasattr(view, "__class__"):
        module = view.__class__.__module__
    else:
        raise TypeError("Expected a view class or instance")

    return module.split(".")[0]


def format_method_badge(method: str) -> str:
    """Create a colored badge for HTTP method"""
    return f'<span class="method-badge method-{method.lower()}">{method.upper()}</span>'
