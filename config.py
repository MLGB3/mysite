
from mysite.books.models import Book

solr_host='localhost:8180'
solr_base='/solr'
solr_uname='solradmin'
solr_pswd='blessing'
solr_commit='false'


#========== settings in following section do not currently (Feb 2014) seem to be used anywhere ========== 
solr_qa = '[* TO *]'

solr_fields = "id,pr,ml1,ml2,ms1,ms2,ev,evn,soc,dt,pm,mc,uk,nt"

solr_fieldsA = ["id","pr","ml1","ml2","ms1","ms2","ev","evn","soc","dt","pm","mc","uk","nt"]

solr_label = {
    "id":"ID",
    "pr":"Provenance",
    "ml1":"place",
    "ml2":"library",
    "sm1":"Shelfmark1",
    "sm2":"Shelfmark2",
    "ev":"Evidence", 
    "evn":"Evidence notes", 
    "soc":"Suggestion of the contents",
    "dt":"Date",
    "pm":"PressMark",
    "mc":"Medieval Catalogue",
    "uk":"Unknown",
    "nt":"Notes"
}
s_sort="pr asc,ml1 asc,ml2 asc,sm1 asc,sm2 asc,ev asc,soc asc,dt asc,pm asc,mc asc,uk asc"
#================= end of section that does not currently seem to be used anywhere =====================

# The following line IS used. It sets the 'writer' type for Solr output to JSON.
s_wt="json"

s_rows=Book.objects.count()


