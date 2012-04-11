from django.db import models
from django.contrib import admin
from django.db.models import permalink
from mysite.feeds.fields import ThumbnailImageField
from mysite.books.models import *
####################Blog##############################

class BlogPost(models.Model):
    title = models.CharField(max_length=150)
    body = models.TextField()
    timestamp = models.DateTimeField()
    def __unicode__( self) :
        return self.title

    class Meta:
        ordering = ('-timestamp',)
#admin.site.register(BlogPost)

class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'timestamp')
    
####################Gallery#######
class Item(models.Model) :
    name = models.CharField(max_length=250)
    description = models.TextField()
    class Meta:
        ordering = ['name']
    def __unicode__(self):
        return self.name
    @permalink #decorator
    def get_absolute_url(self) :
        return ('item_detail',None,{'object_id':self.id})

  
class Photo(models.Model) :
    item = models.ForeignKey( Book)
    title = models.CharField( max_length=100)
    #image = models.ImageField(upload_to='photos')
    image = ThumbnailImageField(upload_to='photos')
    caption = models.CharField(max_length=250, blank=True)
    class Meta:
        ordering = ['title']
    def __unicode__( self) :
        return self.title
    @permalink
    def get_absolute_url(self) :
        return ('photo_detail', None, {'object_id':self.id})
    
class PhotoInline(admin.StackedInline) :
    model = Photo
    extra=1
class ItemAdmin(admin.ModelAdmin) :
    inlines = [PhotoInline]
##############################################   
class Blog(models.Model):
    name = models.CharField(max_length=100)
    tagline = models.TextField()

    def __unicode__(self):
        return self.name

class Author(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField()

    def __unicode__(self):
        return self.name

class Entry(models.Model):
    blog = models.ForeignKey(Blog)
    headline = models.CharField(max_length=255)
    body_text = models.TextField()
    pub_date = models.DateTimeField()
    authors = models.ManyToManyField(Author)
    n_comments = models.IntegerField()
    n_pingbacks = models.IntegerField()
    rating = models.IntegerField()

    def __unicode__(self):
        return self.headline
#############################################################

admin.site.register(Photo)
admin.site.register(BlogPost, BlogPostAdmin)

