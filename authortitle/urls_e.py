from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    ( r'^$',                           'mysite.authortitle.views.browse_e' ),
    ( r'^browse/$',                    'mysite.authortitle.views.browse_e' ),
    ( r'^browse/(?P<letter>\w+)/$',    'mysite.authortitle.views.browse_e' ),
    ( r'^medieval_catalogues/$',              'mysite.authortitle.views.medieval_catalogues_e' ),
    ( r'^medieval_catalogues/(?P<cat>\w+)/$', 'mysite.authortitle.views.medieval_catalogues_e' ),
    )

