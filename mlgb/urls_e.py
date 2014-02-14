from django.conf.urls.defaults import *
from mysite.books.models import *
from django.conf import settings

urlpatterns = patterns('',
    ( r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT} ),
    ( r'^$',                           'mysite.mlgb.views.results_e' ),
    ( r'^fulltext/',                   'mysite.mlgb.views.fulltext' ),
    ( r'^download/',                   'mysite.mlgb.views.download' ),
    ( r'^downloadcsv/',                'mysite.mlgb.views.downloadcsv' ),
    ( r'^home/$',                      'mysite.mlgb.views.index_e' ),
    ( r'^browse/$',                    'mysite.mlgb.views.browse_e' ),
    ( r'^browse/(?P<letter>\w+)/$',    'mysite.mlgb.views.browse_e' ),
    ( r'^category/$',                  'mysite.mlgb.views.category_e' ),
    ( r'^book/(?P<book_id>\d+)/$',     'mysite.mlgb.views.book_e' ),
    )

