import html
import json
import re

from django import template
from django.templatetags.static import static as django_static
from django.utils.safestring import mark_safe

from drf_to_mkdoc.utils.commons.operation_utils import (
    format_method_badge as format_method_badge_util,
)

register = template.Library()


@register.filter
def is_foreign_key(field_type):
    return field_type in ["ForeignKey", "OneToOneField"]


@register.simple_tag
def static_with_prefix(path, prefix=""):
    """Add prefix to static path"""
    return django_static(prefix + path)


@register.filter
def format_method_badge(method):
    """Format HTTP method as badge"""
    return format_method_badge_util(method)


@register.filter
def get_display_name(field_name, field_type):
    if field_type in ["ForeignKey", "OneToOneField"]:
        return f"{field_name}_id"
    return field_name


@register.filter
def split(value, delimiter=","):
    return value.split(delimiter)


@register.filter
def cut(value, arg):
    return value.split(arg)[1] if "." in value else value


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, "")


@register.filter
def format_field_type(field_info):
    field_type = field_info.get("type", "")
    if field_type == "ForeignKey":
        return f"ForeignKey | {field_info.get('field_specific', {}).get('to', '')}"
    if field_type == "CharField":
        max_length = field_info.get("max_length", "")
        return f"CharField | {field_info.get('verbose_name', '')} | max_length={max_length}"
    return field_type


@register.filter
def format_field_extra(field_info):
    extras = []
    if field_info.get("null"):
        extras.append("null=True")
    if field_info.get("blank"):
        extras.append("blank=True")
    if field_info.get("unique"):
        extras.append("unique=True")
    if field_info.get("primary_key"):
        extras.append("primary_key=True")
    if field_info.get("max_length"):
        extras.append(f"max_length={field_info['max_length']}")
    return ", ".join(extras)


@register.filter
def yesno(value, arg=None):
    """
    Given a string mapping values for true, false and (optionally) None,
    return one of those strings according to the value.
    """
    if arg is None:
        arg = "yes,no,maybe"
    bits = arg.split(",")
    if len(bits) < 2:
        return value  # Invalid arg.
    try:
        yes, no, maybe = bits
    except ValueError:
        yes, no, maybe = bits[0], bits[1], bits[1]

    if value is None:
        return maybe
    if value:
        return yes
    return no


@register.filter
def format_json(value):
    if isinstance(value, str):
        value = html.unescape(value)
        try:
            parsed = json.loads(value)
            value = json.dumps(parsed, indent=2)
        except (json.JSONDecodeError, TypeError):
            pass
    elif isinstance(value, dict | list):
        value = json.dumps(value, indent=2)

    return mark_safe(f"```json\n{value}\n```")  # noqa: S308


@register.filter
def extract_json_from_markdown(value):
    """Extract JSON content from markdown code blocks"""
    if not isinstance(value, str):
        return ""

    # Look for ```json code blocks

    json_pattern = r"```json\s*\n(.*?)\n```"
    matches = re.findall(json_pattern, value, re.DOTALL)

    if matches:
        return matches[0].strip()

    # Fallback: look for any code block
    code_pattern = r"```\s*\n(.*?)\n```"
    matches = re.findall(code_pattern, value, re.DOTALL)

    if matches:
        content = matches[0].strip()
        # Try to validate if it's JSON
        try:
            json.loads(content)
        except (json.JSONDecodeError, TypeError):
            pass
        else:
            return content

    return ""


@register.filter
def escape_json_for_attr(value):
    """Escape JSON string for use in HTML data attributes"""
    # Handle mark_safe objects by converting to string
    if hasattr(value, '__html__'):
        value = str(value)
    elif not isinstance(value, str):
        return ""
    # Escape HTML entities and single quotes (since we use single quotes for attributes)
    # JSON uses double quotes, so we mainly need to escape &, <, >, and single quotes
    value = value.replace("&", "&amp;")
    value = value.replace("<", "&lt;")
    value = value.replace(">", "&gt;")
    value = value.replace("'", "&#x27;")  # Escape single quotes
    return value


@register.filter
def json_for_display(value):
    """Prepare JSON string for display in markdown code blocks (unescape if needed)"""
    if not isinstance(value, str):
        return ""
    # Unescape any HTML entities that might have been introduced
    value = html.unescape(value)
    return mark_safe(value)  # noqa: S308


@register.filter
def to_json(value):
    """Convert Python object to JSON string for JavaScript"""
    return mark_safe(json.dumps(value))  # noqa: S308


@register.filter
def format_example(value):
    """Format example value for display in query parameter tables."""
    if value is None:
        return "—"
    if isinstance(value, bool):
        # Format boolean as lowercase string
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        # Format numbers as-is
        return str(value)
    if isinstance(value, (dict, list)):
        # Format complex types as compact JSON
        try:
            formatted = json.dumps(value, separators=(",", ":"))
        except (TypeError, ValueError):
            return str(value)

        # Truncate if too long (max 50 chars for table display)
        if len(formatted) > 50:
            return formatted[:47] + "..."
        return formatted
    # For strings and other types, return as string
    return str(value)


@register.filter
def format_description(value):
    """
    Format description text for MkDocs Material rendering.
    
    Clients write markdown directly in their JSON descriptions.
    This filter normalizes various encoding issues that can occur during JSON processing.
    
    Handles:
    - HTML entities (e.g., &quot; → ")
    - Double-escaped newlines (e.g., \\n → \n) - only if needed
    - Escaped HTML entities (e.g., \&quot; → ")
    
    Example JSON:
    {
      "description": "This endpoint creates a user.\\n\\n- Requires authentication\\n- Returns user ID\\n\\n**Important**: Email must be unique."
    }
    """
    if not isinstance(value, str) or not value:
        return value
    
    formatted = value
    
    # Step 1: Remove backslashes before HTML entities
    # Handles: \&quot; → &quot;, \&#34; → &#34;, \&#x27; → &#x27;
    formatted = re.sub(r'\\(&[a-zA-Z]+;)', r'\1', formatted)  # Named entities
    formatted = re.sub(r'\\(&#\d+;)', r'\1', formatted)        # Numeric entities
    formatted = re.sub(r'\\(&#x[0-9a-fA-F]+;)', r'\1', formatted)  # Hex entities
    
    # Step 2: Unescape HTML entities
    # Handles: &quot; → ", &amp; → &, &lt; → <, etc.
    formatted = html.unescape(formatted)
    
    # Step 3: Convert double-escaped newlines ONLY if they exist
    # Note: If json.loads() already converted these, this won't match anything
    # This is a safety net for edge cases where strings aren't properly loaded
    if '\\n' in formatted:
        formatted = formatted.replace('\\n', '\n')
    if '\\t' in formatted:
        formatted = formatted.replace('\\t', '\t')
    
    # Clean up excessive whitespace at start/end
    return formatted.strip()


@register.filter
def format_enum(value):
    """
    Format enum values for display in validation constraints.
    Converts list of enum values to a comma-separated string.
    """
    if not isinstance(value, list):
        return str(value) if value is not None else ""
    
    # Convert each value to string and join with commas
    return ", ".join(str(v) for v in value)