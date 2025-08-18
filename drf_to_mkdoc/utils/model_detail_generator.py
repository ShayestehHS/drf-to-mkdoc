from typing import Any

from django.templatetags.static import static

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings
from drf_to_mkdoc.utils.common import get_model_description, write_file


def generate_model_docs(models_data: dict[str, Any]) -> None:
    """Generate model documentation from JSON data"""
    for model_name, model_info in models_data.items():
        app_name = model_info.get("app_label", model_name.split(".")[0])
        class_name = model_info.get("name", model_name.split(".")[-1])

        # Create the model page content
        content = create_model_page(model_info)

        # Write the file in app subdirectory
        file_path = f"models/{app_name}/{class_name.lower()}.md"
        write_file(file_path, content)


def render_column_fields_table(fields: dict[str, Any]) -> str:
    """Render the fields table for a model."""
    content = "## Fields\n\n"
    content += "| Field | Type | Description | Extra |\n"
    content += "|-------|------|-------------|-------|\n"

    for field_name, field_info in fields.items():
        field_type = field_info.get("type", "Unknown")
        verbose_name = field_info.get("verbose_name", field_name)
        help_text = field_info.get("help_text", "")

        display_name = field_name
        if field_type in ["ForeignKey", "OneToOneField"]:
            display_name = f"{field_name}_id"

        extra_info = []
        if field_info.get("null"):
            extra_info.append("null=True")
        if field_info.get("blank"):
            extra_info.append("blank=True")
        if field_info.get("unique"):
            extra_info.append("unique=True")
        if field_info.get("primary_key"):
            extra_info.append("primary_key=True")
        if field_info.get("default"):
            extra_info.append(f"default={field_info['default']}")

        field_specific = field_info.get("field_specific", {})
        for key, value in field_specific.items():
            if key not in ["related_name", "related_query_name", "to"]:
                extra_info.append(f"{key}={value}")

        extra_str = ", ".join(extra_info) if extra_info else ""
        description_str = help_text or verbose_name

        content += f"| `{display_name}` | {field_type} | {description_str} | {extra_str} |\n"

    return content


def render_choices_tables(fields: dict[str, Any]) -> str:
    """Render choice tables for fields with choices."""
    choice_tables = []

    for field_name, field_info in fields.items():
        choices = field_info.get("choices")
        if choices:
            table = f"### {field_name} Choices\n\n"
            table += "| Label | Value |\n"
            table += "|-------|--------|\n"
            for choice in choices:
                table += f"| {choice['display']} | `{choice['value']}` |\n"
            table += "\n"
            choice_tables.append(table)

    if choice_tables:
        return "## Choices\n\n" + "\n".join(choice_tables)
    return ""


def create_model_page(model_info: dict[str, Any]) -> str:
    """Create a model documentation page from model info"""
    name = model_info.get("name", "Unknown")
    app_label = model_info.get("app_label", "unknown")
    table_name = model_info.get("table_name", "")
    description = get_model_description(name)

    content = _create_model_header(name, app_label, table_name, description)
    content += _add_fields_section(model_info)
    content += _add_relationships_section(model_info)
    content += _add_methods_section(model_info)
    content += _add_meta_options_section(model_info)

    return content


def _create_model_header(name: str, app_label: str, table_name: str, description: str) -> str:
    """Create the header section of the model documentation."""
    stylesheets = [
        "stylesheets/models/variables.css",
        "stylesheets/models/base.css",
        "stylesheets/models/model-tables.css",
        "stylesheets/models/responsive.css",
    ]
    prefix_path = f"{drf_to_mkdoc_settings.PROJECT_NAME}/"
    css_links = "\n".join(
        f'<link rel="stylesheet" href="{static(prefix_path + path)}">' for path in stylesheets
    )
    return f"""# {name}

<!-- inject CSS directly -->
{css_links}

**App:** {app_label}
**Table:** `{table_name}`

## Description

{description}

"""


def _add_fields_section(model_info: dict[str, Any]) -> str:
    """Add the fields section to the model documentation."""
    column_fields = model_info.get("column_fields", {})
    if not column_fields:
        return ""

    content = ""

    column_fields_content = render_column_fields_table(column_fields)
    if column_fields_content:
        content += column_fields_content
        content += "\n"

    choices_content = render_choices_tables(column_fields)
    if choices_content:
        content += choices_content
        content += "\n"

    return content


def _add_relationships_section(model_info: dict[str, Any]) -> str:
    """Add the relationships section to the model documentation."""
    relationship_fields = model_info.get("relationships", {})
    if not relationship_fields:
        return ""

    content = "## Relationships\n\n"
    content += "| Field | Type | Related Model |\n"
    content += "|-------|------|---------------|\n"

    content += _render_relationship_fields(relationship_fields)
    content += _render_relationships_from_section(relationship_fields)
    content += "\n"

    return content


def _render_relationship_fields(relationship_fields: dict[str, Any]) -> str:
    """Render relationship fields from the fields section."""
    content = ""
    for field_name, field_info in relationship_fields.items():
        field_type = field_info.get("type", "Unknown")
        field_specific = field_info.get("field_specific", {})
        to_model = field_specific.get("to", "")

        if to_model:
            model_link = _create_model_link(to_model)
            content += f"| `{field_name}` | {field_type} | {model_link}|\n"

    return content


def _render_relationships_from_section(relationships: dict[str, Any]) -> str:
    """Render relationships from the relationships section."""
    content = ""
    for rel_name, rel_info in relationships.items():
        rel_type = rel_info.get("type", "Unknown")
        related_model_full = rel_info.get("related_model", "")

        if related_model_full and "." in related_model_full:
            related_app, related_model = related_model_full.split(".", 1)
            model_link = f"[{related_model}](../../{related_app}/{related_model.lower()}/)"
        else:
            model_link = related_model_full

        content += f"| `{rel_name}` | {rel_type} | {model_link} | \n"

    return content


def _create_model_link(to_model: str) -> str:
    """Create a link to a related model."""
    if "." in to_model:
        related_app, related_model = to_model.split(".", 1)
        return f"[{related_model}](../{related_app}/{related_model.lower()}/)"
    return f"[{to_model}]({to_model.lower()}/)"


def _add_methods_section(model_info: dict[str, Any]) -> str:
    """Add the methods section to the model documentation."""
    methods = model_info.get("methods", [])
    if not methods:
        return ""

    content = "## Methods\n\n"
    for method in methods:
        method_name = method.get("name", "")
        docstring = method.get("docstring", "")

        content += f"### `{method_name}()`\n\n"
        if docstring:
            content += f"{docstring}\n\n"
        else:
            content += "No documentation available.\n\n"

    return content


def _add_meta_options_section(model_info: dict[str, Any]) -> str:
    """Add the meta options section to the model documentation."""
    meta_options = model_info.get("meta_options", {})
    if not meta_options:
        return ""

    content = "## Meta Options\n\n"
    for option, value in meta_options.items():
        content += f"- **{option}:** {value}\n"
    content += "\n"

    return content
