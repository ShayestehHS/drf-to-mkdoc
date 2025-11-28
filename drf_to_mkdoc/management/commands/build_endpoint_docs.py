from pathlib import Path

from django.core.management.base import BaseCommand

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings
from drf_to_mkdoc.utils.commons.schema_utils import get_schema
from drf_to_mkdoc.utils.endpoint_detail_generator import (
    generate_endpoint_files,
    parse_endpoints_from_schema,
)
from drf_to_mkdoc.utils.endpoint_list_generator import create_endpoints_index
from drf_to_mkdoc.utils.permission_detail_generator import generate_permission_docs


class Command(BaseCommand):
    help = "Build endpoint documentation from OpenAPI schema"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("🚀 Starting endpoint documentation generation...")
        )

        docs_dir = self._setup_docs_directory()
        schema_data = self._load_schema_data()

        if schema_data:
            self._generate_endpoints_documentation(schema_data, docs_dir)
            self.stdout.write(
                self.style.SUCCESS("✅ Endpoint documentation generation complete!")
            )
        else:
            self.stdout.write(self.style.ERROR("❌ Failed to generate endpoint documentation."))

    def _setup_docs_directory(self):
        docs_dir = Path(drf_to_mkdoc_settings.DOCS_DIR)
        docs_dir.mkdir(parents=True, exist_ok=True)
        return docs_dir

    def _load_schema_data(self):
        try:
            schema = get_schema()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to load OpenAPI schema: {e}"))
            return {}
        if not schema:
            self.stdout.write(self.style.ERROR("❌ Failed to load OpenAPI schema"))
            return {}

        paths = schema.get("paths", {})
        components = schema.get("components", {})

        self.stdout.write(f"📊 Loaded {len(paths)} API paths")

        return {"paths": paths, "components": components}

    def _generate_endpoints_documentation(self, schema_data, docs_dir):
        self.stdout.write("🔗 Generating endpoint documentation...")

        paths = schema_data["paths"]
        components = schema_data["components"]

        endpoints_by_app = parse_endpoints_from_schema(paths)
        total_endpoints = generate_endpoint_files(endpoints_by_app, components)
        create_endpoints_index(endpoints_by_app, docs_dir)

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Generated {total_endpoints} endpoint files with Django view introspection"
            )
        )
        
        # Generate permission detail pages
        self._generate_permission_pages(paths)

    def _generate_permission_pages(self, paths):
        """Collect all unique permissions and generate detail pages."""
        self.stdout.write("🔐 Collecting permissions...")
        
        permissions = {}
        for path_data in paths.values():
            for method_data in path_data.values():
                if not isinstance(method_data, dict):
                    continue
                metadata = method_data.get("x-metadata", {})
                permission_classes = metadata.get("permission_classes", [])
                
                for perm in permission_classes:
                    if isinstance(perm, dict):
                        class_path = perm.get("class_path")
                        if class_path:
                            permissions[class_path] = perm
                    elif isinstance(perm, str):
                        # Backward compatibility with string format
                        permissions[perm] = {"class_path": perm}
        
        if permissions:
            generate_permission_docs(permissions)
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Generated {len(permissions)} permission detail pages"
                )
            )
        else:
            self.stdout.write("ℹ️  No permissions found to document")
