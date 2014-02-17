
from django.conf.urls.defaults import *
from mysite.books.models import *
from django.views.generic.simple import direct_to_template
from django.conf import settings



urlpatterns = patterns( 'django.views.generic', 

    url( r'^photos/(?P<object_id>\d+)/$', 
         'list_detail.object_detail',
         kwargs={ 'queryset' : Photo.objects.all(),
                  'template_name' : 'books/photos_detail.html' },
         name='photo_detail'
    ),
)

urlpatterns += patterns( '',  (  r'^media/(?P<path>.*)$', 
                                 'django.views.static.serve',
                                 { 'document_root': settings.MEDIA_ROOT} ),
)


