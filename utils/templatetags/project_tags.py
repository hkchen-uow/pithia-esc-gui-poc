
from django.urls import reverse
from django import template

register = template.Library()

@register.filter
def get_key_value(dict, key):
    return dict.get(key, '')

@register.inclusion_tag('breadcrumbs/item.html')
def breadcrumb_item(text, viewname, *args, **kwargs):
    return {
        'text': text,
        'url': reverse(viewname, args=[*args, *kwargs.values()])
    }

@register.inclusion_tag('breadcrumbs/item_active.html')
def breadcrumb_item_active(text):
    return {
        'text': text
    }

@register.filter(name='underscore_attribute')
def underscore_attribute(obj, attribute):
    return getattr(obj, attribute)

@register.filter
def get_type(value):
    return type(value).__name__