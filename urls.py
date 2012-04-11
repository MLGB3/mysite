from django.conf.urls.defaults import *
from django.contrib import admin,sitemaps
from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('',

    (r'^$', 'mysite.mlgb.views.index'),
    (r'^mlgb/', include('mysite.mlgb.urls')),
    (r'^admin/', include(admin.site.urls)),

    url(r'^feeds/', include('mysite.feeds.urls')),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.MEDIA_ROOT}),
)
