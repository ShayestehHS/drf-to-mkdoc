from typing import Any

from drf_to_mkdoc.utils.commons.operation_utils import extract_viewset_from_operation_id


def extract_query_parameters_from_view(operation_id: str) -> dict[str, Any]:
    """Extract query parameters from a Django view class"""
    view_class = extract_viewset_from_operation_id(operation_id)
    if not view_class:
        return {
            "search_fields": [],
            "filter_fields": [],
            "ordering_fields": [],
            "pagination_fields": [],
        }

    return {
        "search_fields": extract_query_parameters_from_view_search_fields(view_class),
        "filter_fields": extract_query_parameters_from_view_filter_fields(view_class),
        "ordering_fields": extract_query_parameters_from_view_ordering_fields(view_class),
        "pagination_fields": extract_query_parameters_from_view_pagination_fields(view_class),
    }


def extract_query_parameters_from_view_search_fields(view_class: Any) -> list[str]:
    """Extract search fields from a Django view class"""
    if not view_class:
        return []

    search_fields = []
    if hasattr(view_class, "search_fields") and view_class.search_fields:
        search_fields = sorted(view_class.search_fields)

    return search_fields


def extract_query_parameters_from_view_filter_fields(view_class: Any) -> list[str]:
    """Extract filter fields from a Django view class"""
    if not view_class:
        return []

    filter_fields = []
    if hasattr(view_class, "filterset_class"):
        filter_fields = extract_filterset_fields(view_class.filterset_class)
    elif hasattr(view_class, "filterset_fields") and view_class.filterset_fields:
        filter_fields = sorted(view_class.filterset_fields)

    return list(set(filter_fields))


def extract_query_parameters_from_view_ordering_fields(view_class: Any) -> list[str]:
    """Extract ordering fields from a Django view class"""
    if not view_class:
        return []

    ordering_fields = []
    if hasattr(view_class, "ordering_fields") and view_class.ordering_fields:
        ordering_fields = sorted(view_class.ordering_fields)

    return ordering_fields


def extract_query_parameters_from_view_pagination_fields(view_class: Any) -> list[str]:
    """Extract pagination fields from a Django view class"""
    if not view_class:
        return []

    pagination_fields = []
    if hasattr(view_class, "pagination_class") and view_class.pagination_class:
        pagination_class = view_class.pagination_class
        if hasattr(pagination_class, "get_schema_fields"):
            try:
                # Get pagination fields from the pagination class
                schema_fields = pagination_class().get_schema_fields(view_class())
                pagination_fields = sorted([field.name for field in schema_fields])
            except Exception as e:
                # Check if it's specifically the coreapi missing error
                if "coreapi must be installed" in str(e):
                    raise ValueError(
                        "coreapi is required for pagination schema extraction. "
                        "Install it with: pip install coreapi"
                    ) from e
                raise ValueError(
                    "Failed to get schema fields from pagination class "
                    f"{pagination_class.__name__}: {e}"
                ) from e
        else:
            raise ValueError(
                f"Pagination class {pagination_class.__name__} "
                "must implement get_schema_fields() method"
            )

    return pagination_fields


def _extract_filterset_fields_from_class_attributes(filterset_class: Any) -> list[str]:
    try:
        import django_filters  # noqa: PLC0415
    except ImportError:
        # django_filters not available, skip this strategy
        return []

    fields = []
    # Get all class attributes, including inherited ones
    for attr_name in dir(filterset_class):
        # Skip private attributes and known non-filter attributes
        if attr_name.startswith("_") or attr_name in [
            "Meta",
            "form",
            "queryset",
            "request",
            "errors",
            "qs",
            "is_valid",
        ]:
            continue

        try:
            attr = getattr(filterset_class, attr_name)
            if isinstance(attr, django_filters.Filter):
                if attr_name not in fields:
                    fields.append(attr_name)
        except (AttributeError, TypeError):
            continue
    return fields


def _extract_filterset_fields_from_meta(filterset_class: Any) -> list[str]:
    fields = []

    if hasattr(filterset_class, "Meta") and hasattr(filterset_class.Meta, "fields"):
        meta_fields = filterset_class.Meta.fields
        if isinstance(meta_fields, list | tuple):
            # List/tuple format: ['field1', 'field2']
            for field in meta_fields:
                if field not in fields:
                    fields.append(field)
        elif isinstance(meta_fields, dict):
            # Dictionary format: {'field1': ['exact'], 'field2': ['icontains']}
            for field in meta_fields:
                if field not in fields:
                    fields.append(field)

    return fields


def _extract_filterset_fields_from_internal_attrs(filterset_class: Any) -> list[str]:
    fields = []

    # Use Django's internal FilterSet attributes as fallback
    # This handles cases where the above strategies might miss some filters
    for internal_attr in ["declared_filters", "base_filters"]:
        if hasattr(filterset_class, internal_attr):
            try:
                internal_filters = getattr(filterset_class, internal_attr)
                if hasattr(internal_filters, "keys"):
                    for field in internal_filters:
                        if field not in fields:
                            fields.append(field)
            except (AttributeError, TypeError):
                continue

    return fields


def _extract_filterset_fields_from_get_fields(filterset_class: Any) -> list[str]:
    meta = getattr(filterset_class, "_meta", None)
    if not getattr(meta, "model", None):
        # If the Meta class is not defined in the Filter class,
        # the get_fields function is raise error
        return []

    # Try get_fields() method if available (for dynamic filters)
    if not hasattr(filterset_class, "get_fields"):
        return []

    try:
        filterset_instance = filterset_class()
    except TypeError:
        # Constructor requires args; skip dynamic field discovery
        return []

    filterset_fields = filterset_instance.get_fields()
    if not (filterset_fields and hasattr(filterset_fields, "keys")):
        return []

    return list(set(filterset_fields))


def extract_filterset_fields(filterset_class: Any) -> list[str]:
    """Extract field names from a Django FilterSet class

    This function uses multiple strategies to comprehensively detect all filter fields:
    1. Check class attributes for django_filters.Filter instances (declared filters)
    2. Check Meta.fields (both dict and list formats)
    3. Use Django's internal declared_filters and base_filters as fallback
    4. Handle edge cases and inheritance
    """
    if not filterset_class:
        return []

    fields = []

    # Strategy 1: Check class attributes for Filter instances
    fields.extend(_extract_filterset_fields_from_class_attributes(filterset_class))

    # Strategy 2: Check Meta.fields (handles both dict and list formats)
    fields.extend(_extract_filterset_fields_from_meta(filterset_class))

    # Strategy 3: Use Django's internal FilterSet attributes as fallback
    fields.extend(_extract_filterset_fields_from_internal_attrs(filterset_class))

    # Strategy 4: Try get_fields() method if available (for dynamic filters)
    fields.extend(_extract_filterset_fields_from_get_fields(filterset_class))

    return sorted(fields)
