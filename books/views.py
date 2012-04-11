from django.template import Context, loader
from mysite.polls.models import Poll
from django.http import HttpResponse,Http404,HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.core.urlresolvers import reverse
from mysite.polls.models import *

def index(request):
    latest_poll_list = Poll.objects.all().order_by('-pub_date')[:5]
    t = loader.get_template('books/index.html')
    c = Context({
        'latest_poll_list': latest_poll_list,
    })
    return HttpResponse(t.render(c))

def detail(request, book_id):
    try:
        p = Book.objects.get(pk=book_id)
    except Book.DoesNotExist:
        raise Http404
    return render_to_response('books/detail.html', {'book': p})



    
    
