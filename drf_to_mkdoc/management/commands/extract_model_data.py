import inspect
import json
import re
from collections import defaultdict
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import models

from drf_to_mkdoc.conf.settings import drf_to_mkdoc_settings


class Command(BaseCommand):
    help = "Extract model data from Django model introspection and save as JSON"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            default=drf_to_mkdoc_settings.MODEL_DOCS_FILE,
            help=f"Output JSON file name (default: {drf_to_mkdoc_settings.MODEL_DOCS_FILE})",
        )
        parser.add_argument(
            "--exclude-apps",
            type=str,
            nargs="*",
            default=["admin", "auth", "contenttypes", "sessions", "messages", "staticfiles"],
            help="Apps to exclude from documentation",
        )
        parser.add_argument("--pretty", action="store_true", help="Pretty print JSON output")

    def handle(self, *args, **options):
        output_file = options["output"]
        exclude_apps = options["exclude_apps"]
        pretty = options["pretty"]

        self.stdout.write(self.style.SUCCESS("🔍 Scanning Django models..."))

        model_docs = self.generate_model_documentation(exclude_apps)

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            payload = dict(model_docs)
            if pretty:
                json.dump(payload, f, ensure_ascii=False, sort_keys=True, default=str, indent=2)
            else:
                json.dump(payload, f, ensure_ascii=False, sort_keys=True, default=str)

        self.stdout.write(
            self.style.SUCCESS(f"✅ Generated model documentation: {output_path.absolute()}")
        )
        self.stdout.write(
            f"📊 Total models: {sum([len(model_docs[app_label]) for app_label in model_docs])}"
        )
        self.stdout.write(f"📦 Total apps: {len(model_docs)}")

    def generate_model_documentation(self, exclude_apps):
        """Generate documentation for all Django models"""
        model_docs = defaultdict(dict)

        for app_config in apps.get_app_configs():
            app_label = app_config.label

            # Skip excluded apps
            if app_label in exclude_apps:
                self.stdout.write(f"⏭️  Skipping app: {app_label}")
                continue

            self.stdout.write(f"📱 Processing app: {app_label}")

            for model in app_config.get_models():
                model_name = model.__name__
                self.stdout.write(f"  📋 Processing model: {model_name}")

                model_docs[app_label][model_name] = self.introspect_model(model, app_label)

        return {app_label: dict(models) for app_label, models in model_docs.items()}

    def introspect_model(self, model, app_label):
        """Introspect a single Django model"""
        meta = model._meta

        # Basic model information
        model_doc = {
            "name": model.__name__,
            "app_label": app_label,
            "table_name": meta.db_table,
            "verbose_name": str(meta.verbose_name),
            "verbose_name_plural": str(meta.verbose_name_plural),
            "description": self.get_model_description(model),
            "abstract": meta.abstract,
            "proxy": meta.proxy,
            "column_fields": {},
            "relationships": {},
            "meta_options": self.get_meta_options(meta),
            "methods": self.get_model_methods(model),
        }

        # Process fields
        for field in meta.get_fields():
            if field.many_to_many or field.one_to_many or field.many_to_one or field.one_to_one:
                # Handle relationships separately
                model_doc["relationships"][field.name] = self.introspect_relationship(field)
            if not (field.one_to_many or field.many_to_many):
                # Handle column fields
                model_doc["column_fields"][field.name] = self.introspect_field(field)
        return model_doc

    def introspect_field(self, field):
        """Introspect a single model field"""
        return {
            "name": field.name,
            "type": field.__class__.__name__,
            "verbose_name": (
                str(field.verbose_name) if hasattr(field, "verbose_name") else field.name
            ),
            "help_text": field.help_text if hasattr(field, "help_text") else "",
            "null": getattr(field, "null", False),
            "blank": getattr(field, "blank", False),
            "editable": getattr(field, "editable", True),
            "primary_key": getattr(field, "primary_key", False),
            "unique": getattr(field, "unique", False),
            "db_index": getattr(field, "db_index", False),
            "default": self.get_field_default(field),
            "choices": self.get_field_choices(field),
            "validators": self.get_field_validators(field),
            "field_specific": self.get_field_specific_attrs(field),
        }

    def introspect_relationship(self, field):
        """Introspect relationship fields"""
        # Safely resolve related model label; can be None for generic relations
        related_model_label = None
        try:
            if getattr(field, "related_model", None) is not None:
                related_model_label = (
                    f"{field.related_model._meta.app_label}.{field.related_model.__name__}"
                )
        except Exception:
            related_model_label = None

        relationship_data = {
            "name": field.name,
            "type": field.__class__.__name__,
            "related_model": related_model_label,
            "related_name": getattr(field, "related_name", None),
            "app_label": field.related_model._meta.app_label,
            "table_name": field.related_model._meta.db_table,
            "verbose_name": field.related_model._meta.verbose_name,
            "on_delete": self.get_on_delete_name(field),
            "null": getattr(field, "null", False),
            "blank": getattr(field, "blank", False),
            "many_to_many": getattr(field, "many_to_many", False),
            "one_to_many": getattr(field, "one_to_many", False),
            "many_to_one": getattr(field, "many_to_one", False),
            "one_to_one": getattr(field, "one_to_one", False),
        }

        # Handle Django generic relations where related_model can be None
        field_class_name = field.__class__.__name__
        if field_class_name in ("GenericForeignKey", "GenericRelation"):
            relationship_data["is_generic"] = True
            # Capture common generic relation details when available
            for attr_name in (
                "ct_field",
                "fk_field",
                "object_id_field",
                "content_type_field",
                "for_concrete_model",
                "related_query_name",
            ):
                if hasattr(field, attr_name):
                    relationship_data[attr_name] = getattr(field, attr_name)
        else:
            relationship_data["is_generic"] = False

        return relationship_data

    def get_on_delete_name(self, field):
        """Get readable name for on_delete option"""
        if not hasattr(field, "on_delete") or field.on_delete is None:
            return None

        # Import Django's on_delete functions

        # Map function objects to their readable names
        on_delete_mapping = {
            models.CASCADE: "CASCADE",
            models.PROTECT: "PROTECT",
            models.SET_NULL: "SET_NULL",
            models.SET_DEFAULT: "SET_DEFAULT",
            models.SET: "SET",
            models.DO_NOTHING: "DO_NOTHING",
            models.RESTRICT: "RESTRICT",
        }

        on_delete_func = field.on_delete

        # Handle SET() callable
        if hasattr(on_delete_func, "__name__") and on_delete_func.__name__ == "SET":
            return "SET"

        # Check if it's one of the standard Django on_delete options
        for func, name in on_delete_mapping.items():
            if on_delete_func is func:
                return name

        # Fallback for custom functions or unknown cases
        return getattr(on_delete_func, "__name__", str(on_delete_func))

    def get_model_description(self, model):
        """Get model description from docstring or generate one"""
        if model.__doc__ and not model.__doc__.startswith(model.__name__ + "("):
            # Only use docstring if it's not just the auto-generated field list
            return model.__doc__.strip()
        return ""

    def get_meta_options(self, meta):
        """Extract Meta class options"""
        options = {}

        # Common Meta options
        meta_attrs = [
            "ordering",
            "unique_together",
            "index_together",
            "constraints",
            "indexes",
            "permissions",
            "default_permissions",
            "get_latest_by",
            "order_with_respect_to",
            "managed",
            "default_manager_name",
        ]

        for attr in meta_attrs:
            if hasattr(meta, attr):
                value = getattr(meta, attr)
                if value:
                    options[attr] = str(value)

        return options

    def get_model_methods(self, model):
        """Get custom model methods (excluding built-in Django methods)"""
        methods = []

        # Get all methods that don't start with underscore and aren't Django built-ins
        django_methods = {
            "save",
            "delete",
            "clean",
            "full_clean",
            "validate_unique",
            "get_absolute_url",
            "get_next_by_",
            "get_previous_by_",
            "refresh_from_db",
            "serializable_value",
            "check",
            "from_db",
            "clean_fields",
            "get_deferred_fields",
            "pk",
        }

        model_field_names = {field.name for field in model._meta.get_fields()}

        for attr_name in dir(model):
            if (
                not attr_name.startswith("_")
                and not attr_name.startswith("get_next_by_")
                and not attr_name.startswith("get_previous_by_")
                and attr_name not in django_methods
                and callable(getattr(model, attr_name))
            ):
                display_method_match = re.match(r"^get_(.+)_display$", attr_name)
                if display_method_match:
                    field_name = display_method_match.group(1)
                    if field_name in model_field_names:
                        # Exclude built-in get_<field>_display for fields present on the model
                        continue

                method = getattr(model, attr_name)

                # Check if it's a method defined in this class (not inherited from Django)
                if (
                    inspect.ismethod(method)
                    or inspect.isfunction(method)
                    or (hasattr(method, "__func__") and inspect.isfunction(method.__func__))
                ):
                    # Check if method is defined in the model class itself
                    if hasattr(model, attr_name) and attr_name in model.__dict__:
                        methods.append(
                            {
                                "name": attr_name,
                                "docstring": method.__doc__.strip() if method.__doc__ else "",
                            }
                        )

        return methods

    def get_field_default(self, field):
        """Get field default value"""
        if hasattr(field, "default") and field.default is not models.NOT_PROVIDED:
            default = field.default
            if callable(default):
                return f"<callable: {default.__name__}>"
            return str(default)
        return None

    def get_field_choices(self, field):
        """Get field choices"""
        if hasattr(field, "choices") and field.choices:
            return [{"value": choice[0], "display": choice[1]} for choice in field.choices]
        return []

    def get_field_validators(self, field):
        """Get field validators"""
        if hasattr(field, "validators") and field.validators:
            return [validator.__class__.__name__ for validator in field.validators]
        return []

    def get_field_specific_attrs(self, field):
        """Get field-specific attributes"""
        specific_attrs = {}

        # CharField, TextField
        if hasattr(field, "max_length") and field.max_length:
            specific_attrs["max_length"] = field.max_length

        # DecimalField
        if hasattr(field, "max_digits") and field.max_digits:
            specific_attrs["max_digits"] = field.max_digits
        if hasattr(field, "decimal_places") and field.decimal_places:
            specific_attrs["decimal_places"] = field.decimal_places

        # FileField, ImageField
        if hasattr(field, "upload_to") and field.upload_to:
            specific_attrs["upload_to"] = str(field.upload_to)

        # DateTimeField
        if hasattr(field, "auto_now") and field.auto_now:
            specific_attrs["auto_now"] = field.auto_now
        if hasattr(field, "auto_now_add") and field.auto_now_add:
            specific_attrs["auto_now_add"] = field.auto_now_add

        return specific_attrs
