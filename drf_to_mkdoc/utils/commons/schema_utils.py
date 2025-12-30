import inspect
import json
import logging
from copy import deepcopy
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Any

from drf_spectacular.generators import SchemaGenerator

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings
from drf_to_mkdoc.utils.commons.file_utils import (
    load_json_data,
    load_json_files_from_dir,
    merge_openapi_schemas,
)

logger = logging.getLogger(__name__)


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


def is_endpoint_secure(operation_id: str, endpoint_data: dict[str, Any]) -> bool:
    """
    Check if an endpoint requires authentication.
    
    Checks both OpenAPI security field and custom schema overrides.
    
    Args:
        operation_id: The operation ID of the endpoint
        endpoint_data: The endpoint data from OpenAPI schema
        
    Returns:
        True if endpoint requires authentication, False otherwise
    """
    # Check custom schema first (has higher priority)
    custom_schema_data = get_custom_schema()
    if operation_id in custom_schema_data:
        custom_data = custom_schema_data[operation_id]
        # Check for explicit security flag
        if "need_authentication" in custom_data:
            return bool(custom_data["need_authentication"])
    
    # Check OpenAPI security field
    security = endpoint_data.get("security")
    if security is not None:
        # Empty list means no auth required
        # Non-empty list (even with empty dicts) means auth required
        return len(security) > 0
    
    return False


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

        # Handle security override (need_authentication)
        if "need_authentication" in overrides:
            needs_auth = overrides.get("need_authentication")
            if needs_auth is True:
                # Force security requirement
                if "security" not in target_schema or not target_schema["security"]:
                    target_schema["security"] = [{}]  # Empty dict means auth required
            elif needs_auth is False:
                # Remove security requirement
                target_schema["security"] = []

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


def _load_base_schema() -> dict[str, Any]:
    """
    Load base OpenAPI schema from JSON file(s) if configured, otherwise generate it.
    
    Priority:
    1. SCHEMA_JSON_FILE (single file) - if set, loads from this file
    2. SCHEMA_JSON_DIR (directory) - if set, loads and merges all JSON files from directory
    3. SchemaGenerator - fallback to generating schema dynamically
    
    Returns:
        Base OpenAPI schema dictionary
    """
    # Try loading from single JSON file first
    schema_json_file = drf_to_mkdoc_settings.SCHEMA_JSON_FILE
    if schema_json_file:
        logger.info(f"Loading schema from JSON file: {schema_json_file}")
        base_schema = load_json_data(schema_json_file, raise_not_found=True)
        if not isinstance(base_schema, dict):
            raise SchemaValidationError(
                f"Schema JSON file must contain a JSON object (dict), got {type(base_schema).__name__}"
            )
        return base_schema
    
    # Try loading from directory of JSON files
    schema_json_dir = drf_to_mkdoc_settings.SCHEMA_JSON_DIR
    if schema_json_dir:
        logger.info(f"Loading and merging schemas from directory: {schema_json_dir}")
        schemas = load_json_files_from_dir(schema_json_dir, raise_not_found=True)
        if not schemas:
            raise SchemaValidationError(
                f"No valid JSON schema files found in directory: {schema_json_dir}"
            )
        logger.info(f"Merging {len(schemas)} schema files")
        base_schema = merge_openapi_schemas(schemas)
        return base_schema
    
    # Fallback to generating schema dynamically
    logger.info("Generating schema dynamically using SchemaGenerator")
    return SchemaGenerator().get_schema(request=None, public=True)


@lru_cache(maxsize=1)
def get_schema():
    base_schema = _load_base_schema()
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


@lru_cache(maxsize=1)
def get_references() -> dict[str, Any]:
    """
    Load references from separate JSON file.
    
    References file contains reusable descriptions for permissions, serializers,
    responses, and other components to avoid redundancy in schema files.
    
    Structure:
    {
        "rest_framework.permissions.IsAuthenticated": {
            "description": "User must be authenticated to access this endpoint."
        },
        ...
    }
    
    Returns:
        Dictionary of references, or empty dict if file doesn't exist
    """
    references_data = load_json_data(
        drf_to_mkdoc_settings.REFERENCES_FILE, raise_not_found=False
    )
    if not references_data:
        return {}
    
    # Validate structure - should be a dict
    if not isinstance(references_data, dict):
        raise SchemaValidationError(
            f"References file must contain a JSON object (dict), got {type(references_data).__name__}"
        )
    
    return references_data


def get_permission_description(permission_class_path: str) -> dict[str, str | None]:
    """
    Get permission short description with priority: schema JSON > docstring > None.
    
    Args:
        permission_class_path: Full path to permission class (e.g., "rest_framework.permissions.IsAuthenticated")
    
    Returns:
        Dictionary with 'short' key containing description string or None
    """
    result = {"short": None}
    
    # Priority 1: Check references file
    references = get_references()
    if permission_class_path in references:
        permission_data = references[permission_class_path]
        if isinstance(permission_data, dict):
            # Get short description (custom or from description field)
            short_desc = permission_data.get("short_description")
            if short_desc:
                result["short"] = short_desc
            else:
                # Use description field as short description if short_description not provided
                desc = permission_data.get("description")
                if desc:
                    result["short"] = _truncate_description(desc)
    
    # Priority 2: Extract docstring from permission class
    if not result["short"]:
        try:
            # Parse module and class name
            module_path, class_name = permission_class_path.rsplit(".", 1)
            module = import_module(module_path)
            permission_class = getattr(module, class_name)
            
            # Get docstring directly from the class (not from parent classes)
            # Check if the class itself has a docstring in its __dict__
            docstring = None
            
            # First, check if __doc__ is defined in the class's own __dict__
            if "__doc__" in permission_class.__dict__:
                docstring = permission_class.__dict__["__doc__"]
            else:
                # If not in __dict__, check if __doc__ exists and is not from a parent
                class_doc = getattr(permission_class, "__doc__", None)
                if class_doc:
                    # Verify this docstring is not inherited from a parent class
                    # by checking all parent classes in the MRO
                    is_inherited = False
                    for base in inspect.getmro(permission_class)[1:]:  # Skip the class itself
                        if hasattr(base, "__doc__") and base.__doc__ == class_doc:
                            # This docstring comes from a parent class, skip it
                            is_inherited = True
                            break
                    
                    if not is_inherited:
                        docstring = class_doc
            
            if docstring:
                docstring = docstring.strip()
                # Only use if it's not empty and has meaningful content
                if docstring and len(docstring) > 10:  # Minimum meaningful length
                    # Auto-truncate for short version
                    result["short"] = _truncate_description(docstring)
        except (ImportError, AttributeError, ValueError) as e:
            # Gracefully handle import errors
            logger.debug(f"Could not extract docstring for {permission_class_path}: {e}")
    
    return result


def _truncate_description(description: str, max_length: int = 100) -> str:
    """
    Truncate description to short version.
    
    Args:
        description: Full description text
        max_length: Maximum length for truncated version
    
    Returns:
        Truncated description with ellipsis if needed
    """
    if len(description) <= max_length:
        return description
    
    # Try to truncate at sentence boundary
    truncated = description[:max_length]
    last_period = truncated.rfind('.')
    last_newline = truncated.rfind('\n')
    
    # Use the last sentence boundary if found within reasonable distance
    if last_period > max_length * 0.7:
        return truncated[:last_period + 1]
    elif last_newline > max_length * 0.7:
        return truncated[:last_newline].strip()
    else:
        # Truncate at word boundary
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.7:
            return truncated[:last_space] + '...'
        else:
            return truncated + '...'
