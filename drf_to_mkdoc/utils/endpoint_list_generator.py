from pathlib import Path
from typing import Any

from django.templatetags.static import static

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings
from drf_to_mkdoc.utils.common import extract_viewset_from_operation_id


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
        stylesheets = [
            "stylesheets/endpoints/variables.css",
            "stylesheets/endpoints/base.css",
            "stylesheets/endpoints/theme-toggle.css",
            "stylesheets/endpoints/filter-section.css",
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

        scripts = [
            "javascripts/endpoints-filter.js",
        ]
        prefix_path = f"{drf_to_mkdoc_settings.PROJECT_NAME}/"
        css_links = "\n".join(
            f'<link rel="stylesheet" href="{static(prefix_path + path)}">'
            for path in stylesheets
        )
        js_scripts = "\n".join(
            f'<script src="{static(prefix_path + path)}" defer></script>' for path in scripts
        )

        content = f"""# API Endpoints
<!-- inject CSS and JS directly -->
{css_links}
{js_scripts}

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
