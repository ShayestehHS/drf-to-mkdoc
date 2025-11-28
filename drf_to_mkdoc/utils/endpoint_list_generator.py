from pathlib import Path
from typing import Any

from django.template.loader import render_to_string
from django.templatetags.static import static

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings
from drf_to_mkdoc.utils.commons.auth_utils import get_auth_config
from drf_to_mkdoc.utils.commons.operation_utils import extract_viewset_from_operation_id


class EndpointsIndexGenerator:
    def __init__(self, active_filters: list[str] | None = None):
        self.active_filters = active_filters or [
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
            "permissions",
        ]

    def create_endpoints_index(
        self, endpoints_by_app: dict[str, list[dict[str, Any]]], docs_dir: Path
    ) -> None:
        prefix_path = f"{drf_to_mkdoc_settings.PROJECT_NAME}/"
        stylesheets = [
            static(prefix_path + path)
            for path in [
                "stylesheets/endpoints/variables.css",
                "stylesheets/endpoints/base.css",
                "stylesheets/endpoints/theme-toggle.css",
                "stylesheets/endpoints/filter-section.css",
                "stylesheets/endpoints/settings-modal.css",
                "stylesheets/endpoints/layout.css",
                "stylesheets/endpoints/endpoints-grid.css",
                "stylesheets/endpoints/badges.css",
                "stylesheets/endpoints/endpoint-content.css",
                "stylesheets/endpoints/tags.css",
                "stylesheets/endpoints/sections.css",
                "stylesheets/endpoints/stats.css",
                "stylesheets/endpoints/loading.css",
                "stylesheets/endpoints/animations.css",
                "stylesheets/endpoints/responsive.css",
                "stylesheets/endpoints/accessibility.css",
                "stylesheets/endpoints/fixes.css",
            ]
        ]

        scripts = [
            static(prefix_path + "javascripts/endpoints-filter.js"),
            static(prefix_path + "javascripts/settings-modal.js"),
        ]

        # Process endpoints to add view_class
        processed_endpoints = {}
        
        for app_name, app_endpoints in endpoints_by_app.items():
            processed_endpoints[app_name] = []
            for endpoint in app_endpoints:
                processed_endpoint = endpoint.copy()
                processed_endpoint["view_class"] = extract_viewset_from_operation_id(
                    endpoint["operation_id"]
                )
                processed_endpoint["link_url"] = (
                    f"{app_name}/{processed_endpoint['viewset'].lower()}/{processed_endpoint['filename'].replace('.md', '/index.html')}"
                )
                
                processed_endpoints[app_name].append(processed_endpoint)

        context = {
            "stylesheets": stylesheets,
            "scripts": scripts,
            "endpoints_by_app": processed_endpoints,
            "active_filters": self.active_filters,
            **get_auth_config(),
        }

        content = render_to_string("endpoints/list/base.html", context)

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
            "permissions",
        ]
    )
    generator.create_endpoints_index(endpoints_by_app, docs_dir)
