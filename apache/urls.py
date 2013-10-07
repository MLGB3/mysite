from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^mlgb/', include('mysite.mlgb.urls')),
    (r'^$', 'mysite.mlgb.views.index'),
    (r'^about/', 'mysite.mlgb.views.about'),
    (r'^admin/', include(admin.site.urls)),
    (r'^feeds/', include('mysite.feeds.urls')),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.MEDIA_ROOT}),
 )

