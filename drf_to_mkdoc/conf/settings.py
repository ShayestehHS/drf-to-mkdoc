from pathlib import Path
from typing import Any, ClassVar

from django.conf import settings

from drf_to_mkdoc.conf.defaults import DEFAULTS


class DRFToMkDocSettings:
    required_settings: ClassVar[list[str]] = []
    project_settings: ClassVar[dict[str, Any]] = {"PROJECT_NAME": "drf-to-mkdoc"}

    settings_types: ClassVar[dict[str, type | tuple[type, ...]]] = {
        "ENABLE_AI_DOCS": bool,
        "AI_CONFIG_DIR_NAME": str,
        "SERIALIZERS_INHERITANCE_DEPTH": int,
        "DJANGO_APPS": list,
        "ENABLE_AUTO_AUTH": bool,
        "AUTH_FUNCTION_JS": (str, type(None)),
        "SCHEMA_JSON_FILE": (str, type(None)),
        "SCHEMA_JSON_DIR": (str, type(None)),
    }

    settings_ranges: ClassVar[dict[str, tuple[int, int]]] = {
        "SERIALIZERS_INHERITANCE_DEPTH": (1, 3),
    }

    path_settings = {
        "CONFIG_DIR",
        "ER_DIAGRAMS_DIR",
        "MODEL_DOCS_FILE",
        "DOC_CONFIG_FILE",
        "CUSTOM_SCHEMA_FILE",
        "AI_OPERATION_MAP_FILE",
    }

    def __init__(self, user_settings_key="DRF_TO_MKDOC", defaults=None):
        self.user_settings_key = user_settings_key
        self._user_settings = getattr(settings, user_settings_key, {})
        self.defaults = defaults or {}

    def _validate_type(self, key: str, value: Any) -> None:
        """Validate the type of setting value."""
        if key not in self.settings_types:
            return

        expected_type = self.settings_types[key]
        
        # Handle tuple of types (union types)
        if isinstance(expected_type, tuple):
            if not isinstance(value, expected_type):
                type_names = " | ".join(t.__name__ for t in expected_type)
                raise TypeError(
                    f"DRF_TO_MKDOC setting '{key}' must be of type {type_names}, "
                    f"got {type(value).__name__} instead."
                )
        else:
            if not isinstance(value, expected_type):
                raise TypeError(
                    f"DRF_TO_MKDOC setting '{key}' must be of type {expected_type.__name__}, "
                    f"got {type(value).__name__} instead."
                )

    def _validate_range(self, key: str, value: Any) -> None:
        """Validate the range of a setting value."""
        if key in self.settings_ranges:
            min_val, max_val = self.settings_ranges[key]
            if not min_val <= value <= max_val:
                raise ValueError(
                    f"DRF_TO_MKDOC setting '{key}' must be between {min_val} and {max_val}, "
                    f"got {value} instead."
                )

    def _validate_required(self, key: str, value: Any) -> None:
        """Validate if a required setting is configured."""
        if value is None and key in self.required_settings:
            raise ValueError(
                f"DRF_TO_MKDOC setting '{key}' is required but not configured. "
                f"Please add it to your Django settings under {self.user_settings_key}."
            )

    def _validate_dir(self, key: str, value: str) -> None:
        if key not in self.path_settings or not isinstance(value, str):
            return

        if not value.strip():
            raise ValueError(
                f"DRF_TO_MKDOC path setting '{key}' cannot be empty or contain only whitespace."
            )

        dangerous_components = {"..", "~", "/", "\\"}
        path_parts = Path(value).parts
        for part in path_parts:
            if part in dangerous_components or part.startswith("."):
                raise ValueError(
                    f"DRF_TO_MKDOC path setting '{key}' contains unsafe path component '{part}'. "
                    f"Directory names should be simple names without separators or relative path components."
                )

        if Path(value).is_absolute():
            raise ValueError(
                f"DRF_TO_MKDOC path setting '{key}' cannot be an absolute path. "
                f"Use relative directory names only."
            )

        reserved_names = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        }
        if value.upper() in reserved_names:
            raise ValueError(
                f"DRF_TO_MKDOC path setting '{key}' uses a reserved system name '{value}'. "
                f"Please choose a different name."
            )

        invalid_chars = '<>:"|?*'
        if any(char in value for char in invalid_chars):
            raise ValueError(
                f"DRF_TO_MKDOC path setting '{key}' contains invalid characters. "
                f"Avoid using: {invalid_chars}"
            )

    def get(self, key):
        if key in self.project_settings:
            return self.project_settings[key]

        # User-provided settings take precedence
        if key in self._user_settings:
            value = self._user_settings[key]
        else:
            value = self.defaults.get(key, None)

        # Run all validations
        self._validate_required(key, value)
        self._validate_type(key, value)
        self._validate_range(key, value)
        self._validate_dir(key, value)

        return value

    def __getattr__(self, key):
        return self.get(key)

    def validate_required_settings(self):
        missing_settings = []

        for setting in self.required_settings:
            try:
                self.get(setting)
            except (ValueError, AttributeError):
                missing_settings.append(setting)

        if missing_settings:
            raise ValueError(
                f"Missing required settings: {', '.join(missing_settings)}. "
                f"Please configure these in your Django settings under {self.user_settings_key}."
            )


drf_to_mkdoc_settings = DRFToMkDocSettings(defaults=DEFAULTS)
