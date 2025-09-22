import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

from drf_spectacular.generators import SchemaGenerator

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings
from drf_to_mkdoc.utils.commons.file_utils import load_json_data


class SchemaValidationError(Exception):
    """Custom exception for schema validation errors."""

    pass


class QueryParamTypeError(Exception):
    """Custom exception for query parameter type errors."""

    pass


def get_custom_schema():
    custom_schema_data = load_json_data(
        drf_to_mkdoc_settings.CUSTOM_SCHEMA_FILE, raise_not_found=False
    )
    if not custom_schema_data:
        return {}

    for _operation_id, overrides in custom_schema_data.items():
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
                        "pagination_fields",
                    }
                ):
                    raise QueryParamTypeError("Invalid queryparam_type")

    return custom_schema_data


def _merge_parameters(
    base_parameters: list[dict[str, Any]], custom_parameters: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Merge parameters from base and custom schemas, avoiding duplicates.

    Parameters are considered duplicates if they have the same 'name' and 'in' values.
    Custom parameters will override base parameters with the same (name, in) key.
    """

    def _get_param_key(param: dict[str, Any]) -> tuple[str, str] | None:
        """Extract (name, in) tuple from parameter, return None if invalid."""
        name = param.get("name")
        location = param.get("in")
        return (name, location) if name and location else None

    param_index = {}
    for param in base_parameters:
        key = _get_param_key(param)
        if key:
            param_index[key] = param

    for param in custom_parameters:
        key = _get_param_key(param)
        if key:
            param_index[key] = param

    return list(param_index.values())


def _build_operation_map(base_schema: dict) -> dict[str, tuple[str, str]]:
    """Build a mapping from operationId → (path, method)."""
    op_map = {}
    HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}

    for path, actions in base_schema.get("paths", {}).items():
        for method, op_data in actions.items():
            if method.lower() not in HTTP_METHODS or not isinstance(op_data, dict):
                continue
            if not op_data.get("x-metadata"):
                raise ValueError(
                    "Missing x-metadata in OpenAPI schema. Please ensure you're using the custom AutoSchema in your REST_FRAMEWORK settings:\n"
                    "REST_FRAMEWORK = {\n"
                    "    'DEFAULT_SCHEMA_CLASS': 'drf_to_mkdoc.utils.schema.AutoSchema',\n"
                    "}\n"
                )
            operation_id = op_data.get("operationId")
            if operation_id:
                op_map[operation_id] = (path, method)

    return op_map


def _apply_custom_overrides(
    base_schema: dict,
    op_map: dict[str, tuple[str, str]],
    custom_data: dict,
) -> None:
    """Apply custom overrides to the base schema."""
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

            if key in append_fields:
                if isinstance(base_value, list) and isinstance(custom_value, list):
                    if key == "parameters":
                        target_schema[key] = _merge_parameters(base_value, custom_value)
                    else:
                        target_schema[key].extend(custom_value)
                else:
                    target_schema[key] = custom_value
            else:
                target_schema[key] = custom_value


@lru_cache(maxsize=1)
def get_schema():
    base_schema = SchemaGenerator().get_schema(request=None, public=True)
    custom_data = get_custom_schema()
    if not custom_data:
        return deepcopy(base_schema)

    operation_map = _build_operation_map(base_schema)
    _apply_custom_overrides(base_schema, operation_map, custom_data)

    return deepcopy(base_schema)


class OperationExtractor:
    """Extracts operation IDs and metadata from OpenAPI schema."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.schema = get_schema()
            self._operation_map = None
            self._initialized = True

    def save_operation_map(self) -> None:
        """Save operation map to file."""
        if not self._operation_map:
            self._operation_map = self._build_operation_map()

        operation_map_path = Path(drf_to_mkdoc_settings.AI_OPERATION_MAP_FILE)
        # Create parent directories if they don't exist
        operation_map_path.parent.mkdir(parents=True, exist_ok=True)

        with operation_map_path.open("w", encoding="utf-8") as f:
            json.dump(self._operation_map, f, indent=2)

    @property
    def operation_map(self) -> dict[str, dict[str, Any]] | None:
        """
        Cache and return operation ID mapping.
         Returns dict: operation_id -> {"path": str, ...metadata}
        """
        if self._operation_map is None:
            # Try to load from file first
            self._operation_map = load_json_data(
                drf_to_mkdoc_settings.AI_OPERATION_MAP_FILE, raise_not_found=False
            )

            # If not found or invalid, build and save
            if self._operation_map is None:
                self._operation_map = self._build_operation_map()
                self.save_operation_map()

        return self._operation_map

    def _build_operation_map(self) -> dict[str, dict[str, Any]] | None:
        """Build mapping of operation IDs to paths and metadata."""
        mapping = {}
        paths = self.schema.get("paths", {})

        for path, methods in paths.items():
            for _method, operation in methods.items():
                operation_id = operation.get("operationId")
                if not operation_id:
                    continue

                metadata = operation.get("x-metadata", {})
                mapping[operation_id] = {"path": path, **metadata}

        return mapping
