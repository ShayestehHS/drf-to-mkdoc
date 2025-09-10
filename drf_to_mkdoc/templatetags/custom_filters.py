from django import template

register = template.Library()


@register.filter
def is_foreign_key(field_type):
    return field_type in ["ForeignKey", "OneToOneField"]


@register.filter
def get_display_name(field_name, field_type):
    if field_type in ["ForeignKey", "OneToOneField"]:
        return f"{field_name}_id"
    return field_name


@register.filter
def split(value, delimiter=","):
    return value.split(delimiter)


@register.filter
def cut(value, arg):
    return value.split(arg)[1] if "." in value else value


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, "")


@register.filter
def format_field_type(field_info):
    field_type = field_info.get("type", "")
    if field_type == "ForeignKey":
        return f"ForeignKey | {field_info.get('field_specific', {}).get('to', '')}"
    if field_type == "CharField":
        max_length = field_info.get("max_length", "")
        return f"CharField | {field_info.get('verbose_name', '')} | max_length={max_length}"
    return field_type


@register.filter
def format_field_extra(field_info):
    extras = []
    if field_info.get("null"):
        extras.append("null=True")
    if field_info.get("blank"):
        extras.append("blank=True")
    if field_info.get("unique"):
        extras.append("unique=True")
    if field_info.get("primary_key"):
        extras.append("primary_key=True")
    if field_info.get("max_length"):
        extras.append(f"max_length={field_info['max_length']}")
    return ", ".join(extras)


@register.filter
def yesno(value, arg=None):
    """
    Given a string mapping values for true, false and (optionally) None,
    return one of those strings according to the value.
    """
    if arg is None:
        arg = "yes,no,maybe"
    bits = arg.split(",")
    if len(bits) < 2:
        return value  # Invalid arg.
    try:
        yes, no, maybe = bits
    except ValueError:
        yes, no, maybe = bits[0], bits[1], bits[1]

    if value is None:
        return maybe
    if value:
        return yes
    return no
