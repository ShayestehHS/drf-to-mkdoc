import inspect
import json
import os
import re

import yaml
from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.views import SpectacularAPIView
from rest_framework.viewsets import ViewSetMixin


def get_view_class(view):
    """Extract the actual view class from a view callback."""
    # Check if it's a class-based view (Django CBV)
    if hasattr(view, "view_class"):
        return view.view_class

    # Check if it's a ViewSet (DRF)
    if hasattr(view, "cls"):
        return view.cls

    # Check if it's a regular class-based view
    if hasattr(view, "__self__") and isinstance(view.__self__, type):
        return view.__self__

    # For function-based views, return the function itself
    return view


def get_url_view_mapping(urlconf=None):
    """
    Generate a mapping from URL regex patterns to view classes/functions.

    Args:
        urlconf: URL configuration module (defaults to ROOT_URLCONF)

    Returns:
        dict: Mapping of URL regex patterns to view classes
    """
    resolver = get_resolver(urlconf)
    url_mapping = {}

    def extract_views(url_patterns, prefix=""):
        for pattern in url_patterns:
            if isinstance(pattern, URLResolver):
                # Handle included URL patterns (like include())
                new_prefix = prefix + pattern.pattern.regex.pattern.rstrip("$").rstrip("^")
                extract_views(pattern.url_patterns, new_prefix)
            elif isinstance(pattern, URLPattern):
                # Handle individual URL patterns
                full_pattern = prefix + pattern.pattern.regex.pattern
                view = pattern.callback

                # Get the actual view class
                view_class = get_view_class(view)
                url_mapping[full_pattern] = view_class

    extract_views(resolver.url_patterns)
    return url_mapping


def convert_regex_to_openapi_path(regex_pattern):
    """Convert Django URL regex pattern to OpenAPI path format."""
    # Remove start/end anchors
    path = regex_pattern.strip("^$")

    # Remove any remaining ^ and $ anchors throughout the pattern
    path = path.replace("^", "").replace("$", "")

    # Remove \Z end-of-string anchors
    path = path.replace("\\Z", "")

    # Convert named groups to OpenAPI parameters
    # Pattern like (?P<clinic_id>[^/]+) becomes {clinic_id}
    path = re.sub(r"\(\?P<([^>]+)>[^)]+\)", r"{\1}", path)

    # Convert simple groups to generic parameters
    path = re.sub(r"\([^)]+\)", r"{param}", path)

    # Clean up any remaining regex artifacts
    path = path.replace("\\", "")

    # Fix multiple slashes
    path = re.sub(r"/+", "/", path)

    # Handle escaped hyphens
    path = path.replace("\\-", "-")

    # Remove any remaining regex quantifiers and special characters
    path = re.sub(r"[+*?]", "", path)

    # Ensure it starts with /
    if not path.startswith("/"):
        path = "/" + path

    # Ensure it ends with / for consistency with OpenAPI schema
    if not path.endswith("/"):
        path += "/"

    return path


def extract_model_references_from_serializer(serializer_class):
    """Extract model references from a serializer class."""
    models = set()

    # Check if serializer has a Meta class with model
    if hasattr(serializer_class, "Meta") and hasattr(serializer_class.Meta, "model"):
        models.add(serializer_class.Meta.model)

    # Check fields for related serializers that might have models
    if hasattr(serializer_class, "_declared_fields"):
        for field in serializer_class._declared_fields.values():
            if (
                hasattr(field, "child")
                and hasattr(field.child, "Meta")
                and hasattr(field.child.Meta, "model")
            ):
                models.add(field.child.Meta.model)

    return models


def extract_model_references_from_view(view_class):
    """Extract model references from a view class."""
    models = set()

    # Check if view has a model or queryset
    if hasattr(view_class, "model") and view_class.model:
        models.add(view_class.model)
    elif hasattr(view_class, "queryset") and view_class.queryset is not None:
        models.add(view_class.queryset.model)

    # Check serializer_class
    if hasattr(view_class, "serializer_class"):
        models.update(extract_model_references_from_serializer(view_class.serializer_class))

    return models


class Command(BaseCommand):
    help = "Generates a JSON file with context for new API endpoints to be documented."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url_mapping = get_url_view_mapping()

        # --- LOGGING ---
        with open("url_log.txt", "w") as f:
            f.write("--- Discovered Django URL Patterns ---\n")
            for regex_pattern, view_class in sorted(self.url_mapping.items()):
                class_name = getattr(view_class, "__name__", str(view_class))
                module_name = getattr(view_class, "__module__", "unknown")
                openapi_path = convert_regex_to_openapi_path(regex_pattern)
                f.write(
                    f"{regex_pattern} -> {module_name}.{class_name} (OpenAPI: {openapi_path})\n"
                )
        # --- END LOGGING ---

    def _find_view_for_path(self, schema_path):
        """
        Finds the corresponding view for a given schema path by converting
        Django regex patterns to OpenAPI format and comparing them.
        """
        # Normalize schema path
        normalized_schema_path = schema_path
        if not normalized_schema_path.startswith("/"):
            normalized_schema_path = "/" + normalized_schema_path
        if not normalized_schema_path.endswith("/"):
            normalized_schema_path += "/"

        with open("url_log.txt", "a") as f:
            f.write(f"\n--- Attempting to Match Schema Path: '{normalized_schema_path}' ---\n")

        for regex_pattern, view_class in self.url_mapping.items():
            openapi_path = convert_regex_to_openapi_path(regex_pattern)

            with open("url_log.txt", "a") as f:
                f.write(f"  Comparing with: '{openapi_path}' (Regex: {regex_pattern})\n")

            # Direct match
            if openapi_path == normalized_schema_path:
                with open("url_log.txt", "a") as f:
                    f.write("  !!!!!! EXACT MATCH FOUND !!!!!!\n")
                return view_class

            # Pattern match (handling parameter name differences like pk vs id)
            if self._paths_match_pattern(openapi_path, normalized_schema_path):
                with open("url_log.txt", "a") as f:
                    f.write("  !!!!!! PATTERN MATCH FOUND !!!!!!\n")
                return view_class

        return None

    def _paths_match_pattern(self, django_path, openapi_path):
        """
        Check if paths match by comparing structure, ignoring parameter name differences.
        E.g., /path/{pk}/ matches /path/{id}/
        """
        # Split paths into segments
        django_segments = [s for s in django_path.split("/") if s]
        openapi_segments = [s for s in openapi_path.split("/") if s]

        # Must have same number of segments
        if len(django_segments) != len(openapi_segments):
            return False

        # Compare each segment
        for django_seg, openapi_seg in zip(django_segments, openapi_segments, strict=False):
            # If both are parameters (start with {), they match
            if (
                django_seg.startswith("{") and openapi_seg.startswith("{")
            ) or django_seg == openapi_seg:
                continue
            return False

        return True

    def _determine_action_from_path(self, view_class, method, path):
        """
        Determine the ViewSet action based on the HTTP method and URL path.
        Handles both standard CRUD actions and custom @action decorators.
        """
        # Check for custom actions first
        for attr_name in dir(view_class):
            attr = getattr(view_class, attr_name)
            if hasattr(attr, "mapping") and hasattr(attr, "url_path"):
                # This is a custom action with @action decorator
                action_url_path = attr.url_path
                action_methods = (
                    list(attr.mapping.keys()) if hasattr(attr.mapping, "keys") else []
                )

                # Debug logging
                with open("url_log.txt", "a") as f:
                    f.write(
                        f"  Checking action {attr_name}:"
                        f" url_path='{action_url_path}', "
                        f"methods={action_methods}, path='{path}'\n"
                    )

                # Check if the path ends with this action's url_path and method matches
                if path.rstrip("/").endswith(action_url_path) and method.lower() in [
                    m.lower() for m in action_methods
                ]:
                    with open("url_log.txt", "a") as f:
                        f.write(f"  !!! ACTION MATCH: {attr_name} !!!\n")
                    return attr_name

        # Fall back to standard CRUD actions
        action_map = {
            "get": "list" if "{id}" not in path and "{pk}" not in path else "retrieve",
            "post": "create",
            "put": "update",
            "patch": "partial_update",
            "delete": "destroy",
        }
        action = action_map.get(method.lower(), "list")

        with open("url_log.txt", "a") as f:
            f.write(f"  Using standard action: {action} for {method} {path}\n")

        return action

    def _analyze_endpoint(self, method, path):
        self.stdout.write(f"Analyzing {method} {path}...")
        try:
            view_class = self._find_view_for_path(path)

            if not view_class:
                self.stderr.write(self.style.ERROR(f"Could not resolve view for path: {path}"))
                return None

            # Skip function-based views
            if not inspect.isclass(view_class):
                self.stdout.write(
                    self.style.WARNING(f"Skipping function-based view for {path}")
                )
                return None

            if issubclass(view_class, SpectacularAPIView):
                self.stdout.write(
                    self.style.WARNING(f"Skipping documentation-generator view: {path}")
                )
                return None

            from rest_framework.test import APIRequestFactory

            factory = APIRequestFactory()
            request = getattr(factory, method.lower())(path)

            view_instance = None
            action = None
            if issubclass(view_class, ViewSetMixin):
                # For ViewSets, we need to determine the action
                action = self._determine_action_from_path(view_class, method, path)
                view_instance = view_class()
                view_instance.action = action  # Set the action explicitly
            else:
                view_instance = view_class()

            if not view_instance:
                self.stdout.write(self.style.WARNING(f"Could not instantiate view for {path}"))
                return None

            from django.contrib.auth.models import AnonymousUser

            request.user = AnonymousUser()

            # Mock kwargs from path
            mock_kwargs = {}
            for param in re.findall(r"{([^}]+)}", path):
                if "id" in param.lower():
                    mock_kwargs[param] = 1
                else:
                    mock_kwargs[param] = "test"
            view_instance.kwargs = mock_kwargs

            view_instance.setup(request, *(), **mock_kwargs)

            # For ViewSets, ensure action is set after setup
            if issubclass(view_class, ViewSetMixin) and action:
                view_instance.action = action

            serializer_class, model_class = None, None

            # Gracefully handle missing methods/attributes
            try:
                serializer_class = view_instance.get_serializer_class()
            except (AttributeError, AssertionError) as e:
                # For ViewSets with actions, try to get serializer class from action kwargs
                if issubclass(view_class, ViewSetMixin) and action:
                    action_method = getattr(view_class, action, None)
                    if (
                        action_method
                        and hasattr(action_method, "kwargs")
                        and "serializer_class" in action_method.kwargs
                    ):
                        serializer_class = action_method.kwargs["serializer_class"]
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Found action-specific serializer for {path}:"
                                f" {serializer_class.__name__}"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"Could not get serializer for {path}: {e}")
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"Could not get serializer for {path}: {e}")
                    )

            try:
                queryset = view_instance.get_queryset()
                if queryset is not None:
                    model_class = queryset.model
            except (AttributeError, AssertionError, KeyError) as e:
                # Many action-based ViewSets don't have querysets (auth, profile, etc.)
                # This is normal and expected, so we'll handle it gracefully
                if issubclass(view_class, ViewSetMixin) and action:
                    # For action-based ViewSets, not having a queryset is often normal
                    pass
                else:
                    self.stdout.write(
                        self.style.WARNING(f"Could not get queryset for {path}: {e}")
                    )

            view_code = inspect.getsource(view_class)
            serializer_code = (
                inspect.getsource(serializer_class) if serializer_class else "Not available."
            )

            # Extract model references instead of full model code
            model_references = set()

            # From view
            model_references.update(extract_model_references_from_view(view_class))

            # From serializer
            if serializer_class:
                model_references.update(
                    extract_model_references_from_serializer(serializer_class)
                )

            # From queryset model (if available)
            if model_class:
                model_references.add(model_class)

            # Convert to model names for referencing
            model_names = []
            for model in model_references:
                model_name = f"{model._meta.app_label}.{model.__name__}"
                model_names.append(model_name)

            return {
                "endpoint_info": {
                    "path": path,
                    "method": method,
                    "view_name": view_class.__name__,
                },
                "code_context": {
                    "view_code": view_code,
                    "serializer_code": serializer_code,
                    "model_references": model_names,
                },
            }
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(
                    f"A critical error occurred analyzing endpoint {method} {path}: {e}"
                )
            )
            import traceback

            traceback.print_exc()
            return None

    def handle(self, *args, **options):
        self.stdout.write("Starting the documentation generation process...")
        generator = SchemaGenerator()
        current_schema = generator.get_schema(request=None, public=True)
        self.stdout.write("Successfully generated the current OpenAPI schema.")

        doc_schema_path = os.path.join(settings.BASE_DIR, "docs/configs/doc-schema.yaml")
        existing_schema = {}
        try:
            with open(doc_schema_path) as f:
                existing_schema = yaml.safe_load(f)
            self.stdout.write(f"Successfully loaded existing schema from {doc_schema_path}")
        except FileNotFoundError:
            self.stdout.write(
                self.style.WARNING(
                    f"'{doc_schema_path}' not found. Assuming this is the first run."
                )
            )
        except yaml.YAMLError as e:
            self.stderr.write(self.style.ERROR(f"Error parsing '{doc_schema_path}': {e}"))
            return

        current_paths = current_schema.get("paths", {})
        existing_paths = existing_schema.get("paths", {})
        new_endpoints = []

        for path, methods in current_paths.items():
            if path not in existing_paths:
                for method in methods:
                    new_endpoints.append({"method": method.upper(), "path": path})
            else:
                for method in methods:
                    if method not in existing_paths[path]:
                        new_endpoints.append({"method": method.upper(), "path": path})

        if not new_endpoints:
            self.stdout.write(
                self.style.SUCCESS("No new endpoints found. Documentation is up-to-date.")
            )
            return

        self.stdout.write(self.style.NOTICE("Found new endpoints to document:"))
        for endpoint in new_endpoints:
            self.stdout.write(f"- {endpoint['method']} {endpoint['path']}")

        # Build endpoint contexts and model registry
        endpoint_contexts = []
        model_registry = {}
        all_model_references = set()

        for endpoint in new_endpoints:
            context = self._analyze_endpoint(endpoint["method"], endpoint["path"])
            if context:
                endpoint_contexts.append(context)
                # Collect all model references
                for model_name in context["code_context"]["model_references"]:
                    all_model_references.add(model_name)

        # Build model registry with actual model code
        for model_name in all_model_references:
            try:
                app_label, model_class_name = model_name.split(".", 1)
                from django.apps import apps

                model_class = apps.get_model(app_label, model_class_name)
                model_registry[model_name] = inspect.getsource(model_class)
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"Could not get source for model {model_name}: {e}")
                )
                model_registry[model_name] = "Not available."

        if endpoint_contexts:
            # Build final output with model registry
            output = {"models": model_registry, "endpoints": endpoint_contexts}

            output_filename = "ai-doc-input.json"
            with open(output_filename, "w") as f:
                json.dump(output, f, indent=4)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully generated '{output_filename}'"
                    f" with {len(endpoint_contexts)} "
                    f"endpoints and {len(model_registry)} unique models."
                )
            )
            self.stdout.write("Please copy the contents of this file and provide it to the AI.")

        self.stdout.write(self.style.SUCCESS("Process finished."))
