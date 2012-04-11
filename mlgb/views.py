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
def fulltext(request):
	data=[]
	lists=[]
	data3=list(Book.objects.values('author_title').distinct().order_by('author_title'))
	data2=list(Modern_location_2.objects.values('modern_location_2').distinct().order_by('modern_location_2'))
	data1=list(Modern_location_1.objects.values('modern_location_1').distinct().order_by('modern_location_1'))
	data=list(Provenance.objects.values('provenance').distinct().order_by('provenance'))
	#data4=list(Book.objects.values('modern_location_1','modern_location_2').distinct().order_by('modern_location_1','modern_location_2'))
	lists=[]
	#data = serializers.serialize("json", Provenance.objects.all())
	for e in data:lists.append(e['provenance'])
	for e in data1:lists.append(e['modern_location_1'])
	for e in data2:lists.append(e['modern_location_2'])
	for e in data3:lists.append(e['author_title'])
	query = request.GET.get("q", "")
	lists=sorted(set(lists))
       #lists.sort()
	if len(query) == 0 or query[0] == " " :
		json = simplejson.dumps(lists)
	else:
		json = simplejson.dumps([e for e in lists
		                     if e.lower().find(query.lower()) != -1])
	return HttpResponse(json, mimetype = 'application/json')
    
#-----------------------------
def download(request):
	response=None
	data=[]
	text=""
	
	rc="\r\n"
	if request.GET["q"]=="2":rc="<br/>"
	if request.GET:
		data = Book.objects.filter(id=request.GET["i"])
		text ="Provenance: %s%s" % (data[0].provenance,rc)
		text +="Location: %s, %s%s" % (data[0].modern_location_2,data[0].modern_location_1,rc)
		text +="Shelfmark: %s %s%s" % (data[0].shelfmark_1, data[0].shelfmark_2,rc)
		text +="Author/Title: %s %s%s" % (data[0].evidence, data[0].author_title,rc)

		if data[0].date:
			text +="Date: %s%s" % (data[0].date,rc)
		
		if data[0].pressmark:
			text +="Pressmark: %s%s" % (data[0].pressmark,rc)
		
		if data[0].medieval_catalogue:
			text +="Medieval Catalogue: %s%s" % (data[0].medieval_catalogue,rc)
		
		if data[0].ownership:
			text +="Ownership: %s%s" % (data[0].ownership,rc)
		
		if data[0].notes.strip('" \n\r'):
			text +="Notes: %s" % (data[0].notes.strip('" \n\r'))

	if request.GET["q"]=="1":
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
	elif request.GET["q"]=="2":
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
	else:
		pass
	return response
#--------------------------------------------------------------------------------
def detail(request, book_id):
    try:
        p = Poll.objects.get(pk=book_id)
    except Poll.DoesNotExist:
        raise Http404
    return render_to_response('mlgb/detail.html', {'book': p})
#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------
def index(request):
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
    r.solrresults(s_para,Facet=facet)
    t = loader.get_template('index.html')

    if r.connstatus and r.s_result:
	    resultsets= r.s_result.get('facet')
	    #t = loader.get_template('index.html')
	    lists1= resultsets["pr"]
	    lists2= resultsets["ml1"]
	    lists3= resultsets["ml2"]  
	    c = Context({
		'lists1': len(lists1)/2,
		'lists2': len(lists2)/2,
		'lists3': len(lists3)/2,
	    })
    else:
	    c = Context({
		'lists1': 0,
		'lists2': 0,
		'lists3': 0,
	    })
    return HttpResponse(t.render(c))    
    #return render_to_response('index.html')
#--------------------------------------------------------------------------------
def search(request):
	text=pr=ml1=body=lists=dl=s=resultsets=None
	norecord=tmp=s_rows=s_field=""
	nodis=False
	bod=True

	d_tag ='<div id="sidetreecontrol"> <a href="?#">Collapse All</a> | <a href="?#">Expand All</a> </div>'
	d_tag +='<ul class="treeview" id="tree">'
	dn_tag ='<ul style="display:none;">\n'
	
	if request.GET and request.GET["s"].strip(' %#~@/<>^()?[]{}!"^+-'):
		s=(request.GET["s"])
		s_field ="%s" % s.strip(' %#~@/<>^()?[]{}!"^+-').lower()
		if s=='*':
			s_field ="*:*"
		
		
		s_rows=Book.objects.count()
		
		s_para={'q':s_field,
		        'wt':s_wt,
		        'start':0, 
		        'rows':s_rows,
		        'sort':s_sort}
		r=MLGBsolr()
		r.solrresults(s_para)
		h1_tag_e = '</ul></li>\n'
		h2_tag_e = '</ul></li></ul></li>\n'
	      
		if r.connstatus and r.s_result:
			resultsets= r.s_result.get('docs')
			norecord= r.s_result.get('numFound')
			
			text=h1=h2=d=""
			for i in xrange(0, len(resultsets)):
				id=resultsets[i]['id']
				pr=resultsets[i]['pr'].strip(' ')
				ml1=resultsets[i]['ml1'].strip(' ')
				ml2= "%s&cedil;" % resultsets[i]['ml2'].strip('" ')
				if resultsets[i]['sm1'].strip(' '):sm1="&nbsp;&nbsp;%s." % resultsets[i]['sm1'].strip('" ')
				else: sm1=""
				if resultsets[i]['sm2'].strip(' '):sm2="&nbsp;&nbsp;%s." % resultsets[i]['sm2'].strip('" ')
				else: sm2=""
				if resultsets[i]['ev'].strip(' '):ev="<i>%s</i>" % resultsets[i]['ev'].strip('" ')
				else: ev=""
				soc=resultsets[i]['soc'].strip('" ')
				if resultsets[i]['dt'].strip(' '): dt="&nbsp;&nbsp;%s." % resultsets[i]['dt'].strip('" ')
				else: dt=""
				if resultsets[i]['pm'].strip(' '):pm="&nbsp;&nbsp;%s." % resultsets[i]['pm'].strip('" ')
				else: pm=""
				if resultsets[i]['mc'].strip(' '):mc="&nbsp;&nbsp;[%s]." % resultsets[i]['mc'].strip('" ')
				else: mc=""
				if resultsets[i]['uk'].strip(' '):uk="&nbsp;&nbsp;%s." % resultsets[i]['uk'].strip('" ')
				else: uk=""
				if resultsets[i]['nt'].strip(' '):nt="&nbsp;&nbsp;%s." % resultsets[i]['nt'].strip('" ')
				else: nt=""
				
				body= '<li><span><strong>%s</strong></span>&nbsp;&nbsp;<span class="detail">%s%s&nbsp;&nbsp;%s&nbsp;&nbsp;%s%s%s%s%s <a href="/mlgb/book/%s/"><img src="/mlgb/media/img/detail.gif" alt="detail" border="0" /></a></span></li>\n' % (ml2,sm1,sm2,ev,soc,dt,pm,mc,uk,id)
			    
			    
				if h1<>pr:
					h2=""
					if not bod: text += h2_tag_e
					
					text +='<li class="expandable"><div class="hitarea expandable-hitarea"></div><span><strong>%s</strong></span>\n%s' % (pr,dn_tag)
				if h2<>ml1:
					h2=ml1
					if h1==pr:
						if not bod:text += h1_tag_e
					else:    
						h1=pr
					text += '<li class="expandable"><div class="hitarea expandable-hitarea"></div><span>%s</span>\n%s' % (ml1,dn_tag)
				text += body
				bod=False
			if text:lists=d_tag + text + h2_tag_e + '</ul>'
		nodis=True
    
	t = loader.get_template('mlgb/mlgb.html')

	if norecord :
		if norecord > s_rows: norecord=s_rows
	else:norecord=0
		
	c = Context({
	    'lists': lists,'no':norecord,'nodis':nodis,'s':s,
	})
	return HttpResponse(t.render(c))


#--------------------------------------------------------------------------------
def mlgb(request):
	text=pr=ml1=body=lists=dl=s=resultsets=None
	norecord=tmp=s_rows=s_field=s_sort=se=pa=query=st=""
	nodis=False
	bod=True
	data=[]

	d_tag ='<div id="sidetreecontrol"> <a href="?#">Collapse All</a> | <a href="?#">Expand All</a> </div>'
	d_tag +='<ul class="treeview" id="tree">'
	dn_tag ='<ul style="display:none;">\n'
	
	if request.GET and request.GET["s"].strip(' %#~@/<>^()?[]{}!"^+-'):
		s=request.GET["s"].strip(' %#~@/<>^()?[]{}!"^+-')
		if len(request.GET)>1:
			se=escape(request.GET["se"])
			pa=escape(request.GET["pa"])        
		s_field ="%s" % s.strip(' %#~@/<>^()?[]{}!"^+-').lower()
		if s=='*':
			#s_field ="*:*"
                        s_field=solr_qa
		else:
			if se.lower()=='author/title':
				s_field ="authortitle:%s" % s_field
				#s_sort = "soc asc"
			elif se.lower()=='modern library/institution':
				s_field ="library:%s" % s_field
				#sort = s_sort
			elif se.lower()=='medieval library':
				s_field ="provenance:%s" % s_field
			elif se.lower()=='location':  
				s_field ="location:%s" % s_field
			elif se.lower()=='library/institution':
				#s_field ="institute:%s" % s_field
                                s_field ="library:%s" % s_field
		
		if pa =="100":
			s_rows=100
		elif pa=="200":
			s_rows=200
		elif pa=="500":
			s_rows=500
		elif pa=="1000":
			s_rows=1000
		else: s_rows=Book.objects.count()
		
		if se.lower()=='author/title':
			s_sort = "soc asc,ev asc,pr asc,ct asc,ins asc,ml1 asc,ml2 asc,sm1 asc,sm2 asc"
		else:
		        s_sort="pr asc,ct asc,ins asc,ml1 asc,ml2 asc,sm1 asc,sm2 asc,ev asc,soc asc,dt asc,pm asc,mc asc,uk asc"
		s_para={'q':s_field,
		        'wt':s_wt,
		        'start':0, 
		        'rows':s_rows,
		        'sort':s_sort}
		r=MLGBsolr()
		r.solrresults(s_para,Facet=facet)
		h1_tag_e = '</ul></li>\n'
		h2_tag_e = '</ul></li></ul></li>\n'
	      
		if r.connstatus and r.s_result:
			resultsets= r.s_result.get('docs')
			norecord= r.s_result.get('numFound')
			
			text=h1=h2=d=st=""
			for i in xrange(0, len(resultsets)):
				st=""
				id=resultsets[i]['id']
				pr=resultsets[i]['pr'].strip(' ').upper()
				if resultsets[i]['ct']:pr += ", "+ resultsets[i]['ct'].strip(' ')
				if resultsets[i]['ins']:pr += ", <i>"+ resultsets[i]['ins'].strip(' ')+"</i>"
				ml1=resultsets[i]['ml1'].strip(' ')
				ml2= "%s&cedil;" % resultsets[i]['ml2'].strip('" ')
				if resultsets[i]['sm1'].strip(' '):sm1="&nbsp;&nbsp;%s." % resultsets[i]['sm1'].strip('" ')
				else: sm1=""
				if resultsets[i]['sm2'].strip(' '):sm2="&nbsp;&nbsp;%s." % resultsets[i]['sm2'].strip('" ')
				else: sm2=""
				if resultsets[i]['ev'].strip(' '):ev="<i>%s</i>" % resultsets[i]['ev'].strip('" ')
				else: ev=""
				soc=resultsets[i]['soc'].strip('" ')
				if resultsets[i]['dt'].strip(' '): dt="&nbsp;&nbsp;%s." % resultsets[i]['dt'].strip('" ')
				else: dt=""
				if resultsets[i]['pm'].strip(' '):pm="&nbsp;&nbsp;%s." % resultsets[i]['pm'].strip('" ')
				else: pm=""
				if resultsets[i]['mc'].strip(' '):mc="&nbsp;&nbsp;[%s]." % resultsets[i]['mc'].strip('" ')
				else: mc=""
				if resultsets[i]['uk'].strip(' '):uk="&nbsp;&nbsp;%s." % resultsets[i]['uk'].strip('" ')
				else: uk=""
				if resultsets[i]['nt'].strip(' '):nt="&nbsp;&nbsp;%s." % resultsets[i]['nt'].strip('" ')
				else: nt=""

				query = "select * from feeds_photo where feeds_photo.item_id='%s'" % id
				data=list(Photo.objects.raw(query))
				for e in data:st +="<a href=%s rel='lightbox%s'  title='%s'></a>" % (e.image.url,id,e.title)
				if st:st=st.replace("</a>","%s</a>",1) % ev
				
				if se.lower()=='author/title':
					body= '<li><span><strong>%s&nbsp;%s</strong></span>&nbsp%s&nbsp;&nbsp;<span class="detail">%s&nbsp;&nbsp;<a href="/mlgb/book/%s/"><img src="/mlgb/media/img/detail.gif" alt="detail" border="0" /></a></span></li>\n' % (ml1,ml2,sm1,sm2,id)
					if h1<>"%s%s" % (ev,soc):
						h2=""
						if not bod: text += h2_tag_e
						if len(data)<>0:
							text +='<li class="expandable"><div class="hitarea expandable-hitarea"></div><span><strong>%s&nbsp;&nbsp;%s</strong></span>\n%s' % (st,soc,dn_tag)
						else:
							text +='<li class="expandable"><div class="hitarea expandable-hitarea"></div><span><strong>%s&nbsp;&nbsp;%s</strong></span>\n%s' % (ev,soc,dn_tag)
					if h2<>pr:
						h2=pr
						if h1=="%s%s" % (ev,soc):
							if not bod:text += h1_tag_e
						else:    
							h1="%s%s" % (ev,soc)
						text += '<li class="expandable"><div class="hitarea expandable-hitarea"></div><span>%s</span>\n%s' % (pr,dn_tag)
				
				else:
					#<a href="%s" rel="lightbox-journey"  title="%s">%s</a> % (e.image,e.title)
					if len(data)<>0:
						
						body= '<li><span><strong>%s</strong></span>&nbsp;&nbsp;<span class="detail">%s%s&nbsp;&nbsp;%s&nbsp;&nbsp;%s%s%s%s%s <a href="/mlgb/book/%s/"><img src="/mlgb/media/img/detail.gif" alt="detail" border="0" /></a></span></li>\n' % (ml2,sm1,sm2,st,soc,dt,pm,mc,uk,id)
					else:
						body= '<li><span><strong>%s</strong></span>&nbsp;&nbsp;<span class="detail">%s%s&nbsp;&nbsp;%s&nbsp;&nbsp;%s%s%s%s%s <a href="/mlgb/book/%s/"><img src="/mlgb/media/img/detail.gif" alt="detail" border="0" /></a></span></li>\n' % (ml2,sm1,sm2,ev,soc,dt,pm,mc,uk,id)
							    
					if h1<>pr:
						h2=""
						if not bod: text += h2_tag_e
						
						text +='<li class="expandable"><div class="hitarea expandable-hitarea"></div><span><strong>%s</strong></span>\n%s' % (pr,dn_tag)
					if h2<>ml1:
						h2=ml1
						if h1==pr:
							if not bod:text += h1_tag_e
						else:    
							h1=pr
						text += '<li class="expandable"><div class="hitarea expandable-hitarea"></div><span>%s</span>\n%s' % (ml1,dn_tag)
				text += body
				bod=False
			if text:lists=d_tag + text + h2_tag_e + '</ul>'
		nodis=True
    
	t = loader.get_template('mlgb/mlgb.html')

	if norecord :
		if norecord > s_rows: norecord=s_rows
	else:norecord=0
		
	c = Context({
	    'lists': lists,'no':norecord,'nodis':nodis,'s':s,
	})
	return HttpResponse(t.render(c))
##########################
#--------------------
def category(request):
	text=pr=ml1=body=dl=s=resultsets=None
	norecord=tmp=s_rows=s_field=s_sort=s_field=lists=""
	nodis=False
	bod=facet=True
	
	s_field ="*:*"

	if escape(request.GET["se"])=='3':
		f_field ="ml1"
		s="Location"
		#s_sort = "soc asc"
	elif escape(request.GET["se"])=='2':
		f_field ="ml2"
		s="Library/Institution"
		#sort = s_sort
	else:
		f_field ="pr"
		s="Medieval Library"
		#sort = s_sort
	
	#s_rows=Book.objects.count()

	s_sort="pr asc,ml1 asc,ml2 asc,sm1 asc,sm2 asc,ev asc,soc asc,dt asc,pm asc,mc asc,uk asc"
        
	s_rows=-1
	
	s_para={'q':'*:*',
                'wt':s_wt,
                'start':0, 
                'rows':s_rows,
                'sort':s_sort}
	if facet:
	    s_para['facet.mincount']='1'
	    s_para['facet']='on'
	    s_para['facet.limit']='-1'
	    #s_para['facet.field']=f_field 
	    s_para['facet.field']=["pr","ml1","ml2"]
	r=MLGBsolr()
	r.solrresults(s_para,Facet=facet)
	h1_tag_e = '</ul></li>\n'
	h2_tag_e = '</ul></li></ul></li>\n'
      
	if r.connstatus and r.s_result:
		resultsets= r.s_result.get('facet')
		norecord= r.s_result.get('numFound')
		

	nodis=True

	if escape(request.GET["se"])=='3':
		lists= resultsets["ml1"]
	elif escape(request.GET["se"])=='2':
		lists= resultsets["ml2"]
	else:	
	    lists= resultsets["pr"]
	t = loader.get_template('mlgb/category.html')

	#lists1= resultsets["pr"]
	#lists2= resultsets["ml1"]
	#lists3= resultsets["ml2"] 
	p1=p2=p3=p=[]
	param={}
	j=0
	for i in (lists):
		j +=1
		
		if j%2==0:
			param['v']=i
			p.append(param)
			param={}
		else:param['k']=i
	#j=0
	#param={}
	#for i in (lists2):
		#j +=1
		
		#if j%2==0:
			#param['v']=i
			#p2.append(param)
			#param={}
		#else:param['k']=i	
		
	#j=0
	#param={}
	#for i in (lists3):
		#j +=1
		
		#if j%2==0:
			#param['v']=i
			#p3.append(param)
			#param={}
		#else:param['k']=i
	#for i in p:
		#lists += '<tr> <td>%s</td><td>%s</td></tr>'  % (i['k'],i['v'])
			
	c = Context({
	    'lists': p,'p1':p1,'p2':p2,'p3':p3, 'no':norecord,'nodis':nodis,'s':s,
	})
	return HttpResponse(t.render(c))
