from pathlib import Path

from django.core.management.base import BaseCommand

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings
from drf_to_mkdoc.utils.commons.file_utils import load_json_data
from drf_to_mkdoc.utils.er_diagram_generator import generate_er_diagrams
from drf_to_mkdoc.utils.model_detail_generator import generate_model_docs
from drf_to_mkdoc.utils.model_list_generator import create_models_index


class Command(BaseCommand):
    help = "Build model documentation from model JSON data"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🚀 Starting model documentation generation..."))

        docs_dir = self._setup_docs_directory()
        models_data = self._load_models_data()

        if models_data:
            self._generate_models_documentation(models_data, docs_dir)
            self.stdout.write(self.style.SUCCESS("✅ Model documentation generation complete!"))
        else:
            self.stdout.write(self.style.ERROR("❌ Failed to generate model documentation."))

    def _setup_docs_directory(self):
        docs_dir = Path(drf_to_mkdoc_settings.DOCS_DIR)
        docs_dir.mkdir(parents=True, exist_ok=True)
        return docs_dir

    def _load_models_data(self):
        models_data = load_json_data(
            drf_to_mkdoc_settings.MODEL_DOCS_FILE, raise_not_found=False
        )

        if not models_data:
            self.stdout.write(self.style.WARNING("⚠️  No model data found"))

        return models_data

    def _generate_models_documentation(self, models_data, docs_dir):
        self.stdout.write("📋 Generating model documentation...")

        try:
            # Generate model detail pages
            generate_model_docs(models_data)
            self.stdout.write(self.style.SUCCESS("✅ Model detail pages generated"))

            # Generate ER diagrams
            generate_er_diagrams(models_data, docs_dir)
            self.stdout.write(self.style.SUCCESS("✅ ER diagrams generated"))

            # Create models index page
            create_models_index(models_data, docs_dir)
            self.stdout.write(self.style.SUCCESS("✅ Models index page generated"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️  Failed to generate model docs: {e}"))
            raise
