"""
# Main setup script for all MLGB front end web pages derived from the database of books.
# For author/title index, including medieval catalogues, see the 'authortitle' directory.

# An early version was written by Xiaofeng Yang, 2009-2010
# but this was very, very thoroughly rewritten by Sushila Burgess 2013-2014.
"""
#--------------------------------------------------------------------------------

from django.template          import Context, loader
from django.http              import HttpResponse,Http404,HttpResponseRedirect
from django.shortcuts         import get_object_or_404, render_to_response
from django.core.urlresolvers import reverse
from django.utils             import simplejson
from django.utils.html        import escape
from django.db                import connection
from urllib                   import quote, unquote
from cStringIO                import StringIO

import csv

from mysite.config          import *
from mysite.MLGBsolr        import *
from mysite.apache.settings import MEDIA_URL
from mysite.books.models    import *

#--------------------------------------------------------------------------------

editable = False
baseurl="/mlgb"
medieval_catalogue_url = "/authortitle/medieval_catalogues"

facet=False
default_rows_per_page = 500

default_output_style = 'treeview'
original_print_layout = 'ker_treeview'
possible_output_styles = [ default_output_style, 'table', original_print_layout ]

output_style = default_output_style

# sort by default on provenance (medieval library), then location/modern library, then shelfmark
default_order_by = 'provenance_location_shelfmark'
order_by = default_order_by

printing = False

prev_heading_1 = ""
prev_heading_2 = ""
browse_collapsed_class = "book_row_2_hidden"
browse_expanded_class = "book_row_2_displayed"

newline = '\n'
space = newline + '<span class="spacer"> </span>' + newline
two_spaces = space + space

#================= Top-level functions, called directly from URL ================
#--------------------------------------------------------------------------------
## This sets up the data for the Home page

def index( request, pagename = 'home', called_by_editable_page = False ): #{

  if called_by_editable_page: enable_edit()
  else: disable_edit()

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
  return index( request, pagename, True )
#}
#--------------------------------------------------------------------------------
## This changes links to exclude the 'editable' part of the URL  

def disable_edit(): #{

  global editable
  editable = False

  global baseurl
  baseurl = '/mlgb'
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
# or cities. Each item in the list links through to the search results function, i.e. results().
# In other words, a search will be run based on the name of the medieval library, etc.

def category( request, pagename = 'category', called_by_editable_page = False ): #{

  if called_by_editable_page: enable_edit()
  else: disable_edit()

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
  return category( request, pagename, True )
#}
#--------------------------------------------------------------------------------

def advanced_search( request, pagename = 'advancedsearch' ): #{

  if request.GET: # a search has already been entered
    return results( request, pagename, False, True )
  else:
    return advanced_search_form( request, pagename, False )
#}
#--------------------------------------------------------------------------------

def advanced_search_e( request, pagename = 'advancedsearch' ): #{

  if request.GET: # a search has already been entered
    return results( request, pagename, True, True )
  else:
    return advanced_search_form( request, pagename, True )
#}
#--------------------------------------------------------------------------------

# The function results() sets up display of search results

def results( request, pagename = 'results', called_by_editable_page = False, advanced_search = False ): #{

  if called_by_editable_page: enable_edit()
  else: disable_edit()

  global printing # are we about to print this page, or view it in onscreen mode?
  printing = False

  global output_style # 'treeview', 'table', or original print layout (subset of treeview)
  output_style = default_output_style

  global order_by
  order_by = ''

  global prev_heading_1 # these two globals allow us to see whether there has been a change of heading
  global prev_heading_2
  prev_heading_1 = ""
  prev_heading_2 = ""
  table_control_links = ""

  html = provenance = modern_location1 = result_string = search_term = resultsets = None
  number_of_records = solr_rows = solr_query = solr_sort = field_to_search = page_size = sql_query = ""
  pagination_change_link = ""
  first_record = True

  if request.GET: #{ # was a search term found in GET?

    # Check whether they are searching on a specific field
    if advanced_search:
      field_to_search = 'multiple'
    else:
      field_to_search = get_value_from_GET( request, "field_to_search" )

    # The field being searched may require a different order from the default,
    # or they may have chosen a different sort order themselves.
    order_by = get_value_from_GET( request, "order_by", field_to_search )

    # Check whether they want to print this page
    printing = get_value_from_GET( request, "printing", False )

    # Now run the Solr query
    if advanced_search:
      (resultsets, number_of_records, 
       field_to_search, search_term, solr_start, solr_rows, page_size ) = advanced_solr_query( request )
    else:
      (resultsets, number_of_records, 
       field_to_search, search_term, solr_start, solr_rows, page_size ) = basic_solr_query( request )

    # They may have chosen treeview, table or layout of original book
    # However, 'layout of original book' is only valid for ordering by provenance then location.
    output_style = get_value_from_GET( request, "output_style", default_output_style ) 
    reset_output_style_if_necessary()

    # They may have chosen expand/collapse options (used in 'table' mode)
    expand_2nd_tablerow = get_value_from_GET( request, "expand", "no" ) 

    # Start to display the results
    if number_of_records > 0 : #{ #did we retrieve a result?
      html = ""

      # Start loop through result sets
      for i in xrange( 0, len( resultsets ) ): #{

        if output_style == 'table':  #{
          if first_record: html = get_expand_collapse_script()

          text_for_one_record = display_as_table( resultsets[i], expand_2nd_tablerow, first_record, \
                                field_to_search, '', page_size )
        #}
        else: #{
          text_for_one_record = display_as_treeview( resultsets[i], first_record, \
                                field_to_search, search_term, page_size )
        #}

        # Add the string of HTML that you have generated for this record to the main HTML source
        html += text_for_one_record
        first_record=False

      #} # end loop through result sets

      if html: #{

        if output_style == 'table':  #{
          html += end_results_table()
          table_control_links = get_table_control_links( request, number_of_records, solr_rows )
          html = table_control_links + html
        #}
        else: #{
          html = wrap_in_tree( html )
        #}

        pagination_change_link = get_pagination_change_link( request, number_of_records, solr_rows )

        pag = pagination( rows_found = number_of_records, \
                          current_row = solr_start, \
                          rows_per_page = solr_rows, \
                          pagination_change_link = pagination_change_link, \
                          link_for_print_button = get_link_for_print_button( request ),
                          link_for_download_button = get_link_for_download_button( request ) )

        output_style_radio = get_output_style_change_field()
        order_by_select = get_order_change_field( 'any', order_by )

        result_string = pag
        result_string += '<p>' + order_by_select + space + output_style_radio + '</p>'
        result_string += html

        if number_of_records > solr_rows: # repeat pagination at the bottom
          result_string += '<br>' + pag + '<br>'
      #}
    #} # end of check on whether we retrieved a result
  #} # end of check on whether a search term was found in GET
    
  t = loader.get_template('mlgb/mlgb.html')

  template_vars = {
      'editable'         : editable,
      'result_string'    : result_string,
      'number_of_records': number_of_records,
      'page_size'        : page_size,
      'page_sizes'       : get_page_sizes(),
      'default_rows_per_page': str( default_rows_per_page ),
      'pagename'         : pagename,
      'order_options'    : get_order_change_field( 'any', order_by, False ),
      'output_styles'    : get_output_style_change_field( False ),
      'printing'         : printing,
      'advanced_search'  : advanced_search,
      'empty_form'       : False,
  }

  if advanced_search: #{ # could be searching on multiple fields at once
                         # pass all possible search fields, plus label and value if any, to template
    form_fields_searched = simplejson.loads( search_term )
    template_vars[ 'form_fields' ] = get_adv_search_form_fields_full( form_fields_searched )
    template_vars[ 'printed_book_radio_options' ] = printed_book_radio_options()
    template_vars[ 'evidence_dropdown_options' ] = evidence_search_options()
  #}

  else: #{ # quick search i.e. only on one field at once (as in Home page)
    template_vars[ 'searchable_fields'] = get_searchable_field_list()
    template_vars[ 'field_to_search'  ] = field_to_search
    template_vars[ 'field_label'      ] = get_searchable_field_label( field_to_search )
    template_vars[ 'search_term'      ] = search_term
  #}

  get_everything = False
  if advanced_search:
    if len( form_fields_searched ) == 0: get_everything = True
  else:
    if search_term == '*': get_everything = True
  template_vars[ 'get_everything' ] = get_everything


  c = Context( template_vars )

  return HttpResponse( t.render( c ) )

#}
# end function results() 
#--------------------------------------------------------------------------------
def results_e( request, pagename = 'results' ): #{
  return results( request, pagename, True )
#}
#--------------------------------------------------------------------------------
def advanced_search_form( request, pagename = 'advancedsearch', called_by_editable_page = False ): #{
  
  if called_by_editable_page: enable_edit()
  else: disable_edit()

  page_size = str( default_rows_per_page )

  global output_style # 'treeview', 'table', or original print layout (subset of treeview)
  output_style = default_output_style

  global order_by
  order_by = ''

  t = loader.get_template('mlgb/advanced_search_form.html')

  c = Context( {
      'editable'             : editable,
      'pagename'             : pagename,
      'form_fields'          : get_adv_search_form_fields_full(),
      'page_size'            : page_size,
      'page_sizes'           : get_page_sizes(),
      'default_rows_per_page': str( default_rows_per_page ),
      'order_options'        : get_order_change_field( 'any', order_by, False ),
      'output_styles'        : get_output_style_change_field( False ),
      'printed_book_radio_options': printed_book_radio_options(),
      'evidence_dropdown_options':  evidence_search_options(),
      'empty_form'           : True,
  } )

  return HttpResponse(t.render(c))
#}
#--------------------------------------------------------------------------------

# Function book() calls up the detail page for one single book.

def book( request, book_id, pagename = 'book', called_by_editable_page = False ): #{

  if called_by_editable_page: enable_edit()
  else: disable_edit()

  try:
    bk = Book.objects.get( pk = book_id )

  except Book.DoesNotExist:
    raise Http404

  # If one or more medieval catalogues have been entered, link to them.
  if bk.medieval_catalogue: #{
    bk.medieval_catalogue += get_links_from_book_to_catalogues( bk.id )
  #}


  # See if they have entered a search to get here.
  # If so, allow them to repeat it.
  search_term = get_value_from_GET( request, 'search_term' )
  field_to_search = get_value_from_GET( request, "field_to_search" )
  page_size = get_value_from_GET( request, "page_size" ) 
  
  t = loader.get_template('mlgb/mlgb_detail.html')

  # Apart from 'id' and 'object', most of the following context variables are to do with the
  # 'Search Again' box that appears on the right of the book record. This can repeat 
  # either a 'quick search' or advanced search, so we need to set variables for both types of search.

  advanced_search = False
  form_fields = []

  if field_to_search == 'multiple': #{
    advanced_search = True
    form_fields_searched = simplejson.loads( search_term )
    form_fields = get_adv_search_form_fields_full( form_fields_searched )
  #}
 
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
                 'order_options': get_order_change_field( 'any', '', False ),
                 'output_styles': get_output_style_change_field( False ),
                 'advanced_search': advanced_search,
                 'form_fields': form_fields,
                 'printed_book_radio_options': printed_book_radio_options(),
                 'evidence_dropdown_options':  evidence_search_options(),
                 'empty_form': False,
                 } )

  return HttpResponse(t.render(c))
#}
# end function book()
#--------------------------------------------------------------------------------
def book_e( request, book_id, pagename = 'book' ): #{
  return book( request, book_id, pagename, True )
#}
#--------------------------------------------------------------------------------

# The function browse() allows browsing by modern location and shelfmark

def browse( request, letter = 'A', pagename = 'browse', called_by_editable_page = False ): #{

  if called_by_editable_page: enable_edit()
  else: disable_edit()

  global printing # are we about to print this page, or view it in onscreen mode?
  printing = False

  global output_style # 'treeview', 'table' or original print layout (subset of treeview)
  output_style = default_output_style

  global order_by
  order_by = 'medieval_library' # default value, may be overridden from GET in a moment
  field_to_search = order_by # default value for field being browsed, also used in right-hand Search box

  global prev_heading_1
  global prev_heading_2
  prev_heading_1 = ""
  prev_heading_2 = ""

  html = result_string = resultsets = expand_2nd_tablerow = ""
  number_of_records = solr_rows = solr_query = solr_sort = page_size = ""
  letters = []
  table_control_links = ''
  first_record = True

  # Set default field to search, records per page and start row, 
  # for use in pagination and 'search again' functionality.
  search_term = ''
  solr_field_to_search = 'ml1_initial'
  page_size = str( default_rows_per_page )
  solr_start = 0

  if request.GET: #{ # are there any parameters in GET?

    # Check whether they want to print this page
    printing = get_value_from_GET( request, "printing", False )

    # Get actual records per page and start row from GET
    page_size = get_value_from_GET( request, "page_size", str( default_rows_per_page )) 
    solr_start = get_value_from_GET( request, "start", 0 ) 

    # They may also have chosen to browse by a different sort field
    field_to_search = get_value_from_GET( request, "field_to_search", field_to_search ) 
    if field_to_search == 'modern_library':
      solr_field_to_search = 'ml2_initial'
    elif field_to_search == 'medieval_library':
      solr_field_to_search = 'pr_initial'

    # They may have chosen a different sort order
    order_by = get_value_from_GET( request, "order_by", field_to_search )

    # They may have chosen expand/collapse options
    expand_2nd_tablerow = get_value_from_GET( request, "expand", "no" ) 

    # They may have chosen treeview, table or layout of original book
    # However, 'layout of original book' is only valid for ordering by provenance then location.
    output_style = get_value_from_GET( request, "output_style", default_output_style ) 
    reset_output_style_if_necessary()
  #}

  # Construct Solr query
  if not letter.isalpha(): letter = 'A'
  solr_query = '%s:%s' % (solr_field_to_search, letter.upper())
  
  # Set page size
  if page_size.isdigit():
    solr_rows = int( page_size )
  else: 
    solr_rows=Book.objects.count()
  
  # Set sort field based on which options are valid for this browse type
  sortfields = get_sortfields()
  solr_sort = ", ".join( sortfields )

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
    
    # Start loop through result sets
    for i in xrange( 0, len( resultsets ) ): #{

      if output_style == 'table':  #{
        if first_record: html = get_expand_collapse_script()

        text_for_one_record = display_as_table( resultsets[i], expand_2nd_tablerow, first_record, \
                              field_to_search, '', page_size )
      #}
      else: #{
        text_for_one_record = display_as_treeview( resultsets[i], first_record, \
                              field_to_search, search_term, page_size )
      #}

      # Add the string of HTML that you have generated for this record to the main HTML source
      html += text_for_one_record
      first_record=False

    #} # end loop through result sets

    if number_of_records > 0:  #{

      if output_style == 'table':  #{
        html += end_results_table()
        table_control_links = get_table_control_links( request, number_of_records, solr_rows )

      #}
      else: #{
        html = wrap_in_tree( html )
      #}

      if printing:
        alphabet = ''
      else: #{
        alphabet = '<div class="letterlinks">'
        initials = get_initial_letters( solr_field_to_search )
        for initial in initials: #{
          alphabet += '<a href="%s/browse/%s/?field_to_search=%s&output_style=%s&order_by=%s" ' \
                   % (baseurl, initial, field_to_search, output_style, order_by )
          if initial == letter.upper(): alphabet += ' class="selected" '
          alphabet += '>%s</a>' % initial
          alphabet += space
        #}
        alphabet += '</div><!-- letterlinks -->'
      #}

      pagination_change_link = get_pagination_change_link( request, number_of_records, solr_rows )

      pag = pagination( rows_found = number_of_records, \
                        current_row = solr_start, \
                        rows_per_page = solr_rows, \
                        pagination_change_link = pagination_change_link, \
                        link_for_print_button = get_link_for_print_button( request ),
                        link_for_download_button = get_link_for_download_button(  \
                                                   request, solr_field_to_search, letter.upper() ) )

      output_style_radio = get_output_style_change_field()
      order_by_select = get_order_change_field( field_to_search, order_by )

      result_string = alphabet + pag 
      result_string += '<p>' + order_by_select + space + output_style_radio + '</p>'
      result_string += table_control_links 
      result_string += html 

      if number_of_records > solr_rows: # repeat pagination at the bottom
        result_string += '<br>' + pag + '<br>'
    #}
  #} # end of check on whether we retrieved a result
    
  page_title = 'Browsing by %s' % get_searchable_field_label( field_to_search )
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
      'order_options'    : get_order_change_field( 'any', order_by, False ),
      'output_styles'    : get_output_style_change_field( False ),
      'printing'         : printing,
  } )

  return HttpResponse( t.render( c ) )

#}
# end function browse()
#--------------------------------------------------------------------------------
def browse_e( request, letter = 'A', pagename = 'browse' ): #{
  return browse( request, letter, pagename, True )
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
# It is also called by the admin interface

def download( request, pagename = 'download' ): #{

  response=None
  data=[]
  text=""
  book_id = ""
  selected_output_type = ""

  output_type_csv = "1"
  output_type_pdf = "2"
  
  rc="\r\n"

  if request.GET: #{

    if request.GET.has_key( "i" ):
      book_id = request.GET[ "i" ]

    if request.GET.has_key( "q" ):
      selected_output_type = request.GET[ "q" ]
  #}

  if selected_output_type == output_type_pdf: rc="<br/>"

  if book_id and selected_output_type: #{

    # Either: write out a CSV file
    if selected_output_type == output_type_csv: #{
      return downloadcsv( request )
    #}

    # Or: write out a PDF
    # (WARNING: this section currently fails with an ImportError)
    elif selected_output_type == output_type_pdf: #{

      # Gather the data into a text field
      (data, text) = get_text_for_pdf( book_id, rc )

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
  #}

  return response
#}
# end download
#--------------------------------------------------------------------------------

def about( request, pagename = 'about', called_by_editable_page = False ): #{

  t = loader.get_template('mlgb/about.html')

  c = Context( { 'pagename': pagename, 
                 'editable': editable, 
               } )

  return HttpResponse( t.render( c ) )    
#}

#--------------------------------------------------------------------------------

def about_e( request, pagename = 'about' ): #{
  return about( request, pagename, True )
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
  if evidence_code == 'blank': evidence_code = ''
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
  if pressmark.startswith( '<p>' ): pressmark = pressmark[ 3: ]
  if pressmark.endswith( '</p>' ): pressmark = pressmark[ :-4 ]
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
  general_notes = trim( resultset['nt'] )
  if general_notes.endswith( '<p>&nbsp;</p>' ): # no need for lots of whitespace
    general_notes = general_notes[ 0 : 0 - len( '<p>&nbsp;</p>' ) ]
  if general_notes: #{
    if add_punctuation and not general_notes.endswith( '.' ): 
      general_notes += '.'
  #}

  # notes on evidence
  notes_on_evidence = trim( resultset['evn'] )
  if notes_on_evidence.endswith( '<p>&nbsp;</p>' ): # no need for lots of whitespace
    notes_on_evidence = notes_on_evidence[ 0 : 0 - len( '<p>&nbsp;</p>' ) ]
  if notes_on_evidence: #{
    if add_punctuation and not notes_on_evidence.endswith( '.' ): 
      notes_on_evidence += '.'
  #}

  # ownership
  ownership = ''
  if resultset.has_key('own'): #{
    ownership = trim( resultset['own'] )
    if ownership.endswith( '<p>&nbsp;</p>' ): #{ no need for lots of whitespace
      ownership = ownership[ 0 : 0 - len( '<p>&nbsp;</p>' ) ]
    #}
  #}

  # image data
  images = []
  if resultset.has_key( 'imageurl' ): #{
    img_count = len( resultset[ 'imageurl' ] )
    if img_count > 0 : #{
      every_img_has_title = False
      every_img_has_caption = False
      if resultset.has_key( 'imagetitle' ): #{
        if len( resultset[ 'imagetitle' ] ) == img_count: 
          every_img_has_title = True
      #}

      if resultset.has_key( 'imagecaption' ): #{
        if len( resultset[ 'imagecaption' ] ) == img_count: 
          every_img_has_caption = True
      #}

      for i in range( 0, img_count ): #{

        url = resultset[ 'imageurl' ][ i ]
        title = ''
        caption = ''

        if every_img_has_title:
          title = resultset[ 'imagetitle' ][ i]
        else:
          title = 'photographic evidence'

        if every_img_has_caption:
          caption = resultset[ 'imagecaption' ][ i]
        else:
          caption = 'photographic evidence'

        images.append( (url, title, caption) )
      #}
    #}
  #}

  # contents (as a string)
  contents = ""
  if resultset.has_key( 'contents' ): #{
    contents_list = resultset[ 'contents' ]
    contents = newline.join( contents_list )
  #}

  # content URLs (as a single string)
  content_urls = ""
  if resultset.has_key( 'content_urls' ): #{
    content_urls_list = resultset[ 'content_urls' ]
    content_urls = newline.join( content_urls_list )
  #}

  return (id, provenance, modern_location1, modern_location2, shelfmark1, shelfmark2,
          evidence_code, evidence_desc, suggestion_of_contents, date_of_work,
          pressmark, medieval_catalogue, unknown, general_notes, notes_on_evidence, images,
          ownership, contents, content_urls)

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

def get_photo_evidence( id, images, evidence_code, evidence_desc ): #{ 

  link_to_photos = ""

  for img in images: #{  # each entry in the image list is a 3-part tuple: URL, title, caption

    image_url = MEDIA_URL + img[0]
    image_title = img[1] + ' -- type of evidence: ' + evidence_desc

    link_to_photos += '<a href="%s" rel="lightbox%s" title="%s" class="evidence">%s</a>' \
    % (image_url, id, image_title, evidence_code)
    link_to_photos += newline

    if printing: break # no need to show multiple links in a printed document
  #}

  return link_to_photos
#}
#--------------------------------------------------------------------------------
## This function was copied from code written by Mat Wilcoxson for EMLO/Cultures of Knowledge
## with some adaptation by Sue B.

def pagination( rows_found, current_row, rows_per_page=None, pagination_change_link = '', \
                link_for_print_button = '', link_for_download_button = '' ): #{

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
  if not printing: html += '<p>' + newline
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

    if pagination_change_link and not printing: #{ # offer to show multiple pages as one single page
      html += space + pagination_change_link
    #}

    html += '<br>' + newline

    if not printing: #{
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
    #} ## end of 'if not printing'
  #} ## end of 'if page count > 1'

  elif page_count == 1 : #{
    if pagination_change_link: #{  offer to split up the single page into multiple pages
      html += space + pagination_change_link
    #}
  #}

  if link_for_print_button and not printing: #{
    # Although 'print' button is not part of pagination, could be convenient
    # to have it on same line.
    html += space
    html += '<a href="%s" target="_blank" ' % link_for_print_button
    html += ' class="go_to_page" title="Print current page of results (in new tab)">' + newline
    html += 'Print' + newline
    html += '</a>' + newline
  #}

  if link_for_download_button and not printing: #{
    html += space
    html += '<a href="%s" target="_blank" ' % link_for_download_button
    html += ' class="go_to_page" title="Download current page of results">' + newline
    html += 'Download' + newline
    html += '</a>' + newline
  #}

  if not printing: html += '</p>' + newline
  html += '</div><!--class:pagination-->' + newline
  html += newline

  return html
#}
#--------------------------------------------------------------------------------

def write_page_change_script( page_change_scriptname ): #{

  script = newline

  script += '  <script type="text/javascript">' + newline
  script += '  function ' + page_change_scriptname + '( rowNumber ) {' + newline

  script += '    rowNumber = parseInt( rowNumber );' + newline
  script += '    if( isNaN( rowNumber )) {' + newline
  script += '      alert( \'Invalid row number.\' );' + newline
  script += '      return;' + newline
  script += '    }' + newline

  script += '    jsChangeSearch( "start", rowNumber ); ' # see base.html for jsChangeSearch()

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
      if not value: value = default_value
    #}
  #}
  return value
#}
#--------------------------------------------------------------------------------

def get_searchable_field_list(): #{

  fields = [ { ""                : 'All fields' },
             { 'author_title'    : 'Author/Title' },
             { 'medieval_library': 'Medieval Library' },
             { 'location'        : 'Modern Location' },
             { 'modern_library'  : 'Modern Library/Institution' },
             { 'shelfmark'       : 'Shelfmark' } ]

  return fields
#}
#--------------------------------------------------------------------------------

def get_advanced_search_form_fields(): #{

  fields = [ 
    'author_title'      ,
    'medieval_library'  ,
    'location'          ,
    'modern_library'    ,
    'shelfmark'         ,
    'evidence_code'     ,
    'evidence_notes'    ,
    'contents'          ,
    'pressmark'         ,
    'medieval_catalogue',
    'ownership'         ,
    'general_notes'     ,
    'printed_book'      ,
    'id'                ,
  ]

  return fields
#}
#--------------------------------------------------------------------------------

def get_advanced_search_field_labels(): #{

  field_labels = {
    'author_title'      : 'Author/title' ,
    'medieval_library'  : 'Medieval library' ,
    'location'          : 'Modern location' ,
    'modern_library'    : 'Modern library/institution' ,
    'shelfmark'         : 'Shelfmark' ,
    'evidence_code'     : 'Evidence type',
    'evidence_notes'    : 'Notes on evidence',
    'contents'          : 'Contents',
    'pressmark'         : 'Pressmark',
    'medieval_catalogue': 'Medieval catalogue code',
    'ownership'         : 'Ownership',
    'general_notes'     : 'General notes',
    'printed_book'      : 'Type of book',
    'id'                : 'Book ID',
  }

  return field_labels
#}
#--------------------------------------------------------------------------------

def get_adv_search_form_fields_with_label(): #{

  fieldnames = get_advanced_search_form_fields()
  labels = get_advanced_search_field_labels()

  labelled_fields = []

  for fieldname in fieldnames: #{
    label = ''
    if labels.has_key( fieldname ): label = labels[ fieldname ]
    labelled_fields.append( [ fieldname, label ] )
  #}

  return labelled_fields
#}
#--------------------------------------------------------------------------------

def get_adv_search_form_fields_full( form_fields_searched = {} ): #{

  form_fields_labelled = get_adv_search_form_fields_with_label()
  form_fields_full = []

  for field_info in form_fields_labelled: #{
    fieldname = field_info[ 0 ]
    label = field_info[ 1 ]
    value = ''
    if form_fields_searched.has_key( fieldname ):
      value = form_fields_searched[ fieldname ]
    form_fields_full.append( [ fieldname, label, value ] )
  #}

  return form_fields_full
#}
#--------------------------------------------------------------------------------

def get_form_to_solr_field_dict(): #{

  fields = { 
    'author_title'      : 'authortitle' ,
    'medieval_library'  : 'provenance' ,
    'location'          : 'location' ,
    'modern_library'    : 'library' ,
    'shelfmark'         : 'shelfmarks',  
    'evidence_code'     : 'ev',
    'evidence_notes'    : 'evidence_notes',
    'contents'          : 'contents',
    'pressmark'         : 'pressmark',
    'medieval_catalogue': 'medieval_catalogue',
    'ownership'         : 'own',
    'general_notes'     : 'nt',
    'printed_book'      : 'printed_book',
    'id'                : 'id',
  }

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

  heading = trim( modern_location1, False )
  if modern_location1 and modern_location2: #{
    if not heading.endswith( ',' ): heading += ', ' 
  #}
  heading += ' ' + trim( modern_location2, False )
  if heading.endswith( ',' ): heading = heading[ 0 : -1 ]
  return heading
#}
#--------------------------------------------------------------------------------

def get_provenance_sortfields(): #{

  sortfields = [ 'prsort asc',        # provenance (place, e.g. town/city)
                 'ctsort asc',        # provenance (county)
                 'inssort asc' ]      # provenance (institution name)
  return sortfields
#}
#-------------------------------------------------------------------------------

def get_location_sortfields(): #{

  sortfields = [  'ml1sort asc',       # modern location 1 (city etc)
                  'ml2sort asc' ]      # modern location 2 (library name)
  return sortfields
#}
#--------------------------------------------------------------------------------

def get_modern_library_sortfields(): #{

  sortfields = [ 'ml2sort asc',       # modern location 2 (library name)
                 'ml1sort asc' ]      # modern location 1 (city etc)
  return sortfields
#}
#--------------------------------------------------------------------------------
def get_author_title_sortfields(): #{
  sortfields = [ 'soc asc' ] # suggestion of contents, i.e. author/title
  return sortfields
#}
#--------------------------------------------------------------------------------

def get_shelfmark_sortfields(): #{
  sortfields = [ 'shelfmarksort asc' ] # shelfmark in numerically-sortable format
  return sortfields
#}
#--------------------------------------------------------------------------------

def get_date_sortfields(): #{
  sortfields = [ 'datesort asc', # date converted to numbers as best we can
                 'dt asc' ]      # date as string
  return sortfields
#}
#--------------------------------------------------------------------------------

def get_provenance_and_location_sortfields( secondary_sort_on_shelfmark = True ): #{
  sortfields = get_provenance_sortfields()
  sortfields.extend( get_location_sortfields() ) # add modern location 
  if secondary_sort_on_shelfmark: sortfields.extend( get_shelfmark_sortfields() )
  else: sortfields.extend( get_date_sortfields() )
  return sortfields
#}
#-------------------------------------------------------------------------------
def get_provenance_and_date_sortfields(): #{
  sortfields = get_provenance_sortfields()
  sortfields.extend( get_date_sortfields() )
  return sortfields
#}
#--------------------------------------------------------------------------------
def get_location_and_provenance_sortfields( secondary_sort_on_shelfmark = True ): #{
  sortfields = get_location_sortfields()
  sortfields.extend( get_provenance_sortfields() )
  if secondary_sort_on_shelfmark: sortfields.extend( get_shelfmark_sortfields() )
  else: sortfields.extend( get_date_sortfields() )
  return sortfields
#}
#--------------------------------------------------------------------------------
def get_modern_library_and_provenance_sortfields( secondary_sort_on_shelfmark = True ): #{
  sortfields = get_modern_library_sortfields()
  sortfields.extend( get_provenance_sortfields() )
  if secondary_sort_on_shelfmark: sortfields.extend( get_shelfmark_sortfields() )
  else: sortfields.extend( get_date_sortfields() )
  return sortfields
#}
#--------------------------------------------------------------------------------
def get_location_and_shelfmark_sortfields(): #{
  sortfields = get_location_sortfields()
  sortfields.extend( get_shelfmark_sortfields() )
  return sortfields
#}
#--------------------------------------------------------------------------------
def get_modern_library_and_shelfmark_sortfields(): #{
  sortfields = get_modern_library_sortfields()
  sortfields.extend( get_shelfmark_sortfields() )
  return sortfields
#}
#--------------------------------------------------------------------------------

def get_author_title_provenance_location_sortfields( secondary_sort_on_shelfmark = True ): #{
  sortfields = get_author_title_sortfields()
  sortfields.extend( get_provenance_sortfields() )
  sortfields.extend( get_location_sortfields() ) # add modern location 
  if secondary_sort_on_shelfmark: sortfields.extend( get_shelfmark_sortfields() )
  else: sortfields.extend( get_date_sortfields() )
  return sortfields
#}
#-------------------------------------------------------------------------------

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

  if printing: return ''

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

  if printing: return ''

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

def get_table_control_links( request, rows_found = 0, rows_per_page = 0 ): #{

  if printing: return ''

  links = ""
  new_search = "" 
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

  links += '<a href="%s" title="Expand All">Expand All</a>' % expand_search
  links += ' | '
  links += '<a href="%s" title="Collapse All">Collapse All</a>' % collapse_search

  return links
#}
#--------------------------------------------------------------------------------

def get_pagination_change_link( request, rows_found = 0, rows_per_page = 0 ): #{

  if printing: return ''

  # For page size change option, preserve 
  # any existing parameters except 'page_size' and 'start'

  link = ''
  new_search = ''

  if rows_found > rows_per_page or rows_found > default_rows_per_page: #{
    delim = '?'

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

    link = '<a href="%s" title="%s">%s</a>' % (new_search, new_title, new_title)
  #}

  return link
#}
#--------------------------------------------------------------------------------

def get_link_for_print_button( request ): #{
  if printing: return ''  # already printing, no further button needed
  new_search = "" 
  delim = "?"
  # Preserve any existing parameters except 'printing'
  if request.GET: #{  # 
    for k, v in request.GET.items(): #{
      if k == 'printing': continue
      new_search += delim
      new_search += "%s=%s" % (k, quote( v.encode( 'utf-8' )))
      if delim == "?": delim = "&"
    #}
  #}
  new_search += delim + "printing=yes"
  return new_search
#}
#--------------------------------------------------------------------------------

def get_link_for_download_button( request, field_to_search = '', search_term = '' ): #{

  if not editable: return '' # POSSIBLY TEMPORARY!!! Restrict this functionality to the project editors

  if printing: return ''  # don't display buttons in printed output

  new_search = "" 
  delim = "?"
  # Preserve any existing parameters
  # apart from ones passed in to this function, which override GET.
  if request.GET: #{  # 
    for k, v in request.GET.items(): #{
      if field_to_search and k == 'field_to_search': continue
      if search_term and k == 'search_term': continue

      new_search += delim
      new_search += "%s=%s" % (k, quote( v.encode( 'utf-8' )))
      if delim == "?": delim = "&"
    #}
  #}

  if field_to_search and search_term:
    new_search += '%sfield_to_search=%s&search_term=%s' \
                % (delim, field_to_search, search_term.encode( 'utf-8' ))

  href = '%s/downloadcsv/%s' % ( baseurl, new_search )
  return href
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

# Download search results etc as a CSV file.

def downloadcsv( request, pagename = 'download' ): #{

  response=None
  data=[]

  data.append( [] ) # add a new empty row

  data[0].append( 'Book ID' )
  data[0].append( 'Provenance' )
  data[0].append( 'Modern location 1' )
  data[0].append( 'Modern location 2' )
  data[0].append( 'Shelfmark 1' )
  data[0].append( 'Shelfmark 2' )
  data[0].append( 'Evidence code' )
  data[0].append( 'Evidence description' )
  data[0].append( 'Suggestion of contents' )
  data[0].append( 'Date of work' )
  data[0].append( 'Pressmark' )
  data[0].append( 'Medieval catalogue' )
  data[0].append( '?' )
  data[0].append( 'General notes' )
  data[0].append( 'Notes on evidence' )
  data[0].append( 'Ownership' )
  data[0].append( 'Contents' )
  data[0].append( 'URLs' )
  data[0].append( 'Images'  )
  
  if request.GET: #{

    (resultsets, number_of_records, 
    field_to_search, search_term, solr_start, solr_rows, page_size ) = basic_solr_query( request )

    if number_of_records > 0 : #{
      # Start loop through result sets
      for i in xrange( 0, len( resultsets ) ): #{

        # Get the data from the Solr result set
        (id, provenance, modern_location1, modern_location2, shelfmark1, shelfmark2,
        evidence_code, evidence_desc, suggestion_of_contents, date_of_work,
        pressmark, medieval_catalogue, unknown, general_notes, notes_on_evidence, images,
        ownership, contents, content_urls) = extract_from_result( resultsets[i], False )

        data.append( [] ) # add a new empty row
        j = i + 1

        data[j].append( id )
        data[j].append( strip_formatting_tags(  provenance ) )
        data[j].append( strip_formatting_tags(  modern_location1 ) )
        data[j].append( strip_formatting_tags(  modern_location2 ) )
        data[j].append( strip_formatting_tags(  shelfmark1 ) )
        data[j].append( strip_formatting_tags(  shelfmark2 ) )
        data[j].append( strip_formatting_tags(  evidence_code ) )
        data[j].append( strip_formatting_tags(  evidence_desc ) )
        data[j].append( strip_formatting_tags(  suggestion_of_contents ) )
        data[j].append( strip_formatting_tags(  date_of_work ) )
        data[j].append( strip_formatting_tags(  pressmark ) )
        data[j].append( strip_formatting_tags(  medieval_catalogue ) )
        data[j].append( strip_formatting_tags(  unknown ) )
        data[j].append( strip_formatting_tags(  general_notes ) )
        data[j].append( strip_formatting_tags(  notes_on_evidence ) )
        data[j].append( strip_formatting_tags(  ownership ) )
        data[j].append( strip_formatting_tags(  contents ) )
        data[j].append( strip_formatting_tags(  content_urls ) )

        image_string = ''
        if len( images ) > 0: #{
          for image_tuple in images: #{
            if image_string > '': image_string += ' ' 
            if len( image_tuple ) >= 1: image_string += image_tuple[ 0 ]
            if len( image_tuple ) >= 2: image_string += newline + image_tuple[ 1 ]
          #}
        #}

        data[j].append( image_string )

      #} # end loop through result sets
    #}
  #}

  # Write out a CSV file
  label = ''
  for char in search_term: #{
    if char.isalnum(): label += char
  #}
  if len( label ) > 30: # getting a bit too long
    label = label[ 0 : 30 ]
  if label: label = '-' + label

  response = HttpResponse( mimetype='text/csv' )
  response['Content-Disposition'] = 'attachment; filename=MLGB%s.csv' % label

  writer = csv.writer(response)
  
  for row in data: #{
    writer.writerow( [ cell.encode( 'utf8' ) for cell in row ] )
  #}

  return response
#}
# end downloadcsv
#--------------------------------------------------------------------------------

# Run a *basic* Solr query (i.e. on a single search term)
# and return results, number of records, field to search, search term, start row 
# and page size both as an integer (solr_rows) and as a string (page_size).

def basic_solr_query( request ): #{

  resultsets = []
  number_of_records = 0

  field_to_search = ""
  search_term     = ""
  solr_start      = ""
  page_size       = ""

  solr_query      = ""
  solr_sort       = ""
  solr_rows       = ""

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
        solr_query = "authortitle:%s" % solr_query

      elif field_to_search.lower()=='modern_library':
        solr_query = "library:%s" % solr_query

      elif field_to_search.lower()=='medieval_library':
        solr_query = "provenance:%s" % solr_query

      elif field_to_search.lower()=='location':  
        solr_query = "location:%s" % solr_query

      elif field_to_search.lower()=='shelfmark':
        solr_query = "shelfmarks:%s" % solr_query

      elif field_to_search.lower()=='id':
        solr_query = "id:%s" % solr_query

      elif field_to_search.lower() in [ 'ml1_initial', 'ml2_initial', 'pr_initial' ]:
        solr_query = "%s:%s" % (field_to_search.lower(), solr_query)

      else:
        solr_query = "text:%s" % solr_query

    #}
    
    # Set page size
    if page_size.isdigit():
      solr_rows = int( page_size )
    else: 
      solr_rows=Book.objects.count()
    
    # Set sort field
    sortfields = get_sortfields()
    solr_sort = ", ".join( sortfields )

    # Run the Solr query
    s_para={'q'    : solr_query,
            'wt'   : s_wt,  # 's_wt', i.e. 'writer type' is set in config.py, defaults to "json"
            'start': solr_start, 
            'rows' : solr_rows,
            'sort' : solr_sort}

    r = MLGBsolr()

    r.solrresults( s_para, facet, 'books' )

    if r.connstatus and r.s_result: #{ #did we retrieve a result?

      resultsets = r.s_result.get( 'docs' )
      number_of_records = r.s_result.get( 'numFound' )
    #}
  #} # end of check on whether a search term was found in GET

  return ( resultsets, number_of_records, 
           field_to_search, search_term, solr_start, solr_rows, page_size )
#}
# end function basic_solr_query()
#--------------------------------------------------------------------------------

# Run an *advanced* Solr query (i.e. on a combination of multiple search terms)
# and return same output as basic Solr query.

def advanced_solr_query( request ): #{

  resultsets = []
  number_of_records = 0

  field_to_search = "multiple"
  selection       = ""

  solr_start      = ""
  page_size       = ""
  solr_query      = ""
  solr_sort       = ""
  solr_rows       = ""

  searchable_fields = get_form_to_solr_field_dict()
  selections = []

  template_vars = {} # storing these variables will help us refine the query from the 'Results' template

  if request.GET: #{
    
    # Set page size
    page_size = get_value_from_GET( request, "page_size" ) 
    if page_size.isdigit():
      solr_rows = int( page_size )
    else: 
      solr_rows=Book.objects.count()
    
    # Set start row (e.g. on page 1 = 0)
    solr_start = get_value_from_GET( request, "start", 0 ) 

    # Set sort field
    sortfields = get_sortfields()
    solr_sort = ", ".join( sortfields )
  
    # Set search terms
    for form_field, solr_field in searchable_fields.items(): #{

      # Look for search term for all possible fields in GET
      selection = get_value_from_GET( request, form_field )
      if not selection or selection == '*': continue

      # Store field names/values searched for later use in 'Refine Search' functionality.
      template_vars[ form_field ] = selection

      # Construct Solr query
      selection = escape_for_solr( selection )
      if ' ' in selection:
        selection = '(%s)' % selection
     
      selection = '%s:%s' % (solr_field, selection)

      selections.append( selection )
    #}

    if len( selections ) > 0:
      solr_query = ' AND '.join( selections )
    else:
      solr_query = '*:*'

    # Run the Solr query
    s_para={'q'    : solr_query,
            'wt'   : s_wt,  # 's_wt', i.e. 'writer type' is set in config.py, defaults to "json"
            'start': solr_start, 
            'rows' : solr_rows,
            'sort' : solr_sort}

    r = MLGBsolr()

    r.solrresults( s_para, Facet=facet )

    if r.connstatus and r.s_result: #{ #did we retrieve a result?

      resultsets = r.s_result.get( 'docs' )
      number_of_records = r.s_result.get( 'numFound' )
    #}
  #} # end of check on whether a search term was found in GET

  return ( resultsets, number_of_records, 
           field_to_search, simplejson.dumps( template_vars ), solr_start, solr_rows, page_size )
#}
# end function advanced_solr_query()
#--------------------------------------------------------------------------------

def get_treeview_formatting(): #{

  start_treeview = newline
  start_treeview += '<div id="sidetreecontrol">' + newline
  if not printing:
    start_treeview += '<a href="?#">Expand All</a> | <a href="?#">Collapse All</a>' + newline
  start_treeview += '</div>' + newline + newline

  start_treeview += '<ul class="treeview" id="tree">' + newline + newline

  start_collapsible_list = '<ul style="display:block;"><!-- start "book" list -->' + newline

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
  end_treeview = '</ul><!-- end ID "tree" class "treeview" -->'
        
  return (start_treeview, start_collapsible_list, start_outer_section, start_inner_section,
          end_inner_section, end_inner_and_outer_sections, end_treeview)
#}
# end function get_treeview_formatting()
#--------------------------------------------------------------------------------

def display_as_treeview( one_row, first_record = False, \
                         field_to_search = '', search_term = '', page_size = '' ): #{

  global prev_heading_1 # these two globals allow us to see whether there has been a change of heading
  global prev_heading_2

  html = ""
  link_to_photos = ""

  # Get the data from the Solr result set
  (id, provenance, modern_location1, modern_location2, shelfmark1, shelfmark2,
  evidence_code, evidence_desc, suggestion_of_contents, date_of_work,
  pressmark, medieval_catalogue, unknown, general_notes, notes_on_evidence, images,
  ownership, contents, content_urls) = extract_from_result( one_row )

  # Get photos if any
  link_to_photos = get_photo_evidence( id, images, evidence_code, evidence_desc )

  # Get formatting tags etc.
  (start_treeview, start_collapsible_list, start_outer_section, start_inner_section, end_inner_section,
  end_inner_and_outer_sections, end_treeview) = get_treeview_formatting()

  # If searching on author/title (i.e. 'suggestion of contents'), show author/title as 
  # heading 1, then provenance as heading 2, then modern library and shelfmark in the detail.
  # If not searching on author/title, either have medieval library as main heading, then modern one,
  # or have modern location/library as main heading, then medieval one.

  heading1, heading2, heading3 = get_headings_from_sort_order( one_row )

  if output_style == 'treeview': #{
    heading2 = '<span class="heading2">%s</span>' % heading2
  #}

  if prev_heading_1 <> heading1: #{  # change in heading 1
    prev_heading_2=""
    if not first_record: 
      html += end_inner_and_outer_sections
    html += newline
    html += start_outer_section + newline
    html += '<span class="outerhead" title="expand/collapse this section">%s</span>' % heading1
    html += '<!-- end "outer head" span -->' + newline + start_collapsible_list
  #}

  if prev_heading_2 <> heading2: #{ # change in heading 2
    prev_heading_2 = heading2
    if prev_heading_1 == heading1: #{
      if not first_record: #{
        html += end_inner_section
      #}
    #}
    else: #{
      prev_heading_1 = heading1
    #}
    html += newline
    html += start_inner_section + newline
    html += '<span class="innerhead" title="expand/collapse this section">%s</span>' % heading2
    html += '<!-- end "inner head" span -->' + newline + start_collapsible_list
  #}
  
  # Now set up the 'heading 3' and 'detail' text
  if heading3 and output_style == original_print_layout: #{
    heading3 = '<span class="modern_location_heading">' \
             + newline + heading3 + newline \
             + '</span><!-- end modern location_heading -->' + two_spaces + newline
  #}

  detail_text = newline + '<!-- start book ID ' + id + ' -->' + newline
  detail_text += '<li class="one_book">' + newline

  # 'Heading 3' is not really a heading, but a repeated item of detail text.
  if heading3: detail_text += heading3

  if len( link_to_photos ) > 0:
    detail_text += link_to_photos

  else: #{
    if evidence_code: #{
      detail_text += get_evidence_decoder_button( evidence_code, evidence_desc )
    else:
      detail_text += '<span class="noevidence"> </span>'
    #}
  #}
  detail_text += ' <!-- type of evidence -->'
  detail_text += two_spaces

  if 'location' not in order_by and 'modern_library' not in order_by: #not already displayed as a heading
    detail_text += space + modern_location1 + ' ' + modern_location2

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

  if not order_by.startswith( 'author_title' ): #{  # already displayed as heading 1

    if suggestion_of_contents: #{
      detail_text += suggestion_of_contents + ' <!-- author/title -->'
      detail_text += space
    #}
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

  if not printing: #{
    detail_text += manicule_pointing_right_img() 
  #}
  detail_text += '</a>' + newline
  detail_text += '<!-- end booklink -->' + newline

  if 'provenance' not in order_by:  #not already displayed as a heading
    detail_text += space + provenance

  if editable and not printing: #{
    detail_text += '<a href="/admin/books/book/%s" title="Edit this record" target="_blank"' % id
    detail_text += ' class="editlink">'
    detail_text += space + 'Edit' + '</a>' + newline
  #}

  detail_text += '</li><!-- end book ID ' + id + ' -->' + newline + newline

  # Pass back a string of HTML for display
  html += detail_text
  return html
#}
# end function display_as_treeview()
#--------------------------------------------------------------------------------

def display_as_table( one_row, expand_2nd_tablerow, first_record = False, \
                      field_to_search = '', search_term = '', page_size = '' ): #{

  global prev_heading_1
  html = ""

  if expand_2nd_tablerow == "yes": #{
    class_of_2nd_row = browse_expanded_class
    concertina_label = '-'
  #}
  else: #{
    class_of_2nd_row = browse_collapsed_class
    concertina_label = '+'
  #}


  # Get the data from the Solr result set
  (id, provenance, modern_location1, modern_location2, shelfmark1, shelfmark2,
  evidence_code, evidence_desc, suggestion_of_contents, date_of_work,
  pressmark, medieval_catalogue, unknown, general_notes, notes_on_evidence, images,
  ownership, contents, content_urls) = extract_from_result( one_row, False ) # here False means 'don't 
                                                                             # add punctuation'

  unformatted_provenance = extract_unformatted_provenance( one_row ) # no italics etc

  heading, heading2, heading3 = get_headings_from_sort_order( one_row )

  if prev_heading_1.lower() <> heading.lower(): #{  # change in heading

    if first_record:
      first_record=False
    else:
      html += end_results_table()

    html += newline + "<h3>" + newline
    html += '<p>'
    html += heading
    html += '</p>'
    html += newline + "</h3>" + newline
    html += start_results_table( field_to_search )
    prev_heading_1 = heading
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
  link_to_photos = get_photo_evidence( id, images, evidence_code, evidence_desc )
  if link_to_photos:
    detail_text += link_to_photos
  elif evidence_code: #{
    detail_text += get_evidence_decoder_button( evidence_code, evidence_desc )
  #}
  else:
    detail_text += space
  detail_text += ' <!-- type of evidence -->'
  detail_text += newline + '</div><!-- end evidence -->' + newline

  # Location/modern library if not already a heading
  if not order_by.startswith( 'location' ) and not order_by.startswith( 'modern_library' ): #{ 
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
    detail_text += newline + '</div><!-- end modern location -->' + newline
  #}

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

  # Date
  detail_text += newline + '<div class="browse_date">' + newline
  if date_of_work: #{
    detail_text += booklink_start
    detail_text += date_of_work + ' <!-- date -->'
    detail_text += '</a>'
  #}
  else:
    detail_text += space
  detail_text += newline + '</div><!-- end date -->' + newline


  # Author/title if not already a heading
  if not order_by.startswith( 'author_title' ): #{
    detail_text += newline + '<div class="browse_authortitle">' + newline
    if suggestion_of_contents: #{
      detail_text += booklink_start
      detail_text += suggestion_of_contents + ' <!-- author/title -->'
      detail_text += '</a>'
    #}
    else:
      detail_text += space
    detail_text += newline + '</div><!-- end author/title -->' + newline
  #}

  # Provenance if not already a heading
  if not order_by.startswith( 'provenance' ): #{ show medieval library/provenance in detail text
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
  detail_text += newline + '<ul>' + newline

  if evidence_code.strip() : #{
    detail_text += '<li>'
    detail_text += '<em>Type of evidence:</em> ' + evidence_desc + ' <!-- evidence description -->'
    detail_text += '</li>' + newline
  #}

  if notes_on_evidence: #{
    detail_text += '<li>'
    detail_text += '<em>Notes on evidence:</em> ' + notes_on_evidence + ' <!-- notes on evidence -->'
    detail_text += '</li>' + newline
  #}

  if pressmark : #{
    detail_text += '<li><em>Pressmark:</em> ' + pressmark + ' <!-- pressmark -->'
    detail_text += '</li>' + newline
  #}

  if medieval_catalogue : #{
    detail_text += '<li><em>Medieval catalogue:</em> ' + medieval_catalogue + ' <!--medieval catalogue-->'
    detail_text += '</li>' + newline
  #}

  if general_notes : #{
    detail_text += '<li><em>General notes:</em> ' + general_notes + ' <!-- general notes -->'
    detail_text += '</li>' + newline
  #}

  if unknown : #{
    detail_text += '<li>' + unknown + ' <!-- unknown -->'
    detail_text += '</li>' + newline
  #}
  detail_text += newline + '</ul>' + newline

  detail_text += '</div><!-- end book ID ' + id + ' -->' + newline + newline

  # Pass back a string of HTML for display
  html += detail_text
  return html
#}
# end function display_as_table()
#--------------------------------------------------------------------------------

# I'm actually using divs rather than a table (even though this is perfectly
# valid data for tabular display) because the "colspan" attribute of "td" isn't working.

def start_results_table( field_to_search ): #{

  html = newline + '<div class="browseresults">' + newline
  html += '<div class="book_row_1">' + newline


  # Expand/collapse button and evidence
  html += newline + '<div colspan="2" class="columnhead">' + newline
  html += 'Evidence'
  html += newline + '</div><!-- end evidence -->' + newline

  # Modern library if not already shown in heading
  if not order_by.startswith( 'location' ) and not order_by.startswith( 'modern_library' ): #{ 
    html += newline + '<div class="browse_modern_library columnhead">' + newline
    html += 'Modern location'
    html += newline + '</div><!-- end modern location -->' + newline
  #}

  # Shelfmarks
  html += newline + '<div class="browse_shelfmarks columnhead">' + newline
  html += 'Shelfmark'
  html += newline + '</div><!-- end shelfmarks -->' + newline

  # Date
  html += newline + '<div class="browse_date columnhead">' + newline
  html += 'Date'
  html += newline + '</div><!-- end date -->' + newline


  # Author/title if not already shown in heading
  if not order_by.startswith( 'author_title' ): #{
    html += newline + '<div class="browse_authortitle columnhead">' + newline
    html += 'Suggestion of contents'
    html += newline + '</div><!-- end author/title -->' + newline
  #}

  # Medieval library/provenance if not already shown in heading
  if not order_by.startswith( 'provenance' ): #{ show medieval library/provenance in detail text
    html += newline + '<div class="browse_provenance columnhead">' + newline
    html += 'Medieval library'
    html += newline + '</div><!-- end provenance -->' + newline
  #}

  html += newline + '<div class="browse_editlink columnhead">' + newline
  html += newline + '</div><!-- end edit link -->' + newline

  html += '</div><!-- end column headers -->' + newline

  return html
#}
#--------------------------------------------------------------------------------
def end_results_table():
  return newline + '</div><!-- end browseresults -->' + newline
#--------------------------------------------------------------------------------
def wrap_in_tree( html ): #{

  (start_treeview, start_collapsible_list, start_outer_section, start_inner_section, end_inner_section,
  end_inner_and_outer_sections, end_treeview) = get_treeview_formatting()

  html = start_treeview + html + end_inner_and_outer_sections + end_treeview
  return html
#}
#--------------------------------------------------------------------------------
def get_output_style_change_field( with_onchange = True ): #{

  global output_style

  if printing: return ''

  field_id = 'output_style'
  if not with_onchange: field_id += '2'
  radio = ''

  labels = { default_output_style: 'treeview', 
             'table': 'table', 
             original_print_layout: 'original book layout' }

  radio += 'Output style: '

  for style_choice in [ default_output_style, 'table', original_print_layout ]: #{

    if style_choice == original_print_layout and not can_offer_original_print_layout():
      continue

    if not with_onchange: radio += '<br>'

    label = labels[ style_choice ]
    radio += '<input type="radio" name="output_style" '
    radio += ' id="%s_%s" value="%s" ' % (field_id, style_choice, style_choice)
    if style_choice == output_style: radio += ' CHECKED ';

    if with_onchange: #{
      radio += ' onclick="jsChangeSearch( this.name, this.value )" ' # see base.html for jsChangeSearch()
      radio += ' onchange="jsChangeSearch( this.name, this.value )" '
    #}

    radio += '/> <label for="%s_%s">%s</label>' % (field_id, style_choice, label)

    if with_onchange:
      radio += space
  #}

  return radio
#}
#--------------------------------------------------------------------------------
def get_order_change_options( primary_order_by = 'any' ): #{

  valid_options = []

  all_options = {

    'any': [],

    'medieval_library': [ 'provenance_location_shelfmark',
                          'provenance_location_date',
                          'provenance_date' ],

    'location'        : [ 'location_provenance_shelfmark',
                          'location_provenance_date',
                          'location_shelfmark' ],

    'modern_library'  : [ 'modern_library_provenance_shelfmark',
                          'modern_library_provenance_date',
                          'modern_library_shelfmark' ],

    'author_title'    : [ 'author_title_provenance_location' ],
  }

  all_options[ 'any' ].extend( all_options[ 'medieval_library' ] )
  all_options[ 'any' ].extend( all_options[ 'location' ] )
  all_options[ 'any' ].extend( all_options[ 'modern_library' ] )
  all_options[ 'any' ].extend( all_options[ 'author_title' ] )

  if not all_options.has_key( primary_order_by ):
    primary_order_by = 'any'

  valid_options = all_options[ primary_order_by ]
  return valid_options
#}
#--------------------------------------------------------------------------------
def get_order_change_field( primary_order_by = 'any', selected_order_by = '', with_onchange = True ): #{

  if printing: return ''

  valid_options = get_order_change_options( primary_order_by )
  fieldstring = ''
  field_id = 'order_by'

  if with_onchange: #{
    fieldstring += '<script type="text/javascript">' + newline
    fieldstring += 'function getValueOfOrderBy() {' + newline
    fieldstring += '  indx=document.getElementById("order_by").selectedIndex;' + newline
    fieldstring += '  var orderOptionID = "order_by_" + indx;' + newline
    fieldstring += '  var orderOptionField=document.getElementById( orderOptionID );' + newline
    fieldstring += '  return orderOptionField.value;' + newline
    fieldstring += '}' + newline
    fieldstring += '</script>' + newline
  #}
  else:
    field_id += '2'

  fieldstring += '<label for="%s">Order by: </label>' % field_id

  fieldstring += '<select name="order_by" id="%s" ' % field_id
  if with_onchange: #{
    fieldstring += ' onchange="newChoice=getValueOfOrderBy(); jsChangeSearch( ' # see base.html 
    fieldstring += "'order_by'" + ', newChoice )" '
  #}
  fieldstring += '>' + newline

  i = 0
  for option in valid_options: #{
    label = get_order_by_label( option )

    fieldstring += '<option value="%s" id="%s_%d" ' % (option, field_id, i)

    if selected_order_by == option: 
      fieldstring += ' SELECTED '

    fieldstring += '>%s</option>' % label
    fieldstring += newline
    i += 1
  #}

  fieldstring += '</select>' + newline

  return fieldstring
#}
#--------------------------------------------------------------------------------

def get_order_by_label( fieldname ): #{

  label = fieldname

  label = label.replace( 'modern_library', 'modern library' )
  label = label.replace( 'author_title', 'author/title' )

  label = label.replace( '_', ', ' )
  label = label.capitalize()
  return label
#}
#--------------------------------------------------------------------------------

def get_sortfields(): #{

  global order_by

  if order_by == 'medieval_library': 
    order_by = 'provenance_location_shelfmark'

  elif order_by == 'modern_library':
    order_by = 'modern_library_provenance_shelfmark'

  elif order_by == 'location':
    order_by = 'location_provenance_shelfmark'

  elif order_by == 'author_title':
    order_by = 'author_title_provenance_location'

  #---

  possible_sortfields = {
    'provenance_location_shelfmark': get_provenance_and_location_sortfields(),
    'provenance_location_date'     : get_provenance_and_location_sortfields( False ),
    'provenance_date'              : get_provenance_and_date_sortfields(),
    #---
    'modern_library_provenance_shelfmark': get_modern_library_and_provenance_sortfields(),
    'modern_library_provenance_date'     : get_modern_library_and_provenance_sortfields( False ),
    'modern_library_shelfmark'           : get_modern_library_and_shelfmark_sortfields(),
    #---
    'location_provenance_shelfmark': get_location_and_provenance_sortfields(),
    'location_provenance_date'     : get_location_and_provenance_sortfields( False ),
    'location_shelfmark'           : get_location_and_shelfmark_sortfields(),
    #---
    'author_title_provenance_location': get_author_title_provenance_location_sortfields(),
    #---
  }

  if not possible_sortfields.has_key( order_by ):
    order_by = default_order_by

  sortfields = possible_sortfields[ order_by ]

  sortfields.append( 'id asc' )
  return sortfields
#}
#--------------------------------------------------------------------------------
def get_headings_from_sort_order( one_row ):  #{

  heading1 = ''
  heading2 = ''
  heading3 = ''

  # Get the data from the Solr result set
  (id, provenance, modern_location1, modern_location2, shelfmark1, shelfmark2,
  evidence_code, evidence_desc, suggestion_of_contents, date_of_work,
  pressmark, medieval_catalogue, unknown, general_notes, notes_on_evidence, images,
  ownership, contents, content_urls) = extract_from_result( one_row )

  sort = order_by
  if not sort: sort = default_order_by 

  # Each element of 'order by' string wants to be one complete word
  # so that we can split on underscores.
  sort = sort.replace( 'author_title', 'authortitle' )
  sort = sort.replace( 'modern_library', 'modernlibrary' )

  sort_words = sort.split( '_' )
  headings = []
  for word in sort_words: #{

    if word == 'authortitle':
      headings.append( suggestion_of_contents )

    elif word == 'provenance':
      headings.append( provenance )

    elif word == 'location': #{
      if output_style == original_print_layout: #{
        headings.append( modern_location1 )
        headings.append( modern_location2 )
      #}
      else: #{
        headings.append( get_modern_location_heading( modern_location1, modern_location2 ) )
      #}
    #}

    elif word == 'modernlibrary': #{
      headings.append( get_modern_location_heading( modern_location2, modern_location1 ) )
    #}
  #}

  if len( headings ) >= 1: heading1 = headings[ 0 ]
  if len( headings ) >= 2: heading2 = headings[ 1 ]
  if len( headings ) >= 3: heading3 = headings[ 2 ]

  return heading1, heading2, heading3
#}
#--------------------------------------------------------------------------------

def can_offer_original_print_layout(): #{

  # Original print layout can only be offered if 'order by' starts with provenance, then location
  can_offer_it = False

  valid_orders = [ '',  # if order is blank, it defaults to provenance, location, shelfmark
                   'provenance_location_shelfmark', 
                   'provenance_location_date',
                   'medieval_library' ]

  if order_by in valid_orders: can_offer_it = True

  return can_offer_it
#}
#--------------------------------------------------------------------------------

def reset_output_style_if_necessary(): #{

  global output_style
  if output_style == original_print_layout and not can_offer_original_print_layout(): #{
    output_style = default_output_style
  #}
#}
#--------------------------------------------------------------------------------

def strip_formatting_tags( text ): #{

  if not isinstance( text, (str,unicode) ): return ''

  text = text.replace( newline,  " " )
  text = text.replace( "\r",  " " )

  text = text.replace( "<p>",  " " )
  text = text.replace( "</p>", "  " )
  text = text.replace( "<strong>",  "" )
  text = text.replace( "</strong>", "" )
  text = text.replace( "<em>",      "" )
  text = text.replace( "</em>",     "" )
  text = text.replace( "<sub>",     " " )
  text = text.replace( "</sub>",    " " )
  text = text.replace( "<sup>",     " " )
  text = text.replace( "</sup>",    " " )
  text = text.replace( "<span>",    " " )
  text = text.replace( '<span style="text-decoration: underline;">',    "" )
  text = text.replace( '<span style="text-decoration: line-through;">', "" )
  text = text.replace( "</span>", "" )
  text = text.replace( "<i>",     "" )
  text = text.replace( "</i>",    "" )
  text = text.replace( "<ul>",    "" )
  text = text.replace( "</ul>",   " " )
  text = text.replace( "<li>",    " * " )
  text = text.replace( "</li>",   "" )
  text = text.replace( "<ol>",    "" )
  text = text.replace( "</ol>",   " " )
  text = text.replace( "&nbsp;",  " " )
  text = text.replace( "<br>",    "  " )
  text = text.replace( "<br />",  "  " )
  text = text.replace( "<div>",    " " )
  text = text.replace( "</div>",    " " )
  text = text.replace( "</a>",    " " )

  # Strip out HTML/XML comments giving formatting instructions etc. 
  tags = [ '<!--', '<span ', '<div ', '<p ', '<a ' ]
  for tag_start in tags: #{
    if tag_start == '<!--':
      tag_end = '-->'
    else:
      tag_end = '>'

    while tag_start in text: #{
      before_unwanted_section = ''
      after_unwanted_section = ''

      unwanted_section_start = text.find( tag_start )
      if unwanted_section_start > 0:
        before_unwanted_section = text[ 0 : unwanted_section_start ]

      unwanted_section_end = text.find( tag_end, unwanted_section_start )
      unwanted_section_end += len( tag_end )
      if unwanted_section_end < len( text ):
        after_unwanted_section = text[ unwanted_section_end : ]

      text = before_unwanted_section + after_unwanted_section
    #}
  #}

  text = text.strip()
  return text
#}
#--------------------------------------------------------------------------------

def get_text_for_pdf( book_id, rc = "<br/>" ): #{

  data = []
  text = ""

  data = Book.objects.filter( id = book_id )

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

  return (data, text)
#}
# end get_text_for_pdf
#--------------------------------------------------------------------------------

def get_links_from_book_to_catalogues( book_id ): #{

  the_cursor = connection.cursor()

  statement  = 'select distinct v.document_code, v.document_code_sort, v.document_name, '
  statement += ' v.doc_group_type_name, v.doc_group_name ' 
  statement += ' from index_mlgb_links l, index_medieval_documents_view v ' 
  statement += ' where v.document_code = l.document_code '
  statement += ' and l.mlgb_book_id = %d ' % book_id
  statement += ' order by document_code_sort'

  the_cursor.execute( statement )
  link_results = the_cursor.fetchall()
  the_cursor.close()
  num_links = len( link_results )

  link_string = ''
  plural = ''
  if num_links > 1: plural = 's'
  if num_links > 0: link_string += '<br><br>Further details of medieval catalogue%s: ' % plural
  if num_links > 1: link_string += '<ul>'

  for row in link_results: #{
    document_code       = row[ 0 ]
    document_code_sort  = row[ 1 ]
    document_name       = row[ 2 ]
    doc_group_type_name = row[ 3 ]
    doc_group_name      = row[ 4 ]

    catalogue_desc = doc_group_type_name + ': ' + doc_group_name + ': ' + document_name
    catalogue_desc = escape( catalogue_desc )

    if num_links > 1: link_string += '<li>'

    url = medieval_catalogue_url
    if editable: url = '/e' + url

    link_string += '<a href="%s/%s/" ' % (url, document_code)
    link_string += ' title="Medieval catalogue %s">' % document_code
    link_string += document_code + '. ' + catalogue_desc
    link_string += '</a>'

    if num_links > 1: link_string += '</li>'
  #}

  if num_links > 1: link_string += '</ul>'

  return link_string
#}
# end get_links_from_book_to_catalogues
#--------------------------------------------------------------------------------

def printed_book_radio_options(): #{
  options = [ [ "printed_book_any", "", "Any" ],
              [ "printed_book_yes", "1", "Printed" ],
              [ "printed_book_no",  "0", "Not printed" ] ]
  return options
#}
#--------------------------------------------------------------------------------

def evidence_search_options(): #{ # slightly different from raw values in table
                                  # as we want to be able to search on blank codes,
                                  # so we convert empty strings to the word 'blank'
  options = []
  options.append( [ "", "Any" ] )

  the_cursor = connection.cursor()

  statement = "select evidence, evidence_description from books_evidence order by evidence"
  the_cursor.execute( statement )
  results = the_cursor.fetchall()
  the_cursor.close()

  for row in results: #{
    evcode = row[ 0 ]
    evdesc = row[ 1 ]
    if evcode.strip() == "": evcode = "blank"
    evdesc = "%s: %s" % (evcode, evdesc)

    options.append( [ evcode, evdesc ] )
  #}
  
  return options
#}
#--------------------------------------------------------------------------------

def manicule_pointing_right_img( pointing_at = 'book detail record' ): #{

  return manicule_img( 'right', pointing_at )
#}
#--------------------------------------------------------------------------------

def manicule_pointing_down_img( pointing_at = 'book detail record' ): #{

  return manicule_img( 'down', pointing_at )
#}
#--------------------------------------------------------------------------------

def manicule_img( direction = 'right', pointing_at = 'book detail record' ): #{

  img_height = 20
  if direction == 'down': img_height = 38

  img_text =  '<img src="/mlgb/media/img/tiny-manicule-%s.jpg" ' % direction
  img_text += ' class="manicule" height="%dpx" ' % img_height
  img_text += ' alt="Pointing hand linking to %s' % pointing_at
  img_text += ' (manicule image courtesy of Cristina Willoughby)" '
  img_text += ' border="0" />'
  return img_text
#}
#--------------------------------------------------------------------------------
