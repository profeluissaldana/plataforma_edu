from django import template
from django.utils.safestring import mark_safe
import markdown

register = template.Library()

@register.filter(name='render_markdown')
def render_markdown(text):
    # Convierte Markdown a HTML soportando tablas y bloques de código
    html = markdown.markdown(text, extensions=['fenced_code', 'tables'])
    return mark_safe(html)