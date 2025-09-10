from pathlib import Path
from typing import Any

from django.template.loader import render_to_string
from django.templatetags.static import static

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings
from drf_to_mkdoc.utils.commons.model_utils import get_app_descriptions


def create_models_index(models_data: dict[str, Any], docs_dir: Path) -> None:
    """Create the main models index page that lists all models organized by app."""
    stylesheets = [
        static(f"{drf_to_mkdoc_settings.PROJECT_NAME}/{path}")
        for path in [
            "stylesheets/models/variables.css",
            "stylesheets/models/base.css",
            "stylesheets/models/model-cards.css",
            "stylesheets/models/responsive.css",
            "stylesheets/models/animations.css",
        ]
    ]

    sorted_models = []
    for app_name, models in sorted(models_data.items()):
        model_names = sorted(
            [
                (
                    str(mi.get("verbose_name") or mk).capitalize(),
                    str(mi.get("table_name") or mk),
                )
                for mk, mi in models.items()
                if isinstance(mi, dict)
            ],
            key=lambda x: x[0].casefold(),
        )
        sorted_models.append((app_name, model_names))

    app_descriptions = get_app_descriptions()
    for app_name, _ in sorted_models:
        if app_name not in app_descriptions:
            app_descriptions[app_name] = (
                f"{app_name.replace('_', ' ').title()} application models"
            )

    content = render_to_string(
        "models_index.html",
        {
            "stylesheets": stylesheets,
            "sorted_models": sorted_models,
            "app_descriptions": app_descriptions,
        },
    )

    models_index_path = docs_dir / "models" / "index.md"
    models_index_path.parent.mkdir(parents=True, exist_ok=True)

    with models_index_path.open("w", encoding="utf-8") as f:
        f.write(content)
