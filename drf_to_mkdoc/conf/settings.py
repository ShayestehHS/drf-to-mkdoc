from django.conf import settings

from drf_to_mkdoc.conf.defaults import DEFAULTS


class DRFToMkDocSettings:
    required_settings = ["DJANGO_APPS"]
    project_settings = {"PROJECT_NAME": "drf-to-mkdoc"}

    settings_types = {
        "ENABLE_AI_DOCS": bool,
        "AI_CONFIG_DIR_NAME": str,
        "SERIALIZERS_INHERITANCE_DEPTH": int,
    }

    settings_ranges = {
        "SERIALIZERS_INHERITANCE_DEPTH": (1, 3),
    }

    def __init__(self, user_settings_key="DRF_TO_MKDOC", defaults=None):
        self.user_settings_key = user_settings_key
        self._user_settings = getattr(settings, user_settings_key, {})
        self.defaults = defaults or {}

    def _validate_type(self, key: str, value: any) -> None:
        """Validate the type of setting value."""
        if key in self.settings_types:
            expected_type = self.settings_types[key]
            if not isinstance(value, expected_type):
                raise TypeError(
                    f"DRF_TO_MKDOC setting '{key}' must be of type {expected_type.__name__}, "
                    f"got {type(value).__name__} instead."
                )

    def _validate_range(self, key: str, value: any) -> None:
        """Validate the range of a setting value."""
        if key in self.settings_ranges:
            min_val, max_val = self.settings_ranges[key]
            if not min_val <= value <= max_val:
                raise ValueError(
                    f"DRF_TO_MKDOC setting '{key}' must be between {min_val} and {max_val}, "
                    f"got {value} instead."
                )

    def _validate_required(self, key: str, value: any) -> None:
        """Validate if a required setting is configured."""
        if value is None and key in self.required_settings:
            raise ValueError(
                f"DRF_TO_MKDOC setting '{key}' is required but not configured. "
                f"Please add it to your Django settings under {self.user_settings_key}."
            )

    def get(self, key):
        if key not in self.defaults:
            if key in self.project_settings:
                return self.project_settings[key]
            raise AttributeError(f"Invalid DRF_TO_MKDOC setting: '{key}'")

        value = self._user_settings.get(key, self.defaults[key])

        # Run all validations
        self._validate_required(key, value)
        self._validate_type(key, value)
        self._validate_range(key, value)

        return value

    def __getattr__(self, key):
        return self.get(key)

    def validate_required_settings(self):
        missing_settings = []

        for setting in self.required_settings:
            try:
                self.get(setting)
            except ValueError:
                missing_settings.append(setting)

        if missing_settings:
            raise ValueError(
                f"Missing required settings: {', '.join(missing_settings)}. "
                f"Please configure these in your Django settings under {self.user_settings_key}."
            )


drf_to_mkdoc_settings = DRFToMkDocSettings(defaults=DEFAULTS)
