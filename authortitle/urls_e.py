from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    ( r'^$',                           'mysite.authortitle.views.browse_e' ),
    ( r'^browse/$',                    'mysite.authortitle.views.browse_e' ),
    ( r'^browse/(?P<letter>\w+)/$',    'mysite.authortitle.views.browse_e' ),
    )

