from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Return dictionary[key] if present, otherwise None.

    Usage in template: {{ mydict|get_item:"Select one" }}
    """
    if not dictionary:
        return None
    try:
        # dict-like get
        return dictionary.get(key)
    except Exception:
        try:
            return dictionary[key]
        except Exception:
            return None
