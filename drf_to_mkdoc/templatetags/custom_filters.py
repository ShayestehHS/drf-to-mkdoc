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
