from django.conf import settings

from drf_to_mkdoc.conf.defaults import DEFAULTS


class DRFToMkDocSettings:
    required_settings = ["DJANGO_APPS"]
    project_settings = {"PROJECT_NAME": "drf-to-mkdoc"}

    def __init__(self, user_settings_key="DRF_TO_MKDOC", defaults=None):
        self.user_settings_key = user_settings_key
        self._user_settings = getattr(settings, user_settings_key, {})
        self.defaults = defaults or {}

    def get(self, key):
        if key not in self.defaults:
            if key in self.project_settings:
                return self.project_settings[key]
            raise AttributeError(f"Invalid DRF_TO_MKDOC setting: '{key}'")

        value = self._user_settings.get(key, self.defaults[key])

        if value is None and key in self.required_settings:
            raise ValueError(
                f"DRF_TO_MKDOC setting '{key}' is required but not configured. "
                f"Please add it to your Django settings under {self.user_settings_key}."
            )

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
