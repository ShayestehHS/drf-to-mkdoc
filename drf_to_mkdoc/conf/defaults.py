DEFAULTS = {
    # Path configurations with defaults
    "DOCS_DIR": "docs",  # Directory where docs will be generated
    "CONFIG_DIR": "docs/configs",  # Directory for configuration files
    "ER_DIAGRAMS_DIR": "er_diagrams",  # Directory for ER diagrams (relative to DOCS_DIR)
    "MODEL_DOCS_FILE": "docs/model-docs.json",  # Path to model documentation JSON file
    "DOC_CONFIG_FILE": "docs/configs/doc_config.json",  # Path to documentation configuration file
    "CUSTOM_SCHEMA_FILE": "docs/configs/custom_schema.json",  # Path to custom schema file
    "REFERENCES_FILE": "docs/configs/references.json",  # Path to references file for reusable descriptions
    "SCHEMA_JSON_FILE": None,  # Path to a single JSON schema file (optional, takes precedence over SCHEMA_JSON_DIR)
    "SCHEMA_JSON_DIR": None,  # Path to directory containing multiple JSON schema files to merge (optional)
    "PATH_PARAM_SUBSTITUTE_FUNCTION": None,
    "PATH_PARAM_SUBSTITUTE_MAPPING": {},
    "FIELD_GENERATORS": {},
    # AI documentation settings
    "ENABLE_AI_DOCS": False,
    "AI_CONFIG_DIR_NAME": "ai_code",  # Directory name for AI-generated code files
    "AI_OPERATION_MAP_FILE": "docs/configs/operation_map.json",  # Path to operation map file
    "SERIALIZERS_INHERITANCE_DEPTH": 1,  # Maximum depth for class inheritance analysis
    "DJANGO_APPS": [],  # If it is empty list, there is no any exclusion
    # Auto-authentication settings
    "ENABLE_AUTO_AUTH": False,  # Enable/disable auto-authentication feature
    "AUTH_FUNCTION_JS": "",  # JavaScript code or path to JS file containing getAuthHeader function
}
