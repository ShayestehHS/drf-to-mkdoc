# DRF to MkDocs

Unlock effortless API documentation for your Django REST Framework project. Automatically generate beautiful, interactive, and maintainable docs that accelerate developer onboarding and streamline your team's workflow.

---

## Why DRF to MkDocs?

`DRF to MkDocs` bridges the gap between your API's OpenAPI schema and user-friendly, maintainable documentation. It introspects your Django models and DRF views to automatically generate a polished, feature-rich documentation site that stays in sync with your codebase, empowering your team to build better APIs, faster.

-   **Effortless Documentation**: Automate the entire process of generating and updating your API docs. Say goodbye to manual work and outdated information.
-   **Accelerate Onboarding**: Provide new joiners with interactive, easy-to-navigate documentation. The "Try-it-out" feature and clear model relationships help them become productive from day one.
-   **Deeply Integrated with DRF**: Leverages `drf-spectacular` for accurate schema generation, ensuring your documentation is a true reflection of your API.
-   **Enhance Developer Experience**: Features like the interactive API console and in-depth model pages streamline development, testing, and debugging for the entire team.
-   **Beautiful & Professional**: Built on MkDocs with the Material theme for a clean, modern, and responsive UI that you'll be proud to share.

## Gallery

<details>
<summary>🚀 Interactive Endpoint List & Filtering</summary>
<img width="1434" height="943" alt="List-EndPoint" src="https://github.com/user-attachments/assets/f886fc7f-afa0-4faa-b9c2-d6f754ca3597" />
</details>

<details>
<summary>🔬 Detailed Endpoint View with "Try-it-out"</summary>
<img width="958" height="887" alt="Detail-EndPoint" src="https://github.com/user-attachments/assets/9d9e3d4b-cb92-4ece-831e-aef45ceec768" />
<img width="532" height="804" alt="Try-it-out" src="https://github.com/user-attachments/assets/0f483922-60c4-4f62-8fb4-bc7372e82a03" />
</details>

<details>
<summary>📚 Rich Model Documentation</summary>
<img width="906" height="885" alt="Model-fields" src="https://github.com/user-attachments/assets/a1ca369c-ad40-4b05-83ec-ceb1f80aab23" />
<img width="848" height="886" alt="Model" src="https://github.com/user-attachments/assets/683d6d26-a8e4-4c05-8b5f-11a61a62cb0c" />
</details>

<details>
<summary>📈 Entity-Relationship Diagrams</summary>
<img width="953" height="606" alt="ER-Diagram" src="https://github.com/user-attachments/assets/3d0b1cb0-7ebf-4d4a-a181-1b7dbc9c6a01" />
</details>

## Key Features

| Feature                          | Description                                                                                                                              |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| 🚀 **Interactive API Console**     | Test endpoints directly from the documentation with a "Try-it-out" feature, complete with a request builder and response viewer.         |
| 🔍 **Advanced Filtering & Search** | Instantly find endpoints with multi-criteria filtering by app, method, path, and a real-time search.                                   |
| 📚 **In-Depth Model Pages**        | Automatically generate detailed pages for each model, including fields, relationships, choices, and methods.                           |
| 📊 **Entity-Relationship Diagrams** | Visualize model relationships with auto-generated, interactive ER diagrams for each app and for the entire project.                    |
| 🎨 **Modern & Responsive UI**      | A beautiful and intuitive interface powered by MkDocs Material, featuring light/dark themes and full mobile support.                   |
| 🔧 **Highly Customizable**         | Override templates, configure settings, and use custom functions to tailor the documentation to your project's specific needs.         |
| ⚙️ **Simple Integration**         | Works seamlessly with existing DRF projects and `drf-spectacular` without requiring complex setup.                                     |
| 🤖 **AI-Powered Enhancements**     | (Working on it...) Leverage AI to generate smarter examples and more descriptive documentation for your API.                                     |

## Getting Started

### 1. Installation

```bash
pip install drf-to-mkdoc
```

### 2. Configure Your Django Project

In your `settings.py`:

```python
# settings.py

INSTALLED_APPS = [
    # ... your other apps
    'drf_to_mkdoc',
    'drf_spectacular',  # Required for schema generation
]

# Required for OpenAPI schema generation
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_to_mkdoc.utils.schema.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Your API',
    'DESCRIPTION': 'Your API description',
    'VERSION': '1.0.0',
}

# DRF to MkDocs specific settings
DRF_TO_MKDOC = {
    'DJANGO_APPS': [
        'users',
        'products',
        # ... list all apps you want to document
    ],
}
```

### 3. Create MkDocs Configuration

Create an `mkdocs.yml` file in your project root. You can start with the [default configuration](docs/mkdocs.yml) and customize it.

### 4. Build Your Documentation

```bash
python manage.py build_docs
```

For more detailed instructions, see the full [Installation and Setup Guide](docs/installation.md).

## Usage and Customization

### Building Your Documentation

To build the entire documentation site, run the following command. This will generate a static site in your `site/` directory.

```bash
python manage.py build_docs
```

For more granular control, `DRF to MkDocs` provides several commands, such as `build_endpoint_docs` and `build_model_docs`.

### Serving Docs with Django

You can serve your documentation directly from your Django application, protecting it with Django's authentication system. This is ideal for private or internal APIs.

For a complete guide, see [Serving Docs with Django](docs/serving_docs_with_django.md).

### Customizing the OpenAPI Schema

`DRF to MkDocs` allows you to override and extend the auto-generated OpenAPI schema by providing a custom JSON file. This gives you fine-grained control over the final documentation, enabling you to add examples, descriptions, or even custom endpoints.

For more details, refer to the [Customizing Endpoints](docs/customizing_endpoints.md) guide.

### Best Practices

For better project organization, we recommend creating a separate `docs_settings.py` for documentation-specific configurations and using the `--settings` flag:

```bash
python manage.py build_docs --settings=my_project.docs_settings
```

This keeps your production settings clean and your documentation configuration isolated.

## Configuration

You can customize the behavior of `DRF to MkDocs` by configuring the `DRF_TO_MKDOC` dictionary in your settings file.

| Key                              | Description                                                                    | Default                               |
| -------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------- |
| `DJANGO_APPS` (required)         | A list of Django app names to process.                                         | `[]`                                  |
| `DOCS_DIR`                       | The base directory where documentation will be generated.                      | `'docs'`                              |
| `ER_DIAGRAMS_DIR`                | The directory for ER diagrams, relative to `DOCS_DIR`.                         | `'er_diagrams'`                       |
| `FIELD_GENERATORS`               | Custom field value generators for creating better examples.                    | `{}`                                  |
| `ENABLE_AI_DOCS`                 | A flag to enable AI-powered documentation features.                            | `False`                               |
| `PATH_PARAM_SUBSTITUTE_FUNCTION` | A custom function for substituting path parameters in URLs.                    | `None`                                |
| `PATH_PARAM_SUBSTITUTE_MAPPING`  | A mapping for substituting common path parameters (e.g., `{'pk': 1}`).        | `{}`                                  |

## How It Works

`DRF to MkDocs` operates in a few stages:

1.  **Model Introspection**: It deeply analyzes your Django models, mapping out their fields, relationships (like ForeignKeys and ManyToManyFields), and metadata.
2.  **Schema Generation**: It uses `drf-spectacular` to generate a detailed OpenAPI schema for your API endpoints.
3.  **Template Rendering**: It renders Jinja2 templates for each endpoint, model, and ER diagram, creating Markdown files.
4.  **MkDocs Build**: Finally, it invokes MkDocs to build a static HTML site from the generated Markdown files.

This process ensures that your documentation is always an accurate and comprehensive reflection of your codebase.

## Contributing

Contributions are welcome! Whether it's a bug report, a new feature, or an improvement to the documentation, we appreciate your help. To ensure code quality, we use **CoderabbitAI** for automated code reviews on all pull requests.

Please see our [Contributing Guidelines](CONTRIBUTING.md) to get started.

### Development Setup

```bash
git clone https://github.com/Shayestehhs/drf-to-mkdoc.git
cd drf-to-mkdoc
pip install -e ".[dev]"
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
