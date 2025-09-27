from pathlib import Path
from typing import Any

from django.template.loader import render_to_string

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings

from .commons.file_utils import write_file


def _get_relationship_type_and_description(rel_type_class: str) -> tuple[str, str] | None:
    """Map Django relationship type to Mermaid ER diagram syntax and description."""
    mapping = {
        "ForeignKey": ("}o--||", "many to 1"),
        "OneToOneField": ("||--||", "1 to 1"),
        "OneToOneRel": ("||--||", "1 to 1"),
        "ManyToManyField": ("}o--o{", "many to many"),
        "ManyToManyRel": ("}o--o{", "many to many"),
        "ManyToOneRel": ("||--o{", "1 to many"),
    }
    return mapping.get(rel_type_class)


def _create_entity_from_model(
    app_name: str, model_name: str, model_info: dict[str, Any], include_fields: bool = False
) -> dict[str, Any]:
    """Create entity dictionary from model data, optionally including field details."""
    table_name = model_info.get("table_name", model_name)
    entity_id = f"{app_name}__{table_name}"

    entity = {
        "id": entity_id,
        "app_name": app_name,
        "model_name": model_name,
        "table_name": table_name,
        "fields": [],
    }

    if include_fields:
        fields = []
        has_pk = False

        for field_name, field_info in model_info.get("column_fields", {}).items():
            field_type = field_info.get("type", "")
            is_pk = field_info.get("primary_key", False)
            nullable = field_info.get("null", False) or field_info.get("blank", False)

            fields.append({
                "name": field_name,
                "type": field_type,
                "is_pk": is_pk,
                "nullable": nullable
            })

            if is_pk:
                has_pk = True

        if not has_pk:
            fields.insert(0, {
                "name": "id",
                "type": "AutoField",
                "is_pk": True,
                "nullable": False
            })

        entity["fields"] = fields

    return entity


def _process_model_relationships(
    source_entity_id: str,
    source_model_name: str,
    model_info: dict[str, Any],
    all_models_data: dict[str, Any]
) -> list[dict[str, Any]]:
    """Extract and process model relationships, returning Mermaid-compatible relationship data."""
    relationships = []

    for rel_name, rel_info in model_info.get("relationships", {}).items():
        if not isinstance(rel_info, dict):
            continue

        related_model_label = rel_info.get("related_model", "")
        if not related_model_label or "." not in related_model_label:
            continue

        target_app, target_model = related_model_label.split(".", 1)

        target_table_name = rel_info.get("table_name", target_model.lower())
        if target_app in all_models_data and target_model in all_models_data[target_app]:
            target_table_name = all_models_data[target_app][target_model].get(
                "table_name", target_model.lower()
            )

        target_entity_id = f"{target_app}__{target_table_name}"

        rel_type_class = rel_info.get("type", "")
        type_info = _get_relationship_type_and_description(rel_type_class)
        if not type_info:
            continue

        rel_type, description = type_info

        relationships.append({
            "source": source_entity_id,
            "target": target_entity_id,
            "source_model": source_model_name,
            "target_model": target_model,
            "type": rel_type,
            "label": rel_name,
            "description": description,
        })

    return relationships


def generate_er_diagrams(models_data: dict[str, Any], docs_dir: Path) -> None:
    """Generate main ER diagram, app-specific diagrams, and index page from model data."""
    generate_main_er_diagram(models_data, docs_dir)

    for app_name, models in models_data.items():
        if not isinstance(models, dict):
            continue
        generate_app_er_diagram(app_name, models, models_data, docs_dir)

    generate_er_diagrams_index(models_data, docs_dir)


def generate_main_er_diagram(models_data: dict[str, Any], _docs_dir: Path) -> None:
    """Create main ER diagram showing all models and their relationships."""
    entities = []
    relationships = []

    for app_name, models in models_data.items():
        if not isinstance(models, dict):
            continue

        for model_name, model_info in models.items():
            if not isinstance(model_info, dict):
                continue

            entity = _create_entity_from_model(app_name, model_name, model_info, include_fields=False)
            entities.append(entity)

            model_relationships = _process_model_relationships(
                entity["id"], model_name, model_info, models_data
            )
            relationships.extend(model_relationships)

    content = render_to_string(
        "er_diagrams/main.html", {"entities": entities, "relationships": relationships}
    )

    write_file(f"{drf_to_mkdoc_settings.ER_DIAGRAMS_DIR}/main.md", content)


def generate_app_er_diagram(
    app_name: str, app_models: dict[str, Any], all_models_data: dict[str, Any], _docs_dir: Path
) -> None:
    """Create app-specific ER diagram with detailed fields and related models."""
    app_entities = []
    related_entities = []
    relationships = []
    related_entity_ids = set()

    for model_name, model_info in app_models.items():
        if not isinstance(model_info, dict):
            continue

        entity = _create_entity_from_model(app_name, model_name, model_info, include_fields=True)
        app_entities.append(entity)

        model_relationships = _process_model_relationships(
            entity["id"], model_name, model_info, all_models_data
        )

        for relationship in model_relationships:
            target_entity_id = relationship["target"]
            target_model = relationship["target_model"]
            target_app = target_entity_id.split("__")[0]

            if target_app != app_name and target_entity_id not in related_entity_ids:
                if target_app in all_models_data and target_model in all_models_data[target_app]:
                    target_model_info = all_models_data[target_app][target_model]
                    related_entity = _create_entity_from_model(
                        target_app, target_model, target_model_info, include_fields=False
                    )
                    related_entities.append(related_entity)
                    related_entity_ids.add(target_entity_id)

            relationships.append(relationship)

    content = render_to_string(
        "er_diagrams/app.html",
        {
            "app_name": app_name,
            "app_entities": app_entities,
            "related_entities": related_entities,
            "relationships": relationships,
        },
    )

    write_file(f"{drf_to_mkdoc_settings.ER_DIAGRAMS_DIR}/{app_name}.md", content)


def generate_er_diagrams_index(models_data: dict[str, Any], _docs_dir: Path) -> None:
    """Create index page listing all available ER diagrams with app summaries."""
    apps = []

    for app_name in sorted(models_data.keys()):
        if not isinstance(models_data[app_name], dict):
            continue

        model_count = len([
            m for m in models_data[app_name]
            if isinstance(models_data[app_name][m], dict)
        ])

        model_names = []
        for model_name, model_info in models_data[app_name].items():
            if isinstance(model_info, dict):
                model_names.append(model_name)
                if len(model_names) >= 3:
                    break

        apps.append({"name": app_name, "model_count": model_count})

    content = render_to_string("er_diagrams/index.html", {"apps": apps})
    write_file(f"{drf_to_mkdoc_settings.ER_DIAGRAMS_DIR}/index.md", content)
