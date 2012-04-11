#from django.contrib.syndication.feeds import Feed
#from mysite.feeds.models import BlogPost
#from django.utils.feedgenerator import Atom1Feed
#from django.contrib import admin

#class RssSiteNewsFeed(Feed):
    #title = "Chicagocrime.org site news"
    #link = "/sitenews/"
    #description = "Updates on changes and additions to chicagocrime.org."

    #def items(self):
        #return BlogPost.objects.order_by('-timestamp')[:5]

#class AtomSiteNewsFeed(RssSiteNewsFeed):
    #feed_type = Atom1Feed
    
#admin.site.register(BlogPost, RssSiteNewsFeed)