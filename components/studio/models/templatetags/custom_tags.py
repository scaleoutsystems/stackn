from django import template
import json

register = template.Library()

@register.filter(name='split')
def split(value, arg):
    return value.all()

@register.filter
def sort_by(queryset, order):
    return queryset.order_by(order)

@register.filter(name='exists')
def exists(value, arg):
    if str(arg) in value:
        return True
    return False