import logging

from django.apps import AppConfig

logger = logging.getLogger()


class DrfToMkdocConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_to_mkdoc"
    verbose_name = "DRF to MkDocs Documentation Generator"

    def ready(self):
        """Initialize the app when Django starts."""
        # Import management commands to register them
        try:
            import drf_to_mkdoc.management.commands  # noqa
        except ImportError:
            logger.exception("Failed to import drf_to_mkdoc commands")
