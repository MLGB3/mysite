from MLGBsolr import *
from config import *
from urllib import quote
from xml.etree import ElementTree as et
from elementtree.SimpleXMLWriter import XMLWriter
from solr import SolrConnection


#select/?q=-dt:s*
#select/?q=oxford bod* pe* barl*
s_base="http://localhost:8080/solr/"

s_select="select"
s_field="?q=*:%s" % "*"
s_wt="&wt=json"

s_row="&rows=200"
s_sort="pr asc,ml1 asc,ml2 asc,sm1 asc,sm2 asc,ev asc,soc asc,dt asc,pm asc,mc asc,uk asc,nt asc"
#s_sort=""
#request='%s%s%s%s%s%s' % (s_base,s_select,s_field,s_wt ,s_row,s_sort)
request=quote('%s%s%s') % (s_field,s_wt,s_row)



#solr_host='localhost:8080'
#solr_base='/solr'
#solr_uname='solradmin'
#solr_pswd='blessing'

s_field="%s" % "oxf"
s_wt="json"
s_para={'q':s_field, 
        'wt':s_wt,
        'start':0, 
        'rows':150, 
        'sort':s_sort}

#print request
r=MLGBsolr()

r.solrresults(s_para)

#r = SolrConnection(host=solr_host, solrBase=solr_base, username=solr_uname, password=solr_pswd)
#resultsets_doc=r.search(s_para)
#resultsets=resultsets_doc.get('docs')
h1_tag='<span class="head1">'
h2_tag='<span class="head2">'
d_tag='<span class="detail">'
e_tag='</span>'
if r.connstatus:
    resultsets= r.s_result.get('docs')
    norecord= r.s_result.get('numFound')
    text=h1=h2=d=""
    for i in xrange(0, len(resultsets)):
        
        #for j in xrange(0,len(solr_fieldsA)):
            
            #fname=solr_fieldsA[j]
            #item =  resultsets[i]["%s" % fname]
            #text=""
            pr=resultsets[i]['pr']
            ml1=resultsets[i]['ml1']
            
            if h1<>pr:
                h1=pr
                h2=""
                text += "".join("%s%s%s%s") % (h1_tag,pr,e_tag,"\n")
            if h2<>ml1:
                h2=ml1
                text += "".join("%s%s%s%s") % (h2_tag,ml1,e_tag,"\n")
            ml2=resultsets[i]['ml2']
            if resultsets[i]['sm1']:sm1=resultsets[i]['sm1'].strip('"')
            else: sm1=""
            if resultsets[i]['sm2']:sm2=resultsets[i]['sm2'].strip('"')
            else: sm2=""
            if resultsets[i]['ev']:ev=resultsets[i]['ev'].strip('"')
            else: ev=""
            soc=resultsets[i]['soc'].strip('"')
            if resultsets[i]['dt']: dt=resultsets[i]['dt'].strip('"')
            else: dt=""
            if resultsets[i]['pm']:pm=resultsets[i]['pm'].strip('"')
            else: pm=""
            if resultsets[i]['mc']:mc=resultsets[i]['mc'].strip('"')
            else: mc=""
            if resultsets[i]['uk']:uk=resultsets[i]['uk'].strip('"')
            else: uk=""
            if resultsets[i]['nt']:nt=resultsets[i]['nt'].strip('"')
            else: nt=""

            body='%s  %s  %s  %s  %s  %s  %s  %s  %s  %s' % (ml2,sm1,sm2,ev,soc,dt,pm,mc,uk,nt)
            text += "".join("%s%s%s%s") % (d_tag,body,e_tag,"\n")
    
            
    print text