import ast
import inspect
import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

from django.apps import apps
from rest_framework import serializers

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings
from drf_to_mkdoc.utils.common import (
    create_safe_filename,
    extract_app_from_operation_id,
    extract_viewset_from_operation_id,
    extract_viewset_name_from_operation_id,
    format_method_badge,
    get_custom_schema,
    write_file,
)
from drf_to_mkdoc.utils.extractors.query_parameter_extractors import (
    extract_query_parameters_from_view,
)
from drf_to_mkdoc.utils.md_generators.query_parameters_generators import (
    generate_query_parameters_md,
)

logger = logging.getLogger()


def analyze_serializer_method_field_schema(serializer_class, field_name: str) -> dict:
    """Analyze a SerializerMethodField to determine its actual return type schema."""
    method_name = f"get_{field_name}"

    # Strategy 2: Check type annotations
    schema_from_annotations = _extract_schema_from_type_hints(serializer_class, method_name)
    if schema_from_annotations:
        return schema_from_annotations

    # Strategy 3: Analyze method source code
    schema_from_source = _analyze_method_source_code(serializer_class, method_name)
    if schema_from_source:
        return schema_from_source

    # Strategy 4: Runtime analysis (sample execution)
    schema_from_runtime = _analyze_method_runtime(serializer_class, method_name)
    if schema_from_runtime:
        return schema_from_runtime

    # Fallback to string
    return {"type": "string"}


def _extract_schema_from_decorator(serializer_class, method_name: str) -> dict:
    """Extract schema from @extend_schema_field decorator if present."""
    try:
        method = getattr(serializer_class, method_name, None)
        if not method:
            return None

        # Check if method has the decorator attribute (drf-spectacular)
        if hasattr(method, "_spectacular_annotation"):
            annotation = method._spectacular_annotation
            # Handle OpenApiTypes
            if hasattr(annotation, "type"):
                return {"type": annotation.type}
            if isinstance(annotation, dict):
                return annotation

        # Check for drf-yasg decorator
        if hasattr(method, "_swagger_serializer_method"):
            swagger_info = method._swagger_serializer_method
            if hasattr(swagger_info, "many") and hasattr(swagger_info, "child"):
                return {"type": "array", "items": {"type": "object"}}

    except Exception:
        logger.exception("Failed to extract schema from decorator")
    return None


def _extract_schema_from_type_hints(serializer_class, method_name: str) -> dict:
    """Extract schema from method type annotations."""
    try:
        method = getattr(serializer_class, method_name, None)
        if not method:
            return None

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
    return None


def _analyze_method_source_code(serializer_class, method_name: str) -> dict:
    """Analyze method source code to infer return type."""
    try:
        method = getattr(serializer_class, method_name, None)
        if not method:
            return None

        source = inspect.getsource(method)
        tree = ast.parse(source)

        # Find return statements and analyze them
        return_analyzer = ReturnStatementAnalyzer()
        return_analyzer.visit(tree)

        return _infer_schema_from_return_patterns(return_analyzer.return_patterns)

    except Exception:
        logger.exception("Failed to analyze method source code")
    return None


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
            return None

        # Execute method with mock data
        result = method(mock_obj)
        return _infer_schema_from_value(result)

    except Exception:
        logger.exception("Failed to analyse method runtime")
    return None


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
        return None

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

        return None

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

        return None

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
        return None

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
        logger.exception("Failed to get serializser.")
    return None


def schema_to_example_json(schema: dict, components: dict, for_response: bool = True):
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

    # ENHANCED: Check if this looks like an unanalyzed SerializerMethodField
    schema = _enhance_method_field_schema(schema, components)

    return _generate_example_by_type(schema, components, for_response)


def _enhance_method_field_schema(schema: dict, _components: dict) -> dict:
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
        # Check if this looks like an unanalyzed SerializerMethodField
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
    if "$ref" in schema:
        ref = schema["$ref"]
        return components.get("schemas", {}).get(ref.split("/")[-1], {})
    return schema


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
    # Ensure schema is a dictionary
    if not isinstance(schema, dict):
        return None

    if "enum" in schema:
        return schema["enum"][0]
    if "example" in schema:
        return schema["example"]
    if "default" in schema:
        return schema["default"]
    return None


def _generate_example_by_type(schema: dict, components: dict, for_response: bool):
    """Generate example based on schema type."""
    schema_type = schema.get("type", "object")

    if schema_type == "object":
        return _generate_object_example(schema, components, for_response)
    if schema_type == "array":
        return _generate_array_example(schema, components, for_response)
    return _generate_primitive_example(schema_type)


def _generate_object_example(schema: dict, components: dict, for_response: bool) -> dict:
    """Generate example for object type schema."""
    props = schema.get("properties", {})
    result = {}

    for prop_name, prop_schema in props.items():
        if _should_skip_property(prop_schema, for_response):
            continue
        result[prop_name] = schema_to_example_json(prop_schema, components, for_response)

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


def _generate_array_example(schema: dict, components: dict, for_response: bool) -> list:
    """Generate example for array type schema."""
    items = schema.get("items", {})
    return [schema_to_example_json(items, components, for_response)]


def _generate_primitive_example(schema_type: str):
    """Generate example for primitive types."""
    type_examples = {"integer": 0, "number": 0.0, "boolean": True, "string": "string"}
    return type_examples.get(schema_type)


def format_schema_as_json_example(
    schema_ref: str, components: dict[str, Any], for_response: bool = True
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
    example_json = schema_to_example_json(schema, components, for_response=for_response)

    result = ""
    if description:
        result += f"{description}\n\n"

    result += "```json\n"
    result += json.dumps(example_json, indent=2)
    result += "\n```\n"

    return result


def create_endpoint_page(
    path: str, method: str, endpoint_data: dict[str, Any], components: dict[str, Any]
) -> str:
    """Create a documentation page for a single API endpoint."""
    operation_id = endpoint_data.get("operationId", "")
    summary = endpoint_data.get("summary", "")
    description = endpoint_data.get("description", "")
    parameters = endpoint_data.get("parameters", [])
    request_body = endpoint_data.get("requestBody", {})
    responses = endpoint_data.get("responses", {})

    content = _create_endpoint_header(path, method, operation_id, summary, description)
    content += _add_path_parameters(parameters)
    content += _add_query_parameters(method, path, operation_id)
    content += _add_request_body(request_body, components)
    content += _add_responses(responses, components)

    return content


def _create_endpoint_header(
    path: str, method: str, operation_id: str, summary: str, description: str
) -> str:
    """Create the header section of the endpoint documentation."""
    content = f"# {method.upper()} {path}\n\n"
    content += f"{format_method_badge(method)} `{path}`\n\n"
    content += f"**View class:** {extract_viewset_name_from_operation_id(operation_id)}\n\n"

    if summary:
        content += f"## Overview\n\n{summary}\n\n"
    if operation_id:
        content += f"**Operation ID:** `{operation_id}`\n\n"
    if description:
        content += f"{description}\n\n"

    return content


def _add_path_parameters(parameters: list[dict]) -> str:
    """Add path parameters section to the documentation."""
    path_params = [p for p in parameters if p.get("in") == "path"]
    if not path_params:
        return ""

    content = "## Path Parameters\n\n"
    content += "| Name | Type | Required | Description |\n"
    content += "|------|------|----------|-------------|\n"

    for param in path_params:
        name = param.get("name", "")
        param_type = param.get("schema", {}).get("type", "string")
        required = "Yes" if param.get("required", False) else "No"
        desc = param.get("description", "")
        content += f"| `{name}` | `{param_type}` | {required} | {desc} |\n"

    content += "\n"
    return content


def _add_query_parameters(method: str, path: str, operation_id: str) -> str:
    """Add query parameters section for list endpoints."""
    is_list_endpoint = _is_list_endpoint(method, path, operation_id)
    if not is_list_endpoint:
        return ""

    query_params = extract_query_parameters_from_view(operation_id)
    _add_custom_parameters(operation_id, query_params)

    query_params_content = generate_query_parameters_md(query_params)
    if query_params_content and not query_params_content.startswith("**Error:**"):
        return "## Query Parameters\n\n" + query_params_content

    return ""


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


def _add_request_body(request_body: dict, components: dict[str, Any]) -> str:
    """Add request body section to the documentation."""
    if not request_body:
        return ""

    content = "## Request Body\n\n"
    req_schema = request_body.get("content", {}).get("application/json", {}).get("schema")

    if req_schema and "$ref" in req_schema:
        content += (
            format_schema_as_json_example(req_schema["$ref"], components, for_response=False)
            + "\n"
        )

    return content


def _add_responses(responses: dict, components: dict[str, Any]) -> str:
    """Add responses section to the documentation."""
    if not responses:
        return ""

    content = "## Responses\n\n"
    for status_code, response_data in responses.items():
        content += _format_single_response(status_code, response_data, components)

    return content


def _format_single_response(
    status_code: str, response_data: dict, components: dict[str, Any]
) -> str:
    """Format a single response entry."""
    content = f"### {status_code}\n\n"

    if desc := response_data.get("description", ""):
        content += f"{desc}\n\n"

    resp_schema = response_data.get("content", {}).get("application/json", {}).get("schema", {})

    content += _format_response_schema(resp_schema, components)
    return content


def _format_response_schema(resp_schema: dict, components: dict[str, Any]) -> str:
    """Format the response schema as JSON example."""
    if "$ref" in resp_schema:
        return (
            format_schema_as_json_example(resp_schema["$ref"], components, for_response=True)
            + "\n"
        )
    if resp_schema.get("type") == "array" and "$ref" in resp_schema.get("items", {}):
        item_ref = resp_schema["items"]["$ref"]
        return format_schema_as_json_example(item_ref, components, for_response=True) + "\n"
    content = "```json\n"
    content += json.dumps(schema_to_example_json(resp_schema, components), indent=2)
    content += "\n```\n"
    return content


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


class EndpointsIndexGenerator:
    def __init__(self, active_filters: list[str] | None = None):
        self.active_filters = set(
            active_filters
            or [
                "method",
                "path",
                "app",
                "models",
                "auth",
                "roles",
                "content_type",
                "params",
                "schema",
                "pagination",
                "ordering",
                "search",
                "tags",
            ]
        )

    def create_endpoint_card(
        self, endpoint: dict[str, Any], app_name: str, viewset_name: str
    ) -> str:
        method = endpoint["method"]
        path = endpoint["path"]
        filename = endpoint["filename"]
        view_class = extract_viewset_from_operation_id(endpoint["operation_id"])

        link_url = f"{app_name}/{viewset_name.lower()}/{filename}".replace(".md", "/index.html")
        data_attrs = f"""
            data-method="{method.lower()}"
            data-path="{path.lower()}"
            data-app="{app_name.lower()}"
            data-auth="{str(endpoint.get("auth_required", False)).lower()}"
            data-pagination="{str(endpoint.get("pagination_support", False)).lower()}"
            data-search="{str(bool(getattr(view_class, "search_fields", []))).lower()}"
            data-ordering="{str(endpoint.get("ordering_support", False)).lower()}"
            data-models="{" ".join(endpoint.get("related_models", [])).lower()}"
            data-roles="{" ".join(endpoint.get("permission_roles", [])).lower()}"
            data-content-type="{endpoint.get("content_type", "").lower()}"
            data-tags="{" ".join(endpoint.get("tags", [])).lower()}"
            data-schema="{" ".join(endpoint.get("schema_fields", [])).lower()}"
            data-params="{" ".join(endpoint.get("query_parameters", [])).lower()}"
        """.strip()

        return f"""
    <a href="{link_url}" class="endpoint-card" {data_attrs}>
        <span class="method-badge method-{method.lower()}">{method}</span>
        <span class="endpoint-path">{path}</span>
    </a>
    """

    def create_filter_section(self) -> str:
        filter_fields = {
            "method": """<div class="filter-group">
                <label class="filter-label">HTTP Method</label>
                <select id="filter-method" class="filter-select">
                    <option value="">All</option>
                    <option value="get">GET</option>
                    <option value="post">POST</option>
                    <option value="put">PUT</option>
                    <option value="patch">PATCH</option>
                    <option value="delete">DELETE</option>
                </select>
            </div>""",
            "path": """<div class="filter-group">
                <label class="filter-label">Endpoint Path</label>
                <input type="text" id="filter-path" class="filter-input"
                placeholder="Search path...">
            </div>""",
            "app": """<div class="filter-group">
                <label class="filter-label">Django App</label>
                <select id="filter-app" class="filter-select">
                    <option value="">All</option>
                    <!-- Dynamically filled -->
                </select>
            </div>""",
            "models": """<div class="filter-group">
                <label class="filter-label">Related Models</label>
                <input type="text" id="filter-models" class="filter-input">
            </div>""",
            "auth": """<div class="filter-group">
                <label class="filter-label">Authentication Required</label>
                <select id="filter-auth" class="filter-select">
                    <option value="">All</option>
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                </select>
            </div>""",
            "roles": """<div class="filter-group">
                <label class="filter-label">Permission Roles</label>
                <input type="text" id="filter-roles" class="filter-input">
            </div>""",
            "content_type": """<div class="filter-group">
                <label class="filter-label">Content Type</label>
                <input type="text" id="filter-content-type" class="filter-input">
            </div>""",
            "params": """<div class="filter-group">
                <label class="filter-label">Query Parameters</label>
                <input type="text" id="filter-params" class="filter-input">
            </div>""",
            "schema": """<div class="filter-group">
                <label class="filter-label">Schema Fields</label>
                <input type="text" id="filter-schema" class="filter-input">
            </div>""",
            "pagination": """<div class="filter-group">
                <label class="filter-label">Pagination Support</label>
                <select id="filter-pagination" class="filter-select">
                    <option value="">All</option>
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                </select>
            </div>""",
            "ordering": """<div class="filter-group">
                <label class="filter-label">Ordering Support</label>
                <select id="filter-ordering" class="filter-select">
                    <option value="">All</option>
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                </select>
            </div>""",
            "search": """<div class="filter-group">
                <label class="filter-label">Search Support</label>
                <select id="filter-search" class="filter-select">
                    <option value="">All</option>
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                </select>
            </div>""",
            "tags": """<div class="filter-group">
                <label class="filter-label">Tags</label>
                <input type="text" id="filter-tags" class="filter-input">
            </div>""",
        }

        fields_html = "\n".join(
            [html for key, html in filter_fields.items() if (key in self.active_filters)]
        )

        return f"""
        <div class="filter-sidebar collapsed" id="filterSidebar">
            <h3 class="filter-title">🔍 Filters</h3>
            <div class="filter-grid">
                {fields_html}
            </div>

            <div class="filter-actions">
                <button class="filter-apply" onclick="applyFilters()">Apply</button>
                <button class="filter-clear" onclick="clearFilters()">Clear</button>
            </div>

            <div class="filter-results">Showing 0 endpoints</div>
        </div>
        """

    def create_endpoints_index(
        self, endpoints_by_app: dict[str, list[dict[str, Any]]], docs_dir: Path
    ) -> None:
        content = """# API Endpoints

<!-- inject CSS and JS directly -->
<link rel="stylesheet" href="../stylesheets/endpoints/variables.css">
<link rel="stylesheet" href="../stylesheets/endpoints/base.css">
<link rel="stylesheet" href="../stylesheets/endpoints/theme-toggle.css">
<link rel="stylesheet" href="../stylesheets/endpoints/filter-section.css">
<link rel="stylesheet" href="../stylesheets/endpoints/layout.css">
<link rel="stylesheet" href="../stylesheets/endpoints/endpoints-grid.css">
<link rel="stylesheet" href="../stylesheets/endpoints/badges.css">
<link rel="stylesheet" href="../stylesheets/endpoints/endpoint-content.css">
<link rel="stylesheet" href="../stylesheets/endpoints/tags.css">
<link rel="stylesheet" href="../stylesheets/endpoints/sections.css">
<link rel="stylesheet" href="../stylesheets/endpoints/stats.css">
<link rel="stylesheet" href="../stylesheets/endpoints/loading.css">
<link rel="stylesheet" href="../stylesheets/endpoints/animations.css">
<link rel="stylesheet" href="../stylesheets/endpoints/responsive.css">
<link rel="stylesheet" href="../stylesheets/endpoints/accessibility.css">
<link rel="stylesheet" href="../stylesheets/endpoints/fixes.css">
<script src="../javascripts/endpoints-filter.js" defer></script>

<div class="main-content">
"""
        content += self.create_filter_section()

        for app_name, endpoints in endpoints_by_app.items():
            content += f'<h2>{app_name.title()}</h2>\n<div class="endpoints-grid">\n'
            for endpoint in endpoints:
                viewset = endpoint["viewset"]
                content += self.create_endpoint_card(endpoint, app_name, viewset)
            content += "</div>\n"

        content += "</div>\n"
        output_path = docs_dir / "endpoints" / "index.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with Path(output_path).open("w", encoding="utf-8") as f:
            f.write(content)


def create_endpoints_index(
    endpoints_by_app: dict[str, list[dict[str, Any]]], docs_dir: Path
) -> None:
    generator = EndpointsIndexGenerator(
        active_filters=[
            "method",
            "path",
            "app",
            "search",
        ]
    )
    generator.create_endpoints_index(endpoints_by_app, docs_dir)
