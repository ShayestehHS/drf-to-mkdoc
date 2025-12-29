import ast
import inspect
import json
import logging
import re
import traceback
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
from drf_to_mkdoc.utils.commons.auth_utils import get_auth_config
from drf_to_mkdoc.utils.commons.schema_utils import (
    get_custom_schema,
    get_permission_description,
    is_endpoint_secure,
)
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


def _format_schema_for_swagger_display(
    schema: dict, components: dict, indent: int = 0, prefix: str = ""
) -> str:
    """Format schema in Swagger-style display format."""
    if not schema:
        return ""
    
    # Check for $ref before resolving to preserve reference name
    has_ref = "$ref" in schema
    ref_name = None
    if has_ref:
        ref_name = schema["$ref"].split("/")[-1]
    
    schema = _resolve_schema_reference(schema, components)
    schema = _handle_all_of_schema(schema, components, True)
    
    lines = []
    indent_str = "  " * indent
    
    schema_type = schema.get("type", "object")
    title = schema.get("title", "")
    read_only = schema.get("readOnly", False)
    
    # Format field name with prefix
    field_display = prefix if prefix else "root"
    
    # Build type display
    type_display = schema_type
    is_object_type = False
    has_properties = "properties" in schema and schema["properties"]
    
    if schema_type == "array":
        items = schema.get("items", {})
        if "$ref" in items:
            ref_name = items["$ref"].split("/")[-1]
            type_display = f"array[{ref_name}]"
        elif "type" in items:
            items_type = items.get("type", "string")
            if items_type == "object":
                items_title = items.get("title", "object")
                type_display = f"array[{items_title}]"
            else:
                type_display = f"array[{items_type}]"
    elif schema_type == "object":
        if has_ref and ref_name:
            # Use the reference name
            type_display = ref_name
            is_object_type = True
        else:
            schema_title = schema.get("title", "")
            if schema_title and schema_title != "object":
                type_display = schema_title
                is_object_type = True
            elif has_properties:
                # Inline object with properties
                type_display = "object"
                is_object_type = True
    
    # Build the main line
    if is_object_type and has_properties:
        # For object types with properties, add opening brace
        main_line = f"{field_display}\t{type_display}{{"
    else:
        main_line = f"{field_display}\t{type_display}"
    
    if title:
        main_line += f"\n  title: {title}"
    if read_only:
        main_line += "\n  readOnly: true"
    
    # Add constraints
    if "minLength" in schema:
        main_line += f"\n  minLength: {schema['minLength']}"
    if "maxLength" in schema:
        main_line += f"\n  maxLength: {schema['maxLength']}"
    if "minimum" in schema:
        main_line += f"\n  minimum: {schema['minimum']}"
    if "maximum" in schema:
        main_line += f"\n  maximum: {schema['maximum']}"
    if "pattern" in schema:
        main_line += f"\n  pattern: {schema['pattern']}"
    if "enum" in schema:
        main_line += f"\n  Enum:\n    Array [ {len(schema['enum'])} ]"
    
    lines.append(indent_str + main_line)
    
    # Handle object properties
    if schema_type == "object" and has_properties:
        for prop_name, prop_schema in schema["properties"].items():
            # Skip writeOnly fields for responses
            if prop_schema.get("writeOnly", False):
                continue
            
            prop_lines = _format_schema_for_swagger_display(
                prop_schema, components, indent + 1, prop_name
            )
            if prop_lines:
                lines.append(prop_lines)
        
        # Add closing brace for object types
        if is_object_type:
            lines.append(indent_str + "}")
    
    # Handle array items if it's an object
    if schema_type == "array":
        items = schema.get("items", {})
        if items.get("type") == "object" or "$ref" in items:
            items_lines = _format_schema_for_swagger_display(
                items, components, indent + 1, "items"
            )
            if items_lines:
                lines.append(items_lines)
    
    return "\n".join(lines)


def _generate_typescript_type(
    schema: dict, components: dict, indent: int = 0, interface_name: str = "Response"
) -> str:
    """Generate TypeScript type definition from schema."""
    if not schema:
        return ""
    
    schema = _resolve_schema_reference(schema, components)
    schema = _handle_all_of_schema(schema, components, True)
    
    schema_type = schema.get("type", "object")
    indent_str = "  " * indent
    
    if schema_type == "object":
        properties = schema.get("properties", {})
        if not properties:
            return f"{indent_str}interface {interface_name} {{\n{indent_str}}}"
        
        lines = [f"{indent_str}interface {interface_name} {{"]
        required = schema.get("required", [])
        for prop_name, prop_schema in properties.items():
            # Skip writeOnly fields for responses
            if prop_schema.get("writeOnly", False):
                continue
            
            prop_ts_type = _get_typescript_type(prop_schema, components, None, indent + 1)
            optional = "" if prop_name in required else "?"
            lines.append(f"{indent_str}  {prop_name}{optional}: {prop_ts_type};")
        
        lines.append(f"{indent_str}}}")
        return "\n".join(lines)
    elif schema_type == "array":
        items = schema.get("items", {})
        items_ts_type = _get_typescript_type(items, components, None, indent)
        return f"{indent_str}type {interface_name} = {items_ts_type}[];"
    else:
        ts_type = _get_typescript_type(schema, components, None, indent)
        return f"{indent_str}type {interface_name} = {ts_type};"


def _get_typescript_type(schema: dict, components: dict, _components_cache: dict | None = None, _indent: int = 0) -> str:
    """Get TypeScript type string for a schema."""
    if not isinstance(schema, dict):
        return "any"
    
    schema = _resolve_schema_reference(schema, components)
    schema = _handle_all_of_schema(schema, components, True)
    
    schema_type = schema.get("type", "any")
    
    if schema_type == "string":
        return "string"
    elif schema_type == "integer" or schema_type == "number":
        return "number"
    elif schema_type == "boolean":
        return "boolean"
    elif schema_type == "array":
        items = schema.get("items", {})
        items_type = _get_typescript_type(items, components, _components_cache, _indent)
        return f"{items_type}[]"
    elif schema_type == "object":
        # Inline object type
        properties = schema.get("properties", {})
        if not properties:
            return "Record<string, any>"
        
        prop_lines = []
        required = schema.get("required", [])
        indent_str = "  " * (_indent + 1)
        for prop_name, prop_schema in properties.items():
            if prop_schema.get("writeOnly", False):
                continue
            prop_ts_type = _get_typescript_type(prop_schema, components, _components_cache, _indent + 1)
            optional = "" if prop_name in required else "?"
            prop_lines.append(f"{indent_str}{prop_name}{optional}: {prop_ts_type};")
        
        if prop_lines:
            outer_indent = "  " * _indent
            return "{\n" + "\n".join(prop_lines) + f"\n{outer_indent}}}"
        return "Record<string, any>"
    else:
        return "any"


def _prepare_response_data(operation_id: str, responses: dict, components: dict) -> list:
    """Prepare response data for template rendering."""

    formatted_responses = []
    for status_code, response_data in responses.items():
        # Check if response has no content section (already a 204-like response)
        content = response_data.get("content", {})
        if not content:
            # No content means 204 No Content
            formatted_response = {
                "status_code": "204" if status_code == "200" else status_code,
                "description": response_data.get("description", "") or 
                              "The request was successful. No content is returned in the response body.",
                "examples": [],
                "schema": None,
            }
            formatted_responses.append(formatted_response)
            continue
        
        schema = content.get("application/json", {}).get("schema", {})
        
        # Extract examples from OpenAPI schema (like request body examples)
        extracted_examples = _extract_response_examples(operation_id, response_data, components)
        
        # Build tree structure for schema
        schema_tree = None
        if schema:
            # Resolve schema to get root-level required fields
            resolved_schema = _resolve_schema_reference(schema, components)
            resolved_schema = _handle_all_of_schema(resolved_schema, components, True)
            required_fields = set(resolved_schema.get("required", []))
            schema_tree = _build_response_schema_tree(resolved_schema, components, required_fields)
        
        # Prepare schema display for each example
        formatted_examples = []
        schema_display = _format_schema_for_swagger_display(schema, components) if schema else ""
        
        # If we have extracted examples from the schema, use them
        if extracted_examples:
            seen_json = set()
            for example_obj in extracted_examples:
                example_value = example_obj.get("value")
                json_str = json.dumps(example_value, indent=2) if example_value is not None else "null"
                # Skip if we've already seen this exact JSON
                if json_str not in seen_json:
                    seen_json.add(json_str)
                    formatted_examples.append({
                        "summary": example_obj.get("summary", "Example"),
                        "description": example_obj.get("description", ""),
                        "value": example_value,
                        "json": json_str,
                        "schema_display": schema_display,
                        "schema_tree": schema_tree,
                    })
        else:
            # Fallback: Generate examples from schema if no examples field exists
            generated_examples = _generate_examples(operation_id, schema, components) if schema else []
            
            # Generate JSON example from schema if no generated examples exist
            schema_json_example = None
            if schema and not generated_examples:
                try:
                    schema_json_example = schema_to_example_json(operation_id, schema, components, for_response=True)
                    if schema_json_example is not None:
                        schema_json_example = json.dumps(schema_json_example, indent=2)
                except Exception as e:
                    # If generation fails, log error with full traceback and fall back to null
                    logger.warning(
                        f"Failed to generate JSON example for operation {operation_id}: {e}\n"
                        f"Traceback: {traceback.format_exc()}"
                    )
                    schema_json_example = "null"
            
            # If we have generated examples, add them with schema (deduplicate by JSON string)
            if generated_examples:
                seen_json = set()
                for example in generated_examples:
                    json_str = json.dumps(example, indent=2) if example is not None else "null"
                    # Skip if we've already seen this exact JSON
                    if json_str not in seen_json:
                        seen_json.add(json_str)
                        formatted_examples.append({
                            "summary": "Example",
                            "description": "",
                            "value": example,
                            "json": json_str,
                            "schema_display": schema_display,
                            "schema_tree": schema_tree,
                        })
            # If no examples but we have a schema, create an example with JSON generated from schema
            elif schema:
                json_str = schema_json_example if schema_json_example else "null"
                formatted_examples.append({
                    "summary": "Example",
                    "description": "",
                    "value": schema_json_example if schema_json_example and schema_json_example != "null" else None,
                    "json": json_str,
                    "schema_display": schema_display,
                    "schema_tree": schema_tree,
                })
        
        formatted_response = {
            "status_code": status_code,
            "description": response_data.get("description", ""),
            "examples": formatted_examples,
            "schema": schema,
        }
        
        formatted_responses.append(formatted_response)
    return formatted_responses


def _extract_request_examples(
    operation_id: str, request_body: dict, components: dict
) -> list[dict[str, Any]]:
    """
    Extract all examples from requestBody.content[mediaType].examples.
    
    Returns a list of example dictionaries with keys:
    - summary: The example summary (or example key as fallback)
    - value: The example value (formatted JSON)
    - description: Optional description
    
    Falls back to generating a single example from schema if no examples field exists.
    """
    if not request_body:
        return []
    
    content = request_body.get("content", {})
    if not content:
        return []
    
    # Check for examples in application/json (most common)
    json_content = content.get("application/json", {})
    examples_field = json_content.get("examples", {})
    
    # If examples field exists and is not empty, extract all examples
    if examples_field and isinstance(examples_field, dict) and examples_field:
        extracted_examples = []
        for example_key, example_obj in examples_field.items():
            if not isinstance(example_obj, dict):
                continue
            
            # Extract value from example object
            example_value = example_obj.get("value")
            if example_value is None:
                continue
            
            # Format the value as JSON string
            try:
                formatted_value = json.dumps(example_value, indent=2)
            except (TypeError, ValueError):
                # If value can't be serialized, skip this example
                logger.warning(
                    f"Failed to serialize example '{example_key}' for operation {operation_id}"
                )
                continue
            
            extracted_examples.append({
                "summary": example_obj.get("summary", example_key),
                "value": formatted_value,
                "description": example_obj.get("description", ""),
                "key": example_key,
            })
        
        if extracted_examples:
            return extracted_examples
    
    # Fallback: Generate example from schema if no examples field exists
    schema = json_content.get("schema")
    if schema:
        example_value = _format_schema_for_display(operation_id, schema, components, False)
        if example_value:
            # If example_value is already a string (JSON), use it directly
            if isinstance(example_value, str):
                try:
                    # Try to parse and reformat to ensure it's valid JSON
                    parsed = json.loads(example_value) if not example_value.startswith("```") else None
                    if parsed is not None:
                        formatted_value = json.dumps(parsed, indent=2)
                    else:
                        # Extract JSON from markdown code block if present
                        json_match = re.search(r"```json\s*\n(.*?)\n```", example_value, re.DOTALL)
                        if json_match:
                            formatted_value = json_match.group(1).strip()
                        else:
                            formatted_value = example_value
                except (json.JSONDecodeError, TypeError):
                    formatted_value = example_value
            else:
                formatted_value = json.dumps(example_value, indent=2)
            
            return [{
                "summary": "Example",
                "value": formatted_value,
                "description": "",
                "key": "default",
            }]
    
    return []


def _extract_response_examples(
    _operation_id: str, response_data: dict, _components: dict
) -> list[dict[str, Any]]:
    """
    Extract all examples from response.content[mediaType].examples.
    
    Returns a list of example dictionaries with keys:
    - summary: The example summary (or example key as fallback)
    - value: The example value (dict/object)
    - description: Optional description
    - key: The example key
    
    Falls back to generating examples from schema if no examples field exists.
    """
    if not response_data:
        return []
    
    content = response_data.get("content", {})
    if not content:
        return []
    
    # Check for examples in application/json (most common)
    json_content = content.get("application/json", {})
    examples_field = json_content.get("examples", {})
    
    # If examples field exists and is not empty, extract all examples
    if examples_field and isinstance(examples_field, dict) and examples_field:
        extracted_examples = []
        for example_key, example_obj in examples_field.items():
            if not isinstance(example_obj, dict):
                continue
            
            # Extract value from example object
            example_value = example_obj.get("value")
            if example_value is None:
                continue
            
            extracted_examples.append({
                "summary": example_obj.get("summary", example_key),
                "value": example_value,
                "description": example_obj.get("description", ""),
                "key": example_key,
            })
        
        if extracted_examples:
            return extracted_examples
    
    # Fallback: Return empty list - let _prepare_response_data generate from schema
    return []


def _extract_permissions_data(operation_id: str, endpoint_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract permissions data from endpoint for display in template.

    Args:
        operation_id: Operation ID of the endpoint
        endpoint_data: Endpoint data from OpenAPI schema

    Returns:
        List of permission dictionaries with class_path, display_name, description
    """
    permissions = []
    metadata = endpoint_data.get("x-metadata", {})
    permission_classes = metadata.get("permission_classes", [])

    if not permission_classes:
        return permissions

    # Process each permission (can be string or structured)
    for perm in permission_classes:
        if isinstance(perm, str):
            # Simple string format (backward compatibility)
            class_path = perm
            display_name = perm.rsplit(".", 1)[-1] if "." in perm else perm
        elif isinstance(perm, dict):
            # Structured format - display_name should already be calculated in _flatten_permissions
            class_path = perm.get("class_path", "")
            display_name = perm.get("display_name", class_path.rsplit(".", 1)[-1] if "." in class_path else class_path)
        else:
            continue

        if not class_path:
            continue

        # Get short description only
        descriptions = get_permission_description(class_path)
        short_description = descriptions.get("short") or ""

        permissions.append({
            "class_path": class_path,
            "display_name": display_name,
            "description": short_description,
        })

    return permissions


def _extract_validation_constraints(
    resolved_field_schema: dict[str, Any], field_type: str, components: dict[str, Any]
) -> dict[str, Any]:
    """
    Extract validation constraints from a resolved field schema.
    
    Args:
        resolved_field_schema: The resolved field schema dictionary
        field_type: The type of the field (string, integer, number, array, object)
        components: OpenAPI components dictionary for resolving references
        
    Returns:
        Dictionary containing validation constraints
    """
    validation_info = {}
    
    # Type-specific validations
    if field_type == "string":
        if "minLength" in resolved_field_schema:
            validation_info["minLength"] = resolved_field_schema["minLength"]
        if "maxLength" in resolved_field_schema:
            validation_info["maxLength"] = resolved_field_schema["maxLength"]
        if "pattern" in resolved_field_schema:
            validation_info["pattern"] = resolved_field_schema["pattern"]
        if "format" in resolved_field_schema:
            validation_info["format"] = resolved_field_schema["format"]
        if "enum" in resolved_field_schema:
            validation_info["enum"] = resolved_field_schema["enum"]
    elif field_type in ("integer", "number"):
        if "minimum" in resolved_field_schema:
            validation_info["minimum"] = resolved_field_schema["minimum"]
        if "maximum" in resolved_field_schema:
            validation_info["maximum"] = resolved_field_schema["maximum"]
        if "exclusiveMinimum" in resolved_field_schema:
            validation_info["exclusiveMinimum"] = resolved_field_schema["exclusiveMinimum"]
        if "exclusiveMaximum" in resolved_field_schema:
            validation_info["exclusiveMaximum"] = resolved_field_schema["exclusiveMaximum"]
        if "enum" in resolved_field_schema:
            validation_info["enum"] = resolved_field_schema["enum"]
    elif field_type == "array":
        validation_info["array_type"] = "array"
        items_schema = resolved_field_schema.get("items", {})
        if "$ref" in items_schema:
            items_schema = _resolve_schema_reference(items_schema, components)
        validation_info["items_type"] = items_schema.get("type", "string")
        if "minItems" in resolved_field_schema:
            validation_info["minItems"] = resolved_field_schema["minItems"]
        if "maxItems" in resolved_field_schema:
            validation_info["maxItems"] = resolved_field_schema["maxItems"]
    elif field_type == "object":
        validation_info["object_type"] = "object"
        if "properties" in resolved_field_schema:
            validation_info["has_properties"] = True
    
    # Handle enum for any type
    if "enum" in resolved_field_schema and "enum" not in validation_info:
        validation_info["enum"] = resolved_field_schema["enum"]
    
    return validation_info


def _extract_request_body_fields_with_validation(
    _operation_id: str, request_body: dict[str, Any], components: dict[str, Any]
) -> list[dict[str, Any]]:
    """
    Extract request body fields with validation constraints for display.
    
    Args:
        operation_id: Operation ID of the endpoint
        request_body: Request body from OpenAPI schema
        components: OpenAPI components dictionary
        
    Returns:
        List of field dictionaries with validation information
    """
    if not request_body:
        return []
    
    content = request_body.get("content", {})
    if not content:
        return []
    
    schema = content.get("application/json", {}).get("schema")
    if not schema:
        return []
    
    # Resolve schema reference if needed
    schema = _resolve_schema_reference(schema, components)
    schema = _handle_all_of_schema(schema, components, False)
    
    # Get required fields list
    required_fields = set(schema.get("required", []))
    
    # Extract properties
    properties = schema.get("properties", {})
    if not properties:
        return []
    
    fields = []
    for field_name, field_schema in properties.items():
        # Note: writeOnly fields SHOULD be included in requests per OpenAPI spec
        # (they're only excluded from responses). We don't skip them here.
        # Skip readOnly fields for request body (they shouldn't be in request)
        if field_schema.get("readOnly", False):
            continue
        
        # Resolve field schema reference if needed
        resolved_field_schema = _resolve_schema_reference(field_schema, components)
        resolved_field_schema = _handle_all_of_schema(resolved_field_schema, components, False)
        
        # Extract validation constraints
        field_type = resolved_field_schema.get("type", "string")
        validation_info = {
            "name": field_name,
            "type": field_type,
            "required": field_name in required_fields,
            "description": resolved_field_schema.get("description", ""),
            "default": resolved_field_schema.get("default"),
            "example": resolved_field_schema.get("example"),
        }
        
        # Extract type-specific validation constraints
        validation_info.update(_extract_validation_constraints(resolved_field_schema, field_type, components))
        
        fields.append(validation_info)
    
    return fields


def _extract_response_schema_fields(
    responses: dict[str, Any], components: dict[str, Any]
) -> list[dict[str, Any]]:
    """
    Extract response schema fields with validation constraints for display.
    
    Args:
        responses: Responses dictionary from OpenAPI schema
        components: OpenAPI components dictionary
        
    Returns:
        List of field dictionaries with validation information from the first response with schema
    """
    if not responses:
        return []
    
    # Get the first response with a schema (usually 200)
    for _status_code, response_data in responses.items():
        content = response_data.get("content", {})
        if not content:
            continue
        
        schema = content.get("application/json", {}).get("schema")
        if not schema:
            continue
        
        # Resolve schema reference if needed
        schema = _resolve_schema_reference(schema, components)
        schema = _handle_all_of_schema(schema, components, True)
        
        # Get required fields list
        required_fields = set(schema.get("required", []))
        
        # Extract properties
        properties = schema.get("properties", {})
        if not properties:
            return []
        
        fields = []
        for field_name, field_schema in properties.items():
            # Skip writeOnly fields for responses (they shouldn't be in response)
            if field_schema.get("writeOnly", False):
                continue
            
            # Resolve field schema reference if needed
            resolved_field_schema = _resolve_schema_reference(field_schema, components)
            resolved_field_schema = _handle_all_of_schema(resolved_field_schema, components, True)
            
            # Extract validation constraints
            field_type = resolved_field_schema.get("type", "string")
            validation_info = {
                "name": field_name,
                "type": field_type,
                "required": field_name in required_fields,
                "description": resolved_field_schema.get("description", ""),
                "readOnly": resolved_field_schema.get("readOnly", False),
                "example": resolved_field_schema.get("example"),
            }
            
            # Extract type-specific validation constraints
            validation_info.update(_extract_validation_constraints(resolved_field_schema, field_type, components))
            
            fields.append(validation_info)
        
        return fields
    
    return []


def _build_response_schema_tree(
    schema: dict[str, Any], 
    components: dict[str, Any], 
    required_fields: set[str] | None = None,
    visited_refs: set[str] | None = None,
    depth: int = 0
) -> dict[str, Any]:
    """
    Recursively build a nested tree structure from OpenAPI schema.
    
    Args:
        schema: OpenAPI schema dictionary
        components: OpenAPI components dictionary for resolving references
        required_fields: Set of required field names at current level
        visited_refs: Set of visited $ref names to prevent circular references
        depth: Current nesting depth (for preventing infinite recursion)
        
    Returns:
        Tree structure dictionary with name, type, validation rules, and children
    """
    if not schema or not isinstance(schema, dict):
        return None
    
    if visited_refs is None:
        visited_refs = set()
    if required_fields is None:
        required_fields = set()
    
    # Prevent infinite recursion
    if depth > 20:
        return None
    
    # Check for $ref before resolving to preserve reference name
    ref_name = None
    if "$ref" in schema:
        ref_path = schema["$ref"]
        ref_name = ref_path.split("/")[-1]
        # Prevent circular references
        if ref_name in visited_refs:
            return {
                "name": ref_name,
                "type": "object",
                "ref": ref_name,
                "circular": True,
                "description": f"Circular reference to {ref_name}",
            }
        visited_refs.add(ref_name)
        schema = _resolve_schema_reference(schema, components)
        schema = _handle_all_of_schema(schema, components, True)
    
    schema_type = schema.get("type", "object")
    title = schema.get("title", "")
    description = schema.get("description", "")
    read_only = schema.get("readOnly", False)
    
    # Build base node
    node = {
        "type": schema_type,
        "description": description,
        "readOnly": read_only,
        "validation": {},
    }
    
    if ref_name:
        node["ref"] = ref_name
    if title:
        node["title"] = title
    
    # Extract validation rules
    if "minLength" in schema:
        node["validation"]["minLength"] = schema["minLength"]
    if "maxLength" in schema:
        node["validation"]["maxLength"] = schema["maxLength"]
    if "pattern" in schema:
        node["validation"]["pattern"] = schema["pattern"]
    if "minimum" in schema:
        node["validation"]["minimum"] = schema["minimum"]
    if "maximum" in schema:
        node["validation"]["maximum"] = schema["maximum"]
    if "exclusiveMinimum" in schema:
        node["validation"]["exclusiveMinimum"] = schema["exclusiveMinimum"]
    if "exclusiveMaximum" in schema:
        node["validation"]["exclusiveMaximum"] = schema["exclusiveMaximum"]
    if "minItems" in schema:
        node["validation"]["minItems"] = schema["minItems"]
    if "maxItems" in schema:
        node["validation"]["maxItems"] = schema["maxItems"]
    if "enum" in schema:
        node["validation"]["enum"] = schema["enum"]
    if "format" in schema:
        node["validation"]["format"] = schema["format"]
    if "example" in schema:
        node["example"] = schema["example"]
    
    # Handle array type
    if schema_type == "array":
        items = schema.get("items", {})
        if items:
            items_node = _build_response_schema_tree(
                items, components, set(), visited_refs.copy(), depth + 1
            )
            if items_node:
                node["items"] = items_node
                node["itemsType"] = items_node.get("type", "string")
            else:
                node["itemsType"] = "string"
        else:
            node["itemsType"] = "string"
    
    # Handle object type with properties
    elif schema_type == "object":
        properties = schema.get("properties", {})
        required_at_level = set(schema.get("required", []))
        
        if properties:
            node["children"] = []
            for prop_name, prop_schema in properties.items():
                # Skip writeOnly fields for responses
                if prop_schema.get("writeOnly", False):
                    continue
                
                child_node = _build_response_schema_tree(
                    prop_schema, 
                    components, 
                    required_at_level,
                    visited_refs.copy(),
                    depth + 1
                )
                
                if child_node:
                    child_node["name"] = prop_name
                    child_node["required"] = prop_name in required_at_level
                    node["children"].append(child_node)
    
    return node


def create_endpoint_page(
    path: str, method: str, endpoint_data: dict[str, Any], components: dict[str, Any]
) -> str:
    """Create a documentation page for a single API endpoint."""
    operation_id = endpoint_data.get("operationId", "")
    request_body = endpoint_data.get("requestBody", {})
    
    # Extract all request examples (from examples field or generate from schema)
    request_examples = _extract_request_examples(operation_id, request_body, components)
    
    # For backward compatibility, provide request_example only when request_examples is empty
    # This ensures the fallback template path works correctly
    request_schema = (
        request_body.get("content", {}).get("application/json", {}).get("schema")
    )
    if not request_examples and request_schema:
        # No examples found, use original format for backward compatibility
        request_example = _format_schema_for_display(
            operation_id, request_schema, components, False
        )
    else:
        # Either we have examples (which will be used by template) or no schema
        # Set to empty string to avoid confusion
        request_example = ""

    # Extract request body fields with validation
    request_body_fields = _extract_request_body_fields_with_validation(
        operation_id, request_body, components
    )
    
    # Extract response schema fields
    response_schema_fields = _extract_response_schema_fields(
        endpoint_data.get("responses", {}), components
    )
    
    # Build request schema tree
    request_schema_tree = None
    if request_schema:
        # Get required fields for request schema
        resolved_request_schema = _resolve_schema_reference(request_schema, components)
        resolved_request_schema = _handle_all_of_schema(resolved_request_schema, components, False)
        required_fields = set(resolved_request_schema.get("required", []))
        request_schema_tree = _build_response_schema_tree(
            request_schema, components, required_fields, set(), 0
        )
    
    # Build response schema tree (from first response with schema)
    response_schema_tree = None
    responses = endpoint_data.get("responses", {})
    for _status_code, response_data in responses.items():
        content = response_data.get("content", {})
        if not content:
            continue
        schema = content.get("application/json", {}).get("schema")
        if schema:
            # Get required fields for response schema
            resolved_response_schema = _resolve_schema_reference(schema, components)
            resolved_response_schema = _handle_all_of_schema(resolved_response_schema, components, True)
            required_fields = set(resolved_response_schema.get("required", []))
            response_schema_tree = _build_response_schema_tree(
                schema, components, required_fields, set(), 0
            )
            break
    
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
        "request_body": request_body,
        "request_body_fields": request_body_fields,
        "request_schema_fields": request_body_fields,  # Alias for schema template
        "request_schema_tree": request_schema_tree,
        "request_examples": request_examples,
        "request_example": request_example,  # Keep for backward compatibility
        "responses": _prepare_response_data(
            operation_id, endpoint_data.get("responses", {}), components
        ),
        "response_schema_fields": response_schema_fields,
        "response_schema_tree": response_schema_tree,
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
            "stylesheets/endpoints/query-parameters.css",
            "stylesheets/endpoints/response-schema-tree.css",
            "stylesheets/try-out/main.css",
        ],
        "scripts": [
            "javascripts/try-out/auth-handler.js",  # Load before form-manager (dependency)
            "javascripts/try-out/modal.js",
            "javascripts/try-out/response-modal.js",
            "javascripts/try-out/tabs.js",
            "javascripts/try-out/form-manager.js",
            "javascripts/try-out/request-executor.js",
            "javascripts/try-out/suggestions.js",
            "javascripts/try-out/main.js",
            "javascripts/query-parameters.js",
            "javascripts/response-schema-tree.js",  # Load before viewer (dependency)
            "javascripts/response-schema-viewer.js",
        ],
        "prefix_path": f"{drf_to_mkdoc_settings.PROJECT_NAME}/",
        "auth_required": is_endpoint_secure(operation_id, endpoint_data),
        "permissions": _extract_permissions_data(operation_id, endpoint_data),
        **get_auth_config(),
    }

    # Add query parameters if it's a list endpoint
    if _is_list_endpoint(method, path, operation_id):
        query_params = extract_query_parameters_from_view(operation_id)
        _add_custom_parameters(operation_id, query_params)
        # Extract query parameters from OpenAPI schema with full schema info
        _add_query_params_from_schema(endpoint_data, query_params, components)
        # Deduplicate parameters while preserving order (handle both strings and dicts)
        for key, value in query_params.items():
            query_params[key] = _deduplicate_query_params(value)
        context["query_parameters"] = query_params

    return render_to_string("endpoints/detail/base.html", context)


def _is_list_endpoint(method: str, path: str, operation_id: str) -> bool:
    """Check if the endpoint is a list endpoint that should have query parameters."""
    return (
        method.upper() == "GET"
        and operation_id
        and ("list" in operation_id or not ("{id}" in path or "{pk}" in path))
    )


def _deduplicate_query_params(params: list) -> list:
    """Deduplicate query parameters while preserving order.

    Handles both string format (legacy) and dict format (with schema info).
    Deduplicates based on parameter name.
    """
    seen_names = set()
    result = []

    for param in params:
        if isinstance(param, dict):
            param_name = param.get("name")
        elif isinstance(param, str):
            param_name = param
        else:
            # Skip invalid entries
            continue

        if param_name and param_name not in seen_names:
            seen_names.add(param_name)
            result.append(param)

    return result


def _add_custom_parameters(operation_id: str, query_params: dict) -> None:
    """Add custom parameters to query parameters dictionary."""
    custom_parameters = get_custom_schema().get(operation_id, {}).get("parameters", [])
    for parameter in custom_parameters:
        queryparam_type = parameter["queryparam_type"]
        if queryparam_type not in query_params:
            query_params[queryparam_type] = []
        query_params[queryparam_type].append(parameter["name"])


def _add_query_params_from_schema(
    endpoint_data: dict[str, Any], query_params: dict, components: dict[str, Any]
) -> None:
    """Extract query parameters from OpenAPI schema and merge with view-based extraction.

    This function extracts query parameters from the OpenAPI schema with full schema
    information (type, example, description) and merges them with the view-based
    extraction. Parameters are categorized by their queryparam_type if available,
    otherwise they're added to a generic 'query_params' category.
    """
    schema_query_params = [
        p for p in endpoint_data.get("parameters", []) if p.get("in") == "query"
    ]

    if not schema_query_params:
        return

    # Resolve schema references and extract type/example info
    for param in schema_query_params:
        param_name = param.get("name")
        if not param_name:
            continue

        # Resolve schema reference if needed
        schema = param.get("schema", {})
        if "$ref" in schema:
            schema = _resolve_schema_reference(schema, components)
        elif isinstance(schema, dict) and "$ref" in schema.get("items", {}):
            # Handle array items with $ref
            items_ref = schema.get("items", {}).get("$ref")
            if items_ref:
                schema["items"] = _resolve_schema_reference({"$ref": items_ref}, components)

        # Extract type, example, and description
        param_type = schema.get("type", "string")
        param_example = schema.get("example") or schema.get("default")
        param_description = param.get("description", "")
        param_required = param.get("required", False)

        # Generate example if not provided
        if param_example is None:
            param_example = _generate_query_param_example(schema, components)

        # Create parameter object with schema info
        param_obj = {
            "name": param_name,
            "type": param_type,
            "example": param_example,
            "description": param_description,
            "required": param_required,
            "schema": schema,
        }

        # Determine queryparam_type from custom schema or infer from name
        queryparam_type = param.get("queryparam_type")
        if not queryparam_type:
            # Try to infer from parameter name patterns
            name_lower = param_name.lower()
            if "search" in name_lower or name_lower == "q":
                queryparam_type = "search_fields"
            elif "order" in name_lower or "sort" in name_lower:
                queryparam_type = "ordering_fields"
            elif "page" in name_lower or "limit" in name_lower or "offset" in name_lower:
                queryparam_type = "pagination_fields"
            else:
                queryparam_type = "filter_fields"

        # Add to appropriate category
        if queryparam_type not in query_params:
            query_params[queryparam_type] = []

        # Check if parameter already exists (by name) and update it, or add new
        existing_param = None
        for existing in query_params[queryparam_type]:
            if isinstance(existing, dict) and existing.get("name") == param_name:
                existing_param = existing
                break
            elif isinstance(existing, str) and existing == param_name:
                # Replace string with full object
                idx = query_params[queryparam_type].index(existing)
                query_params[queryparam_type][idx] = param_obj
                existing_param = param_obj
                break

        if existing_param is None:
            query_params[queryparam_type].append(param_obj)
        elif existing_param is not param_obj:
            # Update existing parameter with schema info (only if it's a pre-existing dict, not the one we just created)
            if isinstance(existing_param, dict):
                existing_param.update(param_obj)


def _generate_query_param_example(schema: dict, components: dict[str, Any]) -> Any:
    """Generate an example value for a query parameter based on its schema."""
    if not isinstance(schema, dict):
        return None

    # Resolve schema reference if needed
    if "$ref" in schema:
        schema = _resolve_schema_reference(schema, components)

    param_type = schema.get("type")

    # Handle explicit values first
    enum_values = schema.get("enum")
    if enum_values:
        return enum_values[0]

    if "example" in schema:
        return schema["example"]

    if "default" in schema:
        return schema["default"]

    # Generate based on type
    if param_type == "integer":
        return 1
    elif param_type == "number":
        return 1.0
    elif param_type == "boolean":
        return True
    elif param_type == "array":
        items_schema = schema.get("items", {})
        if "$ref" in items_schema:
            items_schema = _resolve_schema_reference(items_schema, components)
        item_type = items_schema.get("type", "string")
        if item_type == "string":
            return ["example"]
        elif item_type == "integer":
            return [1]
        return []
    elif param_type == "object":
        return {}

    # Default to string example
    return "example"


def _extract_all_permission_class_paths(endpoint_data: dict[str, Any]) -> list[str]:
    """
    Extract ALL permission class paths from endpoint data for filtering.
    This includes all permissions, even those without descriptions.

    Args:
        endpoint_data: Endpoint data from OpenAPI schema

    Returns:
        List of permission class paths
    """
    permission_class_paths = []
    metadata = endpoint_data.get("x-metadata", {})
    permission_classes = metadata.get("permission_classes", [])

    if not permission_classes:
        return permission_class_paths

    # Process each permission (can be string or structured)
    for perm in permission_classes:
        if isinstance(perm, str):
            # Simple string format (backward compatibility)
            permission_class_paths.append(perm)
        elif isinstance(perm, dict):
            # Structured format
            class_path = perm.get("class_path", "")
            if class_path:
                permission_class_paths.append(class_path)

    return permission_class_paths


def _extract_permissions_with_display_names(endpoint_data: dict[str, Any]) -> list[dict[str, str]]:
    """
    Extract permission class paths with their display names for filtering.
    Display names should already be calculated in _flatten_permissions.

    Args:
        endpoint_data: Endpoint data from OpenAPI schema

    Returns:
        List of dictionaries with 'class_path' and 'display_name' keys
    """
    permissions = []
    metadata = endpoint_data.get("x-metadata", {})
    permission_classes = metadata.get("permission_classes", [])

    if not permission_classes:
        return permissions

    # Process each permission (can be string or structured)
    for perm in permission_classes:
        if isinstance(perm, str):
            # Simple string format (backward compatibility)
            class_path = perm
            display_name = perm.rsplit(".", 1)[-1] if "." in perm else perm
        elif isinstance(perm, dict):
            # Structured format - display_name should already be calculated in _flatten_permissions
            class_path = perm.get("class_path", "")
            display_name = perm.get("display_name", class_path.rsplit(".", 1)[-1] if "." in class_path else class_path)
        else:
            continue

        if not class_path:
            continue

        permissions.append({
            "class_path": class_path,
            "display_name": display_name,
        })

    return permissions


def parse_endpoints_from_schema(paths: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Parse endpoints from OpenAPI schema and organize by app"""

    endpoints_by_app = defaultdict(list)
    django_apps = set(drf_to_mkdoc_settings.DJANGO_APPS)

    for path, methods in paths.items():
        app_name = extract_app_from_operation_id(next(iter(methods.values()))["operationId"])
        if django_apps and app_name not in django_apps:
            continue

        for method, endpoint_data in methods.items():
            if method.lower() not in ["get", "post", "put", "patch", "delete"]:
                continue

            operation_id = endpoint_data.get("operationId", "")
            filename = create_safe_filename(path, method)

            # Extract ALL permissions for filtering (including those without descriptions)
            permission_class_paths = _extract_all_permission_class_paths(endpoint_data)
            # Also extract permissions with display names for JavaScript
            permissions_with_names = _extract_permissions_with_display_names(endpoint_data)

            endpoint_info = {
                "path": path,
                "method": method.upper(),
                "viewset": extract_viewset_name_from_operation_id(operation_id),
                "operation_id": operation_id,
                "filename": filename,
                "data": endpoint_data,
                "auth_required": is_endpoint_secure(operation_id, endpoint_data),
                "permissions": permission_class_paths,
                "permissions_data": permissions_with_names,  # Include display names for JS
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
