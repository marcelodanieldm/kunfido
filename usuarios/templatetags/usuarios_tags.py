from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter para acceder a items de un diccionario.
    Uso: {{ mydict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def attr(obj, attr_name):
    """
    Template filter para acceder a atributos de un objeto.
    Uso: {{ obj|attr:"attribute_name" }}
    """
    try:
        return getattr(obj, attr_name)
    except (AttributeError, TypeError):
        return None

@register.filter
def mul(value, arg):
    """
    Template filter para multiplicar dos valores.
    Uso: {{ value|mul:0.30 }}
    """
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError, AttributeError):
        return 0
