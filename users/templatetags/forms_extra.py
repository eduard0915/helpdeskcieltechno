from django import template

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css):
    if not hasattr(field, 'as_widget'):
        return field
    classes = field.field.widget.attrs.get('class', '')
    return field.as_widget(attrs={'class': f'{classes} {css}'.strip()})


@register.filter(name='invalid_class')
def invalid_class(field):
    """Añade la clase `is-invalid` de Bootstrap cuando el campo tiene errores."""
    if not hasattr(field, 'as_widget'):
        return field
    css = 'is-invalid' if field.errors else ''
    if not css:
        return field
    classes = field.field.widget.attrs.get('class', '')
    return field.as_widget(attrs={'class': f'{classes} {css}'.strip()})