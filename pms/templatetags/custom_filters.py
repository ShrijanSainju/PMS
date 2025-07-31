from django import template

register = template.Library()

@register.filter
def length_is(value, arg):
    """
    Returns True if the length of the value is equal to the argument.
    This filter was removed in Django 4.0 but is still used by some packages like Jazzmin.
    
    Usage: {{ some_list|length_is:5 }}
    """
    try:
        return len(value) == int(arg)
    except (ValueError, TypeError):
        return False
