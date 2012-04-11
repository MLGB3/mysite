from django.conf.urls.defaults import *
from mysite.feeds.views import *
from mysite.feeds.feeds import *
from mysite.books.models import *
from django.contrib.syndication.views import feed
from mysite.feeds.models import *
from django.views.generic.simple import direct_to_template
from django.conf import settings

feeds = {
    'rss':RSSFeed,
    'atom':AtomFeed,
}


urlpatterns = patterns( 'django.views.generic',
    url(r'^$', 'simple.direct_to_template',
        kwargs={
            'template':'feeds/index.html',
            'extra_context':{'item_list':lambda:Book.objects.all()}
        },
        name='index'
    ),
    url(r'^items/$', 'list_detail.object_list',
        kwargs={
            'queryset':Book.objects.all(),
            'template_name':'feeds/items_listing.html',
            'allow_empty':True
        },
        name='item_list'
    ),
    url(r'^items/(?P<object_id>\d+)/$', 'list_detail.object_detail',
        kwargs={
            'queryset':Book.objects.all(),
            'template_name' : 'feeds/items_detail.html'
        },
        name='item_detail'
    ),
    url( r'^photos/(?P<object_id>\d+)/$', 'list_detail.object_detail',
        kwargs={
            'queryset' : Photo.objects.all(),
            'template_name' : 'feeds/photos_detail.html'
        },
        name='photo_detail'
    ) ,
)
urlpatterns += patterns('',
    url(r'^archive/$', archive),
    url(r'^feed/(?P<url>.*)/$',feed, {'feed_dict':feeds}),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}),
)


