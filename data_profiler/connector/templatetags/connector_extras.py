from django import template

register = template.Library()

@register.filter(name='calculate_percentage')
def calculate_percentage(value, arg):
    if not value:
        return 0
    percentage = value * 100 // arg
    return percentage

@register.filter(name='get_boxplot_data')
def get_boxplot_data(value, arg):
    if arg == 25:
        return value.get('25%')
    if arg == 50:
        return value.get('50%')
    if arg == 75:
        return value.get('75%')
    if arg == 100:
        return value.get('max')
    if arg == 0:
        return value.get('min')
    return 0
