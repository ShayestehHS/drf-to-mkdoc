import logging
from typing import Any

from drf_spectacular.openapi import AutoSchema as SpectacularAutoSchema
from drf_spectacular.plumbing import ComponentRegistry
from rest_framework.viewsets import ViewSetMixin

logger = logging.getLogger(__name__)


def _extract_view_metadata(view, callback, method):
    """Extract metadata from a single view."""
    action = None
    error_message = None
    action_source_info = {}
    serializer_class = None

    try:
        # Create view instance for introspection
        view_instance = view()

        # If this is a ViewSet, determine the action name
        if isinstance(view_instance, ViewSetMixin):
            action = callback.actions.get(method.lower())
            if action:
                view_instance.action = action
                view_instance.request = type("MockRequest", (), {"method": method.upper()})()

        # Try to get serializer class from view instance
        if hasattr(view_instance, "get_serializer_class"):
            try:
                serializer_cls = view_instance.get_serializer_class()
                serializer_class = f"{serializer_cls.__module__}.{serializer_cls.__name__}"
            except Exception as e:
                logger.debug(f"Failed to get serializer from view instance: {e}")

        # Try action-specific serializer if available
        if serializer_class is None and action:
            action_method = getattr(view, action, None)
            if action_method and callable(action_method):
                if hasattr(action_method, "serializer_class"):
                    serializer_cls = action_method.serializer_class
                    serializer_class = f"{serializer_cls.__module__}.{serializer_cls.__name__}"
                elif (
                    hasattr(action_method, "kwargs")
                    and "serializer_class" in action_method.kwargs
                ):
                    serializer_cls = action_method.kwargs["serializer_class"]
                    serializer_class = f"{serializer_cls.__module__}.{serializer_cls.__name__}"

        # Fallback to class-level serializer_class
        if (
            serializer_class is None
            and hasattr(view, "serializer_class")
            and view.serializer_class
        ):
            serializer_cls = view.serializer_class
            serializer_class = f"{serializer_cls.__module__}.{serializer_cls.__name__}"

        # Get action source info if no serializer found
        if serializer_class is None and action:
            action_method = getattr(view, action, None)
            if action_method and callable(action_method):
                action_source_info = {
                    "importable_path": f"{view.__module__}.{view.__name__}.{action}",
                    "module": view.__module__,
                    "class_name": view.__name__,
                    "method_name": action,
                }

    except Exception as e:
        serializer_class = None
        action = None
        error_message = str(e)

    return {
        "view_class": f"{view.__module__}.{view.__name__}",
        "action": action,
        "serializer_class": serializer_class,
        "error_message": str(error_message) if error_message else None,
        "action_source": action_source_info,
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
                callback = self._get_callback_obj()
                metadata = _extract_view_metadata(view, callback, method)

                # Add metadata to the operation
                operation.setdefault("x-metadata", {})
                operation["x-metadata"].update(metadata)
            except Exception:
                # Log the error but don't break schema generation
                logger.exception("Error adding metadata to operation")

        return operation

    def _get_callback_obj(self):
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
            actions = {self.method.lower(): self.view.action}

        # Create a callback-like object with the necessary attributes
        class CallbackObj:
            def __init__(self, view_cls, actions_dict):
                self.cls = view_cls
                self.actions = actions_dict

        return CallbackObj(self.view.__class__, actions)
