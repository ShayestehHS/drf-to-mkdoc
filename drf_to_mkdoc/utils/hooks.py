import logging

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


def add_view_metadata(result, generator, **_kwargs):
    """
    Postprocessing hook to add view metadata, action name, and serializer class
    for each operation in the generated OpenAPI schema.
    Handles action-specific serializer classes from @action decorator.
    """
    endpoint_map = {}  # {(path, method): {"view": view, "callback": callback, ...}}

    for path, _path_regex, method, callback in generator.endpoints:
        view = callback.cls  # actual view class
        metadata = _extract_view_metadata(view, callback, method)
        endpoint_map[(path, method.lower())] = metadata

    # Apply metadata to OpenAPI operations
    for path, path_item in result.get("paths", {}).items():
        for method, operation in path_item.items():
            # Skip non-operation items (like 'parameters', 'summary', etc.)
            if method.lower() not in [
                "get",
                "post",
                "put",
                "patch",
                "delete",
                "head",
                "options",
            ]:
                continue

            meta = endpoint_map.get((path, method.lower()))
            if not meta:
                continue

            operation.setdefault("x-metadata", {})
            operation["x-metadata"].update(meta)

    return result
