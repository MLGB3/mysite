from mysite.books.solr import *
import simplejson
from config import *

class Solrjson():

    def __init__(self, solrurl=solr_host, solrbase=solr_base, uname=solr_uname, pswd=solr_pswd):          
        self.s = SolrConnection(host=solrurl, solrBase=solrbase, username=uname, password=pswd, persistent=True)
        self.response = None
        self.loaded = False
        self.response_dict = {}

    def search_query(self, sterm, format=output_format, flds=output_flds):
        if flds:
            #self.fields = flds.split(',')
            self.fields = flds
        else:
            self.fields = 'ml1'

        self.search_params = {'q':sterm, 
                              'start':0, 
                              'rows':150, 
                              'fl':self.fields}
        #self.search_params={'q':sterm}
        if format.lower()=='json':self.search_params['wt']='json'

        self.response = self.s.search(self.search_params)
        return

    def parse_response(self):
        if not self.response:
            self.loaded = False
            return False

        try:
            self.parsed_results = simplejson.loads(self.response)
            self.loaded = True
            return True
        except:
            self.loaded = False
            return False

    def create_dict(self):
        self.parse_response()

        if not self.loaded:
            return False

        numFound = self.parsed_results['response'].get('numFound',None)

        search_params = self.parsed_results['responseHeader'].get('params',None)
                
        query = search_params.get('q',None)
        if query:
            query = query.strip()

        start = search_params.get('start',None)
        if start and isinstance(start,list):
            start = start[-1]

        rows = search_params.get('rows',None)
                
        docs = self.parsed_results['response'].get('docs',None)

        names = []
        
        for doc in docs:
            if doc['ml1'] not in names: names.append(doc['ml1'])
            #for i in xrange(0,len(doc['library'])):
                #if 'None' not in doc['f_library'][i]: 
                    
            #if ",".join(doc['f_library']).replace('None','') not in names: names.append(",".join(doc['f_library']).replace('None',''))
        self.response_dict = {'numFound':numFound, 
                              'search_params':search_params, 
                              'query':query,
                              'start':start,
                              'rows':rows,
                              'docs':docs,
                              'names':names
                             }
        return

    def json_encode(self, py_ds):
        json_ds = simplejson.JSONEncoder().encode(py_ds)
        return json_ds       

