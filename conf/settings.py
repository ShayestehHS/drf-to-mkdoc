from django.conf import settings

from .defaults import DEFAULTS


class DocBuilderSettings:
    def __init__(self, user_settings_key="DOC_BUILDER", defaults=None):
        self.user_settings_key = user_settings_key
        self._user_settings = getattr(settings, user_settings_key, {})
        self.defaults = defaults or {}

    def get(self, key):
        if key not in self.defaults:
            raise AttributeError(f"Invalid DOC_BUILDER setting: '{key}'")
        return self._user_settings.get(key, self.defaults[key])

    def __getattr__(self, key):
        return self.get(key)


drf_to_mkdoc_settings = DocBuilderSettings(defaults=DEFAULTS)
