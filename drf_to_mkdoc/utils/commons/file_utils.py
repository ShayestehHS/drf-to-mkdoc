"""File operation utilities."""

import json
from copy import deepcopy
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


def load_json_files_from_dir(dir_path: str, raise_not_found: bool = True) -> list[dict[str, Any]]:
    """
    Load all JSON files from a directory.
    
    Args:
        dir_path: Path to directory containing JSON files
        raise_not_found: If True, raise error if directory doesn't exist
        
    Returns:
        List of loaded JSON data dictionaries, sorted by filename
    """
    json_dir = Path(dir_path)
    if not json_dir.exists():
        if raise_not_found:
            raise FileNotFoundError(f"Directory not found: {json_dir}")
        return []
    
    if not json_dir.is_dir():
        raise ValueError(f"Path is not a directory: {json_dir}")
    
    json_files = sorted(json_dir.glob("*.json"))
    if not json_files:
        if raise_not_found:
            raise FileNotFoundError(f"No JSON files found in directory: {json_dir}")
        return []
    
    loaded_data = []
    for json_file in json_files:
        try:
            with json_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    loaded_data.append(data)
                else:
                    raise TypeError(f"JSON file {json_file} does not contain a JSON object (dict), got {type(data).__name__}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {json_file}: {e}") from e
    
    return loaded_data


def merge_openapi_schemas(schemas: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Merge multiple OpenAPI schema dictionaries into one.
    
    This function intelligently merges OpenAPI schemas by:
    - Merging paths (combining all paths from all schemas)
    - Merging components (schemas, responses, parameters, etc.)
    - Using the first schema's metadata (openapi, info, servers, etc.)
    - Handling conflicts by keeping the first occurrence
    
    Args:
        schemas: List of OpenAPI schema dictionaries to merge
        
    Returns:
        Merged OpenAPI schema dictionary
        
    Raises:
        ValueError: If schemas list is empty or contains invalid schemas
    """
    if not schemas:
        raise ValueError("Cannot merge empty list of schemas")
    
    if len(schemas) == 1:
        return deepcopy(schemas[0])
    
    # Start with the first schema as the base
    merged = deepcopy(schemas[0])
    
    # Merge paths from all schemas
    merged_paths = merged.get("paths", {})
    for schema in schemas[1:]:
        paths = schema.get("paths", {})
        for path, methods in paths.items():
            if path in merged_paths:
                # Merge methods for the same path
                merged_methods = merged_paths[path]
                for method, operation in methods.items():
                    if method in merged_methods:
                        # Path and method conflict - keep the first one
                        # Could be enhanced to merge operation details if needed
                        continue
                    merged_methods[method] = deepcopy(operation)
            else:
                merged_paths[path] = deepcopy(methods)
    
    merged["paths"] = merged_paths
    
    # Merge components
    merged_components = merged.get("components", {})
    for schema in schemas[1:]:
        components = schema.get("components", {})
        for component_type, component_dict in components.items():
            if component_type not in merged_components:
                merged_components[component_type] = {}
            
            merged_component = merged_components[component_type]
            for name, definition in component_dict.items():
                if name in merged_component:
                    # Component name conflict - keep the first one
                    # Could be enhanced to merge definitions if needed
                    continue
                merged_component[name] = deepcopy(definition)
    
    merged["components"] = merged_components
    
    # Merge tags if they exist
    merged_tags = merged.get("tags", [])
    tag_names = {tag.get("name") for tag in merged_tags if isinstance(tag, dict)}
    
    for schema in schemas[1:]:
        tags = schema.get("tags", [])
        for tag in tags:
            if isinstance(tag, dict):
                tag_name = tag.get("name")
                if tag_name and tag_name not in tag_names:
                    merged_tags.append(deepcopy(tag))
                    tag_names.add(tag_name)
            elif tag not in merged_tags:
                merged_tags.append(deepcopy(tag) if isinstance(tag, (dict, list)) else tag)
    
    merged["tags"] = merged_tags
    
    return merged
