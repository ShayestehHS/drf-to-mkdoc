DEFAULTS = {
    # Path configurations with defaults
    "DOCS_DIR": "docs",  # Directory where docs will be generated
    "CONFIG_DIR": "docs/configs",  # Directory for configuration files
    "MODEL_DOCS_FILE": "docs/model-docs.json",  # Path to model documentation JSON file
    "DOC_CONFIG_FILE": "docs/configs/doc_config.json",  # Path to documentation configuration file
    "CUSTOM_SCHEMA_FILE": "docs/configs/custom_schema.json",  # Path to custom schema file
    "PATH_PARAM_SUBSTITUTE_FUNCTION": None,
    "PATH_PARAM_SUBSTITUTE_MAPPING": {},
    "FIELD_GENERATORS": {},
    # AI documentation settings
    "ENABLE_AI_DOCS": False,
    "AI_CONFIG_DIR_NAME": "ai_code",  # Directory name for AI-generated code files
    "AI_OPERATION_MAP_FILE": "docs/configs/operation_map.json",  # Path to operation map file
    "SERIALIZERS_INHERITANCE_DEPTH": 1,  # Maximum depth for class inheritance analysis
    # Django apps - required, no default
    "DJANGO_APPS": None,  # List of Django app names to process
}
