from django.db import models
from django.db.models import permalink
from django.contrib import admin
from mysite.mlgb.mlgb import *

#========================================================================

x=MLGB()

#========================================================================

class Provenance(models.Model):
    provenance = models.CharField(verbose_name='Place', max_length=50)
    county = models.CharField(max_length=50,blank=True)
    institution = models.CharField(max_length=100,blank=True)
    cells = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    def __unicode__(self):
        display= self.provenance
        
        if self.county and self.institution:
                display='%s, %s. %s.' % (self.provenance, self.county,self.institution)
        elif self.county: 
                display='%s, %s.' % (self.provenance, self.county)
        elif self.institution: 
                display='%s, %s.' % (self.provenance, self.institution)

        return display

    class Meta:
        ordering = ('provenance',)  

#========================================================================
        
class Modern_location_1(models.Model):
    modern_location_1 = models.CharField(verbose_name='Place', max_length=50)
    
    def __unicode__(self):
        return self.modern_location_1
    class Meta:
        ordering = ('modern_location_1',)
        verbose_name='Current Location, Place'
        verbose_name_plural='Current Location, Places'

#========================================================================
        
        
class Modern_location_2(models.Model):
    modern_location_2 = models.CharField(verbose_name='Library', max_length=50)
    abbr = models.CharField(max_length=5,blank=True)
    def __unicode__(self):
        return self.modern_location_2
    class Meta:
        ordering = ('modern_location_2',)
        verbose_name='Current Location, Library'
        verbose_name_plural='Current Location, Libraries'

#========================================================================
        

class Evidence(models.Model):
    evidence = models.CharField(verbose_name='Evidence Code', max_length=2, unique=True,blank=True)
    evidence_description = models.CharField(max_length=200)
    notes = models.TextField(blank=True)

    def __unicode__(self):
        return self.evidence
    class Meta:
        ordering = ('evidence',)
    @permalink 
    def get_absolute_url(self):
        return ('item_detail',None,{'object_id':self.id})        

#========================================================================
        

class Book(models.Model):
    provenance = models.ForeignKey(Provenance)
    modern_location_1 = models.ForeignKey(Modern_location_1,verbose_name='Modern Location, Place')
    modern_location_2 = models.ForeignKey( Modern_location_2,verbose_name='Modern Location, Library')
    shelfmark_1 = models.CharField(max_length=50, blank=True)
    shelfmark_2 = models.CharField(max_length=50, blank=True)
    evidence = models.ForeignKey(Evidence,blank=True,default=' ', to_field='evidence', verbose_name='Evidence Code')
    evidence_notes = models.TextField(blank=True)
    author_title = models.CharField(max_length=100)
    date = models.CharField(max_length=50, blank=True)
    pressmark = models.CharField(max_length=100, blank=True)
    medieval_catalogue = models.CharField(max_length=50, blank=True)
    unknown = models.CharField(verbose_name='Query',max_length=50, blank=True)
    ownership = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    urls = models.CharField(max_length=255,blank=True)
    pr_bk = models.BooleanField(verbose_name = "Printed Book")
    #---------------------------------------------------------
    def shelfmark(self):
        return ("%s %s" % (self.shelfmark_1, self.shelfmark_2))
    shelfmark.short_description = 'Shelfmark'
    #---------------------------------------------------------
    def modern_location(self):
        return ("%s, %s" % (self.modern_location_1, self.modern_location_2))
    modern_location.short_description = 'Modern Location'
    #---------------------------------------------------------
    class Meta:
        ordering = ['provenance', 'modern_location_1', 'modern_location_2', 'shelfmark_1', 'shelfmark_2', 'evidence', 'author_title']
    @permalink 
    def get_absolute_url(self) :
        return ('item_detail',None,{'object_id':self.id})
    def __unicode__(self):
        return '%s %s %s %s%s' % (self.provenance,self.shelfmark_1,self.shelfmark_2,self.evidence,self.author_title)

#========================================================================
        
class Contains(models.Model):
    book_id = models.ForeignKey(Book)
    contains = models.TextField(verbose_name='Content',blank=True)
    urls = models.CharField(max_length=255,blank=True)
    def __unicode__(self):
        #return self.contains
        return x.stripoffHtml(self.contains)

    class Meta:
        ordering = ['contains']
        verbose_name='Content'
        verbose_name_plural='Contents'

    @permalink #decorator
    def get_absolute_url(self) :
        return ('item_detail',None,{'object_id':self.id})


#========================================================================
        
class ContainsInline(admin.StackedInline) :
    model = Contains
    extra=1
    
#========================================================================
        
class ItemAdmin(admin.ModelAdmin) :
    inlines = [ContainsInline]


#========================================================================
        
class RawBook(models.Model):
    provenance = models.CharField(max_length=50)
    modern_location_1 = models.CharField(max_length=50)
    modern_location_2 = models.CharField(max_length=50)
    shelfmark_1 = models.CharField(max_length=50, blank=True)
    shelfmark_2 = models.CharField(max_length=50, blank=True)
    evidence = models.CharField(max_length=2, blank=True)
    #ev = models.ForeignKey(Evidence)
    author_title = models.CharField(max_length=50)
    date = models.CharField(max_length=50, blank=True)
    pressmark = models.CharField(max_length=50, blank=True)
    medieval_catalogue = models.CharField(max_length=50, blank=True)
    unknown = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    def __unicode__(self):
        return self.provenance,self.author_title


#========================================================================
        
