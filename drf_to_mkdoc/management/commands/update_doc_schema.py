import os
import shutil

import yaml
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Updates the final schema by copying the documented schema."

    def handle(self, *args, **options):
        self.stdout.write("Starting the schema update process...")

        # Load documented schema
        doc_schema_path = os.path.join(settings.BASE_DIR, "docs/configs/doc-schema.yaml")
        try:
            with open(doc_schema_path) as f:
                documented_schema = yaml.safe_load(f)
            self.stdout.write(f"Successfully loaded documented schema from {doc_schema_path}")
        except FileNotFoundError:
            self.stderr.write(
                self.style.ERROR(f"'{doc_schema_path}' not found. Please create it first.")
            )
            return
        except yaml.YAMLError as e:
            self.stderr.write(self.style.ERROR(f"Error parsing '{doc_schema_path}': {e}"))
            return

        # Save to final schema location
        output_path = os.path.join(settings.BASE_DIR, "schema.yaml")

        # Create backup if schema.yaml exists
        if os.path.exists(output_path):
            backup_path = f"{output_path}.bak"
            shutil.copyfile(output_path, backup_path)
            self.stdout.write(f"Created backup at '{backup_path}'")

        # Write the documented schema
        with open(output_path, "w") as f:
            yaml.dump(documented_schema, f, default_flow_style=False, sort_keys=False)

        # Count documented endpoints
        paths_count = len(documented_schema.get("paths", {}))

        self.stdout.write(
            self.style.SUCCESS(f"Successfully updated schema and saved to '{output_path}'.")
        )
        self.stdout.write(f"Schema now contains {paths_count} documented endpoint(s).")
        self.stdout.write(
            "You can now use this schema for API documentation or import"
            " it into tools like Swagger UI."
        )
