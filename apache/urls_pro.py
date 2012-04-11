from django.conf.urls.defaults import *
#from django.contrib import databrowse
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    #(r'^mlgb/', 'mysite.mlgb.views.mlgb'),
    (r'^$', include('mysite.mlgb.urls')),
    (r'^admin/', include(admin.site.urls)),
    #(r'^$', include(admin.site.urls)),
    #url(r'^%s' % ROOT_URL[1:], include('mysite.feeds.urls')),
    (r'^feeds/', include('mysite.feeds.urls')),
    #(r'^admin/', include('django.contrib.admin.urls')),
    #(r'^dj_survey/', include('dj_project.dj_survey.urls')),
    #(r'^databrowse/(.*)', databrowse.site.root),
)



