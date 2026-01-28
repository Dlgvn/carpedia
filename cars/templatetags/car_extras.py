from django import template

register = template.Library()


@register.filter(name='getattr')
def get_attribute(obj, attr):
    """Get an attribute from an object dynamically."""
    if obj is None:
        return None
    try:
        return getattr(obj, attr, None)
    except (AttributeError, TypeError):
        return None
