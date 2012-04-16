from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter(name='fix_dashes')
@stringfilter
def fix_dashes( value ):
  return value.replace( '--', '&ndash;' )

  

