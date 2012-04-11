from django.contrib.syndication.feeds import Feed,FeedDoesNotExist
from mysite.feeds.models import BlogPost
from django.utils.feedgenerator import Atom1Feed
from django.core.exceptions import ObjectDoesNotExist

class RSSFeed( Feed) :
    title = "MLGB Books feed"
    description = "The 10 latest books from MLGB3"
    link = "/feeds/archive/"
    item_link = link
    def items( self) :
        return BlogPost.objects.order_by('-timestamp')[:5]
       
    #def get_object(self, bits):
        #if len(bits) != 1:
            #raise ObjectDoesNotExist
        #return BlogPost.objects.get(title_exact=bits[0])

    #def title(self, obj):
        #return "MLGB Books feed %s" % obj.title

    #def link(self, obj):
        #if not obj:
            #raise FeedDoesNotExist
        #return obj.get_absolute_url()
    #item_link = link
    #def description(self, obj):
        #return "The 10 latest books from MLGB3 %s" % obj.title

    #def items(self, obj):
        #return BlogPost.objects.filter(id__exact=obj.id).order_by('-timestamp')[:5]
        
    title_template = None
    description_template = None

class AtomFeed(RSSFeed):
    feed_type = Atom1Feed
    subtitle = RSSFeed.description

