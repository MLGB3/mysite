  
from django.db import transaction

@transaction.commit_manually
def viewfunc(request):

    a.save()
    # open transaction now contains a.save()
    sid = transaction.savepoint()
  
    b.save()
    # open transaction now contains a.save() and b.save()
  
    if want_to_keep_b:
        transaction.savepoint_commit(sid)
        # open transaction still contains a.save() and b.save()
    else:
        transaction.savepoint_rollback(sid)
        # open transaction now contains only a.save()
  
    transaction.commit()
