from django.conf.urls.defaults import *
from django.contrib import admin,sitemaps
from django.conf import settings

admin.autodiscover()

# N.B. I am not convinced that the settings here ever get actively used.
# Need to change the urls.py in /usr/share/mysite/apache in order to add a new URL pattern.

urlpatterns = patterns('',

    (r'^$', 'mysite.mlgb.views.index'),
    (r'^mlgb/', include('mysite.mlgb.urls')),
    (r'^admin/', include(admin.site.urls)),

    url(r'^feeds/', include('mysite.feeds.urls')),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.MEDIA_ROOT}),
)
