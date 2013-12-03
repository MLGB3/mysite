from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    ( r'^$',                           'mysite.authortitle.views.browse' ),
    ( r'^browse/$',                    'mysite.authortitle.views.browse' ),
    ( r'^browse/(?P<letter>\w+)/$',    'mysite.authortitle.views.browse' ),
    )

