from django.conf.urls.defaults import *
from mysite.books.models import *
from django.conf import settings

urlpatterns = patterns('',
    ( r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT} ),
    ( r'^$',                           'mysite.mlgb.views.mlgb' ),
    ( r'^fulltext/',                   'mysite.mlgb.views.fulltext' ),
    ( r'^download/',                   'mysite.mlgb.views.download' ),
    ( r'^downloadcsv/',                'mysite.mlgb.views.downloadcsv' ),
    ( r'^home/$',                      'mysite.mlgb.views.index' ),
    ( r'^browse/$',                    'mysite.mlgb.views.browse' ),
    ( r'^browse/(?P<letter>\w+)/$',    'mysite.mlgb.views.browse' ),
    ( r'^category/$',                  'mysite.mlgb.views.category' ),
    ( r'^book/(?P<book_id>\d+)/$',     'mysite.mlgb.views.book' ),
    )

