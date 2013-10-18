"""
# Main setup script for all MLGB front end web pages

# Originally by Xiaofeng Yang, 2009-2010
# but very, very thoroughly rewritten by Sushila Burgess 2013.
"""
#--------------------------------------------------------------------------------

from mysite.books.models import *
from mysite.feeds.models import Photo
from django.utils import simplejson
from mysite.mlgb.MLGBsolr import *
from mysite.mlgb.config import *
from django.template import Context, loader
from django.http import HttpResponse,Http404,HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.core.urlresolvers import reverse
from django.utils.html import escape
from urllib import quote, unquote
import csv
from cStringIO import StringIO

#--------------------------------------------------------------------------------

editable = False
baseurl="/mlgb"

facet=False
default_rows_per_page = 500
newline = '\n'

browse_collapsed_class = "book_row_2_hidden"
browse_expanded_class = "book_row_2_displayed"

#================= Top-level functions, called directly from URL ================
#--------------------------------------------------------------------------------
## This sets up the data for the Home page

def index( request, pagename = 'home' ): #{

  (medieval_library_count, modern_library_count, location_count) = get_category_counts()

  t = loader.get_template( 'index.html' )

  c = Context( {
      'editable'              : editable,
      'medieval_library_count': medieval_library_count,
      'modern_library_count'  : modern_library_count,
      'location_count'        : location_count,
      'pagename'              : pagename,
      'default_rows_per_page' : str( default_rows_per_page ),
      'searchable_fields'     : get_searchable_field_list(),
      'page_sizes'            : get_page_sizes(),
      } )

  return HttpResponse( t.render( c ) )    
#}
# end index() (home page)
#--------------------------------------------------------------------------------
## This sets up the data for the Home page in 'editable' mode

def index_e( request, pagename = 'home' ): #{

  enable_edit()
  return index( request, pagename )
#}
#--------------------------------------------------------------------------------
## This changes links to include the 'editable' part of the URL  

def enable_edit(): #{

  global editable
  editable = True

  global baseurl
  baseurl = '/e/mlgb'
#}
#--------------------------------------------------------------------------------

# The function category() displays a list of medieval libraries, modern libraries
# or cities. Each item in the list links through to the search results function, i.e. mlgb().
# In other words, a search will be run based on the name of the medieval library, etc.

def category( request, pagename = 'category' ): #{

  # Get the facet counts for the appropriate category from Solr
  field_to_search = get_value_from_GET( request, 'field_to_search', default_value = 'medieval_library' )

  if field_to_search == 'location': #{
    facet_field = "ml1"  # modern library 1, i.e. city where modern library is located, e.g. 'Oxford'
  #}
  elif field_to_search == 'modern_library': #{
    facet_field = "ml_full"  # modern library 2: name of library (plus city), e.g. 'Bodleian, Oxford'
  #}
  else: #{
    facet_field = "pr_full"  # provenance, i.e. medieval library
  #}

  facet_results = None

  s_para = { 'q'    : '*:*',
             'wt'   : s_wt,  # 's_wt', i.e. 'writer type' is set in config.py, defaults to "json"
             'rows' : 0 }

  s_para[ 'facet.mincount' ] = '1'
  s_para[ 'facet'          ] = 'on'
  s_para[ 'facet.limit'    ] = '-1'
  s_para[ 'facet.field'    ] = [ facet_field ]

  r = MLGBsolr()
  r.solrresults( s_para, Facet = True )

  if r.connstatus and r.s_result: #{
    facet_results = r.s_result.get( 'facet' )
  #}

  # Extract the facet counts for the relevant category
  facet_list = facet_results[ facet_field ]

  searchable_fields = get_searchable_field_list()
  category_desc = get_searchable_field_label( field_to_search )

  whole_category = []
  entry_initial = ''
  entry_name = ''
  entry_count = 0

  # Create a list of tuples, each tuples containing an uppercase initial, a name and a number.
  j = 0
  for facet_entry in facet_list: #{ # this is a list of key/value pairs
    j +=1
    if j % 2 > 0: #{  # odd-numbered row, so this is the *key* of the key/value pair
      facet_entry = facet_entry.strip()
      entry_name = facet_entry

      # When constructing full names from individual elements,
      # sometimes ugly combinations of commas and whitespace have crept in 
      entry_name = entry_name.replace( ', ,',  ',' ) # remove accidentally doubled-up commas
      entry_name = entry_name.replace( ' ,',   ',' ) # remove space before a comma
      entry_name = entry_name.replace( '\n,',  ',' ) # remove newline before a comma
      entry_name = entry_name.replace( '\r,',  ',' ) # remove carriage return before a comma
      entry_name = entry_name.replace( '\t,',  ',' ) # remove tab before a comma

      entry_initial = entry_name[ 0 : 1 ].upper()
    #}
    else: #{  # even-numbered row, so this is the *value* of the key/value pair
      entry_count = facet_entry
      whole_category.append( (entry_initial, entry_name, entry_count) )
      entry_initial = ''
      entry_name = ''
      entry_count = 0
    #}
  #}

  # Some names beginning with lowercase letters will have been sorted to the end.
  # So, re-sort the list with the uppercase initial as the first sort key.
  whole_category = sorted( whole_category, key = lambda entryvals: entryvals[0] + entryvals[1].upper() )

  # Now set up a list that is sub-divided by initial letter
  divided_category = []
  prev_letter = ''
  letter_index = -1

  for (entry_initial, entry_name, entry_count) in whole_category: #{

    if entry_initial != prev_letter: #{
      letter_index += 1
      divided_category.append( { entry_initial : [] } )
      prev_letter = entry_initial
    #}

    divided_category[ letter_index ][ entry_initial ].append( { 'name': entry_name,
                                                                'number_of_records': entry_count } )
  #}

  t = loader.get_template('mlgb/category.html')

  page_size = get_value_from_GET( request, 'page_size', default_value = default_rows_per_page )

  (medieval_library_count, modern_library_count, location_count) = get_category_counts()

  c = Context( {
      'editable'         : editable,
      'field_to_search'  : field_to_search,
      'category_desc'    : category_desc,
      'category_data'    : divided_category,
      'medieval_library_count': medieval_library_count,
      'modern_library_count'  : modern_library_count,
      'location_count'        : location_count,
      'pagename'         : pagename,
      'page_size'        : page_size,
      'searchable_fields': get_searchable_field_list(),
      'page_sizes'       : get_page_sizes(),
      'default_rows_per_page': str( default_rows_per_page )
  } )

  return HttpResponse(t.render(c))
#}
# end function category() (list of medieval libraries, modern libraries, etc)
#--------------------------------------------------------------------------------

def category_e( request, pagename = 'category' ): #{
  enable_edit()
  return category( request, pagename )
#}
#--------------------------------------------------------------------------------

# The function mlgb() sets up display of search results

def mlgb( request, pagename = 'results' ): #{

  html = provenance = modern_location1 = detail_text = result_string = search_term = resultsets = None
  number_of_records = solr_rows = solr_query = solr_sort = field_to_search = page_size = sql_query = ""
  link_to_photos = ""
  first_record = True
  photo_evidence_data = []

  space = newline + '<span class="spacer">' + newline + '</span>' + newline
  two_spaces = space + space

  start_treeview = newline
  start_treeview += '<div id="sidetreecontrol">' + newline
  start_treeview += '<a href="?#">Expand All</a> | <a href="?#">Collapse All</a>' + newline
  start_treeview += '</div>' + newline
  start_treeview += '<ul class="treeview" id="tree">' + newline + newline

  start_hidden_list = '<ul style="display:block;">' + newline

  start_outer_section = '<li class="expandable outerhead">' + newline \
                      + '<div class="hitarea expandable-hitarea"></div>' + newline

  start_inner_section = '<li class="expandable innerhead">' + newline \
                      + '<div class="hitarea expandable-hitarea"></div>' + newline

  end_inner_section = newline + '</ul><!-- end "book" list -->' + newline \
                    + '</li><!-- end "inner head" list item -->' + newline + newline

  end_inner_and_outer_sections = newline + '</ul><!-- end "book" list -->'  + newline \
                               + '</li><!-- end "inner head" list item -->' + newline \
                               + '</ul><!-- end "inner head" list -->'      + newline \
                               + '</li><!-- end "outer head" list item -->' \
                               + newline + newline
        
  if request.GET: #{ # was a search term found in GET?

    # Get search term, field to search, records per page and start row from GET
    search_term = get_value_from_GET( request, 'search_term' )
    if not search_term: search_term = '*'

    field_to_search = get_value_from_GET( request, "field_to_search" )
    page_size = get_value_from_GET( request, "page_size" ) 
    solr_start = get_value_from_GET( request, "start", 0 ) 

    # Construct Solr query
    solr_query = escape_for_solr( search_term )
    if ' ' in solr_query:
      solr_query = '(%s)' % solr_query

    if search_term=='*' or search_term=='':
      solr_query='*:*'

    else: #{

      if field_to_search.lower()=='author_title':
        solr_query ="authortitle:%s" % solr_query

      elif field_to_search.lower()=='modern_library':
        solr_query ="library:%s" % solr_query

      elif field_to_search.lower()=='medieval_library':
        solr_query ="provenance:%s" % solr_query

      elif field_to_search.lower()=='location':  
        solr_query ="location:%s" % solr_query

      elif field_to_search.lower()=='shelfmark':
        solr_query ="shelfmarks:%s" % solr_query

      else:
        solr_query ="text:%s" % solr_query

    #}
    
    # Set page size
    if page_size.isdigit():
      solr_rows = int( page_size )
    else: 
      solr_rows=Book.objects.count()
    
    # Set sort field
    if field_to_search.lower()=='author_title':
      # sort primarily by author/title, i.e. 'soc' ('suggestion of contents')
      solr_sort = ", ".join( get_author_title_sortfields() )
    else:
      # sort first on provenance (medieval library), then modern library and shelfmark
      solr_sort = ", ".join( get_provenance_sortfields() )

    # Run the Solr query
    s_para={'q'    : solr_query,
            'wt'   : s_wt,  # 's_wt', i.e. 'writer type' is set in config.py, defaults to "json"
            'start': solr_start, 
            'rows' : solr_rows,
            'sort' : solr_sort}
    r=MLGBsolr()
    r.solrresults( s_para, Facet=facet )


    # Start to display the results
    if r.connstatus and r.s_result: #{ #did we retrieve a result?

      resultsets = r.s_result.get( 'docs' )
      number_of_records = r.s_result.get( 'numFound' )
      
      html = h1 = h2 = d = link_to_photos = ""

      # Start loop through result sets
      for i in xrange( 0, len( resultsets ) ): #{

        # Get the data from the Solr result set
        (id, provenance, modern_location1, modern_location2, shelfmark1, shelfmark2,
        evidence_code, evidence_desc, suggestion_of_contents, date_of_work,
        pressmark, medieval_catalogue, unknown, notes_on_evidence) = extract_from_result( resultsets[i] )

        # Get photos if any
        link_to_photos=""

        sql_query = "select * from feeds_photo where feeds_photo.item_id='%s'" % id
        photo_evidence_data = list( Photo.objects.raw( sql_query ) )
        for e in photo_evidence_data: #{
          link_to_photos += '<a href="%s" rel="lightbox%s" title="%s" class="evidence"></a>' \
                         % (e.image.url, id, e.title + ' -- evidence type: ' + evidence_desc)
          link_to_photos += newline
        #}
        if link_to_photos: #{
          link_to_photos=link_to_photos.replace( "</a>", "%s</a>" % evidence_code, 1 )
        #}

        # If searching on author/title (i.e. 'suggestion of contents'), show author/title as 
        # heading 1, then provenance as heading 2, then modern library and shelfmark in the detail.
        # If not searching on author/title, have medieval library as main heading, then modern one.

        if field_to_search.lower()=='author_title': #{
          heading1 = suggestion_of_contents
          heading2 = provenance
          heading3 = '%s%s%s' % (modern_location1, space, modern_location2)
        #}
        else: #{
          heading1 = provenance
          heading2 = modern_location1
          heading3 = modern_location2
        #}

        if h1 <> heading1: #{  # change in heading 1
          h2=""
          if not first_record: 
            html += end_inner_and_outer_sections
          html += newline
          html += start_outer_section + newline
          html += '<span class="outerhead">%s</span>' % heading1
          html += '<!-- end "outer head" span -->' + newline + start_hidden_list
        #}

        if h2 <> heading2: #{ # change in heading 2
          h2 = heading2
          if h1 == heading1: #{
            if not first_record: #{
              html += end_inner_section
            #}
          #}
          else: #{
            h1 = heading1
          #}
          html += newline
          html += start_inner_section + newline
          html += '<span class="innerhead">%s</span>' % heading2
          html += '<!-- end "inner head" span -->' + newline + start_hidden_list
        #}
        
        # Now set up the 'heading 3' and 'detail' text
        heading3 = '<span class="modern_location_heading">' \
                 + newline + heading3 + newline \
                 + '</span><!-- end modern location_heading -->' + newline

        detail_text = newline + '<!-- start book ID ' + id + ' -->' + newline
        detail_text += '<li class="one_book">' + newline

        detail_text += heading3
        detail_text += two_spaces

        if len( photo_evidence_data ) <> 0:
          detail_text += link_to_photos

        else: #{
          if evidence_code: #{
            detail_text += get_evidence_decoder_button( evidence_code, evidence_desc )
          #}
        #}
        detail_text += ' <!-- type of evidence -->'
        detail_text += two_spaces

        detail_text += '<!-- start booklink -->' + newline
        detail_text += '<a href="%s/book/%s/' % (baseurl, id)

        # Pass in your search, so that they can search again from the detail page
        if search_term and search_term != '*': #{
          detail_text += '?search_term=%s' % quote( search_term.encode( 'utf-8' ) )
          if field_to_search:
            detail_text += '&field_to_search=%s' % quote( field_to_search.encode( 'utf-8' ) )
          if page_size:
            detail_text += '&page_size=%s' % quote( page_size.encode( 'utf-8' ) )
        #}

        detail_text += '" class="booklink">'

        detail_text += '%s <!-- shelfmark 1 -->' %  shelfmark1 
        detail_text += space

        if shelfmark2: #{
          detail_text += '%s <!-- shelfmark 2 -->' %  shelfmark2 
          detail_text += space
        #}

        if field_to_search.lower() != 'author_title': #{

          if suggestion_of_contents: #{
            detail_text += suggestion_of_contents + ' <!-- author/title -->'
            detail_text += space
          #}

          if date_of_work : #{
            detail_text += date_of_work + ' <!-- date -->'
            detail_text += space
          #}

          if pressmark : #{
            detail_text += pressmark + ' <!-- pressmark -->'
            detail_text += space
          #}

          if medieval_catalogue : #{
            detail_text += medieval_catalogue + ' <!-- medieval catalogue -->'
            detail_text += space
          #}

          if unknown : #{
            detail_text += unknown + ' <!-- unknown -->'
            detail_text += space
          #}
        #}

        detail_text += '<img src="/mlgb/media/img/detail.gif" alt="detail" border="0" />'
        detail_text += '</a>' + newline
        detail_text += '<!-- end booklink -->' + newline

        if editable: #{
          detail_text += '<a href="/admin/books/book/%s" title="Edit this record" target="_blank"' % id
          detail_text += ' class="editlink">'
          detail_text += space + 'Edit' + '</a>' + newline
        #}

        detail_text += '</li><!-- end book ID ' + id + ' -->' + newline + newline

        # Add the string of HTML that you have generated for this record to the main HTML source
        html += detail_text
        first_record=False

      #} # end loop through result sets

      if html: #{
        pag = pagination( rows_found = number_of_records, \
                          current_row = solr_start, \
                          rows_per_page = solr_rows, \
                          include_print_button = False )

        result_string = pag + start_treeview + html + end_inner_and_outer_sections
        result_string += '</ul><!-- end ID "tree" -->'
      #}
    #} # end of check on whether we retrieved a result
  #} # end of check on whether a search term was found in GET
    
  t = loader.get_template('mlgb/mlgb.html')

  c = Context( {
      'editable'         : editable,
      'result_string'    : result_string,
      'number_of_records': number_of_records,
      'search_term'      : search_term,
      'field_to_search'  : field_to_search,
      'field_label'      : get_searchable_field_label( field_to_search ),
      'searchable_fields': get_searchable_field_list(),
      'page_size'        : page_size,
      'page_sizes'       : get_page_sizes(),
      'default_rows_per_page': str( default_rows_per_page ),
      'pagename'         : pagename,
  } )

  return HttpResponse( t.render( c ) )

#}
# end function mlgb() (search results)
#--------------------------------------------------------------------------------
def mlgb_e( request, pagename = 'results' ): #{
  enable_edit()
  return mlgb( request, pagename )
#}
#--------------------------------------------------------------------------------

# Function book() calls up the detail page for one single book.

def book( request, book_id, pagename = 'book' ): #{

  try:
    bk = Book.objects.get( pk = book_id )

    ev = {}
    evidence_code = bk.evidence
    evidence_desc = 'no evidence'

    try:
      ev = Evidence.objects.get( evidence = evidence_code )
      evidence_desc = ev.evidence_description

    except Evidence.DoesNotExist:
      pass

  except Book.DoesNotExist:
    raise Http404

  # See if they have entered a search to get here.
  # If so, allow them to repeat it.
  search_term = get_value_from_GET( request, 'search_term' )
  field_to_search = get_value_from_GET( request, "field_to_search" )
  page_size = get_value_from_GET( request, "page_size" ) 
  
  t = loader.get_template('mlgb/mlgb_detail.html')

  c = Context( { 'id': book_id, 
                 'object': bk,
                 'pagename': pagename,
                 'search_term': search_term,
                 'editable': editable,
                 'field_to_search': field_to_search,
                 'searchable_fields': get_searchable_field_list(),
                 'page_size': page_size,
                 'page_sizes': get_page_sizes(),
                 'default_rows_per_page': str( default_rows_per_page ),
                 'evidence_desc': evidence_desc  } )

  return HttpResponse(t.render(c))
#}
# end function book()
#--------------------------------------------------------------------------------
def book_e( request, book_id, pagename = 'book' ): #{
  enable_edit()
  return book( request, book_id, pagename )
#}
#--------------------------------------------------------------------------------

# The function browse() allows browsing by modern location and shelfmark

def browse( request, letter = 'A', pagename = 'browse' ): #{

  html = detail_text = result_string = resultsets = expand_2nd_row = ""
  number_of_records = solr_rows = solr_query = solr_sort = field_to_search = page_size = ""
  letters = []
  first_record = True

  space = newline + '<span class="spacer">' + newline + '</span>' + newline
  two_spaces = space + space

  # Set default field to search, records per page and start row, 
  # for use in pagination and 'search again' functionality.
  field_to_search = 'location' # this is used in the 'Search' box on the right-hand side
  solr_field_to_search = 'ml1_initial'
  page_size = str( default_rows_per_page )
  solr_start = 0

  if request.GET: #{ # are there any parameters in GET?
    # Get actual records per page and start row from GET
    page_size = get_value_from_GET( request, "page_size", str( default_rows_per_page )) 
    solr_start = get_value_from_GET( request, "start", 0 ) 

    # They may also have chosen to browse by a different sort field
    field_to_search = get_value_from_GET( request, "order_by", field_to_search ) 
    if field_to_search == 'modern_library':
      solr_field_to_search = 'ml2_initial'
    elif field_to_search == 'medieval_library':
      solr_field_to_search = 'pr_initial'

    # They may have chosen expand/collapse options
    expand_2nd_row = get_value_from_GET( request, "expand", "no" ) 
  #}

  # Construct Solr query
  if not letter.isalpha(): letter = 'A'
  solr_query = '%s:%s' % (solr_field_to_search, letter.upper())
  
  # Set page size
  if page_size.isdigit():
    solr_rows = int( page_size )
  else: 
    solr_rows=Book.objects.count()
  
  # Set sort field
  if field_to_search == 'modern_library':
    solr_sort = ", ".join( get_modern_library_sortfields() )
  elif field_to_search == 'medieval_library':
    solr_sort = ", ".join( get_provenance_sortfields() )
  else:
    solr_sort = ", ".join( get_location_sortfields() )

  # Run the Solr query
  s_para={'q'    : solr_query,
          'wt'   : s_wt,  # 's_wt', i.e. 'writer type' is set in config.py, defaults to "json"
          'start': solr_start, 
          'rows' : solr_rows,
          'sort' : solr_sort}
  r=MLGBsolr()
  r.solrresults( s_para, Facet=facet )


  # Start to display the results
  if r.connstatus and r.s_result: #{ #did we retrieve a result?

    resultsets = r.s_result.get( 'docs' )
    number_of_records = r.s_result.get( 'numFound' )
    
    prev_heading = heading = ""
    html = get_expand_collapse_script()

    if expand_2nd_row == "yes": #{
      class_of_2nd_row = browse_expanded_class
      concertina_label = '-'
    #}
    else: #{
      class_of_2nd_row = browse_collapsed_class
      concertina_label = '+'
    #}

    # Start loop through result sets
    for i in xrange( 0, len( resultsets ) ): #{

      # Get the data from the Solr result set
      (id, provenance, modern_location1, modern_location2, shelfmark1, shelfmark2,
      evidence_code, evidence_desc, suggestion_of_contents, date_of_work,
      pressmark, medieval_catalogue, unknown, notes_on_evidence) = \
      extract_from_result( resultsets[i], False ) # here False means 'don't add punctuation'

      unformatted_provenance = extract_unformatted_provenance( resultsets[i] ) # no italics etc

      if field_to_search == 'medieval_library':
        heading = provenance
      elif field_to_search == 'modern_library':
        heading = get_modern_location_heading( modern_location2, modern_location1 )
      else:
        heading = get_modern_location_heading( modern_location1, modern_location2 )

      if prev_heading.lower() <> heading.lower(): #{  # change in heading

        if first_record:
          first_record=False
        else:
          html += newline + '</div><!-- end div browseresults -->' + newline

        html += newline + "<h3>" + newline
        html += '<p>'
        html += heading
        html += '</p>'
        html += newline + "</h3>" + newline
        html += '<div class="browseresults">' + newline
        prev_heading = heading
      #}

      # Now set up the 'detail' text
      detail_text = newline + '<!-- start book ID ' + id + ' -->' + newline
      detail_text += '<div class="book_row_1">' + newline

      booklink_start = get_booklink_start( id, '', field_to_search, page_size )

      # Expand/collapse button
      detail_text += newline + '<div class="browse_concertina">'
      detail_text += get_expand_collapse_button( id, concertina_label )
      detail_text += newline + '</div><!-- end concertina button -->'

      # Evidence
      detail_text += newline + '<div class="browse_evidence">' + newline
      if evidence_code: #{
        detail_text += get_evidence_decoder_button( evidence_code, evidence_desc )
      #}
      else:
        detail_text += space
      detail_text += ' <!-- type of evidence -->'
      detail_text += newline + '</div><!-- end evidence -->' + newline

      # Shelfmarks
      detail_text += newline + '<div class="browse_shelfmarks">' + newline
      if shelfmark1 or shelfmark2: #{
        detail_text += booklink_start
        detail_text += '%s <!-- shelfmark 1 -->' %  shelfmark1 
        if shelfmark2: #{
          detail_text += space
          detail_text += '%s <!-- shelfmark 2 -->' %  shelfmark2 
        #}
        detail_text += '</a>'
      #}
      else:
        detail_text += space
      detail_text += newline + '</div><!-- end shelfmarks -->' + newline

      # Author/title
      detail_text += newline + '<div class="browse_authortitle">' + newline
      if suggestion_of_contents: #{
        detail_text += booklink_start
        detail_text += suggestion_of_contents + ' <!-- author/title -->'
        detail_text += '</a>'
      #}
      else:
        detail_text += space
      detail_text += newline + '</div><!-- end author/title -->' + newline

      # Provenance OR modern library
      if field_to_search == 'medieval_library': #{ # show modern location in detail text
        detail_text += newline + '<div class="browse_modern_library">' + newline
        if modern_location1 or modern_location2 : #{
          modern_location = modern_location1.strip()
          if modern_location1 and modern_location2 :
            modern_location += ', '
          modern_location += modern_location2.strip()
          detail_text += '<a href="%s/?search_term=%s&field_to_search=modern_library">' \
                      % (baseurl, quote( modern_location.encode( 'utf-8' ) ))
          detail_text += modern_location + ' <!-- modern location -->'
          detail_text += '</a>'
        #}
        else:
          detail_text += space
        detail_text += newline + '</div><!-- end provenance -->' + newline
      #}
      else: #{ # show medieval library/provenance in detail text
        detail_text += newline + '<div class="browse_provenance">' + newline
        if provenance : #{
          detail_text += '<a href="%s/?search_term=%s&field_to_search=medieval_library">' \
                      % (baseurl, quote( unformatted_provenance.encode( 'utf-8' ) ))
          detail_text += provenance + ' <!-- provenance -->'
          detail_text += '</a>'
        #}
        else:
          detail_text += space
        detail_text += newline + '</div><!-- end provenance -->' + newline
      #}

      detail_text += newline + '<div class="browse_editlink">' + newline
      if editable: #{
        detail_text += '<a href="/admin/books/book/%s" title="Edit this record" target="_blank"' % id
        detail_text += ' class="editlink">'
        detail_text += 'Edit' + '</a>' + newline
      #}
      detail_text += newline + '</div><!-- end edit link -->' + newline

      detail_text += '</div><!-- end book_row_1 -->' + newline

      # Now start an optionally hidden row for the rest...
      detail_text += '<div id="%s" class="%s">' % (get_2nd_row_id( id ), class_of_2nd_row)
      detail_text += newline
     
      detail_text += newline + '<ul>' + newline

      if evidence_desc : #{
        detail_text += '<li>Evidence: ' + evidence_desc + ' <!-- evidence description -->'
        detail_text += '</li>' + newline
      #}

      if date_of_work : #{
        detail_text += '<li>Date: ' + date_of_work + ' <!-- date of work -->'
        detail_text += '</li>' + newline
      #}

      if pressmark : #{
        detail_text += '<li>Pressmark: ' + pressmark + ' <!-- pressmark -->'
        detail_text += '</li>' + newline
      #}

      if medieval_catalogue : #{
        detail_text += '<li>Medieval catalogue: ' + medieval_catalogue + ' <!-- medieval catalogue -->'
        detail_text += '</li>' + newline
      #}

      if unknown : #{
        detail_text += '<li>' + unknown + ' <!-- unknown -->'
        detail_text += '</li>' + newline
      #}
      detail_text += newline + '</ul>' + newline

      detail_text += '</div><!-- end book ID ' + id + ' -->' + newline + newline

      # Add the string of HTML that you have generated for this record to the main HTML source
      html += detail_text

    #} # end loop through result sets
    if number_of_records > 0:  #{

      html += newline + '</div><!-- end browseresults -->' + newline

      alphabet = '<div class="letterlinks">'
      initials = get_initial_letters( solr_field_to_search )
      for initial in initials: #{
        alphabet += '<a href="%s/browse/%s/?order_by=%s" ' % (baseurl, initial, field_to_search)
        if initial == letter.upper(): alphabet += ' class="selected" '
        alphabet += '>%s</a>' % initial
        alphabet += space
      #}
      alphabet += '</div><!-- letterlinks -->'

      pag = pagination( rows_found = number_of_records, \
                        current_row = solr_start, \
                        rows_per_page = solr_rows, \
                        include_print_button = False )

      option_string = get_browse_display_options( request, letter, number_of_records, solr_rows )

      result_string = alphabet + pag + option_string + html 

      if number_of_records > solr_rows: # repeat pagination at the bottom
        result_string += '<br>' + pag + '<br>'
    #}
  #} # end of check on whether we retrieved a result
    
  page_title = 'Browsing by %s and ' % get_searchable_field_label( field_to_search )
  if field_to_search == 'medieval_library':
    page_title += 'modern location'
  else:
    page_title += 'shelfmark'
  page_title += ": %s" % letter

  t = loader.get_template('mlgb/browse.html')

  # Get data to fill in the 'Categories' box in the righthand sidebar
  (medieval_library_count, modern_library_count, location_count) = get_category_counts()

  c = Context( {
      'editable'         : editable,
      'result_string'    : result_string,
      'number_of_records': number_of_records,
      'letter'           : letter,
      'field_to_search'  : field_to_search,
      'field_label'      : get_searchable_field_label( field_to_search ),
      'searchable_fields': get_searchable_field_list(),
      'page_size'        : page_size,
      'page_sizes'       : get_page_sizes(),
      'default_rows_per_page': str( default_rows_per_page ),
      'pagename'         : pagename,
      'page_title'       : page_title,
      'medieval_library_count': medieval_library_count,
      'modern_library_count'  : modern_library_count,
      'location_count'        : location_count,
  } )

  return HttpResponse( t.render( c ) )

#}
# end function browse()
#--------------------------------------------------------------------------------
def browse_e( request, letter = 'A', pagename = 'browse' ): #{
  enable_edit()
  return browse( request, letter, pagename )
#}
#--------------------------------------------------------------------------------

# Function fulltext() seems to be used to generate 'auto-complete' settings for the search box
# on the Home page (see index.html)

def fulltext( request, pagename = 'fulltext' ): #{

  data=[]
  lists=[]

  data3=list(Book.objects.values('author_title').distinct().order_by('author_title'))
  data2=list(Modern_location_2.objects.values('modern_location_2').distinct().order_by('modern_location_2'))
  data1=list(Modern_location_1.objects.values('modern_location_1').distinct().order_by('modern_location_1'))
  data=list(Provenance.objects.values('provenance').distinct().order_by('provenance'))

  lists=[]

  for e in data : lists.append( e['provenance'] )
  for e in data1: lists.append( e['modern_location_1'] )
  for e in data2: lists.append( e['modern_location_2'] )
  for e in data3: lists.append( e['author_title'] )

  query = request.GET.get( "q", "" )
  lists = sorted( set(lists) )

  if len(query) == 0 or query[0] == " " :
    json = simplejson.dumps(lists)
  else:
    json = simplejson.dumps( [e for e in lists
                              if e.lower().find(query.lower()) != -1 ] )

  return HttpResponse(json, mimetype = 'application/json')
#}
# end fulltext
#--------------------------------------------------------------------------------

# It seems that function download() should be called from the 'record detail' page (mlgb_detail.html).
# However, the links to it are hidden.

def download( request, pagename = 'download' ): #{

  response=None
  data=[]
  text=""
  
  rc="\r\n"
  if request.GET[ "q" ] == "2": rc="<br/>"

  # Gather the data into a text field
  if request.GET: #{

    data = Book.objects.filter( id = request.GET["i"] )

    text =  "Provenance: %s%s"      % (data[0].provenance, rc)
    text += "Location: %s, %s%s"    % (data[0].modern_location_2, data[0].modern_location_1, rc)
    text += "Shelfmark: %s %s%s"    % (data[0].shelfmark_1, data[0].shelfmark_2, rc)
    text += "Author/Title: %s %s%s" % (data[0].evidence, data[0].author_title, rc)

    if data[0].date:
      text += "Date: %s%s" % (data[0].date, rc)
    
    if data[0].pressmark:
      text += "Pressmark: %s%s" % (data[0].pressmark, rc)
    
    if data[0].medieval_catalogue:
      text += "Medieval Catalogue: %s%s" % (data[0].medieval_catalogue, rc)
    
    if data[0].ownership:
      text += "Ownership: %s%s" % (data[0].ownership, rc)
    
    if data[0].notes.strip('" \n\r'):
      text += "Notes: %s" % (data[0].notes.strip('" \n\r'))
  #}

  # Either: write out a CSV file
  if request.GET[ "q" ] == "1": #{
    rc=""
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s.csv' % request.GET["i"]
    writer = csv.writer(response)

    text = text.replace("<p>","")
    text = text.replace("</p>","")
    text = text.replace("<strong>","")
    text = text.replace("</strong>","")
    text = text.replace("<em>","")
    text = text.replace("</em>","")
    text = text.replace('<span style="text-decoration: underline;">',"")
    text = text.replace("</span>","")
    text = text.replace("<i>","")
    text = text.replace("</i>","")
    text = text.replace("<ul>","")
    text = text.replace("</ul>","")
    text = text.replace("<li>","")
    text = text.replace("</li>","")
    text = text.replace("<ol>","")
    text = text.replace("</ol>","")
    text = text.replace('<span style="text-decoration: line-through;">',"")
    text = text.replace("&nbsp;","")
    
    writer.writerow([text])
    writer.writerows([data])
  #}

  # Or: write out a PDF
  elif request.GET[ "q" ] == "2": #{
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s.pdf' % request.GET["i"]

    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph,Frame,Spacer
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleH = styles['Heading1']
    story = []
    
    story.append(Paragraph("<i>%s</i>%s" % (data[0].evidence, data[0].author_title),styleH))
    story.append(Spacer(inch * .5, inch * .5))
    story.append(Paragraph(text,styleN))
    buffer = StringIO()
    p = Canvas(buffer)
    f = Frame(inch, inch, 6.3*inch, 9.8*inch, showBoundary=0)
    f.addFromList(story,p)
    p.save()
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
  #}

  else:
    pass

  return response
#}
# end download
#--------------------------------------------------------------------------------

def about( request, pagename = 'about' ): #{

  t = loader.get_template('mlgb/about.html')

  c = Context( { 'pagename': pagename, 
                 'editable': editable, 
               } )

  return HttpResponse( t.render( c ) )    
#}

#--------------------------------------------------------------------------------

def about_e( request, pagename = 'about' ): #{
  enable_edit()
  return about( request, pagename )
#}
#--------------------------------------------------------------------------------
#============== End of top-level functions called directly from URL =============
#--------------------------------------------------------------------------------

def trim( the_string, strip_double_quotes = True ): #{

  chars_to_strip = ' \r\n\t'
  if strip_double_quotes:
    chars_to_strip += '"'
  return the_string.strip( chars_to_strip )
#}
#--------------------------------------------------------------------------------

def escape_for_solr( search_term ): #{

  problem_chars = ['\\', '+', '-', '&', '|', '!', '(', ')', '{', '}', '[', ']', '^', '~',  \
                   '?', ':', '"', ';' ]

  for c in problem_chars: #{
    if c not in search_term: continue

    escaped = '\\' + c

    # unescape first, just in case - we don't want to escape twice
    if escaped in search_term:
      search_term = search_term.replace( escaped, c )

    # now escape by putting a backslash before that character
    search_term = search_term.replace( c, escaped )
  #}

  return search_term.encode( 'utf-8' )
#}
#--------------------------------------------------------------------------------

def extract_from_result( resultset, add_punctuation = True ): #{

  # ID
  id = resultset['id']

  # Provenance
  provenance = trim( resultset['pr'], False )
  provenance = provenance.upper()

  # County
  if resultset['ct']:
    provenance += ", " + trim( resultset['ct'], False )

  # Institution
  if resultset['ins']:
    provenance += ", <i>" + trim( resultset['ins'] ) + "</i>"

  # Modern library 1
  modern_location1 = trim( resultset['ml1'], False )

  # Modern library 2
  modern_location2 = trim( resultset['ml2'] )
  if modern_location2 and add_punctuation: modern_location2 += ','

  # shelfmark 1
  shelfmark1 = trim( resultset['sm1'] )

  # shelfmark 2
  shelfmark2 = trim( resultset['sm2'] )
  if shelfmark2: #{
    if add_punctuation and not shelfmark2.endswith( '.' ): shelfmark2 += '.'
  #}

  # make sure there is a full stop at the end of the combined shelfmarks
  elif shelfmark1: #{
    if add_punctuation and not shelfmark1.endswith( '.' ): shelfmark1 += '.'
  #}

  # evidence code
  evidence_code = trim( resultset['ev'] )
  # evidence desc
  evidence_desc = trim( resultset['evdesc'], False )
  
  # suggestion of contents
  suggestion_of_contents = trim( resultset['soc'], False )

  # date
  date_of_work = trim( resultset['dt'] )
  if date_of_work: #{ 
    if add_punctuation and not date_of_work.endswith( '.' ): 
      date_of_work += '.'
  #}
  
  # pressmark
  pressmark = trim( resultset['pm'] )
  if pressmark: #{
    if add_punctuation and not pressmark.endswith( '.' ): 
      pressmark += '.'
  #}

  # medieval catalogue
  medieval_catalogue = trim( resultset['mc'] )
  if medieval_catalogue: #{
    if add_punctuation: 
      medieval_catalogue = '[' + medieval_catalogue + ']'
  #}
  
  # unknown
  unknown = trim( resultset['uk'] )
  if unknown: #{
    if add_punctuation and not unknown.endswith( '.' ) and not unknown.endswith( '?' ): 
      unknown += '.'
  #}

  # notes
  notes_on_evidence = trim( resultset['nt'] )
  if notes_on_evidence: #{
    if add_punctuation and not notes_on_evidence.endswith( '.' ): 
      notes_on_evidence += '.'
  #}


  return (id, provenance, modern_location1, modern_location2, shelfmark1, shelfmark2,
          evidence_code, evidence_desc, suggestion_of_contents, date_of_work,
          pressmark, medieval_catalogue, unknown, notes_on_evidence)

#}
#--------------------------------------------------------------------------------

def extract_unformatted_provenance( resultset ): #{ # no added italics etc

  unformatted_provenance = trim( resultset['pr'] ) 

  # County
  if resultset['ct']:
    unformatted_provenance += ", " + trim( resultset['ct'] )

  # Institution
  if resultset['ins']:
    unformatted_provenance += ", " + trim( resultset['ins'] )

  return unformatted_provenance
#}
#--------------------------------------------------------------------------------
## This function was copied from code written by Mat Wilcoxson for EMLO/Cultures of Knowledge
## with some adaptation by Sue B.

def pagination( rows_found, current_row, rows_per_page=None, include_print_button=False ): #{

  html = newline  # we'll build up all the pagination links in the 'html' string

  if rows_per_page == None:
    rows_per_page = default_rows_per_page
  button_title = ""

  ##=======================================================================
  ## Write some Javascript to change the GET parameters to a new start row.
  ##=======================================================================
  page_change_scriptname = 'js_go_to_row' 
  script = write_page_change_script( page_change_scriptname )
  html += script


  ##==========================================================================
  ## Work out how many rows and pages you have got, and which page you are on.
  ##==========================================================================
  rows_found    = int( rows_found )
  current_row   = int( current_row )
  rows_per_page = int( rows_per_page )

  first_page_start = 0

  if rows_found % rows_per_page == 0 :
    last_page_start = rows_found - rows_per_page
  else :
    last_page_start = rows_found - (rows_found % rows_per_page)

  page_count = int( last_page_start / rows_per_page ) + 1

  current_page = (current_row / rows_per_page) + 1
  
  pages_to_jump = 10  # provide arrow buttons allowing you to jump 10 pages

  jump_back_to_row = current_row - (pages_to_jump*rows_per_page)
  full_backwards_jump = True
  if jump_back_to_row < first_page_start: #{
    jump_back_to_row = first_page_start
    jump_back_to_page = 1
    full_backwards_jump = False
  #}
  else: #{
    jump_back_to_page = (jump_back_to_row / rows_per_page) + 1; # row 0 is on page 1
  #}

  jump_forwards_to_row = current_row + (pages_to_jump*rows_per_page)
  full_forwards_jump = True
  if jump_forwards_to_row > last_page_start: #{
    jump_forwards_to_row = last_page_start
    jump_forwards_to_page = page_count
    full_forwards_jump = False
  #}
  else: #{
    jump_forwards_to_page = (jump_forwards_to_row / rows_per_page) + 1; # if we have 10 rows per page, 
                                                                        # row 20 will be on p3 not p2
  #}

  two_pages = rows_per_page * 2

  ##===============================================================================
  ## Tell the user how many rows and pages you have got, and which page you are on.
  ##===============================================================================
  if rows_found < 1: #{
    html += '<p> <strong> No records found. </strong> </p>' + newline
    return html
  #}

  html += '<div class="pagination">' + newline
  html += '<p>' + newline
  html += '<strong>' + newline
  if rows_found == 1:
    html += 'One record found.' + newline
  else:
    html += str(rows_found) + ' records found.' + newline
  html += '</strong>' + newline

  ##================================================================
  ## If you have more than one page, display page navigation buttons
  ##================================================================
  if page_count > 1 : #{

    html += '<span class="spacer">' + newline
    html += 'Page %d of %d (%d records per page). ' % (current_page, page_count, rows_per_page)
    html += '</span>' + newline
    html += '<br>' + newline

    ##=========================================================================================
    ##====================== start of section with 'jump to page' buttons =====================
    ##=========================================================================================
    ## "Jump backwards" section
    ##=========================

    if current_row == first_page_start : #{

      ## At the start of the first page, so don't provide a 'First' button
      html += '<button class="selected_page" disabled="disabled">First</button>' + newline
      html += '<button class="selected_page" disabled="disabled">&lt;&lt;</button>' + newline

      html += '<span class="spacer">&nbsp;</span>' + newline
      html += '<span class="spacer">&nbsp;</span>' + newline
    #}
    else: #{

      ## Not at the start of the first page, so DO provide a 'First' button
      html += '<button class="go_to_page" '
      html += ' onclick="%s( %d )"' % (page_change_scriptname, first_page_start)
      html += ' title="Go to first page of results">' + newline
      html += 'First' + newline
      html += '</button>' + newline
        
      ## Also provide a 'jump backwards by multiple pages' button
      if rows_found > rows_per_page : #{
        if full_backwards_jump:
          button_title = "Jump back %d pages to page %d of results" % (pages_to_jump, jump_back_to_page)
        else:
          button_title = "Go to page %d of results" % jump_back_to_page
        html += '<button class="go_to_page" '
        html += ' onclick="%s( %d )" ' % (page_change_scriptname, jump_back_to_row)
        html += ' title="%s">' % button_title
        html += newline + '&lt;&lt;' + newline
        html += '</button>' + newline
      #}

      html += '<span class="spacer">&nbsp;</span>' + newline
      
      ## If more than 2 pages from start, put dots to show we're jumping across a block of pages
      if current_row - two_pages > first_page_start: #{
        html += '...' + newline
      #}

      html += '<span class="spacer">&nbsp;</span>' + newline

      ## If at least 2 pages from start, provide a 'back 2 pages' button
      if current_row - two_pages >= first_page_start : #{
        html += '<button class="go_to_page" '
        html += ' onclick="%s( %d )" ' % ( page_change_scriptname, current_row-two_pages ) 
        target_page = current_page - 2
        html += ' title="Go to page %d of results">' % target_page
        html += str( target_page ) + newline
        html += '</button>' + newline
      #}
      
      ## If at least 1 page from start, provide a 'back 1 page' button
      if current_row - rows_per_page >= first_page_start : #{
        html += '<button class="go_to_page" '
        html += ' onclick="%s( %d )" ' % ( page_change_scriptname, current_row-rows_per_page ) 
        target_page = current_page - 1
        html += ' title="Go to page %d of results">' % target_page
        html += str( target_page ) + newline
        html += '</button>' + newline
      #}
    #} ## End of "if we are on the first page" ("jump backwards" section)
    ##=========================================================================================

    ## Display the current page number
    html += newline 
    html += '<button class="selected_page" disabled="disabled">%d</button>' % current_page 
    html += newline 

    ##=========================================================================================
    ## "Jump forwards" section
    ##========================

    ## If at least 1 page from end, provide a 'forward 1 page' button
    if current_row + rows_per_page <= last_page_start : #{
      html += '<button class="go_to_page" '
      html += ' onclick="%s( %d )" ' % ( page_change_scriptname, current_row+rows_per_page ) 
      target_page = current_page + 1
      html += ' title="Go to page %d of results">' % target_page
      html += str( target_page ) + newline
      html += '</button>' + newline
    #}
    
    ## If at least 2 pages from end, provide a 'forward 2 pages' button
    if current_row + two_pages <= last_page_start : #{
      html += '<button class="go_to_page" '
      html += ' onclick="%s( %d )" ' % ( page_change_scriptname, current_row+two_pages ) 
      target_page = current_page + 2
      html += ' title="Go to page %d of results">' % target_page
      html += str( target_page ) + newline
      html += '</button>' + newline
    #}
    
    ## If more than 2 pages from end, put dots to show we're jumping across a block of pages
    html += '<span class="spacer">&nbsp;</span>' + newline
    if current_row + two_pages < last_page_start: #{
      html += '...' + newline
    #}

    html += '<span class="spacer">&nbsp;</span>' + newline

    if current_row == last_page_start : #{
      ## At the start of the last page, so don't provide a 'Last' button
      html += '<button class="selected_page" disabled="disabled">&gt;&gt;</button>' + newline
      html += '<button class="selected_page" disabled="disabled">Last</button>' + newline
    #}
    else : #{
      ## NOT at the start of the last page, so DO provide 'jump forward' and 'Last' buttons
      if rows_found > rows_per_page : #{
        if full_forwards_jump:
          button_title = "Jump forwards %d pages to page %d of results" \
                       % (pages_to_jump, jump_forwards_to_page)
        else:
          button_title = "Go to page %d of results" % jump_forwards_to_page

        html += '<button class="go_to_page" '
        html += ' onclick="%s( %d )" ' % (page_change_scriptname, jump_forwards_to_row)
        html += ' title="%s">' % button_title
        html += '&gt;&gt;' + newline
        html += '</button>' + newline
      #}

      html += '<button class="go_to_page" '
      html += ' onclick="%s( %d )"' % (page_change_scriptname, last_page_start)
      html += ' title="Go to last page of results">' + newline
      html += 'Last' + newline
      html += '</button>' + newline
    #}
    ## End of 'if we are on the last page' ("jump forwards" section)
    ##=========================================================================================
    ##====================== end of section with 'jump to page' buttons =======================
    ##=========================================================================================
  #} ## end of 'if page count > 1'

  if include_print_button: #{
    # Although 'print' button is not part of pagination, could be convenient
    # to have it on same line, so, if required, add 'print' button here.
    pass
  #}

  html += '</p>' + newline
  html += '</div><!--class:pagination-->' + newline
  html += newline

  return html
#}
#--------------------------------------------------------------------------------

def write_page_change_script( page_change_scriptname ): #{

  script = newline

  script += '  <script type="text/javascript">' + newline
  script += '  function ' + page_change_scriptname + '( rowNumber ) {' + newline

  script += '    var foundStart = false;' + newline

  script += '    rowNumber = parseInt( rowNumber );' + newline
  script += '    if( isNaN( rowNumber )) {' + newline
  script += '      alert( \'Invalid row number.\' );' + newline
  script += '      return;' + newline
  script += '    }' + newline

  script += '    var search = window.location.search;' + newline
  script += '    if( search.length == 0 ) {' + newline
  script += '      window.location.search = \'?start=\' + rowNumber;' + newline
  script += '      return;' + newline
  script += '    }' + newline

  script += '    var parts = search.split( \'&\' );' + newline
  script += '    var numParts = parts.length;' + newline

  script += '    for( i = 0; i < numParts; i++ ) {' + newline
  script += '      var part = parts[ i ];' + newline
  script += '      if( i == 0 ) {' + newline
  script += '        var firstChar = part.substring( 0, 1 );' + newline
  script += '        if( firstChar == \'?\' ) {       // that\'s what it *should* be!' + newline
  script += '          part = part.substring( 1 );  // trim off the leading question mark' + newline
  script += '          parts[i] = part;' + newline
  script += '        }' + newline
  script += '      }' + newline

  script += '      var pair = part.split( \'=\' );' + newline
  script += '      if( pair.length == 2 ) { // once again, that\'s what it *should* be!' + newline
  script += '        var searchName = pair[0];' + newline
  script += '        if( searchName == \'start\' ) {' + newline
  script += '          foundStart = true;' + newline
  script += '          parts[i] = searchName + \'=\' + rowNumber;' + newline
  script += '          break;' + newline
  script += '        }' + newline
  script += '      }' + newline
  script += '      else {' + newline
  script += '        alert( \'Invalid search term(s).\' );' + newline
  script += '        return;' + newline
  script += '      }' + newline
  script += '    }' + newline

  script += '    var newSearch = \'?\' + parts.join( \'&\' );' + newline

  script += '    if( ! foundStart ) {' + newline
  script += '      newSearch = newSearch + \'&start=\' + rowNumber;' + newline
  script += '    }' + newline
  script += '    window.location.search = newSearch;' + newline
  script += '  }' + newline
  script += '  </script>' + newline + newline

  return script
#}
#--------------------------------------------------------------------------------

def get_value_from_GET( request, key, default_value = '' ): #{

  value = default_value
  if request.GET: #{
    if request.GET.has_key( key ): #{
      value = request.GET[ key ].strip()
    #}
  #}
  return value
#}
#--------------------------------------------------------------------------------

def get_searchable_field_list(): #{

  fields = [ { ""                : 'All fields' },
             { 'author_title'    : 'Author/Title' },
             { 'location'        : 'Location' },
             { 'medieval_library': 'Medieval Library' },
             { 'modern_library'  : 'Modern Library/Institution' },
             { 'shelfmark'       : 'Shelfmark' } ]

  return fields
#}
#--------------------------------------------------------------------------------

def get_page_sizes(): #{

  sizes = [ '100', '200', '500', '1000', 'All' ]
  return sizes
#}
#--------------------------------------------------------------------------------

def get_searchable_field_label( field_to_search = 'medieval_library' ): #{

  searchable_field_label = ''
  searchable_fields = get_searchable_field_list()
  for fieldname_and_desc in searchable_fields: #{
    if fieldname_and_desc.has_key( field_to_search ): #{
      searchable_field_label = fieldname_and_desc[ field_to_search ]
      break
    #}
  #}
  return searchable_field_label
#}
#--------------------------------------------------------------------------------

def get_modern_location_heading( modern_location1, modern_location2 ): #{

  heading = modern_location1.strip()
  if modern_location1 and modern_location2: heading += ', ' 
  heading += modern_location2.strip()
  return heading
#}
#--------------------------------------------------------------------------------

def get_author_title_sortfields(): #{

  author_title_sortfields = [ 'soc asc',           # suggestion of contents, i.e. author/title
                              'ev asc',            # evidence code
                              'prsort asc',        # provenance (place, e.g. town/city)
                              'ctsort asc',        # provenance (county)
                              'inssort asc',       # provenance (institution name)
                              'ml1sort asc',       # modern location 1 (city etc)
                              'ml2sort asc',       # location location 2 (library name)
                              'shelfmarksort asc', # shelfmark in numerically-sortable format
                              'id asc']

  return author_title_sortfields
#}
#--------------------------------------------------------------------------------

def get_provenance_sortfields(): #{

  provenance_sortfields = [ 'prsort asc',        # provenance (place, e.g. town/city)
                            'ctsort asc',        # provenance (county)
                            'inssort asc',       # provenance (institution name)
                            'ml1sort asc',       # modern location 1 (city etc)
                            'ml2sort asc',       # location location 2 (library name)
                            'shelfmarksort asc', # shelfmark in numerically-sortable format
                            'soc asc',           # suggestion of contents, i.e. author/title
                            'ev asc',            # evidence code
                            'id asc']

  return provenance_sortfields
#}
#--------------------------------------------------------------------------------

def get_location_sortfields(): #{

  location_sortfields = [  'ml1sort asc',       # modern location 1 (city etc)
                           'ml2sort asc',       # location location 2 (library name)
                           'shelfmarksort asc', # shelfmark in numerically-sortable format
                           'soc asc',           # suggestion of contents, i.e. author/title
                           'ev asc',            # evidence code
                           'prsort asc',        # provenance (place, e.g. town/city)
                           'ctsort asc',        # provenance (county)
                           'inssort asc',       # provenance (institution name)
                           'id asc']

  return location_sortfields
#}
#--------------------------------------------------------------------------------

def get_modern_library_sortfields(): #{

  shelfmark_sortfields = [ 'ml2sort asc',       # location location 2 (library name)
                           'ml1sort asc',       # modern location 1 (city etc)
                           'shelfmarksort asc', # shelfmark in numerically-sortable format
                           'soc asc',           # suggestion of contents, i.e. author/title
                           'ev asc',            # evidence code
                           'prsort asc',        # provenance (place, e.g. town/city)
                           'ctsort asc',        # provenance (county)
                           'inssort asc',       # provenance (institution name)
                           'id asc']

  return shelfmark_sortfields
#}
#--------------------------------------------------------------------------------

def get_evidence_decoder_button( evidence_code = '', evidence_desc = '' ): #{

  button_text = ''

  alert_text = evidence_desc.replace( "'", "\\'" )
  alert_text = alert_text.replace( '"', "\\'" )

  button_text += '<button class="evidence_decoder"'
  button_text += ' title="%s" ' % alert_text
  button_text += ' onclick="alert(' + "'" + alert_text + "'" + ')">'
  button_text += evidence_code
  button_text += '</button>'

  return button_text
#}
#--------------------------------------------------------------------------------

def get_booklink_start( book_id = '', search_term = '', field_to_search = '', page_size = '' ): #{

  booklink = '<!-- start booklink -->' + newline
  booklink += '<a href="%s/book/%s/' % (baseurl, book_id)

  s = '?'

  # Pass in your search, so that they can search again from the detail page
  if search_term and search_term != '*': #{
    booklink += '%ssearch_term=%s' % (s, quote( search_term.encode( 'utf-8' ) ))
    s = '&'
  #}

  if field_to_search: #{
    booklink += '%sfield_to_search=%s' % (s, quote( field_to_search.encode( 'utf-8' ) ))
    s = '&'
  #}

  if page_size: #{
    booklink += '%spage_size=%s' % (s, quote( page_size.encode( 'utf-8' ) ))
    s = '&'
  #}

  booklink += '" class="booklink">'
  return booklink
#}
#--------------------------------------------------------------------------------

def get_initial_letters( facet_field ): #{

  facet = True
  facet_results = {}
  letters = []

  s_para = {'q'    : '*:*',
            'wt'   : s_wt,
            'start': 0, 
            'rows' : 0,
           }

  s_para[ 'facet.mincount' ] = '1'
  s_para[ 'facet'          ] = 'on'
  s_para[ 'facet.limit'    ] = '-1'
  s_para[ 'facet.field'    ] = [ facet_field ]

  facet_getter = MLGBsolr()

  facet_getter.solrresults( s_para, Facet=facet )

  if facet_getter.connstatus and facet_getter.s_result: #{
    facet_results = facet_getter.s_result.get( 'facet' )
    letters_and_counts = facet_results[ facet_field ]
  #}
  
  i = 0
  for letter_or_count in letters_and_counts: #{ odd-numbered entries = letter, even-numbered = count
   i += 1
   if i % 2: 
     letters.append( letter_or_count )
  #}

  return letters
#}
#--------------------------------------------------------------------------------

def get_expand_collapse_button( book_id, label = '+' ): #{

  button_id = "concertina%s" % book_id

  button_text = '<button name="%s" id="%s" ' % (button_id, button_id)
  button_text += ' value="%s" ' % label
  button_text += ' onclick="expand_or_collapse_2nd_row( %s, this.value )" ' % book_id
  button_text += '>%s</button>' % label

  return button_text
#}
#--------------------------------------------------------------------------------

def get_2nd_row_id( book_id ): #{
  return "book_row_2_%s" % book_id
#}
#--------------------------------------------------------------------------------

def get_expand_collapse_script(): #{

  script = newline + newline

  script += '<script type="text/javascript">'                             + newline
  script += 'function expand_or_collapse_2nd_row( book_id, new_value ) {' + newline

  script += '  var button_id = "concertina" + book_id;'                   + newline
  script += '  var the_button = document.getElementById( button_id );'    + newline

  script += '  var row_id = "%s" + book_id;' % get_2nd_row_id( "" )       + newline
  script += '  var the_row = document.getElementById( row_id );'          + newline

  script += '  if( new_value == "+" ) {'                                  + newline
  script += '    the_row.className = "%s";' % browse_expanded_class       + newline
  script += '    the_button.value = "-";'                                 + newline
  script += '    the_button.innerHTML = "-";'                             + newline
  script += '  }'                                                         + newline
  script += '  else {'                                                    + newline
  script += '    the_row.className = "%s";' % browse_collapsed_class      + newline
  script += '    the_button.value = "+";'                                 + newline
  script += '    the_button.innerHTML = "+";'                             + newline
  script += '  }'                                                         + newline
  script += '}'                                                           + newline
  script += '</script>'                                                   + newline

  script += newline + newline

  return script
#}
#--------------------------------------------------------------------------------

def get_browse_display_options( request, letter = 'A', rows_found = 0, rows_per_page = 0 ): #{

  options = ""
  new_search = "%s/browse/%s/" % (baseurl, letter)
  delim = "?"

  # For expand/collapse options, preserve 
  # any existing parameters except 'expand'
  if request.GET: #{  # 
    for k, v in request.GET.items(): #{

      if k == 'expand': continue

      new_search += delim
      new_search += "%s=%s" % (k, quote( v.encode( 'utf-8' )))

      if delim == "?": delim = "&"
    #}
  #}

  new_search += delim + "expand="
  expand_search = new_search + "yes"
  collapse_search = new_search + "no"

  options += '<a href="%s" title="Expand All">Expand All</a>' % expand_search
  options += ' | '
  options += '<a href="%s" title="Collapse All">Collapse All</a>' % collapse_search


  # For page size change option, preserve 
  # any existing parameters except 'page_size' and 'start'
  if rows_found > rows_per_page or rows_found > default_rows_per_page: #{
    delim = '?'
    new_search = ''

    if request.GET: #{  # 

      for k, v in request.GET.items(): #{

        if k == 'page_size': continue
        if k == 'start': continue

        new_search += delim
        new_search += "%s=%s" % (k, quote( v.encode( 'utf-8' )))

        if delim == "?": delim = "&"
      #}
    #}

    new_search += delim + "page_size="

    if rows_found > rows_per_page : #{
      new_search += 'All'
      new_title = 'Show as one page'
    #}
    elif rows_found > default_rows_per_page: #{
      new_search += str( default_rows_per_page )
      new_title = 'Paginate'
    #}

    options += ' | <a href="%s" title="%s">%s</a>' % (new_search, new_title, new_title)
  #}


  return options
#}
#--------------------------------------------------------------------------------

def get_category_counts(): #{

  facet = True
  facet_results = {}
  medieval_library_count = modern_library_count = location_count = 0

  s_para = {'q'    : '*:*',
            'wt'   : s_wt,
            'start': 0, 
            'rows' : 0,
           }

  s_para[ 'facet.mincount' ] = '1'
  s_para[ 'facet'          ] = 'on'
  s_para[ 'facet.limit'    ] = '-1'
  s_para[ 'facet.field'    ] = [ "pr_full", "ml1", "ml_full" ]

  r = MLGBsolr()

  r.solrresults( s_para, Facet=facet )

  if r.connstatus and r.s_result: #{
    facet_results = r.s_result.get( 'facet' )

    medieval_library_results = facet_results[ "pr_full" ]
    modern_library_results   = facet_results[ "ml_full" ]
    location_results         = facet_results[ "ml1" ]  

    # Each list consists of a series of key/value pairs, so is twice as long as the actual total.
    medieval_library_count = len( medieval_library_results ) / 2
    modern_library_count   = len( modern_library_results ) / 2
    location_count         = len( location_results ) / 2
  #}

  return (medieval_library_count, modern_library_count, location_count)
#}
# end get_category_counts()
#--------------------------------------------------------------------------------
