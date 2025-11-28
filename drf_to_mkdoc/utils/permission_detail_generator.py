"""Permission detail page generation utilities."""

from pathlib import Path
from typing import Any

from django.template.loader import render_to_string
from django.templatetags.static import static

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings
from drf_to_mkdoc.utils.commons.file_utils import write_file
from drf_to_mkdoc.utils.commons.path_utils import get_permission_url
from drf_to_mkdoc.utils.commons.schema_utils import get_permission_description


def generate_permission_docs(permissions: dict[str, dict[str, Any]]) -> None:
    """
    Generate permission detail pages for all unique permissions.
    
    Args:
        permissions: Dictionary mapping permission class paths to permission data
    """
    for permission_class_path, permission_data in permissions.items():
        # Get descriptions (short and long)
        descriptions = get_permission_description(permission_class_path)
        long_description = descriptions.get("long") or descriptions.get("short")
        short_description = descriptions.get("short")
        
        # Only create page if there's a description
        if not long_description:
            continue
        
        # Create the permission page content
        content = create_permission_page(permission_class_path, long_description, short_description)
        
        # Generate file path: permissions/{full_class_path}/index.md
        url_path = get_permission_url(permission_class_path)
        file_path = f"{url_path}index.md"
        
        write_file(file_path, content)


def create_permission_page(
    permission_class_path: str, long_description: str, short_description: str | None
) -> str:
    """
    Create a permission documentation page.
    
    Args:
        permission_class_path: Full path to permission class
        long_description: Full permission description (shown on detail page)
        short_description: Short permission description (for reference)
    
    Returns:
        Rendered template content
    """
    # Extract display name (class name without module path)
    display_name = permission_class_path.rsplit(".", 1)[-1] if "." in permission_class_path else permission_class_path
    
    stylesheets = [
        static(f"{drf_to_mkdoc_settings.PROJECT_NAME}/stylesheets/endpoints/variables.css"),
        static(f"{drf_to_mkdoc_settings.PROJECT_NAME}/stylesheets/endpoints/base.css"),
    ]
    
    context = {
        "permission_class_path": permission_class_path,
        "display_name": display_name,
        "description": long_description,
        "short_description": short_description,
        "stylesheets": stylesheets,
    }
    
    return render_to_string("permissions/base.html", context)

