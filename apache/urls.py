from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    ( r'^mlgb/',     include( 'mysite.mlgb.urls' )),
    ( r'^e/mlgb/',   include( 'mysite.mlgb.urls_e' )),

    ( r'^$',         'mysite.mlgb.views.index'   ),
    ( r'^e/$',       'mysite.mlgb.views.index_e' ),

    ( r'^about/',    'mysite.mlgb.views.about'  ),
    ( r'^e/about/',  'mysite.mlgb.views.about_e'),

    ( r'^admin/',    include( admin.site.urls) ),

    ( r'^feeds/',      include( 'mysite.feeds.urls' ) ),

    ( r'^e/media/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': settings.MEDIA_ROOT } ),
    ( r'^media/(?P<path>.*)$',   'django.views.static.serve', { 'document_root': settings.MEDIA_ROOT } ),
 )

