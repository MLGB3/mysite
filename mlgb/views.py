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

def detail(request, book_id): #{

  try:
    p = Poll.objects.get(pk=book_id)
  except Poll.DoesNotExist:
    raise Http404

  return render_to_response('mlgb/detail.html', {'book': p})
#}
# end detail
#--------------------------------------------------------------------------------

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
  norecord = tmp = s_rows = s_field = ""
  nodis = False
  bod = True

  d_tag = '<div id="sidetreecontrol"> <a href="?#">Collapse All</a> | <a href="?#">Expand All</a> </div>'
  d_tag += '<ul class="treeview" id="tree">'

  dn_tag = '<ul style="display:none;">\n'
  
  if request.GET and request.GET["s"].strip(' %#~@/<>^()?[]{}!"^+-'): #{

    s =( request.GET[ "s" ] )
    s_field = "%s" % s.strip(' %#~@/<>^()?[]{}!"^+-').lower()
    if s == '*':
      s_field ="*:*"
    
    
    s_rows = Book.objects.count()
    
    s_para={'q'    : s_field,
            'wt'   : s_wt,
            'start': 0, 
            'rows' : s_rows,
            'sort' : s_sort}

    r=MLGBsolr()

    r.solrresults( s_para )

    h1_tag_e = '</ul></li>\n'
    h2_tag_e = '</ul></li></ul></li>\n'
        
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
            text += h2_tag_e
          text += '<li class="expandable"><div class="hitarea expandable-hitarea"></div>' \
               +  '<span><strong>%s</strong></span>\n%s' % (pr,dn_tag)
        #}

        if h2 <> ml1: #{
          h2=ml1
          if h1==pr: #{
            if not bod:
              text += h1_tag_e
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
        lists=d_tag + text + h2_tag_e + '</ul>'
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

  text = pr = ml1 = body = lists = dl = s = resultsets = None
  norecord = tmp = s_rows = s_field = s_sort = se = pa = query = st = ""
  nodis = False
  bod = True
  data = []

  d_tag =  '<div id="sidetreecontrol"> <a href="?#">Collapse All</a> | <a href="?#">Expand All</a> </div>'
  d_tag += '<ul class="treeview" id="tree">'
  dn_tag = '<ul style="display:none;">\n'
  
  space = '&nbsp;'
  two_spaces = space + space

  punctuation = ' %#~@/<>^()?[]{}!"^+-'

  if request.GET and request.GET["s"].strip( punctuation ): #{ # was a search term found in GET?

    s = request.GET["s"].strip( punctuation )

    if len( request.GET ) > 1: #{
      se = escape( request.GET["se"] )
      pa = escape( request.GET["pa"] )        
    #}

    # Set search term
    # N.B. This way of setting the search term introduces a BUG: names containing brackets
    # cause the search to fail. TODO - fix this!
    s_field ="%s" % s.strip( punctuation ).lower()

    if s=='*':
      s_field=solr_qa # '[* TO *]' (from config.py)

    else: #{

      if se.lower()=='author/title':
        s_field ="authortitle:%s" % s_field

      elif se.lower()=='modern library/institution':
        s_field ="library:%s" % s_field

      elif se.lower()=='medieval library':
        s_field ="provenance:%s" % s_field

      elif se.lower()=='location':  
        s_field ="location:%s" % s_field

      elif se.lower()=='library/institution':
        s_field ="library:%s" % s_field
    #}
    
    # Set page size
    if pa =="100":
      s_rows=100
    elif pa=="200":
      s_rows=200
    elif pa=="500":
      s_rows=500
    elif pa=="1000":
      s_rows=1000
    else: 
      s_rows=Book.objects.count()
    
    # Set sort field
    if se.lower()=='author/title':
      s_sort = "soc asc,ev asc,pr asc,ct asc,ins asc,ml1 asc,ml2 asc,sm1 asc,sm2 asc"
    else:
      s_sort="pr asc,ct asc,ins asc,ml1 asc,ml2 asc,sm1 asc,sm2 asc,ev asc,soc asc,dt asc,pm asc,mc asc,uk asc"

    # Run the Solr query
    s_para={'q'    : s_field,
            'wt'   : s_wt,
            'start': 0, 
            'rows' : s_rows,
            'sort' : s_sort}
    r=MLGBsolr()
    r.solrresults( s_para, Facet=facet )


    # Start to display the results
    h1_tag_e = '</ul></li>\n'
    h2_tag_e = '</ul></li></ul></li>\n'
        
    if r.connstatus and r.s_result: #{ #did we retrieve a result?

      resultsets = r.s_result.get( 'docs' )
      norecord = r.s_result.get( 'numFound' )
      
      text = h1 = h2 = d = st = ""

      # Start loop through result sets
      for i in xrange( 0, len( resultsets ) ): #{
        st=""

        # ID
        id=resultsets[i]['id']

        # Provenance
        pr = trim( resultsets[i]['pr'], False )
        pr = pr.upper()

        # County
        if resultsets[i]['ct']:
          pr += ", " + trim( resultsets[i]['ct'], False )

        # Institution
        if resultsets[i]['ins']:
          pr += ", <i>" + trim( resultsets[i]['ins'] ) + "</i>"

        # Modern library 1
        ml1 = trim( resultsets[i]['ml1'], False )

        # Modern library 2
        ml2 = trim( resultsets[i]['ml2'] ) + "&cedil;"

        # shelfmark 1
        sm1 = trim( resultsets[i]['sm1'] )
        if sm1: sm1 = two_spaces + sm1

        # shelfmark 2
        sm2 = trim( resultsets[i]['sm2'] )
        if sm2: #{
          sm2 = two_spaces + sm2
          if not sm2.endswith( '.' ): sm2 += '.'
        #}

        # make sure there is a full stop at the end of the combined shelfmarks
        elif sm1: #{
          if not sm1.endswith( '.' ): sm1 += '.'
        #}

        # evidence code
        ev = "<i>" + trim( resultsets[i]['ev'] ) + "</i>" 
        
        # suggestion of contents
        soc = trim( resultsets[i]['soc'] )

        # date
        dt = trim( resultsets[i]['dt'] )
        if dt: #{ 
          dt = two_spaces + dt
          if not dt.endswith( '.' ): dt += '.'
        #}
        
        # pressmark
        pm = trim( resultsets[i]['pm'] )
        if pm: #{
          pm = two_spaces + pm
          if not pm.endswith( '.' ): pm += '.'
        #}

        # medieval catalogue
        mc = trim( resultsets[i]['mc'] )
        if mc: #{
          if mc.endswith( '.' ):
            mc = two_spaces + '[' + mc + ']'
          else:
            mc = two_spaces + '[' + mc + ']' + '.'
        #}
        
        # unknown
        uk = trim( resultsets[i]['uk'] )
        if uk: uk = two_spaces + uk + '.'

        # notes
        nt = trim( resultsets[i]['nt'] )
        if nt: nt = two_spaces + nt + '.'

        # photos
        query = "select * from feeds_photo where feeds_photo.item_id='%s'" % id
        data=list(Photo.objects.raw(query))
        for e in data: #{
          st += '<a href="%s" rel="lightbox%s" title="%s"></a>' % (e.image.url, id, e.title)
        #}
        if st: #{
          st=st.replace("</a>","%s</a>",1) % ev
        #}
        
        # If searching on author/title (i.e. 'suggestion of contents'), 
        # show author/title as heading 1, then provenance as heading 2, then modern library and shelfmark.
        if se.lower()=='author/title': #{

          # Set up a string containing modern library and shelfmark
          body = '<li><span><strong>'
          body += '%s%s%s' % (ml1, space, ml2)
          body += '</strong></span>'
          body += '%s%s%s' % ( space, sm1, two_spaces )
          body += '<span class="detail">'
          body += '%s%s' % (sm2, two_spaces)
          body += '<a href="/mlgb/book/%s/">' % id
          body += '<img src="/mlgb/media/img/detail.gif" alt="detail" border="0" />'
          body += '</a></span></li>\n'

          # See if heading 1 has changed
          if h1 <> "%s%s" % (ev,soc): #{ start new combination of evidence code & 'suggestion of contents'
            h2=""
            if not bod: #{
              text += h2_tag_e
            #}

            text += '<li class="expandable">'
            text += '<div class="hitarea expandable-hitarea"></div>'
            text += '<span><strong>'

            if len(data) <> 0:
              text += '%s%s%s' % (st, two_spaces, soc)
            else:
              text +='%s%s%s' % (ev, two_spaces, soc)

            text += '</strong></span>\n%s' % dn_tag
          #}

          # See if heading 2 has changed
          if h2 <> pr: #{ start new provenance
            h2 = pr
            if h1 == "%s%s" % (ev,soc): #{
              if not bod: #{
                text += h1_tag_e
              #}
            #}
            else: #{
              h1="%s%s" % (ev,soc)
            #}

            text += '<li class="expandable">'
            text += '<div class="hitarea expandable-hitarea"></div>'
            text += '<span>%s</span>\n%s' % (pr,dn_tag)
          #}
        #}

        else: #{ not searching on author/title, have medieval library as main heading, then modern one
          
          body = '<li><span><strong>'
          body += ml2
          body += '</strong></span>' + two_spaces
          body += '<span class="detail">'
          body += '%s%s' % (sm1, sm2)
          body += two_spaces

          if len( data ) <> 0:
            body += st
          else:
            body += ev

          body += two_spaces
          body += '%s%s%s%s%s ' % (soc, dt, pm, mc, uk)
          body += '<a href="/mlgb/book/%s/">' % id
          body += '<img src="/mlgb/media/img/detail.gif" alt="detail" border="0" />'
          body += '</a></span></li>\n'
                  
          if h1 <> pr: #{  # new provenance
            h2=""
            if not bod: text += h2_tag_e
            
            text += '<li class="expandable">'
            text += '<div class="hitarea expandable-hitarea"></div>'
            text += '<span><strong>%s</strong></span>\n%s' % (pr,dn_tag)
          #}

          if h2 <> ml1: #{
            h2 = ml1
            if h1 == pr: #{
              if not bod: #{
                text += h1_tag_e
              #}
            else:    
              h1 = pr
            #}
            text += '<li class="expandable"><div class="hitarea expandable-hitarea"></div>'
            text += '<span>%s</span>\n%s' % (ml1,dn_tag)
          #}
        #}

        # Add the string of HTML that you have generated for this record to the main HTML source
        text += body
        bod=False

      #} # end loop through result sets

      if text:
        lists=d_tag + text + h2_tag_e + '</ul>'

    #} # end of check on whether we retrieved a result

    nodis=True

  #} # end of check on whether a search term was found in GET
    
  t = loader.get_template('mlgb/mlgb.html')

  # check number of records displayed
  if norecord : #{ 
    if norecord > s_rows:
      norecord = s_rows
  #}
  else:
    norecord = 0
    
  c = Context( {
      'lists': lists,
      'no'   : norecord,
      'nodis': nodis,
      's'    : s,
  } )

  return HttpResponse( t.render( c ) )

#}
# end function mlgb()
#--------------------------------------------------------------------------------

def category(request):

  text = pr = ml1 = body = dl = s = resultsets = None
  norecord = tmp = s_rows = s_field = s_sort = s_field = lists = ""
  nodis = False
  bod = facet = True
  
  s_field = "*:*"

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

  h1_tag_e = '</ul></li>\n'
  h2_tag_e = '</ul></li></ul></li>\n'
      
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
  for i in (lists):
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
