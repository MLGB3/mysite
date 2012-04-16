from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter(name='fix_dashes')
@stringfilter
def fix_dashes( value ):

  dashstring = value.replace( '--', '&ndash;' )

  # However, don't mess up HTML comments!
  dashstring = dashstring.replace( '<!&ndash;', '<!--' )
  dashstring = dashstring.replace( '&ndash;>', '-->' )
  
  return dashstring

  

