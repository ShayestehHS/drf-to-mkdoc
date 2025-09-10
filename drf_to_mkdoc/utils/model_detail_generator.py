from typing import Any

from django.template.loader import render_to_string
from django.templatetags.static import static

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings
from drf_to_mkdoc.utils.commons.file_utils import write_file
from drf_to_mkdoc.utils.commons.model_utils import get_model_description


def generate_model_docs(models_data: dict[str, Any]) -> None:
    """Generate model documentation from JSON data"""
    for app_name, models in models_data.items():
        if not isinstance(models, dict):
            raise TypeError(f"Expected dict for models in app '{app_name}', got {type(models)}")

        for model_name, model_info in models.items():
            if not isinstance(model_info, dict) or "name" not in model_info:
                raise ValueError(
                    f"Model info for '{model_name}' in app '{app_name}' is invalid"
                )

            # Create the model page content
            content = create_model_page(model_info)

            # Write the file in app subdirectory
            file_path = f"models/{app_name}/{model_info['table_name']}.md"
            write_file(file_path, content)


def create_model_page(model_info: dict[str, Any]) -> str:
    """Create a model documentation page from model info"""
    name = model_info.get("name", "Unknown")
    app_label = model_info.get("app_label", "unknown")
    table_name = model_info.get("table_name", "")
    description = get_model_description(name)
    column_fields = model_info.get("column_fields", {})

    # Check if any fields have choices
    has_choices = any(field_info.get("choices") for field_info in column_fields.values())

    stylesheets = [
        static(f"{drf_to_mkdoc_settings.PROJECT_NAME}/stylesheets/models/variables.css"),
        static(f"{drf_to_mkdoc_settings.PROJECT_NAME}/stylesheets/models/base.css"),
        static(f"{drf_to_mkdoc_settings.PROJECT_NAME}/stylesheets/models/model-tables.css"),
        static(f"{drf_to_mkdoc_settings.PROJECT_NAME}/stylesheets/models/responsive.css"),
    ]

    context = {
        "name": name,
        "app_label": app_label,
        "table_name": table_name,
        "description": description,
        "stylesheets": stylesheets,
        "fields": column_fields,  # Changed from column_fields to fields for template consistency
        "has_choices": has_choices,  # Added choices flag
        "relationships": model_info.get("relationships", {}),
        "methods": model_info.get("methods", []),
        "meta_options": model_info.get("meta_options", {}),
    }

    return render_to_string("model_detail/base.html", context)
