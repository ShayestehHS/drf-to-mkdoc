import ast
import inspect
import json
import logging
from collections import defaultdict
from typing import Any

from django.apps import apps
from django.template.loader import render_to_string
from rest_framework import serializers

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings
from drf_to_mkdoc.utils.commons.file_utils import write_file
from drf_to_mkdoc.utils.commons.operation_utils import (
    extract_app_from_operation_id,
    extract_viewset_name_from_operation_id,
)
from drf_to_mkdoc.utils.commons.path_utils import create_safe_filename
from drf_to_mkdoc.utils.commons.schema_utils import get_custom_schema
from drf_to_mkdoc.utils.extractors.query_parameter_extractors import (
    extract_query_parameters_from_view,
)

logger = logging.getLogger()


def analyze_serializer_method_field_schema(serializer_class, field_name: str) -> dict:
    """Analyze a SerializerMethodField to determine its actual return type schema."""
    method_name = f"get_{field_name}"

    # Strategy 1: Check type annotations
    schema_from_annotations = _extract_schema_from_type_hints(serializer_class, method_name)
    if schema_from_annotations:
        return schema_from_annotations

    # Strategy 2: Analyze method source code
    schema_from_source = _analyze_method_source_code(serializer_class, method_name)
    if schema_from_source:
        return schema_from_source

    # Strategy 3: Runtime analysis (sample execution)
    schema_from_runtime = _analyze_method_runtime(serializer_class, method_name)
    if schema_from_runtime:
        return schema_from_runtime

    # Fallback to string
    return {"type": "string"}


def _extract_schema_from_type_hints(serializer_class, method_name: str) -> dict:
    """Extract schema from method type annotations."""
    try:
        method = getattr(serializer_class, method_name, None)
        if not method:
            return {}

        signature = inspect.signature(method)
        return_annotation = signature.return_annotation

        if return_annotation and return_annotation != inspect.Signature.empty:
            # Handle common type hints
            if return_annotation in (int, str, bool, float):
                return {
                    int: {"type": "integer"},
                    str: {"type": "string"},
                    bool: {"type": "boolean"},
                    float: {"type": "number"},
                }[return_annotation]

            if hasattr(return_annotation, "__origin__"):
                # Handle generic types like List[str], Dict[str, Any]
                origin = return_annotation.__origin__
                if origin is list:
                    return {"type": "array", "items": {"type": "string"}}
                if origin is dict:
                    return {"type": "object"}

    except Exception:
        logger.exception("Failed to extract schema from type hints")
    return {}


def _analyze_method_source_code(serializer_class, method_name: str) -> dict:
    """Analyze method source code to infer return type."""
    try:
        method = getattr(serializer_class, method_name, None)
        if not method:
            return {}

        source = inspect.getsource(method)
        tree = ast.parse(source)

        # Find return statements and analyze them
        return_analyzer = ReturnStatementAnalyzer()
        return_analyzer.visit(tree)

        return _infer_schema_from_return_patterns(return_analyzer.return_patterns)

    except Exception:
        logger.exception("Failed to analyze method source code")
    return {}


def _analyze_method_runtime(serializer_class, method_name: str) -> dict:
    """Analyze method by creating mock instances and examining return values."""
    try:
        # Create a basic mock object with common attributes
        mock_obj = type(
            "MockObj",
            (),
            {
                "id": 1,
                "pk": 1,
                "name": "test",
                "count": lambda: 5,
                "items": type("items", (), {"count": lambda: 3, "all": lambda: []})(),
            },
        )()

        serializer_instance = serializer_class()
        method = getattr(serializer_instance, method_name, None)

        if not method:
            return {}

        # Execute method with mock data
        result = method(mock_obj)
        return _infer_schema_from_value(result)

    except Exception:
        logger.exception("Failed to analyse method runtime")
    return {}


class ReturnStatementAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze return statements in method source code."""

    def __init__(self):
        self.return_patterns = []

    def visit_Return(self, node):
        """Visit return statements and extract patterns."""
        if node.value:
            pattern = self._analyze_return_value(node.value)
            if pattern:
                self.return_patterns.append(pattern)
        self.generic_visit(node)

    def _analyze_return_value(self, node) -> dict:
        """Analyze different types of return value patterns."""
        if isinstance(node, ast.Dict):
            return self._analyze_dict_return(node)
        if isinstance(node, ast.List):
            return self._analyze_list_return(node)
        if isinstance(node, ast.Constant):
            return self._analyze_constant_return(node)
        if isinstance(node, ast.Call):
            return self._analyze_method_call_return(node)
        if isinstance(node, ast.Attribute):
            return self._analyze_attribute_return(node)
        return {}

    def _analyze_dict_return(self, node) -> dict:
        """Analyze dictionary return patterns."""
        properties = {}
        for key, value in zip(node.keys, node.values, strict=False):
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                prop_schema = self._infer_value_type(value)
                if prop_schema:
                    properties[key.value] = prop_schema

        return {"type": "object", "properties": properties}

    def _analyze_list_return(self, node) -> dict:
        """Analyze list return patterns."""
        if node.elts:
            # Analyze first element to determine array item type
            first_element_schema = self._infer_value_type(node.elts[0])
            return {"type": "array", "items": first_element_schema or {"type": "string"}}
        return {"type": "array", "items": {"type": "string"}}

    def _analyze_constant_return(self, node) -> dict:
        """Analyze constant return values."""
        return self._python_type_to_schema(type(node.value))

    def _analyze_method_call_return(self, node) -> dict:
        """Analyze method call returns (like obj.count(), obj.items.all())."""
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr

            # Common Django ORM patterns
            if method_name in ["count"]:
                return {"type": "integer"}
            if method_name in ["all", "filter", "exclude"]:
                return {"type": "array", "items": {"type": "object"}}
            if method_name in ["first", "last", "get"]:
                return {"type": "object"}
            if method_name in ["exists"]:
                return {"type": "boolean"}

        return {}

    def _analyze_attribute_return(self, node) -> dict:
        """Analyze attribute access returns (like obj.name, obj.id)."""
        if isinstance(node, ast.Attribute):
            attr_name = node.attr

            # Common field name patterns
            if attr_name in ["id", "pk", "count"]:
                return {"type": "integer"}
            if attr_name in ["name", "title", "description", "slug"]:
                return {"type": "string"}
            if attr_name in ["is_active", "is_published", "enabled"]:
                return {"type": "boolean"}

        return {}

    def _infer_value_type(self, node) -> dict:
        """Infer schema type from AST node."""
        if isinstance(node, ast.Constant):
            return self._python_type_to_schema(type(node.value))
        if isinstance(node, ast.Call):
            return self._analyze_method_call_return(node)
        if isinstance(node, ast.Attribute):
            return self._analyze_attribute_return(node)
        return {"type": "string"}  # Default fallback

    def _python_type_to_schema(self, python_type) -> dict:
        """Convert Python type to OpenAPI schema."""
        type_mapping = {
            int: {"type": "integer"},
            float: {"type": "number"},
            str: {"type": "string"},
            bool: {"type": "boolean"},
            list: {"type": "array", "items": {"type": "string"}},
            dict: {"type": "object"},
        }
        return type_mapping.get(python_type, {"type": "string"})


def _infer_schema_from_return_patterns(patterns: list) -> dict:
    """Infer final schema from collected return patterns."""
    if not patterns:
        return {}

    # If all patterns are the same type, use that
    if all(p.get("type") == patterns[0].get("type") for p in patterns):
        # Merge object properties if multiple object returns
        if patterns[0]["type"] == "object":
            merged_properties = {}
            for pattern in patterns:
                merged_properties.update(pattern.get("properties", {}))
            return {"type": "object", "properties": merged_properties}
        return patterns[0]

    # Mixed types - could be union, but default to string for OpenAPI compatibility
    return {"type": "string"}


def _infer_schema_from_value(value: Any) -> dict:
    """Infer schema from actual runtime value."""
    if isinstance(value, dict):
        properties = {}
        for key, val in value.items():
            properties[str(key)] = _infer_schema_from_value(val)
        return {"type": "object", "properties": properties}
    if isinstance(value, list):
        if value:
            return {"type": "array", "items": _infer_schema_from_value(value[0])}
        return {"type": "array", "items": {"type": "string"}}
    if type(value) in (int, float, str, bool):
        return {
            int: {"type": "integer"},
            float: {"type": "number"},
            str: {"type": "string"},
            bool: {"type": "boolean"},
        }[type(value)]
    return {"type": "string"}


def _get_serializer_class_from_schema_name(schema_name: str):
    """Try to get the serializer class from schema name."""
    try:
        # Search through all apps for the serializer
        for app in apps.get_app_configs():
            app_module = app.module
            try:
                # Try to import serializers module from the app
                serializers_module = __import__(
                    f"{app_module.__name__}.serializers", fromlist=[""]
                )

                # Look for serializer class matching the schema name
                for attr_name in dir(serializers_module):
                    attr = getattr(serializers_module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, serializers.Serializer)
                        and attr.__name__.replace("Serializer", "") in schema_name
                    ):
                        return attr
            except ImportError:
                continue

    except Exception:
        logger.exception("Failed to get serializer.")
    return None


def schema_to_example_json(
    operation_id: str, schema: dict, components: dict, for_response: bool = True
):
    """Recursively generate a JSON example, respecting readOnly/writeOnly based on context."""
    # Ensure schema is a dictionary
    if not isinstance(schema, dict):
        return None

    schema = _resolve_schema_reference(schema, components)
    schema = _handle_all_of_schema(schema, components, for_response)

    # Handle explicit values first
    explicit_value = _get_explicit_value(schema)
    if explicit_value is not None:
        return explicit_value

    # ENHANCED: Check if this looks like a not analyzed SerializerMethodField
    schema = _enhance_method_field_schema(operation_id, schema, components)

    return _generate_example_by_type(operation_id, schema, components, for_response)


def _enhance_method_field_schema(_operation_id, schema: dict, _components: dict) -> dict:
    """Enhance schema by analyzing SerializerMethodField types."""
    if not isinstance(schema, dict) or "properties" not in schema:
        return schema

    # Try to get serializer class from schema title or other hints
    schema_title = schema.get("title", "")
    serializer_class = _get_serializer_class_from_schema_name(schema_title)

    if not serializer_class:
        return schema

    enhanced_properties = {}
    for prop_name, prop_schema in schema["properties"].items():
        # Check if this looks like a not analyzed SerializerMethodField
        if (
            isinstance(prop_schema, dict)
            and prop_schema.get("type") == "string"
            and not prop_schema.get("enum")
            and not prop_schema.get("format")
            and not prop_schema.get("example")
        ):
            # Try to analyze the method field
            analyzed_schema = analyze_serializer_method_field_schema(
                serializer_class, prop_name
            )
            enhanced_properties[prop_name] = analyzed_schema
        else:
            enhanced_properties[prop_name] = prop_schema

    enhanced_schema = schema.copy()
    enhanced_schema["properties"] = enhanced_properties
    return enhanced_schema


def _resolve_schema_reference(schema: dict, components: dict) -> dict:
    """Resolve $ref references in schema."""
    if "$ref" not in schema:
        return schema

    ref = schema["$ref"]
    target = components.get("schemas", {}).get(ref.split("/")[-1], {})
    # Work on a copy to avoid mutating components
    resolved = dict(target) if isinstance(target, dict) else {}
    for key, value in schema.items():
        if key != "$ref":
            resolved[key] = value
    return resolved


def _handle_all_of_schema(schema: dict, components: dict, _for_response: bool) -> dict:
    """Handle allOf schema composition."""
    if "allOf" not in schema:
        return schema

    merged = {}
    for part in schema["allOf"]:
        # Resolve the part schema first
        resolved_part = _resolve_schema_reference(part, components)
        if isinstance(resolved_part, dict):
            merged.update(resolved_part)
        else:
            # If we can't resolve it, skip this part
            continue

    # Merge with the original schema properties (like readOnly)
    if merged:
        result = merged.copy()
        # Add any properties from the original schema that aren't in allOf
        for key, value in schema.items():
            if key != "allOf":
                result[key] = value
        return result

    return schema


def _get_explicit_value(schema: dict):
    """Get explicit value from schema (enum, example, or default)."""
    if not isinstance(schema, dict):
        return None

    if "enum" in schema:
        return schema["enum"][0]

    if "example" in schema:
        return schema["example"]

    if "default" in schema:
        # For array types with items schema, don't use empty default
        # Let the generator create a proper example instead
        if schema.get("type") == "array" and "items" in schema:
            return None
        return schema["default"]

    return None


def _generate_example_by_type(
    operation_id: str, schema: dict, components: dict, for_response: bool
):
    """Generate example based on schema type."""
    schema_type = schema.get("type", "object")

    if schema_type == "object":
        return _generate_object_example(operation_id, schema, components, for_response)
    if schema_type == "array":
        return _generate_array_example(operation_id, schema, components, for_response)
    return _generate_primitive_example(schema_type)


def _generate_object_example(
    operation_id: str, schema: dict, components: dict, for_response: bool
) -> dict:
    """Generate example for object type schema."""
    props = schema.get("properties", {})
    result = {}

    for prop_name, prop_schema in props.items():
        if _should_skip_property(prop_schema, for_response):
            continue
        result[prop_name] = schema_to_example_json(
            operation_id, prop_schema, components, for_response
        )

    return result


def _should_skip_property(prop_schema: dict, for_response: bool) -> bool:
    """
    Args:
        prop_schema: Property schema containing readOnly/writeOnly flags
        for_response: True for response example, False for request example

    Returns:
        True if property should be skipped, False otherwise
    """
    is_write_only = prop_schema.get("writeOnly", False)
    is_read_only = prop_schema.get("readOnly", False)

    if for_response:
        return is_write_only
    return is_read_only


def _generate_array_example(
    operation_id: str, schema: dict, components: dict, for_response: bool
) -> list:
    """Generate example for array type schema."""
    items = schema.get("items", {})
    return [schema_to_example_json(operation_id, items, components, for_response)]


def _generate_primitive_example(schema_type: str):
    """Generate example for primitive types."""
    type_examples = {"integer": 0, "number": 0.0, "boolean": True, "string": "string"}
    return type_examples.get(schema_type)


def format_schema_as_json_example(
    operation_id: str, schema_ref: str, components: dict[str, Any], for_response: bool = True
) -> str:
    """
    Format a schema as a JSON example, resolving $ref and respecting readOnly/writeOnly flags.
    """
    if not schema_ref.startswith("#/components/schemas/"):
        return f"Invalid $ref: `{schema_ref}`"

    schema_name = schema_ref.split("/")[-1]
    schema = components.get("schemas", {}).get(schema_name)

    if not schema:
        return f"**Error**: Schema `{schema_name}` not found in components."

    description = schema.get("description", "")
    example_json = schema_to_example_json(
        operation_id, schema, components, for_response=for_response
    )

    result = ""
    if description:
        result += f"{description}\n\n"

    return json.dumps(example_json, indent=2)


def _format_schema_for_display(
    operation_id: str, schema: dict, components: dict, for_response: bool = True
) -> str:
    """Format schema as a displayable string with JSON example."""
    if not schema:
        return ""

    if "$ref" in schema:
        return format_schema_as_json_example(
            operation_id, schema["$ref"], components, for_response
        )

    return schema_to_example_json(operation_id, schema, components, for_response)


def _generate_field_value(
    field_name: str,
    prop_schema: dict,
    operation_id: str,
    components: dict,
    is_response: bool = True,
) -> Any:
    """Generate a realistic value for a specific field based on its name and schema."""
    # Get field-specific generator from settings
    field_generator = get_field_generator(field_name)

    if field_generator:
        return field_generator(prop_schema)

    # Fallback to schema-based generation
    return schema_to_example_json(operation_id, prop_schema, components, is_response)


def get_field_generator(field_name: str):
    """Get appropriate generator function for a field name from settings."""
    return drf_to_mkdoc_settings.FIELD_GENERATORS.get(field_name.lower())


def _generate_examples(operation_id: str, schema: dict, components: dict) -> list:
    """Generate examples for a schema."""

    if "$ref" in schema:
        schema = _resolve_schema_reference(schema, components)

    examples = []

    # Handle object with array properties
    if schema.get("type") == "object" and "properties" in schema:
        empty_example = {}
        populated_example = {}
        has_array_default = False

        # Check for array fields with default=[]
        for _prop_name, prop_schema in schema["properties"].items():
            resolved_prop_schema = (
                _resolve_schema_reference(prop_schema, components)
                if "$ref" in prop_schema
                else prop_schema
            )
            if (
                resolved_prop_schema.get("type") == "array"
                and resolved_prop_schema.get("default") == []
            ):
                has_array_default = True
                break

        # Generate examples
        for prop_name, prop_schema in schema["properties"].items():
            resolved_prop_schema = (
                _resolve_schema_reference(prop_schema, components)
                if "$ref" in prop_schema
                else prop_schema
            )

            if (
                resolved_prop_schema.get("type") == "array"
                and resolved_prop_schema.get("default") == []
            ):
                empty_example[prop_name] = []
                items_schema = resolved_prop_schema.get("items", {})
                populated_example[prop_name] = [
                    _generate_field_value(
                        prop_name, items_schema, operation_id, components, True
                    )
                ]
            else:
                value = _generate_field_value(
                    prop_name, resolved_prop_schema, operation_id, components, True
                )
                empty_example[prop_name] = value
                populated_example[prop_name] = value

        if has_array_default:
            examples.append(empty_example)
            examples.append(populated_example)
        else:
            examples.append(empty_example)

    # Handle array field with default=[]
    elif schema.get("type") == "array" and schema.get("default") == []:
        examples.append([])
        items_schema = schema.get("items", {})
        populated_example = [
            _generate_field_value("items", items_schema, operation_id, components, True)
        ]
        examples.append(populated_example)
    else:
        example = _generate_field_value("root", schema, operation_id, components, True)
        examples.append(example)

    return examples


def _prepare_response_data(operation_id: str, responses: dict, components: dict) -> list:
    """Prepare response data for template rendering."""

    formatted_responses = []
    for status_code, response_data in responses.items():
        schema = response_data.get("content", {}).get("application/json", {}).get("schema", {})

        examples = _generate_examples(operation_id, schema, components)

        formatted_response = {
            "status_code": status_code,
            "description": response_data.get("description", ""),
            "examples": examples,
        }
        formatted_responses.append(formatted_response)
    return formatted_responses


def create_endpoint_page(
    path: str, method: str, endpoint_data: dict[str, Any], components: dict[str, Any]
) -> str:
    """Create a documentation page for a single API endpoint."""
    operation_id = endpoint_data.get("operationId", "")
    request_schema = (
        endpoint_data.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema")
    )

    # Prepare template context
    context = {
        "path": path,
        "method": method,
        "operation_id": operation_id,
        "summary": endpoint_data.get("summary", ""),
        "description": endpoint_data.get("description", ""),
        "viewset_name": extract_viewset_name_from_operation_id(operation_id),
        "path_params": [
            p for p in endpoint_data.get("parameters", []) if p.get("in") == "path"
        ],
        "request_body": endpoint_data.get("requestBody", {}),
        "request_example": _format_schema_for_display(
            operation_id, request_schema, components, False
        )
        if request_schema
        else "",
        "responses": _prepare_response_data(
            operation_id, endpoint_data.get("responses", {}), components
        ),
        "stylesheets": [
            "stylesheets/endpoints/endpoint-content.css",
            "stylesheets/endpoints/badges.css",
            "stylesheets/endpoints/base.css",
            "stylesheets/endpoints/responsive.css",
            "stylesheets/endpoints/theme-toggle.css",
            "stylesheets/endpoints/layout.css",
            "stylesheets/endpoints/sections.css",
            "stylesheets/endpoints/animations.css",
            "stylesheets/endpoints/accessibility.css",
            "stylesheets/endpoints/loading.css",
            "stylesheets/try-out/main.css",
        ],
        "scripts": [
            "javascripts/try-out/modal.js",
            "javascripts/try-out/response-modal.js",
            "javascripts/try-out/tabs.js",
            "javascripts/try-out/form-manager.js",
            "javascripts/try-out/request-executor.js",
            "javascripts/try-out/suggestions.js",
            "javascripts/try-out/main.js",
        ],
        "prefix_path": f"{drf_to_mkdoc_settings.PROJECT_NAME}/",
    }

    # Add query parameters if it's a list endpoint
    if _is_list_endpoint(method, path, operation_id):
        query_params = extract_query_parameters_from_view(operation_id)
        _add_custom_parameters(operation_id, query_params)
        for key, value in query_params.items():
            # Prevent duplicates while preserving order
            query_params[key] = list(dict.fromkeys(value))
        context["query_parameters"] = query_params

    return render_to_string("endpoints/detail/base.html", context)


def _is_list_endpoint(method: str, path: str, operation_id: str) -> bool:
    """Check if the endpoint is a list endpoint that should have query parameters."""
    return (
        method.upper() == "GET"
        and operation_id
        and ("list" in operation_id or not ("{id}" in path or "{pk}" in path))
    )


def _add_custom_parameters(operation_id: str, query_params: dict) -> None:
    """Add custom parameters to query parameters dictionary."""
    custom_parameters = get_custom_schema().get(operation_id, {}).get("parameters", [])
    for parameter in custom_parameters:
        queryparam_type = parameter["queryparam_type"]
        if queryparam_type not in query_params:
            query_params[queryparam_type] = []
        query_params[queryparam_type].append(parameter["name"])


def parse_endpoints_from_schema(paths: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Parse endpoints from OpenAPI schema and organize by app"""

    endpoints_by_app = defaultdict(list)
    django_apps = set(drf_to_mkdoc_settings.DJANGO_APPS)

    for path, methods in paths.items():
        app_name = extract_app_from_operation_id(next(iter(methods.values()))["operationId"])
        if app_name not in django_apps:
            continue

        for method, endpoint_data in methods.items():
            if method.lower() not in ["get", "post", "put", "patch", "delete"]:
                continue

            operation_id = endpoint_data.get("operationId", "")
            filename = create_safe_filename(path, method)

            endpoint_info = {
                "path": path,
                "method": method.upper(),
                "viewset": extract_viewset_name_from_operation_id(operation_id),
                "operation_id": operation_id,
                "filename": filename,
                "data": endpoint_data,
            }

            endpoints_by_app[app_name].append(endpoint_info)

    return endpoints_by_app


def generate_endpoint_files(
    endpoints_by_app: dict[str, list[dict[str, Any]]], components: dict[str, Any]
) -> int:
    """Generate individual endpoint documentation files"""
    total_endpoints = 0

    for app_name, endpoints in endpoints_by_app.items():
        for endpoint in endpoints:
            content = create_endpoint_page(
                endpoint["path"], endpoint["method"], endpoint["data"], components
            )

            file_path = (
                f"endpoints/{app_name}/{endpoint['viewset'].lower()}/{endpoint['filename']}"
            )
            write_file(file_path, content)
            total_endpoints += 1

    return total_endpoints
