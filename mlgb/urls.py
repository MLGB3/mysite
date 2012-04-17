from django.conf.urls.defaults import *
from mysite.books.models import *
from django.conf import settings

urlpatterns = patterns('',
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    (r'^$', 'mysite.mlgb.views.mlgb'),
    (r'^fulltext/', 'mysite.mlgb.views.fulltext'),
    (r'^download/', 'mysite.mlgb.views.download'),
    (r'^category/$', 'mysite.mlgb.views.category'),
    )

urlpatterns += patterns( 'django.views.generic',
    url(r'^book/(?P<object_id>\d+)/$', 'list_detail.object_detail',
        kwargs={
            'queryset':Book.objects.all(),
            #'template_name' : '%smlgb/mlgb_detail.html' % settings.TEMPLATE_DIRS
            'template_name' : 'mlgb/mlgb_detail.html'
        },
        name='mlgb_detail'
    ),
)
