from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import quote

from django.templatetags.static import static

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings
from drf_to_mkdoc.utils.commons.model_utils import get_app_descriptions


def create_models_index(models_data: dict[str, Any], docs_dir: Path) -> None:
    """Create the main models index page that lists all models organized by app."""
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

    for app_name, models in sorted(models_data.items()):
        app_desc = escape(
            app_descriptions.get(
                app_name, f"{app_name.replace('_', ' ').title()} application models"
            )
        )
        app_title = escape(app_name.replace("_", " ").title())
        content += f'<div class="app-header">{app_title} App</div>\n'
        content += f'<div class="app-description">{app_desc}</div>\n\n'

        content += '<div class="model-cards">\n'

        model_names = sorted(
            [
                (
                    str(mi.get("verbose_name") or mk),
                    str(mi.get("table_name") or mk),
                )
                for mk, mi in models.items()
                if isinstance(mi, dict)
            ],
            key=lambda x: x[0].casefold(),
        )
        for verbose_name, table_name in model_names:
            content += f"""
            <a href="{quote(app_name, safe="")}/{quote(table_name, safe="")}/"
             class="model-card">{escape(verbose_name)}</a>\n
"""

        content += "</div>\n\n"

    content += """</div>


Each model page contains detailed field documentation, method signatures, and relationships to other models."""

    models_index_path = docs_dir / "models" / "index.md"
    models_index_path.parent.mkdir(parents=True, exist_ok=True)

    with models_index_path.open("w", encoding="utf-8") as f:
        f.write(content)
