import shutil
import subprocess
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings


class Command(BaseCommand):
    help = "Build MkDocs documentation"

    def handle(self, *args, **options):
        drf_to_mkdoc_settings.validate_required_settings()
        self.stdout.write(self.style.SUCCESS("✅ DRF_TO_MKDOC settings validated."))

        try:
            apps.check_apps_ready()
        except Exception as e:
            raise CommandError(f"Django apps not properly configured: {e}") from e

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
            # Extract model data from Django models
            self.stdout.write("Extracting model data...")
            call_command("extract_model_data", "--pretty")
            self.stdout.write(self.style.SUCCESS("Model data extracted."))

            # Generate the documentation content
            self.stdout.write("Building documentation content...")
            call_command("build_model_docs")
            call_command("build_endpoint_docs")
            self.stdout.write(self.style.SUCCESS("Documentation content built."))

            # Build the MkDocs site
            self.stdout.write("Building MkDocs site...")
            self._build_mkdocs_site(base_dir, site_dir)
            self.stdout.write(self.style.SUCCESS("Documentation built successfully!"))
            self.stdout.write(f"Site built in: {site_dir}")

        except FileNotFoundError as e:
            raise CommandError(
                "MkDocs not found. Please install it with: pip install mkdocs mkdocs-material"
            ) from e

    def _build_mkdocs_site(self, base_dir: Path, site_dir: Path) -> None:
        """
        Build the MkDocs site with proper security checks.

        Args:
            base_dir: The base directory of the Django project
            site_dir: The directory where the site will be built

        Raises:
            FileNotFoundError: If mkdocs executable is not found
            CommandError: If the build process fails
        """
        mkdocs_path = shutil.which("mkdocs")
        if not mkdocs_path:
            raise FileNotFoundError("mkdocs executable not found in PATH")

        mkdocs_path_obj = Path(mkdocs_path)
        if not mkdocs_path_obj.exists() or not mkdocs_path_obj.is_file():
            raise CommandError(f"Invalid mkdocs executable path: {mkdocs_path}")

        if not base_dir.is_absolute():
            base_dir = base_dir.resolve()

        if not base_dir.exists():
            raise CommandError(f"Base directory does not exist: {base_dir}")

        cmd = [
            str(mkdocs_path_obj),  # Convert to string for subprocess
            "build",
            "--clean",
        ]

        try:
            result = subprocess.run(  # noqa S603
                cmd,
                check=True,
                cwd=str(base_dir),
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.stdout:
                self.stdout.write(f"MkDocs output: {result.stdout}")

        except subprocess.TimeoutExpired as e:
            raise CommandError("MkDocs build timed out after 5 minutes") from e
        except subprocess.CalledProcessError as e:
            error_msg = f"MkDocs build failed (exit code {e.returncode})"
            if e.stderr:
                error_msg += f": {e.stderr}"
            raise CommandError(error_msg) from e
