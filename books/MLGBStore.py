import os,sys
from mysite.books.models import *
import rdflib
from rdflib.Graph import ConjunctiveGraph
from rdflib import plugin
from rdflib.store import Store, NO_STORE, VALID_STORE
from rdflib import Namespace
from rdflib import Literal
from rdflib import URIRef
from rdflib.store.FOPLRelationalModel.QuadSlot import *
from config import *

def OpenGraph(storeType=defaultStoreType, configStr=defaultConfigString, graphUri=defaultGraphUri, storeName=defaultStoreName):   
    store = plugin.get(storeType, Store)(storeName,debug=False)
    try:
        store.open(configStr, False)
    except Exception, e:
        if e.args[0] == 1050:
            store.open(configStr, False)
        else:
            print "Exception", str(e)
            sys.exit(1)
    graph = ConjunctiveGraph(store, identifier = URIRef(graphUri))
    return graph
sg=OpenGraph()
Modern_location_1 = Modern_location_1.objects.all().order_by('Modern_location_1')
Modern_location_2 = Modern_location_2.objects.all().order_by('Modern_location_2')
book = book.objects.all().order_by('provenance')
#for e in Modern_location_1:
    #print e.Modern_location_1

###################
#sg.bind("mlgb", "http://rdf.yangx/mlgb/")
#sg.bind("dc", "http://http://purl.org/dc/elements/1.1/")
#sg.bind("rdfs",  "http://www.w3.org/2000/01/rdf-schema#")
#sg.bind("xsd","http://www.w3.org/2001/XMLSchema#")
#sg.bind("owl","http://www.w3.org/2002/07/owl#")

#rdf    'http://www.w3.org/1999/02/22-rdf-syntax-ns#'>
    #<!ENTITY rdfs   'http://www.w3.org/2000/01/rdf-schema#'>
    #<!ENTITY xsd    'http://www.w3.org/2001/XMLSchema#'>
    #<!ENTITY owl   'http://www.w3.org/2002/07/owl#'>
    #<!ENTITY mlgb  'http://mlgb.xyang/media/rdf/mlgb'>
#########################
#mlgb_ns = Namespace("http://rdf.yangx/mlgb/")

#dc = Namespace("http://http://purl.org/dc/elements/1.1/")

#sg.bind("foaf", "http://xmlns.com/foaf/0.1/")


#sg.add((URIRef('http://www.google.com/'), dc['author'],        
        #Literal('Google home page',datatype="&xsd;string")))
#sg.add((URIRef('http://wikipedia.org/'), mlgb_ns['title'],    
        #Literal('Wikipedia home page'))) 
#Literal('2006-01-01',datatype=_XSD_NS.date)
sg.commit()
print sg.serialize()