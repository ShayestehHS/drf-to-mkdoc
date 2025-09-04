# DRF to MkDocs

Generate beautiful, interactive Markdown API documentation from Django REST Framework OpenAPI schema for MkDocs.

## Why you'll love it

- **Zero-hassle docs**: Beautiful, always-in-sync API docs straight from your codebase
- **Model deep dive**: Auto-generated model pages with fields, relationships, and choices
- **Lightning-fast discovery**: Interactive endpoint index with powerful filters and search
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
    'DEFAULT_SCHEMA_CLASS': 'drf_to_mkdoc.utils.schema.AutoSchema',  # Use our custom AutoSchema
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
}
```

2. **Create MkDocs configuration**:  
   Copy the [`docs/mkdocs.yml`](docs/mkdocs.yml) file to your project root and customize it as needed.

3. **Build documentation**:

```bash
python manage.py build_docs --settings=docs_settings
```

## Available Commands

- `build_docs`: Build the complete documentation site with MkDocs
- `build_endpoint_docs`: Build endpoint documentation from OpenAPI schema
- `build_model_docs`: Build model documentation from model JSON data
- `extract_model_data`: Extract model data from Django model introspection and save as JSON
- `update_doc_schema`: Update the final schema by copying the documented schema

## What you get

See a detailed overview of generated files in `docs/structure.md` and a feature breakdown in `docs/features.md`.


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
│   │       └── update_doc_schema.py    # Schema updates
│   └── utils/
│       ├── common.py        # Shared utilities
│       ├── endpoint_generator.py  # Endpoint documentation
│       ├── model_generator.py     # Model documentation
│       └── extractors/      # Query parameter extraction
├── pyproject.toml           # Project configuration
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
This will ensure that only the source configuration and scripts are versioned, while the generated documentation is excluded.