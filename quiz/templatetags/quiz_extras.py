from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def attr(obj, name):
    return getattr(obj, name, None)