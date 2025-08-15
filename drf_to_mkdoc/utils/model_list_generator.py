from pathlib import Path
from typing import Any

from django.templatetags.static import static

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings
from drf_to_mkdoc.utils.common import get_app_descriptions


def create_models_index(models_data: dict[str, Any], docs_dir: Path) -> None:
    """Create the main models index page that lists all models organized by app."""
    models_by_app = {}
    for model_name, model_info in models_data.items():
        app_name = model_info.get("app_label", model_name.split(".")[0])
        class_name = model_info.get("name", model_name.split(".")[-1])
        if app_name not in models_by_app:
            models_by_app[app_name] = []
        models_by_app[app_name].append((class_name, model_name, model_info))

    stylesheets = [
        "stylesheets/models/variables.css",
        "stylesheets/models/base.css",
        "stylesheets/models/model-cards.css",
        "stylesheets/models/responsive.css",
        "stylesheets/models/animations.css",
    ]
    prefix_path = f"{drf_to_mkdoc_settings.PROJECT_NAME}/"
    css_links = "\n".join(
        f'<link rel="stylesheet" href="{static(prefix_path + path)}">' for path in stylesheets
    )
    content = f"""# Django Models

This section contains documentation for all Django models in the system, organized by Django application.

<!-- inject CSS directly -->
{css_links}

<div class="models-container">
"""

    app_descriptions = get_app_descriptions()

    for app_name in sorted(models_by_app.keys()):
        app_desc = app_descriptions.get(app_name, f"{app_name.title()} application models")
        content += f'<div class="app-header">{app_name.title()} App</div>\n'
        content += f'<div class="app-description">{app_desc}</div>\n\n'

        content += '<div class="model-cards">\n'

        for class_name, _model_name, _model_info in sorted(models_by_app[app_name]):
            content += f"""
            <a href="{app_name}/{class_name.lower()}/"
             class="model-card">{class_name}</a>\n
"""

        content += "</div>\n\n"

    content += """</div>


Each model page contains detailed field documentation, method signatures, and relationships to other models."""

    models_index_path = docs_dir / "models" / "index.md"
    models_index_path.parent.mkdir(parents=True, exist_ok=True)

    with models_index_path.open("w", encoding="utf-8") as f:
        f.write(content)
