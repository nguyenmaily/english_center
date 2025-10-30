from django import template

register = template.Library()


@register.filter
def startswith(value, arg):
    """Check if a string starts with a given prefix"""
    if not value or not arg:
        return False
    return str(value).startswith(str(arg))

