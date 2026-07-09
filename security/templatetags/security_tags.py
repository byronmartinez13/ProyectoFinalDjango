from django import template

register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name):
    """
    Uso en template:
        {% load security_tags %}
        {% if user|has_group:'Vendedor' %} ... {% endif %}
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:  # el superusuario ve todo
        return True
    return user.groups.filter(name=group_name).exists()


@register.filter(name='has_any_group')
def has_any_group(user):
    """True si el usuario tiene al menos un rol asignado (o es superusuario)."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.exists()
