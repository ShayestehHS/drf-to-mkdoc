"""File operation utilities."""

import json
from pathlib import Path
from typing import Any

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings


def write_file(file_path: str, content: str) -> None:
    full_path = Path(drf_to_mkdoc_settings.DOCS_DIR) / file_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    with full_path.open("w", encoding="utf-8") as f:
        f.write(content)


def load_model_json_data() -> dict[str, Any] | None:
    """Load the JSON mapping data for model information"""
    json_file = Path(drf_to_mkdoc_settings.MODEL_DOCS_FILE)
    if not json_file.exists():
        return None

    with json_file.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_doc_config() -> dict[str, Any] | None:
    """Load the documentation configuration file"""
    config_file = Path(drf_to_mkdoc_settings.DOC_CONFIG_FILE)
    if not config_file.exists():
        return None

    with config_file.open("r", encoding="utf-8") as f:
        return json.load(f)
