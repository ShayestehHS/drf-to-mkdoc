from pathlib import Path
from typing import Any

from django.template.loader import render_to_string


def generate_er_diagrams(models_data: dict[str, Any], docs_dir: Path) -> None:
    # Create directory for ER diagrams
    er_dir = docs_dir / "er_diagrams"
    er_dir.mkdir(parents=True, exist_ok=True)

    # Generate the main ER diagram with all models
    generate_main_er_diagram(models_data, docs_dir)

    # Generate ER diagrams for each app
    for app_name, models in models_data.items():
        if not isinstance(models, dict):
            continue
        generate_app_er_diagram(app_name, models, models_data, docs_dir)

    # Generate the ER diagrams index page
    generate_er_diagrams_index(models_data, docs_dir)


def generate_main_er_diagram(models_data: dict[str, Any], docs_dir: Path) -> None:
    entities = []
    relationships = []

    # Process all models to extract entities and relationships
    for app_name, models in models_data.items():
        if not isinstance(models, dict):
            continue

        for model_name, model_info in models.items():
            if not isinstance(model_info, dict):
                continue

            table_name = model_info["table_name"]
            entity_id = f"{app_name}__{table_name}"

            entities.append(
                {
                    "id": entity_id,
                    "app_name": app_name,
                    "model_name": model_name,
                    "table_name": table_name,
                    "fields": [],  # No fields for main diagram - just show model boxes
                }
            )

            # Process relationships directly from the relationships field
            source_table = entity_id
            for rel_name, rel_info in model_info.get("relationships", {}).items():
                if not isinstance(rel_info, dict):
                    continue

                related_model_label = rel_info.get("related_model", "")
                if not related_model_label or "." not in related_model_label:
                    continue

                # Parse app_label.ModelName format
                target_app, target_model = related_model_label.split(".", 1)

                # Find target table name
                target_table_name = rel_info.get("table_name", target_model.lower())
                if target_app in models_data and target_model in models_data[target_app]:
                    target_table_name = models_data[target_app][target_model].get(
                        "table_name", target_model.lower()
                    )

                target_table = f"{target_app}__{target_table_name}"

                # Determine relationship type and description
                rel_type_class = rel_info.get("type", "")
                if rel_type_class == "ForeignKey":
                    rel_type = "}o--||"
                    description = "many to 1"
                elif rel_type_class == "OneToOneField" or rel_type_class == "OneToOneRel":
                    rel_type = "||--||"
                    description = "1 to 1"
                elif rel_type_class == "ManyToManyField" or rel_type_class == "ManyToManyRel":
                    rel_type = "}o--o{"
                    description = "many to many"
                elif rel_type_class == "ManyToOneRel":
                    rel_type = "||--o{"
                    description = "1 to many"
                else:
                    continue  # Skip unknown relationship types

                # Add relationship
                relationships.append(
                    {
                        "source": source_table,
                        "target": target_table,
                        "source_model": model_name,
                        "target_model": target_model,
                        "type": rel_type,
                        "label": rel_name,
                        "description": description,
                    }
                )

    # Render the template with the collected data
    content = render_to_string(
        "er_diagrams/main.html", {"entities": entities, "relationships": relationships}
    )

    # Write the main ER diagram file
    er_main_path = docs_dir / "er_diagrams" / "main.md"
    er_main_path.parent.mkdir(parents=True, exist_ok=True)

    with er_main_path.open("w", encoding="utf-8") as f:
        f.write(content)


def generate_app_er_diagram(
    app_name: str, app_models: dict[str, Any], all_models_data: dict[str, Any], docs_dir: Path
) -> None:
    app_entities = []
    related_entities = []
    relationships = []
    related_entity_ids = set()

    # First pass: Create entities for this app and collect related entities
    for model_name, model_info in app_models.items():
        if not isinstance(model_info, dict):
            continue

        table_name = model_info.get("table_name", model_name)
        entity_id = f"{app_name}__{table_name}"

        # Extract fields for this entity
        fields = []
        has_pk = False

        # Add all fields
        for field_name, field_info in model_info.get("column_fields", {}).items():
            field_type = field_info.get("type", "")
            is_pk = field_info.get("primary_key", False)
            nullable = field_info.get("null", False) or field_info.get("blank", False)

            fields.append(
                {"name": field_name, "type": field_type, "is_pk": is_pk, "nullable": nullable}
            )

            if is_pk:
                has_pk = True

        # If no PK found, add a default id field
        if not has_pk:
            fields.insert(
                0, {"name": "id", "type": "AutoField", "is_pk": True, "nullable": False}
            )

        # Add entity to the list
        app_entities.append(
            {
                "id": entity_id,
                "app_name": app_name,
                "model_name": model_name,
                "table_name": table_name,
                "fields": fields,
            }
        )

        # Process relationships to find related entities
        for rel_name, rel_info in model_info.get("relationships", {}).items():
            if not isinstance(rel_info, dict):
                continue

            related_model_label = rel_info.get("related_model", "")
            if not related_model_label or "." not in related_model_label:
                continue

            # Parse app_label.ModelName format
            target_app, target_model = related_model_label.split(".", 1)

            # Find target table name
            target_table_name = rel_info.get("table_name", target_model.lower())
            if target_app in all_models_data and target_model in all_models_data[target_app]:
                target_table_name = all_models_data[target_app][target_model].get(
                    "table_name", target_model.lower()
                )

            target_entity_id = f"{target_app}__{target_table_name}"

            # Add to related entities if from another app
            if target_app != app_name and target_entity_id not in related_entity_ids:
                related_entities.append(
                    {
                        "id": target_entity_id,
                        "app_name": target_app,
                        "model_name": target_model,
                        "table_name": target_table_name,
                        "fields": [],
                    }
                )
                related_entity_ids.add(target_entity_id)

            # Create relationship with proper description
            rel_type_class = rel_info.get("type", "")
            if rel_type_class == "ForeignKey":
                rel_type = "}o--||"
                description = "many to 1"
            elif rel_type_class == "OneToOneField" or rel_type_class == "OneToOneRel":
                rel_type = "||--||"
                description = "1 to 1"
            elif rel_type_class == "ManyToManyField" or rel_type_class == "ManyToManyRel":
                rel_type = "}o--o{"
                description = "many to many"
            elif rel_type_class == "ManyToOneRel":
                rel_type = "||--o{"
                description = "1 to many"
            else:
                continue  # Skip unknown relationship types

            relationships.append(
                {
                    "source": entity_id,
                    "target": target_entity_id,
                    "source_model": model_name,
                    "target_model": target_model,
                    "type": rel_type,
                    "label": rel_name,
                    "description": description,
                }
            )

    # Render the template
    content = render_to_string(
        "er_diagrams/app.html",
        {
            "app_name": app_name,
            "app_entities": app_entities,
            "related_entities": related_entities,
            "relationships": relationships,
        },
    )

    # Write the file
    er_app_path = docs_dir / "er_diagrams" / f"{app_name}.md"
    er_app_path.parent.mkdir(parents=True, exist_ok=True)

    with er_app_path.open("w", encoding="utf-8") as f:
        f.write(content)


def generate_er_diagrams_index(models_data: dict[str, Any], docs_dir: Path) -> None:
    """Generate the ER diagrams index page"""
    # Prepare app data for the template
    apps = []

    # Sort app names alphabetically
    for app_name in sorted(models_data.keys()):
        if not isinstance(models_data[app_name], dict):
            continue

        # Count models in this app
        model_count = len(
            [
                m
                for m in models_data[app_name].keys()
                if isinstance(models_data[app_name][m], dict)
            ]
        )

        # Get some model names for description
        model_names = []
        for model_name, model_info in models_data[app_name].items():
            if isinstance(model_info, dict):
                model_names.append(model_name)
                if len(model_names) >= 3:
                    break

        # Create description with sample models
        if model_names:
            description = f"Includes {', '.join(model_names[:2])}"
            if len(model_names) > 2:
                description += " and others"
        else:
            description = "No models found"

        # Add app data
        apps.append({"name": app_name, "model_count": model_count, "description": description})

    # Render the template
    content = render_to_string("er_diagrams/index.html", {"apps": apps})

    # Write the index file
    er_index_path = docs_dir / "er_diagrams" / "index.md"
    er_index_path.parent.mkdir(parents=True, exist_ok=True)

    with er_index_path.open("w", encoding="utf-8") as f:
        f.write(content)
