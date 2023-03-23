from django import template

register = template.Library()


@register.simple_tag
def get_range(start=0, stop=10, step=1):
    return range(start, stop, step)
