"""Model-related utilities."""

import importlib

from django.apps import apps
from django.core.exceptions import AppRegistryNotReady

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings
from drf_to_mkdoc.utils.commons.file_utils import load_json_data


def get_model_docstring(class_name: str) -> str | None:
    """Extract docstring from Django model class"""
    try:
        # Check if Django is properly initialized
        apps.check_apps_ready()

        # Common Django app names to search
        app_names = drf_to_mkdoc_settings.DJANGO_APPS

        for app_name in app_names:
            try:
                # Try to import the models module
                models_module = importlib.import_module(f"{app_name}.models")

                # Check if the class exists in this module
                if hasattr(models_module, class_name):
                    model_class = getattr(models_module, class_name)

                    # Get the docstring
                    docstring = getattr(model_class, "__doc__", None)

                    if docstring:
                        # Clean up the docstring
                        docstring = docstring.strip()

                        # Filter out auto-generated or generic docstrings
                        if (
                            docstring
                            and not docstring.startswith(class_name + "(")
                            and not docstring.startswith("str(object=")
                            and not docstring.startswith("Return repr(self)")
                            and "django.db.models" not in docstring.lower()
                            and len(docstring) > 10
                        ):  # Minimum meaningful length
                            return docstring

            except (ImportError, AttributeError):
                continue

    except (ImportError, AppRegistryNotReady):
        # Django not initialized or not available - skip docstring extraction
        pass

    return None


def get_model_description(class_name: str) -> str:
    """Get a brief description for a model with priority-based selection"""
    # Priority 1: Description from config file
    config = load_json_data(drf_to_mkdoc_settings.DOC_CONFIG_FILE, raise_not_found=False)
    if config and "model_descriptions" in config:
        config_description = config["model_descriptions"].get(class_name, "").strip()
        if config_description:
            return config_description

    # Priority 2: Extract docstring from model class
    docstring = get_model_docstring(class_name)
    if docstring:
        return docstring

    # Priority 3: static value
    return "Not provided"


def get_app_descriptions() -> dict[str, str]:
    """Get descriptions for Django apps from config file"""
    config = load_json_data(drf_to_mkdoc_settings.DOC_CONFIG_FILE, raise_not_found=False)
    if config and "app_descriptions" in config:
        return config["app_descriptions"]

    # Fallback to empty dict if config not available
    return {}
