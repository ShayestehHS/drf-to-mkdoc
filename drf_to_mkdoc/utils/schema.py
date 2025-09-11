import inspect
import logging
from importlib import import_module
from types import SimpleNamespace
from typing import Any

from drf_spectacular.openapi import AutoSchema as SpectacularAutoSchema
from drf_spectacular.plumbing import ComponentRegistry
from rest_framework.serializers import BaseSerializer, ListSerializer
from rest_framework.viewsets import ViewSetMixin

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings

logger = logging.getLogger(__name__)


class ViewMetadataExtractor:
    """Extracts metadata from DRF views."""

    def __init__(self, view, callback, method):
        self.view = view
        self.callback = callback
        self.method = method
        self.view_instance = None
        self.action = None
        self.error_message = None

    def _create_view_instance(self):
        """Create view instance for introspection."""
        try:
            self.view_instance = self.view()
        except (TypeError, AttributeError, ImportError) as e:
            self.error_message = str(e)
            return False
        else:
            return True

    def _extract_permissions(self):
        """Extract permission classes from view."""
        permission_classes = []
        if hasattr(self.view, "permission_classes"):
            for perm_class in self.view.permission_classes:
                permission_classes.append(f"{perm_class.__module__}.{perm_class.__name__}")
        return permission_classes

    def _extract_action(self):
        """Extract action name from ViewSet."""
        if isinstance(self.view_instance, ViewSetMixin):
            self.action = self.callback.actions.get(self.method.lower())
            if self.action:
                self.view_instance.action = self.action
                self.view_instance.request = SimpleNamespace(method=self.method.upper())

    def _extract_serializer_from_view_instance(self):
        """Try to get serializer class from view instance."""
        if not hasattr(self.view_instance, "get_serializer_class"):
            return None

        try:
            serializer_cls = self.view_instance.get_serializer_class()
        except Exception as e:
            logger.debug(f"Failed to get serializer from view instance: {e}")
            return None
        else:
            return f"{serializer_cls.__module__}.{serializer_cls.__name__}"

    def _extract_serializer_from_action(self):
        """Try to get serializer class from action method."""
        if not self.action:
            return None

        action_method = getattr(self.view, self.action, None)
        if not (action_method and callable(action_method)):
            return None

        if hasattr(action_method, "serializer_class"):
            serializer_cls = action_method.serializer_class
            return f"{serializer_cls.__module__}.{serializer_cls.__name__}"
        if hasattr(action_method, "kwargs") and "serializer_class" in action_method.kwargs:
            serializer_cls = action_method.kwargs["serializer_class"]
            return f"{serializer_cls.__module__}.{serializer_cls.__name__}"

        return None

    def _extract_serializer_from_class(self):
        """Try to get serializer class from view class."""
        if hasattr(self.view, "serializer_class") and self.view.serializer_class:
            serializer_cls = self.view.serializer_class
            return f"{serializer_cls.__module__}.{serializer_cls.__name__}"
        return None

    def _extract_action_source(self):
        """Get action source info if no serializer found."""
        if not self.action:
            return {}

        action_method = getattr(self.view, self.action, None)
        if not (action_method and callable(action_method)):
            return {}

        return {
            "importable_path": f"{self.view.__module__}.{self.view.__name__}.{self.action}",
            "module": self.view.__module__,
            "class_name": self.view.__name__,
            "method_name": self.action,
        }

    def _extract_serializer_parents(self, serializer_cls):
        """Extract parent classes of serializer up to specified depth."""
        if not serializer_cls:
            return []

        parents = []
        for base in inspect.getmro(serializer_cls)[
            1 : drf_to_mkdoc_settings.SERIALIZERS_INHERITANCE_DEPTH + 1
        ]:
            if base is object or base.__module__ == "builtins":
                continue
            parents.append(f"{base.__module__}.{base.__name__}")

        return parents

    def _extract_serializer_attrs(self, serializer_cls):
        """Extract nested serializer attributes up to specified depth."""
        if not serializer_cls:
            return {}

        attrs = {}
        try:
            serializer_instance = serializer_cls()
            for field_name, field in getattr(serializer_instance, "fields", {}).items():
                if isinstance(field, ListSerializer) and isinstance(
                    field.child, BaseSerializer
                ):
                    # Handle ListSerializer and similar fields
                    child_class = field.child.__class__
                    attrs[field_name] = {
                        "type": "list",
                        "child_serializer": f"{child_class.__module__}.{child_class.__name__}",
                    }
                elif isinstance(field, BaseSerializer):
                    # Handle nested serializers
                    nested_class = field.__class__
                    attrs[field_name] = {
                        "type": "nested",
                        "serializer": f"{nested_class.__module__}.{nested_class.__name__}",
                    }
        except (TypeError, AttributeError) as e:
            logger.debug(f"Failed to extract serializer attributes: {e}")

        return attrs

    def extract(self):
        """Extract all metadata from view."""
        if not self._create_view_instance():
            return {
                "view_class": f"{self.view.__module__}.{self.view.__name__}",
                "action": None,
                "serializer_class": None,
                "permission_classes": [],
                "error_message": str(self.error_message),
                "action_source": {},
                "serializer_parents": [],
                "serializer_attrs": {},
            }

        permission_classes = self._extract_permissions()
        self._extract_action()

        serializer_class = None
        serializer_class_str = (
            self._extract_serializer_from_view_instance()
            or self._extract_serializer_from_action()
            or self._extract_serializer_from_class()
        )

        if serializer_class_str:
            module_name, class_name = serializer_class_str.rsplit(".", 1)
            try:
                module = import_module(module_name)
                serializer_class = getattr(module, class_name)
            except (ImportError, AttributeError) as e:
                logger.debug(f"Failed to import serializer class: {e}")

        action_source = {} if serializer_class_str else self._extract_action_source()
        serializer_parents = (
            self._extract_serializer_parents(serializer_class) if serializer_class else []
        )
        serializer_attrs = (
            self._extract_serializer_attrs(serializer_class) if serializer_class else {}
        )

        return {
            "view_class": f"{self.view.__module__}.{self.view.__name__}",
            "action": self.action,
            "serializer_class": serializer_class_str,
            "permission_classes": permission_classes,
            "error_message": str(self.error_message) if self.error_message else None,
            "action_source": action_source,
            "serializer_parents": serializer_parents,
            "serializer_attrs": serializer_attrs,
        }


class AutoSchema(SpectacularAutoSchema):
    """
    Custom AutoSchema that extends drf_spectacular's AutoSchema to add view metadata
    directly to the operation during schema generation instead of using a postprocessing hook.
    """

    def get_operation(
        self,
        path: str,
        path_regex: str,
        path_prefix: str,
        method: str,
        registry: ComponentRegistry,
    ) -> dict[str, Any] | None:
        # Call the parent's get_operation to get the base operation
        operation = super().get_operation(path, path_regex, path_prefix, method, registry)

        if operation:
            try:
                # Extract metadata from the view
                view = self.view.__class__
                callback = self._get_callback_obj(method)
                metadata = ViewMetadataExtractor(view, callback, method).extract()

                # Add metadata to the operation
                operation.setdefault("x-metadata", {})
                operation["x-metadata"].update(metadata)
            except Exception:
                # Log the error but don't break schema generation
                logger.exception("Error adding metadata to operation")

        return operation

    def _get_callback_obj(self, method: str):
        """
        Helper method to get the callback object with actions.
        This is needed to extract the action name from the callback.
        """
        # Access the view's action_map or action to determine the mapping
        actions = {}

        # For ViewSets, the action_map contains the method->action mapping
        if hasattr(self.view, "action_map") and self.view.action_map is not None:
            actions = {m.lower(): a for m, a in self.view.action_map.items()}
        # For APIViews with an explicit action
        elif hasattr(self.view, "action"):
            actions = {method.lower(): self.view.action}

        # Create a callback-like object with the necessary attributes
        class CallbackObj:
            def __init__(self, view_cls, actions_dict):
                self.cls = view_cls
                self.actions = actions_dict

        return CallbackObj(self.view.__class__, actions)
