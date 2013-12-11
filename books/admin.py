from mysite.books.models import *
from django.contrib import admin
from mysite.feeds.models import *

#=================================================

class BooksAdmin(admin.ModelAdmin):

    fields = [ 'provenance',
               'modern_location_1',
               'modern_location_2',
               'shelfmark_1',
               'shelfmark_2',
               'evidence',
               'evidence_notes',
               'author_title',
               'date',
               'pressmark',
               'medieval_catalogue',
               'medieval_catalogue_notes',
               'unknown',
               'ownership',
               'notes',
               'urls',
               'pr_bk']

    inlines = [ ContainsInline, PhotoInline ]

    list_display = ( 'provenance',
                     'modern_location',
                     'shelfmark',
                     'evidence',
                     'author_title',
                     'date',
                     'medieval_catalogue',
                     'medieval_catalogue_notes' )

    list_filter = [ 'provenance',
                    'modern_location_1',
                    'modern_location_2' ]
 
    search_fields = [ 'author_title',
                      'shelfmark_1',
                      'evidence_notes',
                      'date',
                      'ownership',
                      'notes',
                      'medieval_catalogue',
                      'medieval_catalogue_notes' ]

    list_per_page = 15
    ordering = fields
    list_display_links = list_display

#=================================================

class Booksml1Admin(admin.ModelAdmin):

    ordering = ['modern_location_1']
    search_fields = ['modern_location_1']

#=================================================


class Booksml2Admin(admin.ModelAdmin):

    ordering = ['modern_location_2']
    search_fields = ['modern_location_2']

#=================================================


class EvidenceAdmin(admin.ModelAdmin):

    ordering = ['evidence']
    search_fields = ['evidence','evidence_description','notes']

#=================================================


class ContainsAdmin(admin.ModelAdmin):

    ordering = ['contains']
    search_fields = ['contains']

#=================================================


admin.site.register(Book,BooksAdmin)
admin.site.register(Provenance)
admin.site.register(Modern_location_1,Booksml1Admin)
admin.site.register(Modern_location_2,Booksml2Admin)
admin.site.register(Evidence,EvidenceAdmin)
admin.site.register(Contains,ContainsAdmin)


