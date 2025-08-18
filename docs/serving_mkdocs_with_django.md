# Serving MkDocs Docs with Django (with Permissions)

This guide shows how to serve the built MkDocs site from your Django app while enforcing access control (e.g., staff-only).

## Prerequisites

1) Build the docs so the static site exists under `site/` at your project root:
```bash
python manage.py build_docs --settings=docs_settings
```
2) Ensure `site/` is gitignored (see README recommendations).

## URL routes

```python
# urls.py
from django.urls import path, re_path
from . import views

urlpatterns = [
    # Root of docs (redirect to index.html)
    path("", views.documentation_root, name="docs_root"),
    # Serve any file under the built MkDocs site directory
    re_path(r"^(?P<path>.*)$", views.DocumentationView.as_view(), name="docs_serve"),
]
```

## Views with staff-only access

```python
# views.py
import mimetypes
from pathlib import Path

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views import View


@staff_member_required
def documentation_root(request):
    """Redirect root documentation URL to index.html"""
    return HttpResponseRedirect("/docs/index.html")


@method_decorator(staff_member_required, name="dispatch")
class DocumentationView(View):
    """
    Serve static files from the MkDocs site directory.
    Requires staff authentication for security.
    """

    def get(self, request, path):
        site_dir = Path(settings.BASE_DIR) / "site"

        if not path or path == "/":
            path = "index.html"
        elif not Path(path).suffix:
            path = path.rstrip("/") + "/index.html"

        # Basic traversal protections
        if ".." in path or path.startswith("/"):
            raise Http404("Invalid path")

        file_path = (site_dir / path).resolve()

        # Ensure the file exists and is within the site directory
        try:
            file_path = file_path.resolve()
            site_dir = site_dir.resolve()

            # Security check: ensure file is within site directory
            if not str(file_path).startswith(str(site_dir)):
                return HttpResponseRedirect("/docs/404/index.html?error=access_denied")

            if not file_path.exists() or not file_path.is_file():
                return HttpResponseRedirect("/docs/404/index.html")

        except (OSError, ValueError) as e:
                return HttpResponseRedirect("/docs/404/index.html?error=invalid_file_path")

        # Determine content type
        content_type, _ = mimetypes.guess_type(str(file_path))
        if content_type is None:
            content_type = "application/octet-stream"

        # Read and serve the file
        try:
            with Path(file_path).open("rb") as f:
                response = HttpResponse(f.read(), content_type=content_type)

            # Set appropriate headers
            if content_type.startswith("text/html"):
                response["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response["Pragma"] = "no-cache"
                response["Expires"] = "0"
            else:
                response["Cache-Control"] = "public, max-age=3600"

        except OSError as e:
            return HttpResponseRedirect("/docs/404/index.html?error=could_not_read_file")
        else:
            return response

```

## Permission options

- Staff-only: `@staff_member_required` (shown above)
- Logged-in users: `@login_required`
- Custom rule: `@user_passes_test(lambda u: u.has_perm("yourapp.view_docs"))`
- Per-group/role: check `request.user.groups` or a custom permission class

Choose the decorator that matches your policy and apply it to both the root view and the class-based view (`name="dispatch"`).

## Notes

- Not recommended for production: serving static files with Django is generally a bad practice. Prefer a real static server (e.g., Nginx), reverse proxy, or object storage/CDN.
- Paths are resolved against `BASE_DIR / "site"` to match `mkdocs build` output.
- Directory traversal is blocked (no `..`, no absolute paths), and resolution is re-checked.
- HTML responses disable caching; other assets get short-lived caching by default.
- For production, front this with a reverse proxy or serve from object storage/CDN; the above example is best for admin-only internal access.