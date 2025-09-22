# DRF to MkDocs

Generate beautiful, interactive Markdown API documentation from Django REST Framework OpenAPI schema for MkDocs.

## Why you'll love it

- **Zero-hassle docs**: Beautiful, always-in-sync API docs straight from your codebase
- **Model deep dive**: Auto-generated model pages with fields, relationships, and choices
- **Lightning-fast discovery**: Interactive endpoint index with powerful filters and search
- **Try-it-out**: Interactive API testing directly in the documentation with request/response examples
- **AI-powered**: Optional AI-generated documentation with custom field generators(Wait for it...)
- **DRF-native**: Works with DRF Spectacular; no custom schema wiring needed
- **MkDocs Material**: Looks great out of the box with the Material theme

## Installation

See the full installation guide in `docs/installation.md`.

## Quick Start

1. **Configure your Django project**:

```python
# settings.py
INSTALLED_APPS = [
    # ... your other apps
    'drf_to_mkdoc',
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

DRF_TO_MKDOC = {
    'DJANGO_APPS': [
        'users',
        'products',
        'orders',
        'inventory',
    ],
    # Optional: Override default paths
    # 'DOCS_DIR': 'docs',
    # 'CONFIG_DIR': 'docs/configs',
    # 'MODEL_DOCS_FILE': 'docs/model-docs.json',
    # 'DOC_CONFIG_FILE': 'docs/configs/doc_config.json',
    # 'CUSTOM_SCHEMA_FILE': 'docs/configs/custom_schema.json',
    # 'FIELD_GENERATORS': {
    #     'email': 'faker.email',
    #     'name': 'faker.name',
    #     'created_at': 'datetime.now',
    # },
    # 'ENABLE_AI_DOCS': False,
}
```

2. **Create MkDocs configuration**:  
   Copy the [`docs/mkdocs.yml`](docs/mkdocs.yml) file to your project root and customize it as needed.

3. **Build documentation**:

```bash
python manage.py build_docs --settings=docs_settings
```

### Configuration Options

The `DRF_TO_MKDOC` setting supports several configuration options:

- **`DJANGO_APPS`** (required): List of Django app names to process
- **`DOCS_DIR`**: Directory where docs will be generated (default: `docs`)
- **`CONFIG_DIR`**: Directory for configuration files (default: `docs/configs`)
- **`FIELD_GENERATORS`**: Custom field value generators for better examples
- **`ENABLE_AI_DOCS`**: Enable AI-powered documentation features (default: `False`)
- **`PATH_PARAM_SUBSTITUTE_FUNCTION`**: Custom function for path parameter substitution
- **`PATH_PARAM_SUBSTITUTE_MAPPING`**: Mapping for path parameter substitution

## Available Commands

- `build_docs`: Build the complete documentation site with MkDocs
- `build_endpoint_docs`: Build endpoint documentation from OpenAPI schema
- `build_model_docs`: Build model documentation from model JSON data
- `extract_model_data`: Extract model data from Django model introspection and save as JSON
- `generate_doc_json`: Generate JSON context for new API endpoints to be documented
- `update_doc_schema`: Update the final schema by copying the documented schema

## What you get

See a detailed overview of generated files in `docs/structure.md` and a feature breakdown in `docs/features.md`.

## Key Features

### 🚀 Interactive API Testing (Try-Out)
- **Live API testing**: Test endpoints directly from the documentation
- **Request builder**: Interactive forms for parameters, headers, and request body
- **Response viewer**: Real-time response display with syntax highlighting
- **Floating action button**: Easy access to testing interface
- **Multiple examples**: Support for both empty and populated response examples

### 🤖 AI-Powered Documentation
- **Custom field generators**: Define custom value generators for specific fields
- **AI documentation**: Optional AI-generated documentation with context analysis
- **Smart examples**: Enhanced example generation for better API understanding

### 📊 Advanced Filtering & Search
- **Multi-criteria filtering**: Filter by app, HTTP method, path, and search terms
- **Real-time search**: Instant search across all endpoints
- **Smart suggestions**: Auto-complete for query parameters and field names

### 🎨 Beautiful UI
- **Material Design**: Modern, responsive interface with dark/light themes
- **Interactive elements**: Hover effects, animations, and smooth transitions
- **Mobile-friendly**: Fully responsive design for all devices

## How it works

Under the hood, drf-to-mkdoc introspects your models and reads your DRF OpenAPI schema to generate clean, organized Markdown. Then MkDocs turns it into a polished static site. Always current, no manual updates.

## Explore more

- Customizing endpoint docs: `docs/customizing_endpoints.md`
- Serving docs through Django (with permissions): `docs/serving_mkdocs_with_django.md`

## Dependencies

- Django >= 3.2, < 6.0
- Django REST Framework >= 3.12, < 4.0
- drf-spectacular >= 0.26.0
- PyYAML >= 6.0
- MkDocs >= 1.4.0
- MkDocs Material >= 9.0.0
- coreapi >= 2.3.0

## Development

### Setup Development Environment

```bash
git clone https://github.com/Shayestehhs/drf-to-mkdoc.git
cd drf-to-mkdoc
pip install -e ".[dev]"
```

## Project Structure

```
drf-to-mkdoc/
├── drf_to_mkdoc/
│   ├── conf/
│   │   ├── defaults.py      # Default configuration values
│   │   └── settings.py      # Settings management
│   ├── management/
│   │   └── commands/
│   │       ├── build_docs.py           # Build MkDocs site
│   │       ├── build_endpoint_docs.py  # Build endpoint documentation
│   │       ├── build_model_docs.py     # Build model documentation
│   │       ├── extract_model_data.py   # Extract model data from Django
│   │       ├── generate_doc_json.py    # Generate JSON context for AI docs
│   │       └── update_doc_schema.py    # Schema updates
│   ├── static/
│   │   └── drf-to-mkdoc/
│   │       ├── javascripts/
│   │       │   ├── try-out/            # Interactive API testing
│   │       │   └── endpoints-filter.js # Endpoint filtering
│   │       └── stylesheets/            # CSS for styling
│   ├── templates/
│   │   ├── endpoints/                  # Endpoint documentation templates
│   │   ├── model_detail/               # Model documentation templates
│   │   └── try-out/                    # Interactive testing templates
│   └── utils/
│       ├── ai_tools/                   # AI-powered documentation features
│       ├── commons/                    # Shared utilities
│       ├── extractors/                 # Query parameter extraction
│       ├── endpoint_detail_generator.py
│       ├── endpoint_list_generator.py
│       ├── model_detail_generator.py
│       ├── model_list_generator.py
│       └── schema.py
├── docs/                      # Generated documentation
├── pyproject.toml            # Project configuration
└── README.md
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Recommendations

### .gitignore Configuration

To avoid committing generated files to your repository, add the following to your `.gitignore` file:

```gitignore
# Documentation
/docs/endpoints/
/docs/models/
/docs/configs/doc-schema.yaml

# Build artifacts
/site/
```

This will ensure that only the source configuration and scripts are versioned, while the generated documentation is excluded.

### docs_settings.py Best Practices

Create a separate `docs_settings.py` file that inherits from your main settings:

```python
# docs_settings.py
from .settings import *

DRF_TO_MKDOC = {
    'DJANGO_APPS': ['your_app1', 'your_app2'],
}
# Other doc settings...
```

Then use the `--settings` argument when running the build command:

```bash
python manage.py build_docs --settings=docs_settings
```

### Project Organization

```
your-project/
├── settings.py          # Main Django settings
├── docs_settings.py     # Documentation-specific settings
├── mkdocs.yml          # MkDocs configuration
├── docs/               # Generated documentation (gitignored)
└── site/               # Built site (gitignored)
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.