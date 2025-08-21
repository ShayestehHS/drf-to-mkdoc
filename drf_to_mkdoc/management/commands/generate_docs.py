from pathlib import Path

from django.core.management.base import BaseCommand

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings
from drf_to_mkdoc.utils.common import get_schema, load_model_json_data
from drf_to_mkdoc.utils.endpoint_detail_generator import (
    generate_endpoint_files,
    parse_endpoints_from_schema,
)
from drf_to_mkdoc.utils.endpoint_list_generator import create_endpoints_index
from drf_to_mkdoc.utils.model_detail_generator import generate_model_docs
from drf_to_mkdoc.utils.model_list_generator import create_models_index


class Command(BaseCommand):
    help = "Generate complete API documentation (models + endpoints + navigation)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--endpoints-only",
            action="store_true",
            help="Generate only endpoint documentation",
        )
        parser.add_argument(
            "--models-only",
            action="store_true",
            help="Generate only model documentation",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🚀 Starting documentation generation..."))

        docs_dir = self._setup_docs_directory()

        generate_models = not options["endpoints_only"]
        generate_endpoints = not options["models_only"]

        models_data = self._load_models_data() if generate_models else {}
        schema_data = self._load_schema_data() if generate_endpoints else {}

        if generate_models and models_data:
            self._generate_models_documentation(models_data, docs_dir)

        if generate_endpoints and schema_data:
            self._generate_endpoints_documentation(schema_data, docs_dir)

        self.stdout.write(self.style.SUCCESS("✅ Documentation generation complete!"))

    def _setup_docs_directory(self):
        docs_dir = Path(drf_to_mkdoc_settings.DOCS_DIR)
        docs_dir.mkdir(parents=True, exist_ok=True)
        return docs_dir

    def _load_models_data(self):
        json_data = load_model_json_data()
        models_data = json_data.get("models", {}) if json_data else {}

        if not models_data:
            self.stdout.write(self.style.WARNING("⚠️  No model data found"))

        return models_data

    def _load_schema_data(self):
        schema = get_schema()
        if not schema:
            self.stdout.write(self.style.ERROR("❌ Failed to load OpenAPI schema"))
            return {}

        paths = schema.get("paths", {})
        components = schema.get("components", {})

        self.stdout.write(f"📊 Loaded {len(paths)} API paths")

        return {"paths": paths, "components": components}

    def _generate_models_documentation(self, models_data, docs_dir):
        self.stdout.write("📋 Generating model documentation...")

        try:
            generate_model_docs(models_data)
            create_models_index(models_data, docs_dir)
            self.stdout.write(self.style.SUCCESS("✅ Model documentation generated"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️  Failed to generate model docs: {e}"))
            if hasattr(self, "_generating_all"):
                self.stdout.write(self.style.WARNING("Continuing with endpoint generation..."))
            raise

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
