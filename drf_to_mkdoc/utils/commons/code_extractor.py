"""Code extraction utilities."""

from pathlib import Path

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings


def create_ai_code_directories() -> None:
    """Create the directory structure for AI-generated code files."""
    # Get base config directory
    config_dir = Path(drf_to_mkdoc_settings.CONFIG_DIR)

    # Create AI code directory
    ai_code_dir = config_dir / drf_to_mkdoc_settings.AI_CONFIG_DIR_NAME

    # Create subdirectories
    subdirs = ["serializers", "views", "permissions"]

    # Create all directories
    for subdir in subdirs:
        dir_path = ai_code_dir / subdir
        Path.mkdir(dir_path, parents=True, exist_ok=True)
