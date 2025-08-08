from typing import Any


def _md_query_parameters_format_error_section(query_params: dict[str, Any]) -> str:
    if "error" in query_params:
        return f"**Error:** {query_params['error']}\n\n"
    return ""


def _md_query_parameters_format_search_section(query_params: dict[str, Any]) -> str:
    search_fields = query_params.get("search_fields", [])
    if search_fields:
        content = "### Search Parameters\n\n"
        for field in search_fields:
            content += f"- `{field}`\n"
        content += "\n"
        return content
    return ""


def _md_query_parameters_format_filter_section(query_params: dict[str, Any]) -> str:
    filter_fields = query_params.get("filter_fields", [])
    if filter_fields:
        content = "### Filter Parameters\n\n"
        for field in filter_fields:
            content += f"- `{field}`\n"
        content += "\n"
        return content
    return ""


def _md_query_parameters_format_ordering_section(query_params: dict[str, Any]) -> str:
    ordering_fields = query_params.get("ordering_fields", [])
    if ordering_fields:
        content = "### Ordering Parameters\n\n"
        for field in ordering_fields:
            content += f"- `{field}`\n"
        content += "\n"
        return content
    return ""


def _md_query_parameters_format_pagination_section(query_params: dict[str, Any]) -> str:
    pagination_fields = query_params.get("pagination_fields", [])
    if pagination_fields:
        content = "### Pagination Parameters\n\n"
        for field in pagination_fields:
            content += f"- `{field}`\n"
        content += "\n"
        return content
    return ""


def _md_query_parameters_format_filter_backends_section(query_params: dict[str, Any]) -> str:
    filter_backends = query_params.get("filter_backends", [])
    if filter_backends:
        return f"**Filter Backends:** {', '.join(filter_backends)}\n\n"
    return ""


def generate_query_parameters_md(query_params: dict[str, Any]) -> str:
    """Format query parameters into markdown documentation"""
    if "error" in query_params:
        return _md_query_parameters_format_error_section(query_params)

    content = ""
    content += _md_query_parameters_format_search_section(query_params)
    content += _md_query_parameters_format_filter_section(query_params)
    content += _md_query_parameters_format_ordering_section(query_params)
    content += _md_query_parameters_format_pagination_section(query_params)
    content += _md_query_parameters_format_filter_backends_section(query_params)
    return content
