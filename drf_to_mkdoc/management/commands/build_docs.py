import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings
from django.core.management import call_command


class Command(BaseCommand):
    help = "Build MkDocs documentation"

    def handle(self, *args, **options):
        drf_to_mkdoc_settings.validate_required_settings()
        self.stdout.write(self.style.SUCCESS("✅ DRF_TO_MKDOC settings validated."))

        try:
            apps.check_apps_ready()
        except Exception as e:
            raise CommandError(f"Django apps not properly configured: {e}")

        base_dir = Path(settings.BASE_DIR)
        site_dir = base_dir / "site"
        mkdocs_config = base_dir / "mkdocs.yml"
        mkdocs_config_alt = base_dir / "mkdocs.yaml"
        
        if not mkdocs_config.exists() and not mkdocs_config_alt.exists():
            raise CommandError(
                "MkDocs configuration file not found. Please create either 'mkdocs.yml' or 'mkdocs.yaml' "
                "in your project root directory."
            )

        try:
            # Generate the model documentation JSON first
            self.stdout.write("Generating model documentation...")

            try:
                call_command(
                    "generate_model_docs", "--pretty"
                )
                self.stdout.write(self.style.SUCCESS("Model documentation generated."))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Failed to generate model docs: {e}"))

            # Generate the documentation content
            self.stdout.write("Generating documentation content...")
            try:
                call_command("generate_docs")
                self.stdout.write(self.style.SUCCESS("Documentation content generated."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to generate docs: {e}"))
                raise

            # Build the MkDocs site
            self.stdout.write("Building MkDocs site...")
            result = subprocess.run(
                ["mkdocs", "build", "--clean"],
                check=False,
                cwd=base_dir,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                raise CommandError(f"MkDocs build failed: {result.stderr}")

            self.stdout.write(self.style.SUCCESS("Documentation built successfully!"))
            self.stdout.write(f"Site built in: {site_dir}")

        except FileNotFoundError as e:
            raise CommandError(
                "MkDocs not found. Please install it with: pip install mkdocs mkdocs-material"
            ) from e
        except Exception as e:
            raise CommandError(f"Error building documentation: {e!s}") from e
