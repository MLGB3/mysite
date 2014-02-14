from urllib2 import *
import simplejson
from solr import SolrConnection
from config import *

class MLGBsolr:
    def __init__(self):
        self.s_result   = ()
        self.conn       = None
        self.connstatus = False
        self.req        = None

    def solrconn( self, core = 'books' ):
        try:
            solr_base_and_core = "%s/%s" % (solr_base, core)

            self.conn = SolrConnection( host=solr_host, solrBase=solr_base_and_core, \
                                        username=solr_uname, password=solr_pswd )
            self.connstatus=True
            return True
        except:
            #print "solr connection error!"
            return False
        
    def solrquery( self, para ):
        if self.solrconn():
            try:
                self.search = self.conn.search( para )
                self.connstatus=True
                return True
            except:
                #print "solr query failed!"
                return False
            
    def solrresults( self, para, Facet = False ):
        if self.solrquery( para ):
            rsp = simplejson.loads( self.search )

            s_numFound = rsp[ 'response' ].get( 'numFound', None )
            s_docs     = rsp[ 'response' ].get( 'docs', None )
            s_params   = rsp[ 'responseHeader' ].get( 'params', None )
            s_rows  = s_params.get( 'rows',  None )
            s_start = s_params.get( 'start', None )
            s_q     = s_params.get( 'q',     None )
            if Facet :
                s_facet_fields=rsp['facet_counts'].get( 'facet_fields', None )
         
            self.s_result = {'numFound'     : s_numFound, 
                             'search_params': s_params, 
                             'query'        : s_q,
                             'start'        : s_start,
                             'rows'         : s_rows,
                             'docs'         : s_docs
                            }
            if Facet :
                self.s_result['facet'] = s_facet_fields

            def __unicode__(self):
                return self.s_result
        
