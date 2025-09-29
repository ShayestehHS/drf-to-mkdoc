# Serving MkDocs with Django

This guide explains how to serve your generated MkDocs documentation directly from your Django application, allowing you to protect it with Django's authentication system.

## 1. Add Views to Your Project

First, create a `views.py` file in your main project directory (the same directory as `settings.py` and `urls.py`) if one doesn't already exist. Then, add the following code to handle serving the static documentation files.

```python
# your_project/views.py

import mimetypes
from pathlib import Path

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views import View

@staff_member_required
def documentation_root(request):
    """Redirects the root documentation URL to index.html."""
    return HttpResponseRedirect("index.html")

@method_decorator(staff_member_required, name="dispatch")
class DocumentationView(View):
    """
    Serves static files from the MkDocs `site` directory.
    This view is protected by staff_member_required.
    """

    def get(self, request, path):
        # The base directory where MkDocs builds the site
        site_dir = Path(settings.BASE_DIR) / "site"

        # If no path is specified, default to index.html
        if not path:
            path = "index.html"
        # If the path is a directory, append index.html
        elif not Path(path).suffix:
            path = path.rstrip("/") + "/index.html"

        # Security check: prevent directory traversal attacks
        if ".." in path or path.startswith("/"):
            raise Http404("Invalid path specified.")

        # Construct the full file path
        file_path = site_dir / path

        # Ensure the requested file exists and is within the site directory
        try:
            # Resolve paths to prevent symbolic link traversal
            file_path = file_path.resolve()
            site_dir = site_dir.resolve()

            if not str(file_path).startswith(str(site_dir)):
                raise Http404("Access denied.")

            if not file_path.exists() or not file_path.is_file():
                raise Http404("Documentation file not found.")

        except (OSError, ValueError):
            raise Http404("Invalid file path.")

        # Guess the content type of the file
        content_type, _ = mimetypes.guess_type(str(file_path))
        if content_type is None:
            content_type = "application/octet-stream"

        # Open and serve the file
        try:
            with file_path.open("rb") as f:
                response = HttpResponse(f.read(), content_type=content_type)
        except OSError:
            raise Http404("Could not read documentation file.")
        
        return response
```

## 2. Update Your Project's URLs

Next, open your project's root `urls.py` file to integrate the documentation views.

```python
# your_project/urls.py

from django.urls import path, re_path, include
from . import views  # Import the views.py you just created

# Define the URL patterns for the documentation
docs_urlpatterns = [
    path("", views.documentation_root, name="root"),
    re_path(r"^(?P<path>.*)$", views.DocumentationView.as_view(), name="documentation"),
]

urlpatterns = [
    # ... your other admin and app URLs
    path("docs/", include((docs_urlpatterns, "docs"), namespace="docs")),
]
```

## 3. Build and Serve

With the views and URLs configured, the process to build and serve your documentation is straightforward:

1.  **Build the docs**:
    ```bash
    python manage.py build_docs
    ```
    This will generate the static site in the `site/` directory.

2.  **Run the Django server**:
    ```bash
    python manage.py runserver
    ```

Now, you can navigate to `/docs/` in your browser. If you are logged in as a staff user, you will see your documentation. Otherwise, you'll be redirected to the Django admin login page.
