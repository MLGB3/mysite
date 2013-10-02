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
#from django.core.paginator import Paginator, InvalidPage, EmptyPage
#-----------------------------

facet=False

#-----------------------------

def fulltext(request): #{

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
#-----------------------------

def download( request ): #{

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
## This sets up the data for the Home page

def index(request): #{

  f_field=""
  resultsets=lists1=list2=list3=None
  facet=True
  s_sort="pr asc,ml1 asc,ml2 asc,sm1 asc,sm2 asc,ev asc,soc asc,dt asc,pm asc,mc asc,uk asc"

  s_para={'q':'*:*',
          'wt':s_wt,
          'start':0, 
          'rows':'-1',
          'sort':s_sort}

  s_para['facet.mincount']='1'
  s_para['facet']='on'
  s_para['facet.limit']='-1'
  s_para['facet.field']=["pr","ml1","ml2"]

  r=MLGBsolr()

  r.solrresults( s_para, Facet=facet )

  t = loader.get_template('index.html')

  if r.connstatus and r.s_result: #{
    resultsets= r.s_result.get('facet')

    lists1 = resultsets[ "pr" ]
    lists2 = resultsets[ "ml1" ]
    lists3 = resultsets[ "ml2" ]  

    c = Context( {
        'lists1': len( lists1 ) / 2,
        'lists2': len( lists2 ) / 2,
        'lists3': len( lists3 ) / 2,
        } )
  #}
  else: #{
    c = Context( {
        'lists1': 0,
        'lists2': 0,
        'lists3': 0,
        } )
  #}

  return HttpResponse( t.render( c ) )    
#}
# end index
#--------------------------------------------------------------------------------

def search(request): #{
  # I'm not convinced that function search() ever gets used. Everything seems to go to function mlgb().

  text = pr = ml1 = body = lists = dl = s = resultsets = None
  norecord = s_rows = solr_query = ""
  nodis = False
  bod = True

  d_tag = '<div id="sidetreecontrol"> <a href="?#">Collapse All</a> | <a href="?#">Expand All</a> </div>'
  d_tag += '<ul class="treeview" id="tree">'

  dn_tag = '<ul style="display:none;">\n'
  
  if request.GET and request.GET["s"].strip(' %#~@/<>^()?[]{}!"^+-'): #{

    s =( request.GET[ "s" ] )
    solr_query = "%s" % s.strip(' %#~@/<>^()?[]{}!"^+-').lower()
    if s == '*':
      solr_query ="*:*"
    
    
    s_rows = Book.objects.count()
    
    s_para={'q'    : solr_query,
            'wt'   : s_wt,
            'start': 0, 
            'rows' : s_rows,
            'sort' : s_sort}

    r=MLGBsolr()

    r.solrresults( s_para )

    end_inner_section = '</ul></li>\n'
    end_inner_and_outer_sections = '</ul></li></ul></li>\n'
        
    if r.connstatus and r.s_result: #{
      resultsets = r.s_result.get( 'docs' )
      norecord = r.s_result.get( 'numFound' )
      
      text = h1 = h2 = d = ""

      for i in xrange( 0, len(resultsets) ): #{

        id=resultsets[i]['id']

        pr = resultsets[ i ][ 'pr' ].strip(' ')              # provenance
        ml1 = resultsets[ i ][ 'ml1' ].strip(' ')            # modern library 1
        ml2 = "%s&cedil;" % resultsets[i]['ml2'].strip('" ') # modern library 2 
                                                             # with 'spacing cedilla' instead of comma (why?)
        # Shelfmark 1
        if resultsets[i]['sm1'].strip(' '):
          sm1="&nbsp;&nbsp;%s." % resultsets[i]['sm1'].strip('" ')
        else:
          sm1=""

        # Shelfmark 2
        if resultsets[i]['sm2'].strip(' '):
          sm2="&nbsp;&nbsp;%s." % resultsets[i]['sm2'].strip('" ')
        else:
          sm2=""

        # Evidence code
        if resultsets[i]['ev'].strip(' '):
          ev="<i>%s</i>" % resultsets[i]['ev'].strip('" ')
        else:
          ev=""

        # Suggestion of contents
        soc=resultsets[i]['soc'].strip('" ')

        # Date
        if resultsets[i]['dt'].strip(' '):
          dt="&nbsp;&nbsp;%s." % resultsets[i]['dt'].strip('" ')
        else:
          dt=""

        # Pressmark
        if resultsets[i]['pm'].strip(' '):
          pm="&nbsp;&nbsp;%s." % resultsets[i]['pm'].strip('" ')
        else:
          pm=""

        # Medieval catalogue
        if resultsets[i]['mc'].strip(' '):
          mc="&nbsp;&nbsp;[%s]." % resultsets[i]['mc'].strip('" ')
        else:
          mc=""

        # Unknown
        if resultsets[i]['uk'].strip(' '):
          uk="&nbsp;&nbsp;%s." % resultsets[i]['uk'].strip('" ')
        else:
          uk=""

        # Notes
        if resultsets[i]['nt'].strip(' '):
          nt="&nbsp;&nbsp;%s." % resultsets[i]['nt'].strip('" ')
        else:
          nt=""
        
        body = '<li><span><strong>%s</strong></span>  ' % ml2
        body += '<span class="detail">%s%s  %s  %s%s%s%s%s ' % (sm1,sm2,ev,soc,dt,pm,mc,uk)
        body += '<a href="/mlgb/book/%s/">' % id
        body += '<img src="/mlgb/media/img/detail.gif" alt="detail" border="0" />'
        body += '</a>' 
        body += '</span>' 
        body += '</li>\n' 
          
          
        if h1 <> pr: #{
          h2=""
          if not bod: 
            text += end_inner_and_outer_sections
          text += '<li class="expandable"><div class="hitarea expandable-hitarea"></div>' \
               +  '<span><strong>%s</strong></span>\n%s' % (pr,dn_tag)
        #}

        if h2 <> ml1: #{
          h2=ml1
          if h1==pr: #{
            if not bod:
              text += end_inner_section
          #}
          else: #{
            h1=pr
          #}
          text += '<li class="expandable"><div class="hitarea expandable-hitarea"></div>' \
               +  '<span>%s</span>\n%s' % (ml1,dn_tag)
        #}

        text += body
        bod=False

      #}  # end loop through result sets

      if text:
        lists=d_tag + text + end_inner_and_outer_sections + '</ul>'
    #} # end of check on whether a result was retrieved

    nodis=True
  #} # end of check on whether a search query was entered in GET
    
  t = loader.get_template('mlgb/mlgb.html')

  if norecord : #{
    if norecord > s_rows: 
      norecord=s_rows
  #}
  else:
    norecord=0
    
  c = Context( {
      'lists': lists, 'no':norecord, 'nodis':nodis, 's':s,
  } )

  return HttpResponse(t.render(c))
#}
# end function search() (possibly unused)
#--------------------------------------------------------------------------------

def trim( the_string, strip_double_quotes = True ): #{

  chars_to_strip = ' \r\n\t'
  if strip_double_quotes:
    chars_to_strip += '"'
  return the_string.strip( chars_to_strip )
#}
#--------------------------------------------------------------------------------

def mlgb( request ): #{

  html = provenance = modern_location1 = detail_text = lists = search_term = resultsets = None
  number_of_records = solr_rows = solr_query = solr_sort = field_to_search = page_size = sql_query = ""
  link_to_photos = ""
  no_display = False
  first_record = True
  photo_evidence_data = []

  space = '&nbsp;'
  two_spaces = space + space
  newline = '\n'

  start_treeview = newline
  start_treeview += '<div id="sidetreecontrol">' + newline
  start_treeview += '<a href="?#">Collapse All</a> | <a href="?#">Expand All</a>' + newline
  start_treeview += '</div>' + newline
  start_treeview += '<ul class="treeview" id="tree">' + newline + newline

  start_hidden_list = '<ul style="display:none;">' + newline

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

    if request.GET.has_key( 's' ): #{
      search_term = request.GET["s"].strip()
    #}
    else:
      search_term = '*'

    if len( request.GET ) > 1: #{
      if request.GET.has_key( 'se' ):
        field_to_search = escape( request.GET["se"] )
      if request.GET.has_key( 'pa' ):
        page_size = escape( request.GET["pa"] )        
    #}

    # Set search term
    solr_query = escape_for_solr( search_term )
    if ' ' in solr_query:
      solr_query = '(%s)' % solr_query

    if search_term=='*' or search_term=='':
      solr_query='*:*'

    else: #{

      if field_to_search.lower()=='author/title':
        solr_query ="authortitle:%s" % solr_query

      elif field_to_search.lower()=='modern library/institution':
        solr_query ="library:%s" % solr_query

      elif field_to_search.lower()=='medieval library':
        solr_query ="provenance:%s" % solr_query

      elif field_to_search.lower()=='location':  
        solr_query ="location:%s" % solr_query

      elif field_to_search.lower()=='library/institution':
        solr_query ="library:%s" % solr_query
    #}
    
    # Set page size
    if page_size =="100":
      solr_rows=100
    elif page_size=="200":
      solr_rows=200
    elif page_size=="500":
      solr_rows=500
    elif page_size=="1000":
      solr_rows=1000
    else: 
      solr_rows=Book.objects.count()
    
    # Set sort field
    if field_to_search.lower()=='author/title':
      solr_sort = "soc asc,ev asc,pr asc,ct asc,ins asc,ml1 asc,ml2 asc,sm1 asc,sm2 asc"
    else:
      solr_sort="pr asc,ct asc,ins asc,ml1 asc,ml2 asc,sm1 asc,sm2 asc,ev asc,soc asc,dt asc,pm asc,mc asc,uk asc"

    # Run the Solr query
    s_para={'q'    : solr_query,
            'wt'   : s_wt,  # 's_wt', i.e. 'writer type' is set in config.py, defaults to "json"
            'start': 0, 
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
        link_to_photos=""

        # ID
        id=resultsets[i]['id']

        # Provenance
        provenance = trim( resultsets[i]['pr'], False )
        provenance = provenance.upper()

        # County
        if resultsets[i]['ct']:
          provenance += ", " + trim( resultsets[i]['ct'], False )

        # Institution
        if resultsets[i]['ins']:
          provenance += ", <i>" + trim( resultsets[i]['ins'] ) + "</i>"

        # Modern library 1
        modern_location1 = trim( resultsets[i]['ml1'], False )

        # Modern library 2
        modern_location2 = trim( resultsets[i]['ml2'] ) + "&cedil;"

        # shelfmark 1
        shelfmark1 = trim( resultsets[i]['sm1'] )
        if shelfmark1: shelfmark1 = two_spaces + shelfmark1

        # shelfmark 2
        shelfmark2 = trim( resultsets[i]['sm2'] )
        if shelfmark2: #{
          shelfmark2 = two_spaces + shelfmark2
          if not shelfmark2.endswith( '.' ): shelfmark2 += '.'
        #}

        # make sure there is a full stop at the end of the combined shelfmarks
        elif shelfmark1: #{
          if not shelfmark1.endswith( '.' ): shelfmark1 += '.'
        #}

        # evidence code
        evidence_code = "<i>" + trim( resultsets[i]['ev'] ) + "</i>" 
        
        # suggestion of contents
        suggestion_of_contents = trim( resultsets[i]['soc'] )

        # date
        date_of_work = trim( resultsets[i]['dt'] )
        if date_of_work: #{ 
          date_of_work = two_spaces + date_of_work
          if not date_of_work.endswith( '.' ): date_of_work += '.'
        #}
        
        # pressmark
        pressmark = trim( resultsets[i]['pm'] )
        if pressmark: #{
          pressmark = two_spaces + pressmark
          if not pressmark.endswith( '.' ): pressmark += '.'
        #}

        # medieval catalogue
        medieval_catalogue = trim( resultsets[i]['mc'] )
        if medieval_catalogue: #{
          if medieval_catalogue.endswith( '.' ):
            medieval_catalogue = two_spaces + '[' + medieval_catalogue + ']'
          else:
            medieval_catalogue = two_spaces + '[' + medieval_catalogue + ']' + '.'
        #}
        
        # unknown
        unknown = trim( resultsets[i]['uk'] )
        if unknown: #{
          unknown = two_spaces + unknown
          if not unknown.endswith( '.' ): unknown += '.'
        #}

        # notes
        notes_on_evidence = trim( resultsets[i]['nt'] )
        if notes_on_evidence: notes_on_evidence = two_spaces + notes_on_evidence + '.'

        # photos
        sql_query = "select * from feeds_photo where feeds_photo.item_id='%s'" % id
        photo_evidence_data = list( Photo.objects.raw( sql_query ) )
        for e in photo_evidence_data: #{
          link_to_photos += '<a href="%s" rel="lightbox%s" title="%s"></a>' % (e.image.url, id, e.title)
          link_to_photos += newline
        #}
        if link_to_photos: #{
          link_to_photos=link_to_photos.replace( "</a>", "%s</a>" % evidence_code, 1 )
        #}
        
        # If searching on author/title (i.e. 'suggestion of contents'), 
        # show author/title as heading 1, then provenance as heading 2, then modern library and shelfmark.
        if field_to_search.lower()=='author/title': #{

          # Set up a string containing modern library and shelfmark
          detail_text = newline + '<!-- start book ID ' + id + ' -->' + newline
          detail_text = '<li class="one_book">' + newline
          detail_text += '<span class="modern_location_heading"><strong>' + newline
          detail_text += '%s%s%s' % (modern_location1, space, modern_location2)
          detail_text += newline + '</strong></span><!-- end modern location_heading -->' + newline
          detail_text += '%s<!-- shelfmark 1 -->%s%s' % ( space, shelfmark1, two_spaces )
          detail_text += newline
          detail_text += '<span class="detail">' + newline
          detail_text += '<!-- shelfmark 2 -->%s%s' % (shelfmark2, two_spaces)
          detail_text += newline
          detail_text += '<a href="/mlgb/book/%s/">' % id
          detail_text += '<img src="/mlgb/media/img/detail.gif" alt="detail" border="0" />'
          detail_text += '</a>' + newline
          detail_text += '</span></li><!-- end book ID ' + id + ' -->' + newline + newline

          # See if heading 1 has changed
          if h1 <> "%s%s" % (evidence_code, suggestion_of_contents): #{ new combination of evidence 
                                                                     #  and 'suggestion of contents'
            h2=""
            if not first_record: #{
              html += end_inner_and_outer_sections
            #}

            html += start_outer_section + newline
            html += '<span class="outerhead"><strong>' + newline

            if len( photo_evidence_data ) <> 0:
              html += '%s%s%s' % (link_to_photos, two_spaces, suggestion_of_contents)
            else:
              html +='%s%s%s' % (evidence_code, two_spaces, suggestion_of_contents)

            html += newline + '</strong></span><!-- end "outer head" span -->' + newline
            html += start_hidden_list
          #}

          # See if heading 2 has changed
          if h2 <> provenance: #{ start new provenance
            h2 = provenance
            if h1 == "%s%s" % (evidence_code, suggestion_of_contents): #{
              if not first_record: #{
                html += end_inner_section
              #}
            #}
            else: #{
              h1="%s%s" % (evidence_code, suggestion_of_contents)
            #}

            html += start_inner_section + newline
            html += '<span class="innerhead">%s</span><!-- end "inner head" span -->' % provenance
            html += newline + start_hidden_list
          #}
        #}

        else: #{ not searching on author/title, have medieval library as main heading, then modern one
          
          detail_text = newline + '<!-- start book ID ' + id + ' -->' + newline
          detail_text += '<li class="one_book"><span class="modern_location_heading"><strong>' + newline
          detail_text += modern_location2 + newline
          detail_text += '</strong></span><!-- end modern location heading -->' + two_spaces + newline
          detail_text += '<span class="detail">' + newline
          detail_text += '<!-- shelfmark 1 -->%s<!-- shelfmark 2 -->%s' % (shelfmark1, shelfmark2)
          detail_text += two_spaces + newline

          if len( photo_evidence_data ) <> 0:
            detail_text += link_to_photos
          else:
            detail_text += evidence_code

          detail_text += two_spaces
          detail_text += '%s%s%s%s%s ' \
                      % (suggestion_of_contents, date_of_work, pressmark, medieval_catalogue, unknown)
          detail_text += newline
          detail_text += '<a href="/mlgb/book/%s/">' % id
          detail_text += '<img src="/mlgb/media/img/detail.gif" alt="detail" border="0" />'
          detail_text += '</a>' + newline
          detail_text += '</span></li><!-- end book ID ' + id + ' -->' + newline + newline
                  
          if h1 <> provenance: #{  # new provenance
            h2=""
            if not first_record: html += end_inner_and_outer_sections
            
            html += newline
            html += start_outer_section + newline
            html += '<span class="outerhead"><strong>%s</strong></span>' % provenance
            html += '<!-- end "outer head" span -->' + newline + start_hidden_list
          #}

          if h2 <> modern_location1: #{
            h2 = modern_location1
            if h1 == provenance: #{
              if not first_record: #{
                html += end_inner_section
              #}
            else:    
              h1 = provenance
            #}
            html += newline
            html += start_inner_section + newline
            html += '<span class="innerhead">%s</span>' % modern_location1
            html += '<!-- end "inner head" span -->' + newline + start_hidden_list
          #}
        #}

        # Add the string of HTML that you have generated for this record to the main HTML source
        html += detail_text
        first_record=False

      #} # end loop through result sets

      if html:
        lists = start_treeview + html + end_inner_and_outer_sections + '</ul><!-- end ID "tree" -->'

    #} # end of check on whether we retrieved a result

    no_display=True

  #} # end of check on whether a search term was found in GET
    
  t = loader.get_template('mlgb/mlgb.html')

  # check number of records displayed
  # N.B. this displays the requested page size, not the number of rows in the index!
  # TODO - must fix this and make it behave more sensibly!
  if number_of_records : #{ 
    if number_of_records > solr_rows:
      number_of_records = solr_rows
  #}
  else:
    number_of_records = 0
    
  c = Context( {
      'lists': lists,
      'no'   : number_of_records,
      'nodis': no_display,
      's'    : search_term,
  } )

  return HttpResponse( t.render( c ) )

#}
# end function mlgb()
#--------------------------------------------------------------------------------

def category(request): #{

  text = pr = ml1 = body = dl = s = resultsets = None
  norecord = s_rows = s_sort = lists = ""
  nodis = False
  bod = facet = True
  
  if escape(request.GET["se"]) == '3':
    f_field = "ml1"
    s = "Location"
    
  elif escape(request.GET["se"]) == '2':
    f_field = "ml2"
    s = "Library/Institution"
    
  else:
    f_field = "pr"
    s = "Medieval Library"

  s_sort="pr asc,ml1 asc,ml2 asc,sm1 asc,sm2 asc,ev asc,soc asc,dt asc,pm asc,mc asc,uk asc"
        
  s_rows=-1
  
  s_para = { 'q':'*:*',
             'wt':s_wt,
             'start':0, 
             'rows':s_rows,
             'sort':s_sort}
  if facet:
    s_para['facet.mincount']='1'
    s_para['facet']='on'
    s_para['facet.limit']='-1'
    s_para['facet.field']=["pr","ml1","ml2"]

  r = MLGBsolr()
  r.solrresults( s_para, Facet = facet )

  end_inner_section = '</ul></li>\n'
  end_inner_and_outer_sections = '</ul></li></ul></li>\n'
      
  if r.connstatus and r.s_result: #{
    resultsets = r.s_result.get('facet')
    norecord = r.s_result.get('numFound')
  #}

  nodis=True

  if escape(request.GET["se"])=='3':
    lists= resultsets["ml1"]

  elif escape(request.GET["se"])=='2':
    lists= resultsets["ml2"]

  else:  
      lists= resultsets["pr"]

  t = loader.get_template('mlgb/category.html')

  p1 = p2 = p3 = p = []
  param = {}
  j = 0
  for i in (lists): #{
    j +=1
    
    if j%2 == 0: #{
      param['v'] = i
      p.append(param)
      param={}
    #}
    else: #{
      param['k']=i
    #}
  #}

  c = Context( {
      'lists': p,
      'p1'   : p1,
      'p2'   : p2,
      'p3'   : p3, 
      'no'   : norecord,
      'nodis': nodis,
      's':s,
  } )

  return HttpResponse(t.render(c))
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
