"""File operation utilities."""

import json
from pathlib import Path
from typing import Any

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings


def write_file(file_path: str, content: str) -> None:
    full_path = Path(drf_to_mkdoc_settings.DOCS_DIR) / file_path
    try:
        full_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = full_path.with_suffix(full_path.suffix + ".tmp")

        with tmp_path.open("w", encoding="utf-8") as f:
            # Use atomic writes to avoid partially written docs.
            f.write(content)
        tmp_path.replace(full_path)
    except OSError as e:
        raise OSError(f"Failed to write file {full_path}: {e}") from e


def load_json_data(file_path: str, raise_not_found: bool = True) -> dict[str, Any] | None:
    json_file = Path(file_path)
    if not json_file.exists():
        if raise_not_found:
            raise FileNotFoundError(f"File not found: {json_file}")
        return None

    with json_file.open("r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {json_file}: {e}") from e
