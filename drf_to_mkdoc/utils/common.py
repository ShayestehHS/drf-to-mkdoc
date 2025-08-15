import importlib
import json
import re
from asyncio.log import logger
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from django.apps import apps
from django.core.exceptions import AppRegistryNotReady
from django.urls import resolve
from django.utils.module_loading import import_string
from drf_spectacular.generators import SchemaGenerator

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings


class SchemaValidationError(Exception):
    """Custom exception for schema validation errors."""

    pass


class QueryParamTypeError(Exception):
    """Custom exception for query parameter type errors."""

    pass


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


def load_schema() -> dict[str, Any] | None:
    """Load the OpenAPI schema from doc-schema.yaml"""
    schema_file = Path(drf_to_mkdoc_settings.CONFIG_DIR) / "doc-schema.yaml"
    if not schema_file.exists():
        return None

    with schema_file.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_model_json_data() -> dict[str, Any] | None:
    """Load the JSON mapping data for model information"""
    json_file = Path(drf_to_mkdoc_settings.MODEL_DOCS_FILE)
    if not json_file.exists():
        return None

    with json_file.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_doc_config() -> dict[str, Any] | None:
    """Load the documentation configuration file"""
    config_file = Path(drf_to_mkdoc_settings.DOC_CONFIG_FILE)
    if not config_file.exists():
        return None

    with config_file.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_model_docstring(class_name: str) -> str | None:
    """Extract docstring from Django model class"""
    try:
        # Check if Django is properly initialized

        # Try to access Django apps to see if it's initialized
        apps.check_apps_ready()

        # Common Django app names to search
        app_names = drf_to_mkdoc_settings.DJANGO_APPS

        for app_name in app_names:
            try:
                # Try to import the models module
                models_module = importlib.import_module(f"{app_name}.models")

                # Check if the class exists in this module
                if hasattr(models_module, class_name):
                    model_class = getattr(models_module, class_name)

                    # Get the docstring
                    docstring = getattr(model_class, "__doc__", None)

                    if docstring:
                        # Clean up the docstring
                        docstring = docstring.strip()

                        # Filter out auto-generated or generic docstrings
                        if (
                            docstring
                            and not docstring.startswith(class_name + "(")
                            and not docstring.startswith("str(object=")
                            and not docstring.startswith("Return repr(self)")
                            and "django.db.models" not in docstring.lower()
                            and len(docstring) > 10
                        ):  # Minimum meaningful length
                            return docstring

            except (ImportError, AttributeError):
                continue

    except (ImportError, AppRegistryNotReady):
        # Django not initialized or not available - skip docstring extraction
        pass

    return None


def extract_app_from_operation_id(operation_id: str) -> str:
    view = extract_viewset_from_operation_id(operation_id)

    if isinstance(view, type):
        module = view.__module__
    elif hasattr(view, "__class__"):
        module = view.__class__.__module__
    else:
        raise TypeError("Expected a view class or instance")

    return module.split(".")[0]


@lru_cache
def get_custom_schema():
    custom_schema_path = Path(drf_to_mkdoc_settings.CUSTOM_SCHEMA_FILE)
    if not custom_schema_path.exists():
        return {}

    try:
        with custom_schema_path.open(encoding="utf-8") as file:
            data = json.load(file)
    except Exception:
        return {}

    for _operation_id, overrides in data.items():
        parameters = overrides.get("parameters", [])
        if not parameters:
            continue
        for parameter in parameters:
            if {"name", "in", "description", "required", "schema"} - set(parameter.keys()):
                raise SchemaValidationError("Required keys are not passed")

            if parameter["in"] == "query":
                queryparam_type = parameter.get("queryparam_type")
                if not queryparam_type:
                    raise QueryParamTypeError("queryparam_type is required for query")

                if queryparam_type not in (
                    {
                        "search_fields",
                        "filter_fields",
                        "ordering_fields",
                        "filter_backends",
                        "pagination_fields",
                    }
                ):
                    raise QueryParamTypeError("Invalid queryparam_type")
    return data


def convert_to_django_path(path: str, parameters: list[dict[str, Any]]) -> str:
    """
    Convert a path with {param} to a Django-style path with <type:param>.
    If PATH_PARAM_SUBSTITUTOR is set, use that function instead.
    """
    function = None
    func_path = getattr(drf_to_mkdoc_settings, "PATH_PARAM_SUBSTITUTOR", None)

    if func_path:
        try:
            function = import_string(func_path)
        except ImportError:
            logger.warning("PATH_PARAM_SUBSTITUTOR is not a valid import path")

    # If custom function exists and returns a valid value, use it
    if callable(function):
        try:
            value = function(path, parameters)
            if isinstance(value, str) and value.strip():
                return value
        except Exception as e:
            logger.exception("Error in custom path substitutor: %s", e)

    # Default Django path conversion
    def replacement(match):
        param_name = match.group(1)
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

    django_path = re.sub(r"{(\w+)}", replacement, path)

    if not django_path.endswith("/"):
        django_path += "/"

    return django_path


@lru_cache
def get_schema():
    base_schema = SchemaGenerator().get_schema(request=None, public=True)

    custom_data = get_custom_schema()
    if not custom_data:
        return base_schema

    # Map operation_id → (path, method)
    op_map = {}
    for path, actions in base_schema.get("paths", {}).items():
        for method, op_data in actions.items():
            operation_id = op_data.get("operationId")
            if operation_id:
                op_map[operation_id] = (path, method)

    allowed_keys = {"description", "parameters", "requestBody", "responses"}
    for operation_id, overrides in custom_data.items():
        if operation_id not in op_map:
            continue

        append_fields = set(overrides.get("append_fields", []))
        path, method = op_map[operation_id]
        target_schema = base_schema["paths"][path][method]
        for key in allowed_keys:
            if key not in overrides:
                continue

            custom_value = overrides[key]
            base_value = target_schema.get(key)

            if key in append_fields and isinstance(base_value, list):
                target_schema[key].extend(list(custom_value))
            else:
                #  Otherwise, replace
                target_schema[key] = custom_value

    return base_schema


@lru_cache
def get_operation_id_path_map() -> dict[str, str]:
    schema = get_schema()
    paths = schema.get("paths", {})
    mapping = {}

    for path, actions in paths.items():
        for _http_method_name, action_data in actions.items():
            operation_id = action_data.get("operationId")
            if operation_id:
                mapping[operation_id] = path, action_data.get("parameters", [])

    return mapping


def extract_viewset_from_operation_id(operation_id: str):
    """Extract the ViewSet class from an OpenAPI operation ID."""
    operation_map = get_operation_id_path_map()
    path, parameters = operation_map.get(operation_id)

    if not path:
        raise ValueError(f"Path not found for operation ID: {operation_id}")

    try:
        resolved_path = substitute_path_params(path, parameters)
        match = resolve(resolved_path)
        view_func = match.func
        if hasattr(view_func, "view_class"):
            # For generic class-based views
            return view_func.view_class
        try:
            # For viewsets
            return view_func.cls
        except AttributeError:
            pass
        else:
            return view_func

    except Exception:
        logger.error(f"Failed to resolve path {path}")


def extract_viewset_name_from_operation_id(operation_id: str):
    view_cls = extract_viewset_from_operation_id(operation_id)
    return view_cls.__name__ if hasattr(view_cls, "__name__") else str(view_cls)


def format_method_badge(method: str) -> str:
    """Create a colored badge for HTTP method"""
    return f'<span class="method-badge method-{method.lower()}">{method.upper()}</span>'


def write_file(file_path: str, content: str) -> None:
    full_path = Path(drf_to_mkdoc_settings.DOCS_DIR) / file_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    with full_path.open("w", encoding="utf-8") as f:
        f.write(content)


def get_model_description(class_name: str) -> str:
    """Get a brief description for a model with priority-based selection"""
    # Priority 1: Description from config file
    config = load_doc_config()
    if config and "model_descriptions" in config:
        config_description = config["model_descriptions"].get(class_name, "").strip()
        if config_description:
            return config_description

    # Priority 2: Extract docstring from model class
    docstring = get_model_docstring(class_name)
    if docstring:
        return docstring

    # Priority 3: static value
    return "Not provided"


def get_app_descriptions() -> dict[str, str]:
    """Get descriptions for Django apps from config file"""
    config = load_doc_config()
    if config and "app_descriptions" in config:
        return config["app_descriptions"]

    # Fallback to empty dict if config not available
    return {}


def create_safe_filename(path: str, method: str) -> str:
    """Create a safe filename from path and method"""
    safe_path = re.sub(r"[^a-zA-Z0-9_-]", "_", path.strip("/"))
    return f"{method.lower()}_{safe_path}.md"
