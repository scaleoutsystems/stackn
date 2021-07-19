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

@register.filter(name='count_str')
def split(value):
    total_length = 0
    num_tags = 0
    for tag in value:
        total_length += len(str(tag))
        if total_length > 50:
            break
        num_tags += 1
    if num_tags == 0:
        num_tags = 1
    return num_tags

@register.filter(name='subtract')
def subtract(value, arg):
    return value - arg